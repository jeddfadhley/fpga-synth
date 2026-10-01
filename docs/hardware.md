# Hardware

## Board: Digilent Basys 3

Artix-7 `xc7a35tcpg236-1`, borrowed from the uni tech hub. 100 MHz oscillator
on W5.

## Signal chain

```
Keystation Mini 32 / P-125 --USB--> Teensy 4.1 USB host (tools/teensy_midi_bridge/)
  --Serial1 TX, 31 250 baud--> Basys 3 Pmod JB1
  [UART RX -> MIDI parser -> voices -> mixer -> I2S TX]
  --Pmod JA--> MAX98357A I2S class-D amp --> passive speaker (4–8 Ω)
```

Both keyboards are USB MIDI devices, and neither has a 5-pin DIN socket, so
something has to be the USB host. The Basys 3's own USB host port (a PIC24)
only handles HID keyboards and mice. A borrowed Teensy 4.1 does it instead:
`USBHost_t36` powers and enumerates the keyboard, the sketch strips each
4-byte USB-MIDI packet down to its MIDI bytes and sends them out of `Serial1`.
No Mac is needed while playing. The RTL doesn't know which keyboard is
connected. The P-125's sustain pedal arrives as CC64 over the same path.

The link runs at 31 250 baud, the DIN MIDI rate, so the same `midi_uart_rx`
build would also accept a real MIDI input through an opto-isolator.

### Teensy 4.1 wiring

| Teensy 4.1 | Goes to | Notes |
|---|---|---|
| USB host header (5 pins, centre of the board by the micro-USB socket) | PJRC USB host cable → keyboard | Header must be fitted; red 5 V wire towards the micro-USB socket |
| Pin 1 (`Serial1` TX) | Basys 3 JB1 (A14) | 3.3 V logic on both sides; no level shifting |
| GND | Basys 3 JB pin 5 (GND) | Common ground is required |
| Micro-USB | USB charger, or the Mac when reprogramming | Also supplies the keyboard's 5 V |

Fallback: the Mac as host (`mido` → `pyserial`) into the Basys 3's USB-UART
on B18. That needs the `uart_rx` line in `basys3.xdc` moved back to B18.

## Pins

Checked against Digilent's `Basys-3-Master.xdc`.

| Signal | Basys 3 pin | Notes |
|---|---|---|
| `clk` | W5 | 100 MHz; `create_clock -period 10.00` |
| `uart_rx` | JB1 = A14 | from Teensy `Serial1` TX (B18 = USB-UART `RsRx` if the Mac bridge is used) |
| `led[0]` | U16 | blinky / debug |
| `rst` | U18 | centre button `btnC`, active-high |
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

Checked 2026-09-30: blinky builds in about 5 s (266 MHz max against the
100 MHz needed), `clk`, `rst` and `led[0]` land on W5, U18 and U16, and it
runs on the board: LED0 blinks at 1 Hz and btnC resets it.

## Still to buy / sort

- Teensy 4.1 (borrow) with the USB host header fitted, plus PJRC's USB host
  cable (5-pin header → USB-A socket)
- Passive speaker, 4–8 Ω, about 3 W
- Male-to-female jumper wires
- The amp's header pins fitted (tech hub)

## Not used

- Teensy 4.0 + Audio Shield Rev D (borrowed). The 4.0's USB host is only two
  SMD pads on the underside, so it can't easily act as the MIDI host.
- Alternatives considered for the USB host: a Pi Pico + OTG adapter; a
  USB-MIDI host box → DIN → opto-isolator; a pure-RTL USB host (adapting
  m1nl/usb_hid_host, weeks of work, possible stretch goal).
