"""Tests for rtl/voice_allocator.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `voice_allocator`
Model:  model/voice_allocator.py: apply(events, num_voices, voice_active) -> voice table after each event
Run:    python3 sim/run.py voice_allocator [--config one_voice]

Assumption-breaking case: NUM_VOICES=1 (every note-on steals); note-off for a note never pressed; the same note twice.

Every test below raises NotImplementedError until written. The module stays
out of the regression until its status in sim/modules.py is set to "active".
Write assert messages as key=value pairs (docs/verification.md).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

CLK_PERIOD_NS = 20            # 50 MHz
import random


@cocotb.test()
async def test_note_on_off(dut):
    """Note-on takes a free voice; note-off clears its gate."""
    # TODO(you): write it
    raise NotImplementedError("test_note_on_off: not written yet")


@cocotb.test()
async def test_retrigger_same_note(dut):
    """A second note-on for a held note reuses its voice and toggles trig."""
    # TODO(you): write it
    raise NotImplementedError("test_retrigger_same_note: not written yet")


@cocotb.test()
async def test_stealing(dut):
    """N+1 notes: the oldest released voice is stolen, else the oldest held."""
    # TODO(you): drive voice_active to mark which voices are still releasing
    raise NotImplementedError("test_stealing: not written yet")


@cocotb.test()
async def test_sustain(dut):
    """Pedal down: note-off keeps gate; pedal up releases all sustained voices."""
    # TODO(you): write it
    raise NotImplementedError("test_sustain: not written yet")


@cocotb.test()
async def test_random_events(dut):
    """Random event streams against the model, table compared after each event."""
    # TODO(you): write it
    raise NotImplementedError("test_random_events: not written yet")
