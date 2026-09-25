#!/usr/bin/env python3
"""Generic cocotb runner (Verilator backend).

Usage:
    python sim/run.py <toplevel> [test_module] [-p NAME=VALUE ...]

  <toplevel>     name of the Verilog module under rtl/ (also the file stem)
  [test_module]  cocotb test module under tb/ (default: test_<toplevel>)
  -p NAME=VALUE  override a Verilog parameter, e.g. -p WIDTH=24 (repeatable)

Builds with Verilator and runs the cocotb tests. Reference models under
model/ are importable from tests (e.g. `from phase_accumulator import ...`).
Waveforms are dumped to tb/dump.vcd; open with `surfer tb/dump.vcd`.
"""

import argparse
import sys
from pathlib import Path

from cocotb_tools.runner import get_runner

ROOT = Path(__file__).resolve().parent.parent
RTL = ROOT / "rtl"
TB = ROOT / "tb"
MODEL = ROOT / "model"


def parse_param(text: str) -> tuple[str, int]:
    name, sep, value = text.partition("=")
    if not sep or not name:
        raise argparse.ArgumentTypeError(f"expected NAME=VALUE, got {text!r}")
    return name, int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("toplevel")
    parser.add_argument("test_module", nargs="?")
    parser.add_argument("-p", "--param", type=parse_param, action="append", default=[])
    args = parser.parse_args()

    toplevel = args.toplevel
    test_module = args.test_module or f"test_{toplevel}"
    parameters = dict(args.param)

    sources = [RTL / f"{toplevel}.v"]
    build_dir = ROOT / "sim_build" / toplevel

    runner = get_runner("verilator")
    runner.build(
        sources=sources,
        hdl_toplevel=toplevel,
        build_dir=build_dir,
        parameters=parameters,
        always=True,
        waves=True,
        build_args=["-Wall"],
    )
    # the runner passes its own sys.path to the simulator's Python, so this
    # makes model/ importable from the tests
    sys.path.insert(0, str(MODEL))
    runner.test(
        hdl_toplevel=toplevel,
        test_module=test_module,
        test_dir=TB,
        waves=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
