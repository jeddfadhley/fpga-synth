"""Tests for rtl/note_inc_rom.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `note_inc_rom`
Model:  model/note_inc_rom.py: increment(note, phase_w, fs), inc_recip(note, ...), write_hex(...)
Run:    python3 sim/run.py note_inc_rom

Assumption-breaking case: Note 127 (12.5 kHz, above fs/4) and note 0: the extremes of inc_recip's range.

Every test below raises NotImplementedError until written. The module stays
out of the regression until its status in sim/modules.py is set to "active".
Write assert messages as key=value pairs (docs/verification.md).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from synthtb.audio import note_hz, cents

CLK_PERIOD_NS = 20            # 50 MHz


@cocotb.test()
async def test_all_notes(dut):
    """All 128 increments and reciprocals match the model, 1 clock latency."""
    # TODO(you): write it
    raise NotImplementedError("test_all_notes: not written yet")


@cocotb.test()
async def test_pitch_accuracy(dut):
    """Every increment is within 0.01 cent of equal temperament."""
    # TODO(you): f = increment * FS / 2**PHASE_W; compare with note_hz(note) using cents()
    # TODO(you): this checks the model against first principles, not just the RTL against the model
    raise NotImplementedError("test_pitch_accuracy: not written yet")
