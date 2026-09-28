#!/usr/bin/env python3
"""Regression: lint and test every active module at every config.

Usage:
    python sim/regress.py [-m MODULE ...] [--seed N] [--repeat N] [--lint-only]

  -m, --module M   limit to these modules (repeatable; default: all active)
  --seed N         fixed RANDOM_SEED for every run (default: a fresh seed each)
  --repeat N       run each config N times with different seeds (default 1)
  --lint-only      Verilator -Wall lint only, no simulation
  --timeout S      per-run timeout, passed to run.py (default 600)

Modules and configs come from sim/modules.py. Each run is a separate
`sim/run.py` process, so one crash cannot take the regression down.

Prints a table, then one machine-readable line:

    SYNTH_REGRESSION {"status": "PASS"|"FAIL", "runs": [...], "planned": [...],
                      "optional": [...]}

and writes the same object to sim/results/regression.json. Each entry in
"runs" is a run.py summary (see docs/verification.md) plus its lint result.
Exit code: 0 if every lint and run passed, 1 otherwise.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "sim" / "results"
sys.path.insert(0, str(ROOT / "sim"))
from modules import MODULES  # noqa: E402
from run import to_verilog  # noqa: E402

VERILATOR = Path(sys.executable).parent / "verilator"


def lint(name: str, params: dict) -> dict:
    spec = MODULES[name]
    cmd = [str(VERILATOR if VERILATOR.exists() else "verilator"),
           "--lint-only", "-Wall", "--top-module", name]
    cmd += [f"-G{k}={to_verilog(v)}" for k, v in params.items()]
    cmd += [str(ROOT / s) for s in spec.sources]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    messages = [l for l in proc.stderr.splitlines() if l.startswith("%")]
    return {"status": "PASS" if proc.returncode == 0 and not messages else "FAIL",
            "messages": messages[:20]}


def simulate(name: str, config: str, seed: int | None, timeout: float) -> dict:
    cmd = [sys.executable, str(ROOT / "sim" / "run.py"), name,
           "--config", config, "--no-waves", "--timeout", str(timeout)]
    if seed is not None:
        cmd += ["--seed", str(seed)]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    for line in reversed(proc.stdout.splitlines()):
        if line.startswith("SYNTH_SUMMARY "):
            return json.loads(line.removeprefix("SYNTH_SUMMARY "))
    tail = (proc.stdout + proc.stderr).splitlines()[-10:]
    return {"module": name, "config": config, "status": "ERROR",
            "error": "run.py produced no summary", "error_details": tail}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-m", "--module", action="append")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--lint-only", action="store_true")
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args()

    active = [n for n, m in MODULES.items() if m.status == "active"]
    planned = [n for n, m in MODULES.items() if m.status == "planned"]
    optional = [n for n, m in MODULES.items() if m.status == "optional"]
    names = args.module or active
    unknown = [n for n in names if n not in MODULES]
    if unknown:
        parser.error(f"unknown module(s): {', '.join(unknown)}")

    runs = []
    for name in names:
        spec = MODULES[name]
        for config, params in spec.configs.items():
            missing = [f for f in spec.requires.get(config, []) if not (ROOT / f).exists()]
            if missing:
                runs.append({"module": name, "config": config, "status": "SKIP",
                             "error": "required file missing", "error_details": missing})
                print(f"{name:20} {config:14} SKIP   missing {', '.join(missing)}", flush=True)
                continue
            lint_result = lint(name, params)
            for _ in range(1 if args.lint_only else args.repeat):
                if args.lint_only:
                    result = {"module": name, "config": config, "status": lint_result["status"]}
                else:
                    result = simulate(name, config, args.seed, args.timeout)
                    if lint_result["status"] == "FAIL" and result["status"] == "PASS":
                        result["status"] = "FAIL"
                result["lint"] = lint_result
                runs.append(result)
                detail = result.get("error") or (
                    f"{result.get('passed', 0)} passed, {result.get('failed', 0)} failed"
                    if not args.lint_only else "")
                if lint_result["status"] == "FAIL":
                    detail = f"lint: {lint_result['messages'][0] if lint_result['messages'] else 'failed'}; {detail}"
                seed = f"seed {result['seed']}" if result.get("seed") is not None else ""
                print(f"{name:20} {config:14} {result['status']:6} {detail}  {seed}", flush=True)

    ok = all(r["status"] in ("PASS", "SKIP") for r in runs)
    report = {
        "schema": 1,
        "status": "PASS" if ok else "FAIL",
        "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runs": runs,
        "planned": planned,
        "optional": optional,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "regression.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"\n{sum(r['status'] == 'PASS' for r in runs)} passed, "
          f"{sum(r['status'] in ('FAIL', 'ERROR') for r in runs)} failed, "
          f"{sum(r['status'] == 'SKIP' for r in runs)} skipped; "
          f"{len(planned)} modules planned, {len(optional)} optional")
    print(f"SYNTH_REGRESSION {json.dumps(report, sort_keys=True)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
