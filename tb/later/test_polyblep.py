"""Tests for rtl/polyblep.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `polyblep`
Model:  model/polyblep.py: correction(t, recip) in the RTL's fixed-point formats
Run:    python3 sim/run.py polyblep

Assumption-breaking case: dt > 0.5 (highest notes): both correction regions overlap.

TIER 3 (optional). Parked in tb/later/: move this file to tb/ when starting
the module, and set its status to "active" in sim/modules.py.

Every test below raises NotImplementedError until written. The module stays
out of the regression until its status in sim/modules.py is set to "active".
Write assert messages as key=value pairs (docs/verification.md).
"""

import cocotb
import random
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

CLK_PERIOD_NS = 20            # 50 MHz


@cocotb.test()
async def test_regions(dut):
    """Zero outside the two regions; correct shape inside, bit-exact with the model."""
    # TODO(you): write it
    raise NotImplementedError("test_regions: not written yet")


@cocotb.test()
async def test_random(dut):
    """Random (t, recip) pairs against the model."""
    # TODO(you): write it
    raise NotImplementedError("test_random: not written yet")
