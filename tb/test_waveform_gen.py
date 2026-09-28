"""Tests for rtl/waveform_gen.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `waveform_gen`
Model:  model/waveform_gen.py: sample(phase, wave_sel, recip)
Run:    python3 sim/run.py waveform_gen

Assumption-breaking case: Switching wave_sel mid-stream: every select path has the same latency, so no slot is misaligned.

Every test below raises NotImplementedError until written. The module stays
out of the regression until its status in sim/modules.py is set to "active".
Write assert messages as key=value pairs (docs/verification.md).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

CLK_PERIOD_NS = 20            # 50 MHz
from synthtb.audio import measure_frequency, sfdr_db


@cocotb.test()
async def test_each_wave_bit_exact(dut):
    """Sine, saw and square match the model for a sweep of phases (triangle: tier 3)."""
    # TODO(you): write it
    raise NotImplementedError("test_each_wave_bit_exact: not written yet")


@cocotb.test()
async def test_polyblep_reduces_aliasing(dut):
    """TIER 3 (skip until PolyBLEP): a high-note saw with PolyBLEP has more SFDR than naive."""
    # TODO(you): generate a long capture at e.g. 5 kHz; compare sfdr_db of the RTL output with the naive model
    raise NotImplementedError("test_polyblep_reduces_aliasing: not written yet")


@cocotb.test()
async def test_select_switch_alignment(dut):
    """Changing wave_sel never misaligns voice and data."""
    # TODO(you): write it
    raise NotImplementedError("test_select_switch_alignment: not written yet")
