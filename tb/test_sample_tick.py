"""Tests for rtl/sample_tick.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `sample_tick`
Model:  model/sample_tick.py: tick_cycles(clk_hz, sample_hz, n) -> clock indices of the first n ticks
Run:    python3 sim/run.py sample_tick [--config exact_divide]

Assumption-breaking case: CLK_HZ not a multiple of SAMPLE_HZ: spacing alternates, and over many ticks the average must be exact (no drift).

Every test below raises NotImplementedError until written. The module stays
out of the regression until its status in sim/modules.py is set to "active".
Write assert messages as key=value pairs (docs/verification.md).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

CLK_PERIOD_NS = 20            # 50 MHz


@cocotb.test()
async def test_tick_times(dut):
    """Ticks occur exactly on the clocks the model predicts."""
    # TODO(you): count clocks after reset; record the index of every cycle where tick == 1
    # TODO(you): compare the first ~200 against the model
    raise NotImplementedError("test_tick_times: not written yet")


@cocotb.test()
async def test_no_drift(dut):
    """Average spacing over thousands of ticks equals CLK_HZ / SAMPLE_HZ."""
    # TODO(you): spacing must only ever be floor or ceil of the ratio
    # TODO(you): total clocks for N ticks within 1 clock of N * ratio
    raise NotImplementedError("test_no_drift: not written yet")


@cocotb.test()
async def test_single_cycle_pulse(dut):
    """tick is high for exactly one clock at a time."""
    # TODO(you): never two consecutive cycles with tick high
    raise NotImplementedError("test_single_cycle_pulse: not written yet")
