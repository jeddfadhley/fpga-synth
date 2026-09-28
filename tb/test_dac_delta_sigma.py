"""Tests for rtl/dac_delta_sigma.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `dac_delta_sigma`
Model:  model/dac_delta_sigma.py (optional): bitstream, or check only the mean
Run:    python3 sim/run.py dac_delta_sigma

Assumption-breaking case: Input at +/-full scale: second-order loop must stay stable (or the input is limited, as specified).

Every test below raises NotImplementedError until written. The module stays
out of the regression until its status in sim/modules.py is set to "active".
Write assert messages as key=value pairs (docs/verification.md).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

CLK_PERIOD_NS = 20            # 50 MHz


@cocotb.test()
async def test_dc_mean(dut):
    """Mean of dac_out over a window tracks a DC input (several levels)."""
    # TODO(you): write it
    raise NotImplementedError("test_dc_mean: not written yet")


@cocotb.test()
async def test_sine_through_filter(dut):
    """A sine input, low-pass filtered in Python, has the right pitch."""
    # TODO(you): capture dac_out, filter + decimate with numpy, measure_frequency
    raise NotImplementedError("test_sine_through_filter: not written yet")


@cocotb.test()
async def test_full_scale_stable(dut):
    """Full-scale input: integrators stay bounded."""
    # TODO(you): write it
    raise NotImplementedError("test_full_scale_stable: not written yet")
