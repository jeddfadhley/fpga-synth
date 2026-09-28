"""Tests for rtl/envelope_exp.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `envelope_exp`
Model:  model/envelope_exp.py: level sequence for a gate/trig pattern per voice
Run:    python3 sim/run.py envelope_exp [--config one_voice]

Assumption-breaking case: Release must terminate (a pure exponential never reaches 0), which frees the voice.

Every test below raises NotImplementedError until written. The module stays
out of the regression until its status in sim/modules.py is set to "active".
Write assert messages as key=value pairs (docs/verification.md).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

CLK_PERIOD_NS = 20            # 50 MHz
from synthtb.stream import SlotMonitor


@cocotb.test()
async def test_adsr_shape(dut):
    """Attack, decay, sustain, release follow the model, sample by sample."""
    # TODO(you): write it
    raise NotImplementedError("test_adsr_shape: not written yet")


@cocotb.test()
async def test_release_terminates(dut):
    """Release reaches 0 and voice_active clears in bounded time."""
    # TODO(you): write it
    raise NotImplementedError("test_release_terminates: not written yet")


@cocotb.test()
async def test_retrigger_from_current_level(dut):
    """A trig toggle in release restarts the attack from the current level (no jump)."""
    # TODO(you): write it
    raise NotImplementedError("test_retrigger_from_current_level: not written yet")


@cocotb.test()
async def test_voices_independent(dut):
    """Voices with different gate patterns don't disturb each other."""
    # TODO(you): write it
    raise NotImplementedError("test_voices_independent: not written yet")
