"""Tests for rtl/midi_uart_rx.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `midi_uart_rx`
Model:  none needed: the bytes sent are the expected bytes
Run:    python3 sim/run.py midi_uart_rx [--config fast_bridge]

Assumption-breaking case: Sender baud off by +/-1% (MIDI tolerance); back-to-back bytes with no idle gap.

Every test below raises NotImplementedError until written. The module stays
out of the regression until its status in sim/modules.py is set to "active".
Write assert messages as key=value pairs (docs/verification.md).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

CLK_PERIOD_NS = 20            # 50 MHz
import random
from synthtb.midi import uart_send, start_uart_send


@cocotb.test()
async def test_single_bytes(dut):
    """Each of 0x00, 0xFF, 0x55, 0xAA and random bytes is received exactly."""
    # TODO(you): baud = int(dut.BAUD.value), so the same test runs at every config
    # TODO(you): collect byte_data on every byte_valid pulse; compare with what was sent
    raise NotImplementedError("test_single_bytes: not written yet")


@cocotb.test()
async def test_baud_tolerance(dut):
    """Receives correctly with the sender skewed +1% and -1%."""
    # TODO(you): uart_send(..., baud_error_ppm=+10000) and -10000, with no idle gap between bytes
    raise NotImplementedError("test_baud_tolerance: not written yet")


@cocotb.test()
async def test_framing_error(dut):
    """Stop bit held low -> framing_error pulse, byte dropped."""
    # TODO(you): hand-drive a byte whose stop bit is 0
    raise NotImplementedError("test_framing_error: not written yet")


@cocotb.test()
async def test_glitch_rejected(dut):
    """A low pulse shorter than half a bit on an idle line produces no byte."""
    # TODO(you): drive rx low for ~0.3 bit then high; expect no byte_valid
    raise NotImplementedError("test_glitch_rejected: not written yet")
