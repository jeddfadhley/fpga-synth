#!/usr/bin/env python3
"""Synthesise one module with Yosys and report resource use.

Usage:
    python sim/synth.py <toplevel> [--target generic|ice40|gowin|xilinx]
                                   [-c CONFIG] [-p NAME=VALUE ...]

  --target  generic (default): technology-independent cells, vendor-neutral
            ice40 / gowin / xilinx: that family's primitives, which shows
            whether memories map to block RAM and multipliers to DSPs
  -c, -p    as for run.py (configs come from sim/modules.py)

Runs yowasp-yosys (pip package; falls back to a `yosys` on PATH). Prints the
cell counts and one line for tools:

    SYNTH_UTIL {"module": ..., "target": ..., "cells": {...}, "total_cells": N}

and writes sim/results/<toplevel>/<config>/synth_<target>.json. This is
utilisation only: timing (Fmax) needs place-and-route (nextpnr), which comes
once a board is chosen.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "sim"))
from modules import MODULES, Module  # noqa: E402
from run import parse_param, to_verilog  # noqa: E402

SYNTH_CMD = {
    "generic": "synth -top {top}",
    "ice40": "synth_ice40 -top {top}",
    "gowin": "synth_gowin -top {top}",
    "xilinx": "synth_xilinx -top {top} -family xc7",
}


def yosys_exe() -> str:
    for name in ("yowasp-yosys", "yosys"):
        local = Path(sys.executable).parent / name
        if local.exists():
            return str(local)
        found = shutil.which(name)
        if found:
            return found
    sys.exit("no yosys found: pip install yowasp-yosys")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("toplevel")
    parser.add_argument("--target", choices=SYNTH_CMD, default="generic")
    parser.add_argument("-c", "--config", default="default")
    parser.add_argument("-p", "--param", type=parse_param, action="append", default=[])
    args = parser.parse_args()

    top = args.toplevel
    spec = MODULES.get(top, Module(sources=[f"rtl/{top}.v"]))
    overrides = dict(args.param)
    params = {**spec.configs.get(args.config, {}), **overrides}
    config = args.config if not overrides else f"{args.config}+custom"

    out_dir = ROOT / "sim" / "results" / top / config
    out_dir.mkdir(parents=True, exist_ok=True)
    # relative to ROOT: yowasp-yosys runs sandboxed with only the cwd visible
    stat_file = (out_dir / f"yosys_stat_{args.target}.json").relative_to(ROOT)

    script = [f"read_verilog -sv {Path(s)}" for s in spec.sources]
    script += [f"chparam -set {k} {to_verilog(v)} {top}" for k, v in params.items()]
    script += [SYNTH_CMD[args.target].format(top=top),
               f"tee -q -o {stat_file} stat -json"]

    proc = subprocess.run([yosys_exe(), "-q", "-p", "; ".join(script)],
                          capture_output=True, text=True, cwd=ROOT)
    if proc.returncode != 0:
        print(proc.stdout[-3000:], proc.stderr[-3000:], sep="\n")
        return 2

    stat = json.loads((ROOT / stat_file).read_text())
    cells = stat["design"]["num_cells_by_type"]
    record = {
        "schema": 1,
        "module": top,
        "config": config,
        "params": params,
        "target": args.target,
        "cells": cells,
        "total_cells": sum(cells.values()),
    }
    (out_dir / f"synth_{args.target}.json").write_text(json.dumps(record, indent=2) + "\n")

    for name, n in sorted(cells.items(), key=lambda kv: -kv[1]):
        print(f"  {n:6}  {name}")
    print(f"SYNTH_UTIL {json.dumps(record, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
