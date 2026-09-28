"""Tests for rtl/synth_core.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `synth_core`
Model:  all of the above, composed
Run:    python3 sim/run.py synth_core

Assumption-breaking case: More simultaneous notes than NUM_VOICES, with the sustain pedal down.

Every test below raises NotImplementedError until written. The module stays
out of the regression until its status in sim/modules.py is set to "active".
Write assert messages as key=value pairs (docs/verification.md).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

CLK_PERIOD_NS = 20            # 50 MHz
from synthtb.audio import check_pitch, note_hz
from synthtb.midi import encode, note_on, note_off, sustain, start_uart_send


@cocotb.test()
async def test_single_note_pitch(dut):
    """MIDI note 69 in -> mix_sample at 440 Hz within 1 cent."""
    # TODO(you): send over midi_rx with start_uart_send; capture mix_sample on mix_valid; check_pitch
    raise NotImplementedError("test_single_note_pitch: not written yet")


@cocotb.test()
async def test_chord(dut):
    """Three notes -> three spectral peaks at the right pitches."""
    # TODO(you): write it
    raise NotImplementedError("test_chord: not written yet")


@cocotb.test()
async def test_steal_and_sustain(dut):
    """NUM_VOICES+1 notes with pedal down: stealing policy holds; pedal up releases."""
    # TODO(you): write it
    raise NotImplementedError("test_steal_and_sustain: not written yet")


@cocotb.test()
async def test_release_frees_voice(dut):
    """After note-off and release, voice_active clears."""
    # TODO(you): write it
    raise NotImplementedError("test_release_frees_voice: not written yet")
