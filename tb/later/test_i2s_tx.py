"""Tests for rtl/i2s_tx.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `i2s_tx`
Model:  none: decode the I2S waveform in the test and compare with the samples loaded
Run:    python3 sim/run.py i2s_tx

Assumption-breaking case: Most negative sample 0x8000...: MSB first, sign preserved.

TIER 3 (optional). Parked in tb/later/: move this file to tb/ when starting
the module, and set its status to "active" in sim/modules.py.

Every test below raises NotImplementedError until written. The module stays
out of the regression until its status in sim/modules.py is set to "active".
Write assert messages as key=value pairs (docs/verification.md).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

CLK_PERIOD_NS = 20            # 50 MHz


@cocotb.test()
async def test_frame_decode(dut):
    """Decoded left/right samples equal those loaded, MSB one BCLK after LRCLK."""
    # TODO(you): write it
    raise NotImplementedError("test_frame_decode: not written yet")


@cocotb.test()
async def test_bclk_rate(dut):
    """BCLK averages 64 * SAMPLE_HZ."""
    # TODO(you): write it
    raise NotImplementedError("test_bclk_rate: not written yet")
