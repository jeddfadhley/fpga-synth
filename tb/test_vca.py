"""Tests for rtl/vca.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `vca`
Model:  model/vca.py: out(sample, level) with the RTL's rounding
Run:    python3 sim/run.py vca

Assumption-breaking case: Most negative sample times full-scale level (the signed x unsigned trap).

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
async def test_corners(dut):
    """Corners: +/-full scale x 0, x max level."""
    # TODO(you): write it
    raise NotImplementedError("test_corners: not written yet")


@cocotb.test()
async def test_random(dut):
    """Random pairs against the model, latency-checked."""
    # TODO(you): write it
    raise NotImplementedError("test_random: not written yet")
