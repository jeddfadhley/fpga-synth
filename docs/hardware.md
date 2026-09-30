# Hardware

## Board: Digilent Basys 3

Artix-7 `xc7a35tcpg236-1`, borrowed from the uni tech hub. 100 MHz oscillator
on W5.

## Signal chain

```
Keystation Mini 32 / P-125 --USB--> Mac (tools/midi_bridge.py: mido -> pyserial)
  --USB-UART (115200)--> Basys 3 [UART RX -> MIDI parser -> voices -> mixer -> I2S TX]
  --Pmod JA--> MAX98357A I2S class-D amp --> passive speaker (4–8 Ω)
```

Both keyboards are USB MIDI devices, so the Mac acts as USB host and forwards
raw MIDI bytes over the board's USB-UART. The RTL doesn't know which keyboard
is connected. The P-125's sustain pedal arrives as CC64 over the same path.

## Pins

Checked against Digilent's `Basys-3-Master.xdc`.

| Signal | Basys 3 pin | Notes |
|---|---|---|
| `clk` | W5 | 100 MHz; `create_clock -period 10.00` |
| `uart_rx` | B18 | USB-UART RX (`RsRx` in the master XDC) |
| `led[0]` | U16 | blinky / debug |
| `i2s_bclk` | JA1 = J1 | → amp BCLK |
| `i2s_lrclk` | JA2 = L2 | → amp LRC |
| `i2s_data` | JA3 = J2 | → amp DIN |
| GND / 3.3 V | JA pin 5 / 6 | → amp GND / Vin |

All pins use `IOSTANDARD LVCMOS33`. The XDC also needs
`set_property CONFIG_VOLTAGE 3.3 [current_design]` and
`set_property CFGBVS VCCO [current_design]`.

Amp GAIN and SD are left unconnected: 9 dB gain, (L+R)/2 mix (Adafruit board
defaults). The amp's header pins must be soldered before use.

## Clocking and sample rate

| Quantity | Value |
|---|---|
| System clock | 100 MHz |
| BCLK | 100 MHz / 32 = 3.125 MHz |
| Frame | 64 BCLKs (2 × 32-bit slots) |
| Sample rate fs | 3.125 MHz / 64 = **48 828.125 Hz** |
| Clocks per sample | **2048** (exact): the time-multiplexing budget |

The sample tick comes from the I²S frame (once per LRCLK period), so the
synth and the output can never drift. Every increment table uses this exact
fs: `increment = round(f × 2^32 / 48828.125)`.

## Toolchain

- **Simulation:** cocotb + Verilator on the Mac.
- **Build:** openXC7 via FPGAwars/tools-openxc7 (release 2026-09-24,
  darwin-arm64, plus the `xc7a35tcpg236` chip database), installed in
  `~/tools/openxc7`. Synthesis uses `yowasp-yosys`. Fallback: Vivado on the
  uni lab PCs.

  ```
  make bit TOP=<module>     # python sim/fpga.py build <module> -> build/<module>/<module>.bit
  ```

  Pins come from `constraints/basys3.xdc`; lines for ports the top module
  doesn't have are dropped automatically. The build prints cell counts and
  the maximum clock frequency (it must be at least 100 MHz). Do **not** `source
  ~/tools/openxc7/environment`: it overrides `VERILATOR_ROOT` and breaks the
  simulator; `sim/fpga.py` calls the tools by path instead.
- **Program:** `openFPGALoader` (Homebrew, v1.1.1).

  ```
  make prog TOP=<module>    # SRAM: lost at power-off
  make flash TOP=<module>   # flash: survives power-off
  ```

Checked 2026-09-30 with a throwaway counter design: the build takes about
5 s and reaches 298 MHz, and `clk` and `led[0]` land on W5 and U16. Programming
is untested until the board is connected.

## Still to buy / sort

- Keystation Mini 32
- Passive speaker, 4–8 Ω, about 3 W
- Male-to-female jumper wires
- The amp's header pins fitted (tech hub)

## Not used

- Teensy 4.1 + Audio Shield Rev D (borrowed; its USB host header can't be
  soldered).
- Possibly later: a Pi Pico H + OTG adapter as a standalone USB-MIDI host →
  UART into a Pmod pin, to remove the Mac from the chain.
