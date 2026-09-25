#!/usr/bin/env python3
"""Generic cocotb runner (Icarus backend).

Usage:
    python sim/run.py <toplevel> [test_module]

  <toplevel>     name of the Verilog module under rtl/ (also the file stem)
  [test_module]  cocotb test module under tb/ (default: test_<toplevel>)

Builds with Icarus and runs the cocotb tests. Waveforms are dumped to
sim_build/<toplevel>/dump.fst for GTKWave.
"""

import sys
from pathlib import Path

from cocotb_tools.runner import get_runner

ROOT = Path(__file__).resolve().parent.parent
RTL = ROOT / "rtl"
TB = ROOT / "tb"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    toplevel = sys.argv[1]
    test_module = sys.argv[2] if len(sys.argv) > 2 else f"test_{toplevel}"

    sources = [RTL / f"{toplevel}.v"]
    build_dir = ROOT / "sim_build" / toplevel

    runner = get_runner("verilator")
    runner.build(
        sources=sources,
        hdl_toplevel=toplevel,
        build_dir=build_dir,
        always=True,
        waves=True,
        build_args=["-Wall"],
    )
    runner.test(
        hdl_toplevel=toplevel,
        test_module=test_module,
        test_dir=TB,
        waves=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
