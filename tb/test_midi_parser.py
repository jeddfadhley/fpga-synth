"""Tests for rtl/midi_parser.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `midi_parser`
Model:  model/midi_parser.py: parse(byte_stream, omni, channel) -> list of (type, channel, key, value)
Run:    python3 sim/run.py midi_parser

Assumption-breaking case: Real-time bytes (0xF8) inside a message, with running status: the event list must be unchanged.

Every test below raises NotImplementedError until written. The module stays
out of the regression until its status in sim/modules.py is set to "active".
Write assert messages as key=value pairs (docs/verification.md).
"""

import cocotb
import random
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from synthtb.midi import encode, note_on, note_off, sustain, insert_realtime

CLK_PERIOD_NS = 20            # 50 MHz


@cocotb.test()
async def test_basic_messages(dut):
    """Note-on, note-off, CC each give one correct event."""
    # TODO(you): drive byte_valid/byte_data directly (no UART needed); collect ev_* on ev_valid
    raise NotImplementedError("test_basic_messages: not written yet")


@cocotb.test()
async def test_velocity_zero_is_note_off(dut):
    """Note-on with velocity 0 emits NOTE_OFF."""
    # TODO(you): write it
    raise NotImplementedError("test_velocity_zero_is_note_off: not written yet")


@cocotb.test()
async def test_running_status(dut):
    """encode(..., running_status=True) streams give the same events as without."""
    # TODO(you): write it
    raise NotImplementedError("test_running_status: not written yet")


@cocotb.test()
async def test_realtime_interleaved(dut):
    """insert_realtime() anywhere in the stream changes nothing."""
    # TODO(you): write it
    raise NotImplementedError("test_realtime_interleaved: not written yet")


@cocotb.test()
async def test_sysex_and_unused(dut):
    """SysEx, program change, pitch bend and aftertouch produce no events and don't desync."""
    # TODO(you): write it
    raise NotImplementedError("test_sysex_and_unused: not written yet")


@cocotb.test()
async def test_random_stream(dut):
    """Random valid message streams against the model."""
    # TODO(you): log the seed via the assert message
    raise NotImplementedError("test_random_stream: not written yet")
