# Hardware

## FPGA board (not yet bought)

| Board | Cost | Toolchain | Fit |
|---|---|---|---|
| **Tang Nano 9K** (Gowin GW1NR-9) | ~£15–20 | Gowin IDE, or open-source Yosys + nextpnr | 20 multipliers and 26 BSRAM blocks: enough for 16 voices plus the filter. Cheapest board that won't run out |
| iCE40 UP5K boards | ~£20–50 | fully open-source | 8 DSPs: fine for mono, tight for 16 voices with the SVF |
| Arty A7 (Artix-7) | ~£200+ | Vivado | What job specs name; more than needed |

The design stays vendor-neutral. `sim/synth.py --target xilinx` gives Artix-7
utilisation without owning the board, which is worth quoting alongside the
real board's numbers. Measured so far:

| Module | iCE40 | Gowin | Xilinx 7 |
|---|---|---|---|
| `sine_rom` (1024×16) | 4 × SB_RAM40_4K | 1 × SPX9 (BSRAM) | 1 × RAMB18E1 |
| `phase_accumulator` (32 bit) | 33 LUT4, 32 DFF, 31 carry | | |

## MIDI input from the Yamaha P-125

The P-125's MIDI is **USB-to-Host only** (no 5-pin DIN). It is a USB MIDI
*device*, so something has to act as USB host. Implementing a USB host in the
FPGA is its own project, so bridge it:

| Option | Parts | Pros | Cons |
|---|---|---|---|
| **A. PC or Pi bridge** (bring-up) | USB-serial adapter, 3.3 V TTL (FTDI/CP2102, ~£5) | No soldering. Can log, replay recorded MIDI files, and inject test sequences. `BAUD` can be raised to 115 200 | Needs the computer on |
| **B. USB-MIDI host box** (standalone) | Host-to-DIN adapter (~£30–60) + optocoupler input: 6N138 or H11L1, 220 Ω, 1N4148, pull-up to 3.3 V | Standalone instrument; standard MIDI electrical interface | Parts + a small circuit |
| C. Raspberry Pi Pico as USB host | Pico (TinyUSB host MIDI) → UART | Cheap, standalone | Firmware to write |

Recommendation: **A now, B for the demo.** The RTL is the same for both:
`midi_uart_rx` takes `BAUD` as a parameter.

For option A, the bridge script (`tools/midi_bridge.py`, to write) forwards
raw MIDI bytes from the P-125's USB port to the serial port unchanged,
including running status. That keeps the parser's job identical to DIN.

**Sustain:** plug the pedal into the P-125. It sends CC64 over MIDI.
**Active sensing (0xFE):** Yamaha instruments may send it about every 300 ms.
The parser ignores it; a timeout that silences all notes when it stops is a
possible extension.

## Audio output

| Option | Parts | Notes |
|---|---|---|
| 1-bit delta-sigma (first) | 1 kΩ + 10 nF RC (fc ≈ 16 kHz), 3.5 mm jack, DC-blocking cap | Nothing to buy; the output pin's supply noise limits quality |
| I²S DAC (later) | PCM5102A breakout (~£5–10) | Proper 16/24-bit audio; recommended for the demo recording |

Never drive headphones directly from an FPGA pin. Go through the filter into
a line input or an amplifier.
