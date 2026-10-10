#!/usr/bin/env python3
"""Generic cocotb runner (Verilator backend).

Usage:
    python sim/run.py <toplevel> [test_module] [options]

  <toplevel>        module name; sources come from sim/modules.py
                    (falls back to rtl/<toplevel>.v if not listed there)
  [test_module]     cocotb test module under tb/ (default: test_<toplevel>)
  -c, --config NAME named parameter set from sim/modules.py (default: "default")
  -p NAME=VALUE     override a Verilog parameter, e.g. -p WIDTH=24 or
                    -p INIT_FILE=rtl/mem/sine_1024x16.hex (repeatable; applied
                    on top of the config)
  -t, --testcase T  run only this test (repeatable)
  -s, --seed N      RANDOM_SEED, to replay a failing randomised run
  --timeout S       kill the simulation after S seconds (default 600)
  --no-waves        skip the VCD dump (faster; regress.py uses this)

Builds with Verilator and runs the cocotb tests. Parameters are public, so a
test can read any integer parameter as int(dut.NAME.value). Reference models under
model/ are importable from tests, and so are the helpers in tb/synthtb/.
Waveforms are dumped to tb/dump.vcd; open with `surfer tb/dump.vcd`.

Output for tools: after the normal cocotb log, one line per test and one
summary line, each a JSON object behind a fixed prefix:

    SYNTH_RESULT  {"module": ..., "test": ..., "status": "PASS"|"FAIL"|"SKIP", ...}
    SYNTH_SUMMARY {"module": ..., "status": "PASS"|"FAIL"|"ERROR", "replay": ...}

Each failing test also gets one line in the triage format, carrying the
assert message (write asserts as key=value pairs, e.g. expected=.. got=..):

    FAIL test=<name> t=<sim time>ns module=<m> config=<c> seed=<n> <assert message>

A module whose manifest entry sets `tb` (a Verilog testbench) is built with
`verilator --binary --timing` and run directly instead; see run_verilog_tb().

The same data is written to sim/results/<toplevel>/<config>/summary.json.
Exit code: 0 all passed, 1 a test failed, 2 build error, crash or timeout.
The schema is described in docs/verification.md.
"""

import argparse
import json
import multiprocessing
import os
import re
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RTL = ROOT / "rtl"
TB = ROOT / "tb"
MODEL = ROOT / "model"
RESULTS = ROOT / "sim" / "results"

sys.path.insert(0, str(ROOT / "sim"))
from modules import MODULES, Module  # noqa: E402

SCHEMA_VERSION = 1

# Verilator prints these and then stops; cocotb does not always exit after them,
# so seeing one starts a short grace period before the simulation is killed.
FATAL_MARKERS = ("%Error", "Aborting...")
FATAL_GRACE_S = 3.0


def parse_value(text: str) -> int | str:
    try:
        return int(text, 0)
    except ValueError:
        return text


def parse_param(text: str) -> tuple[str, int | str]:
    name, sep, value = text.partition("=")
    if not sep or not name:
        raise argparse.ArgumentTypeError(f"expected NAME=VALUE, got {text!r}")
    return name, parse_value(value)


def to_verilog(value: int | str) -> int | str:
    """Integers pass through; strings become Verilog strings.

    String values that name an existing file are made absolute, because the
    simulator runs from tb/ and would otherwise resolve relative paths there.
    """
    if isinstance(value, int):
        return value
    path = Path(value) if Path(value).is_absolute() else ROOT / value
    if path.exists():
        value = str(path.resolve())
    return f'"{value}"'


def emit(prefix: str, record: dict) -> None:
    print(f"{prefix} {json.dumps(record, sort_keys=True)}", flush=True)


def _run_tests(runner, kwargs: dict) -> None:
    """Child process: own process group, so a hung simulator can be killed whole."""
    os.setsid()
    runner.test(**kwargs)


def run_tests_with_watchdog(runner, kwargs: dict, log_file: Path,
                            timeout_s: float) -> str | None:
    """Run the test phase; echo its log live. Returns an error string or None.

    `runner` is the one that did the build: its test() relies on state that
    build() set, so it is passed to the child rather than recreated there.
    """
    log_file.unlink(missing_ok=True)
    ctx = multiprocessing.get_context("spawn")
    proc = ctx.Process(target=_run_tests, args=(runner, kwargs))
    proc.start()

    start = time.monotonic()
    fatal_seen_at = None
    pos = 0
    error = None
    while True:
        proc.join(timeout=0.2)
        if log_file.exists():
            with open(log_file, errors="replace") as f:
                f.seek(pos)
                chunk = f.read()
                pos = f.tell()
            if chunk:
                sys.stdout.write(chunk)
                sys.stdout.flush()
                if fatal_seen_at is None and any(m in chunk for m in FATAL_MARKERS):
                    fatal_seen_at = time.monotonic()
        if not proc.is_alive():
            break
        now = time.monotonic()
        if fatal_seen_at is not None and now - fatal_seen_at > FATAL_GRACE_S:
            error = "simulator reported a fatal error and did not exit"
        elif now - start > timeout_s:
            error = f"timeout after {timeout_s:g} s"
        if error:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.join()
            break

    if error is None and proc.exitcode not in (0, None):
        error = f"test process exited with code {proc.exitcode}"
    return error


def fatal_lines(log_file: Path, limit: int = 5) -> list[str]:
    if not log_file.exists():
        return []
    lines = log_file.read_text(errors="replace").splitlines()
    return [l.strip() for l in lines if any(m in l for m in FATAL_MARKERS)][:limit]


def parse_results(results_xml: Path) -> tuple[list[dict], int | None]:
    """Read cocotb's JUnit XML into one record per test."""
    if not results_xml.exists():
        return [], None
    root = ET.parse(results_xml).getroot()
    seed = None
    for prop in root.iter("property"):
        if prop.get("name") == "random_seed":
            seed = int(prop.get("value"))
    tests = []
    for case in root.iter("testcase"):
        failure = case.find("failure")
        if failure is None:
            failure = case.find("error")
        skipped = case.find("skipped")
        if failure is not None:
            status = "FAIL"
            text = (failure.get("error_msg") or failure.get("message")
                    or (failure.text or "").strip())
            kind = failure.get("error_type")
            message = f"{kind}: {text}" if kind and text else (text or kind or None)
        elif skipped is not None:
            status = "SKIP"
            message = skipped.get("message")
        else:
            status = "PASS"
            message = None
        file = case.get("file")
        tests.append({
            "test": case.get("name"),
            "status": status,
            "message": message,
            "sim_time_ns": float(case.get("sim_time_ns", 0) or 0),
            "file": str(Path(file).relative_to(ROOT)) if file and file.startswith(str(ROOT)) else file,
            "line": int(case.get("lineno", 0) or 0),
        })
    return tests, seed


VERILATOR = Path(sys.executable).parent / "verilator"
VERILOG_FAIL = re.compile(r"^\s*(?:FAIL|fail)\b[\s:]*(.*)$")
VERILOG_TIME = re.compile(r"\bt=(\d+)")


def run_verilog_tb(spec: Module, params: dict, build_dir: Path, log_file: Path,
                   timeout_s: float) -> tuple[list[dict], str | None, list[str]]:
    """Build and run a plain Verilog testbench; returns (tests, error, details).

    The testbench is one test, named after its top module. Protocol:
      - each line starting "FAIL" (or "fail") is one failure; the rest of the
        line is its message, ideally key=value pairs ending expected=.. got=..
        and including t=<ns> so the triage line gets a time
      - the test passes only if the simulation reaches $finish, prints a line
        that is exactly "PASS", and prints no failure lines
      - $error/$fatal or a non-zero exit is an ERROR
    The DUT is linted with -Wall separately (regress.py); the testbench itself
    is built with warnings non-fatal, since it is not synthesised.
    """
    tb = ROOT / spec.tb
    top = tb.stem
    verilator = str(VERILATOR if VERILATOR.exists() else "verilator")
    cmd = [verilator, "--binary", "--timing", "-Wno-fatal", "-j", "0",
           "--top-module", top, "--Mdir", str(build_dir), "-o", top]
    cmd += [f"-G{k}={to_verilog(v)}" for k, v in params.items()]
    cmd += [str(ROOT / s) for s in spec.sources] + [str(tb)]
    build_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if proc.returncode != 0:
        errors = [l for l in proc.stderr.splitlines() if l.startswith("%Error")]
        return [], "build failed", errors[:10] or proc.stderr.splitlines()[-10:]

    try:
        proc = subprocess.run([str(build_dir / top)], capture_output=True, text=True,
                              cwd=TB, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return [], f"timeout after {timeout_s:g} s", []
    output = proc.stdout + proc.stderr
    log_file.write_text(output)
    sys.stdout.write(output)
    if proc.returncode != 0:
        return [], f"simulation exited with code {proc.returncode}", fatal_lines(log_file)

    lines = output.splitlines()
    fails = [m.group(1).strip() for l in lines if (m := VERILOG_FAIL.match(l))]
    test = {"test": top, "sim_time_ns": 0.0, "file": spec.tb, "line": 0}
    if fails:
        tests = []
        for msg in fails:
            t = VERILOG_TIME.search(msg)
            tests.append({**test, "status": "FAIL", "message": msg,
                          "sim_time_ns": float(t.group(1)) if t else 0.0})
        return tests, None, []
    if not any(l.strip() == "PASS" for l in lines):
        last = lines[-1].strip() if lines else ""
        return [{**test, "status": "FAIL",
                 "message": f"no PASS line printed; last_line={last!r}"}], None, []
    return [{**test, "status": "PASS", "message": None}], None, []


def replay_command(toplevel: str, test_module: str, config: str,
                   overrides: dict, seed: int | None) -> str:
    cmd = ["python3", "sim/run.py", toplevel]
    if test_module != f"test_{toplevel}":
        cmd.append(test_module)
    cmd += ["--config", config]
    cmd += [f"-p {k}={v}" for k, v in overrides.items()]
    if seed is not None:
        cmd += ["--seed", str(seed)]
    return " ".join(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("toplevel")
    parser.add_argument("test_module", nargs="?")
    parser.add_argument("-c", "--config", default="default")
    parser.add_argument("-p", "--param", type=parse_param, action="append", default=[])
    parser.add_argument("-t", "--testcase", action="append")
    parser.add_argument("-s", "--seed", type=int)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--no-waves", action="store_true")
    args = parser.parse_args()

    toplevel = args.toplevel
    spec = MODULES.get(toplevel, Module(sources=[f"rtl/{toplevel}.v"],
                                        configs={"default": {}}))
    test_module = args.test_module or (Path(spec.tb).stem if spec.tb else f"test_{toplevel}")
    if args.config not in spec.configs:
        parser.error(f"{toplevel} has no config {args.config!r}; "
                     f"known: {', '.join(spec.configs)}")

    overrides = dict(args.param)
    params = {**spec.configs[args.config], **overrides}
    config = args.config if not overrides else f"{args.config}+custom"
    out_dir = RESULTS / toplevel / config
    out_dir.mkdir(parents=True, exist_ok=True)

    base = {
        "schema": SCHEMA_VERSION,
        "module": toplevel,
        "test_module": test_module,
        "config": config,
        "params": params,
    }

    def finish(status: str, tests: list[dict], seed: int | None, error: str | None,
               details: list[str]) -> int:
        for t in tests:
            emit("SYNTH_RESULT", {**base, "seed": seed, **t})
        for t in tests:
            if t["status"] == "FAIL":
                msg = (t["message"] or "").removeprefix("AssertionError: ")
                print(f"FAIL test={t['test']} t={t['sim_time_ns']:g}ns module={toplevel} "
                      f"config={config} seed={seed} {msg}".rstrip(), flush=True)
        if status == "ERROR":
            print(f"ERROR module={toplevel} config={config} error={error!r}", flush=True)
        counts = {s: sum(t["status"] == s for t in tests) for s in ("PASS", "FAIL", "SKIP")}
        summary = {
            **base,
            "status": status,
            "seed": seed,
            "passed": counts["PASS"],
            "failed": counts["FAIL"],
            "skipped": counts["SKIP"],
            "error": error,
            "error_details": details,
            "replay": replay_command(toplevel, test_module, args.config, overrides, seed),
        }
        (out_dir / "summary.json").write_text(
            json.dumps({"summary": summary, "tests": tests}, indent=2, sort_keys=True) + "\n")
        emit("SYNTH_SUMMARY", summary)
        return {"PASS": 0, "FAIL": 1}.get(status, 2)

    missing = [s for s in spec.sources if not (ROOT / s).exists()]
    if spec.tb and not (ROOT / spec.tb).exists():
        missing.append(spec.tb)
    if missing:
        return finish("ERROR", [], None, "missing source files", missing)

    if spec.tb:
        tests, error, details = run_verilog_tb(
            spec, params, ROOT / "sim_build" / toplevel / config,
            out_dir / "sim.log", args.timeout)
        if error or not tests:
            return finish("ERROR", tests, None, error or "no test results", details)
        status = "FAIL" if any(t["status"] == "FAIL" for t in tests) else "PASS"
        return finish(status, tests, None, None, [])

    from cocotb_tools.runner import get_runner

    build_dir = ROOT / "sim_build" / toplevel / config
    runner = get_runner("verilator")
    try:
        runner.build(
            sources=[ROOT / s for s in spec.sources],
            hdl_toplevel=toplevel,
            build_dir=build_dir,
            parameters={k: to_verilog(v) for k, v in params.items()},
            always=True,
            waves=not args.no_waves,
            build_args=["-Wall", "--public-params"],
        )
    except Exception as exc:  # the runner raises on a failed Verilator build
        return finish("ERROR", [], None, "build failed", [str(exc)])

    results_xml = out_dir / "results.xml"
    results_xml.unlink(missing_ok=True)
    log_file = out_dir / "sim.log"
    # the child's sys.path is passed to the simulator's Python, so this makes
    # model/ importable from the tests (tb/ is added by cocotb as test_dir)
    sys.path.insert(0, str(MODEL))
    error = run_tests_with_watchdog(
        runner,
        {
            "hdl_toplevel": toplevel,
            "test_module": test_module,
            "test_dir": TB,
            "build_dir": build_dir,
            "testcase": args.testcase,
            "seed": args.seed,
            "waves": not args.no_waves,
            "results_xml": str(results_xml),
            "log_file": str(log_file),
        },
        log_file,
        args.timeout,
    )

    tests, seed = parse_results(results_xml)
    if seed is None:
        seed = args.seed
    if error or not tests:
        return finish("ERROR", tests, seed, error or "no test results written",
                      fatal_lines(log_file))
    status = "FAIL" if any(t["status"] == "FAIL" for t in tests) else "PASS"
    return finish(status, tests, seed, None, [])


if __name__ == "__main__":
    raise SystemExit(main())
