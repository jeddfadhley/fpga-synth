"""MIDI stimulus: message encoding and a bit-level UART driver.

Encoding follows the MIDI 1.0 wire format: a status byte (top bit set) then
data bytes (top bit clear). encode() can apply running status, which real
keyboards use, so the parser must handle it.

    stream = encode([note_on(0, 60, 100), note_on(0, 64, 90), note_off(0, 60)])
    await uart_send(dut.midi_rx, stream)
"""

import cocotb
from cocotb.triggers import Timer

MIDI_BAUD = 31_250

NOTE_OFF = 0x80
NOTE_ON = 0x90
CONTROL_CHANGE = 0xB0
CC_SUSTAIN = 64                 # value >= 64 means pedal down

# System real-time bytes: single byte, may appear between the bytes of any
# other message, and must not disturb running status.
TIMING_CLOCK = 0xF8
ACTIVE_SENSING = 0xFE
SYSEX_START = 0xF0
SYSEX_END = 0xF7


def _check(channel: int, *data: int) -> None:
    if not 0 <= channel <= 15:
        raise ValueError(f"channel {channel} out of range 0..15")
    for d in data:
        if not 0 <= d <= 127:
            raise ValueError(f"data byte {d} out of range 0..127")


def note_on(channel: int, note: int, velocity: int) -> bytes:
    _check(channel, note, velocity)
    return bytes([NOTE_ON | channel, note, velocity])


def note_off(channel: int, note: int, velocity: int = 64) -> bytes:
    _check(channel, note, velocity)
    return bytes([NOTE_OFF | channel, note, velocity])


def control_change(channel: int, controller: int, value: int) -> bytes:
    _check(channel, controller, value)
    return bytes([CONTROL_CHANGE | channel, controller, value])


def sustain(channel: int, down: bool) -> bytes:
    return control_change(channel, CC_SUSTAIN, 127 if down else 0)


def encode(messages: list[bytes], running_status: bool = True) -> bytes:
    """Concatenate messages, dropping repeated status bytes if running_status."""
    out = bytearray()
    last_status = None
    for msg in messages:
        status = msg[0]
        if running_status and status == last_status and status < 0xF0:
            out += msg[1:]
        else:
            out += msg
        if status < 0xF0:
            last_status = status
        elif status < 0xF8:        # system common cancels running status
            last_status = None
    return bytes(out)


def insert_realtime(stream: bytes, byte: int = TIMING_CLOCK, every: int = 2) -> bytes:
    """Put a real-time byte after every `every` bytes, including mid-message."""
    out = bytearray()
    for i, b in enumerate(stream):
        out.append(b)
        if (i + 1) % every == 0:
            out.append(byte)
    return bytes(out)


async def uart_send(pin, data: bytes, baud: float = MIDI_BAUD,
                    baud_error_ppm: float = 0.0, gap_bits: float = 0.0) -> None:
    """Drive bytes onto `pin` as 8N1 UART: idle high, start bit 0, eight data
    bits LSB first, stop bit 1.

    baud_error_ppm skews the sender's bit rate, to test the receiver's
    tolerance (MIDI allows +/-1%, i.e. 10000 ppm). gap_bits adds idle time
    between bytes.
    """
    bit_ps = round(1e12 / (baud * (1 + baud_error_ppm * 1e-6)))
    pin.value = 1
    for byte in data:
        bits = [0] + [(byte >> i) & 1 for i in range(8)] + [1]
        for bit in bits:
            pin.value = bit
            await Timer(bit_ps, unit="ps")
        if gap_bits:
            await Timer(round(bit_ps * gap_bits), unit="ps")


def start_uart_send(pin, data: bytes, **kwargs):
    """Send in the background; returns the task (await it to wait for the end)."""
    return cocotb.start_soon(uart_send(pin, data, **kwargs))
