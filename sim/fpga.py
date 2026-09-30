#!/usr/bin/env python3
"""Build a bitstream for the Basys 3 with openXC7, and program the board.

Usage:
    python sim/fpga.py build <top> [source.v ...]   # -> build/<top>/<top>.bit
    python sim/fpga.py prog  <top> [--flash]         # load it onto the board

  <top>      top-level module name. Sources default to sim/modules.py's list
             for <top>, else rtl/<top>.v.
  --flash    write to the board's flash (survives power-off) instead of SRAM

Steps (see docs/hardware.md):
  1. yowasp-yosys    synth_xilinx          Verilog -> netlist (JSON)
  2. nextpnr-xilinx  place and route       + constraints/basys3.xdc -> FASM
  3. fasm2frames     FASM -> frames
  4. xc7frames2bit   frames -> <top>.bit
  5. openFPGALoader  -b basys3             (prog only)

The openXC7 tools live in ~/tools/openxc7 (override with OPENXC7=<dir>).
constraints/basys3.xdc lists every board pin the project uses; lines for ports
the top module doesn't have are dropped, so one file serves every design.

Reports go to build/<top>/: yosys_stat.json (utilisation) and
nextpnr.log (timing: look for "Max frequency for clock").
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "sim"))
from modules import MODULES  # noqa: E402

PART = "xc7a35tcpg236-1"
XDC = ROOT / "constraints" / "basys3.xdc"
OPENXC7 = Path(os.environ.get("OPENXC7", Path.home() / "tools" / "openxc7"))
CHIPDB = OPENXC7 / "chipdb" / "xc7a35tcpg236.bin"
PRJXRAY_DB = OPENXC7 / "share" / "nextpnr" / "external" / "prjxray-db" / "artix7"


def tool(name: str) -> str:
    if name == "yosys":
        local = Path(sys.executable).parent / "yowasp-yosys"
        return str(local) if local.exists() else (shutil.which("yowasp-yosys") or "yosys")
    if name == "openFPGALoader":
        return shutil.which("openFPGALoader") or "openFPGALoader"
    return str(OPENXC7 / "bin" / name)


def run(step: str, cmd: list[str], log: Path | None = None) -> None:
    print(f"== {step}", flush=True)
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    if log:
        log.write_text(out)
    if proc.returncode != 0:
        print(out[-4000:])
        sys.exit(f"{step} failed (exit {proc.returncode})" + (f"; full log: {log}" if log else ""))


def top_ports(netlist: Path, top: str) -> set[str]:
    mod = json.loads(netlist.read_text())["modules"][top]
    return set(mod["ports"])


def filtered_xdc(ports: set[str], out: Path) -> None:
    """Keep constraint lines whose get_ports target is a port of the top
    (a bus bit like led[0] matches port led); keep lines with no get_ports."""
    kept = []
    for line in XDC.read_text().splitlines():
        m = re.search(r"get_ports\s+\{?\s*([A-Za-z_]\w*)", line)
        if m is None or m.group(1) in ports:
            kept.append(line)
    out.write_text("\n".join(kept) + "\n")


def build(top: str, sources: list[str]) -> Path:
    if not CHIPDB.exists():
        sys.exit(f"missing {CHIPDB}; install openXC7 (docs/hardware.md)")
    out = ROOT / "build" / top
    out.mkdir(parents=True, exist_ok=True)
    rel = lambda p: str(Path(p).resolve().relative_to(ROOT))  # yowasp sees only ROOT
    netlist, stat = out / f"{top}.json", out / "yosys_stat.json"

    script = [f"read_verilog -sv {rel(ROOT / s)}" for s in sources]
    script += [f"synth_xilinx -flatten -abc9 -arch xc7 -top {top}",
               f"tee -q -o {rel(stat)} stat -json",
               f"write_json {rel(netlist)}"]
    run("synthesis (yosys)", [tool("yosys"), "-q", "-p", "; ".join(script)], out / "yosys.log")

    xdc = out / "basys3.xdc"
    filtered_xdc(top_ports(netlist, top), xdc)
    fasm = out / f"{top}.fasm"
    run("place and route (nextpnr-xilinx)",
        [tool("nextpnr-xilinx"), "--chipdb", str(CHIPDB), "--xdc", str(xdc),
         "--json", str(netlist), "--fasm", str(fasm)], out / "nextpnr.log")

    frames = out / f"{top}.frames"
    run("frames (fasm2frames)",
        [tool("fasm2frames"), "--part", PART, "--db-root", str(PRJXRAY_DB),
         str(fasm), str(frames)])

    bit = out / f"{top}.bit"
    run("bitstream (xc7frames2bit)",
        [tool("xc7frames2bit"), "--part_file", str(PRJXRAY_DB / PART / "part.yaml"),
         "--part_name", PART, "--frm_file", str(frames), "--output_file", str(bit)])

    cells = json.loads(stat.read_text())["design"]["num_cells_by_type"]
    fmax = re.findall(r"Max frequency for clock\s+'?([^':]+)'?:\s*([\d.]+) MHz",
                      (out / "nextpnr.log").read_text())
    print(f"\nbitstream: {bit.relative_to(ROOT)}")
    print("cells:", ", ".join(f"{n} {k}" for k, n in sorted(cells.items(), key=lambda kv: -kv[1])))
    for clk, mhz in fmax[-1:]:
        print(f"max frequency ({clk.strip()}): {mhz} MHz  (needs 100)")
    return bit


def prog(top: str, flash: bool) -> None:
    bit = ROOT / "build" / top / f"{top}.bit"
    if not bit.exists():
        sys.exit(f"no {bit.relative_to(ROOT)}; run: python sim/fpga.py build {top}")
    cmd = [tool("openFPGALoader"), "-b", "basys3"] + (["-f"] if flash else []) + [str(bit)]
    print(" ".join(cmd), flush=True)
    sys.exit(subprocess.run(cmd).returncode)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["build", "prog"])
    parser.add_argument("top")
    parser.add_argument("sources", nargs="*")
    parser.add_argument("--flash", action="store_true")
    args = parser.parse_args()

    if args.action == "prog":
        prog(args.top, args.flash)
        return
    sources = args.sources or (MODULES[args.top].sources if args.top in MODULES
                               else [f"rtl/{args.top}.v"])
    missing = [s for s in sources if not (ROOT / s).exists()]
    if missing:
        sys.exit(f"missing sources: {', '.join(missing)}")
    build(args.top, sources)


if __name__ == "__main__":
    main()
