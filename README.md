# FPGA Synthesiser

A MIDI-controlled polyphonic synthesiser written in Verilog, running on a
Digilent Basys 3 (Artix-7) and played from a USB MIDI keyboard. The goal is a
working synth on an FPGA, with every module verified against an independent
Python reference model.

## Status

| Tier | Block | Status |
|---|---|---|
| 1 | Blinky on the Basys 3 (toolchain check) | Done: runs on the board |
| 1 | Phase accumulator | Done: RTL, model, tests |
| 1 | Sine wavetable ROM | Done: RTL, model, tests (non-default width run pending) |
| 1 | I²S transmitter + sample tick, mono NCO: **first sound** | Next |
| 1 | Note-to-increment ROM, UART RX, MIDI parser, Mac MIDI bridge | Planned |
| 1 | Envelope, VCA | Planned |
| 2 | RAM for per-voice state | Done: RTL, tests |
| 2 | Polyphony: time-multiplexed voices, allocation, stealing, sustain; mixer | Planned |
| 3 | PolyBLEP, resonant filter, detune (stretch) | Optional |

Hardware: Digilent Basys 3 (Artix-7), MAX98357A I²S amplifier, played from a
Keystation Mini 32 or Yamaha P-125 through a small Mac-side MIDI bridge.

## Architecture

```
Keyboard --USB--> Mac (MIDI bridge) --UART--> Basys 3:
  UART RX -> MIDI parser -> voices -> mixer -> I2S TX --> MAX98357A amp --> speaker
```

The 100 MHz clock gives exactly 2048 clocks per sample (fs = 48 828.125 Hz, set
by the I²S frame). Polyphony uses one voice pipeline, time-multiplexed: it
handles one voice per clock, with per-voice state (phase, envelope) in small
RAMs indexed by voice number. A mono chain comes first, to get sound early.

Details: `docs/architecture.md` (design and trade-offs), `docs/interfaces.md`
(every module's ports, fixed-point formats and latency), `docs/hardware.md`
(board, MIDI from the USB-only P-125, audio output).

The module plan was inspired by
[UA3MQJ/fpga-synth](https://github.com/UA3MQJ/fpga-synth); no code from it is
used. `docs/architecture.md` lists what this design changes.

## Verification

Each module has a self-checking cocotb testbench, run on Verilator.

- Expected values come from a Python model in `model/`, not from the RTL.
- Tests combine directed cases (reset, counting) with randomised stimulus
  checked every clock cycle. Random seeds are logged and replayable.
- Tests read parameters from the design, and every module is re-run at
  non-default values to catch hard-coded assumptions.
- Timing is checked as well as values: the sine ROM test checks the output
  holds its old value until the clock edge after a new address, so a
  combinational read fails (confirmed against a combinational copy of the ROM).
- Audio outputs are checked by measurement: pitch to within cents via FFT and
  sine fitting, and spur level (SFDR). The 10-bit sine ROM measures 60.1 dB,
  matching the 6.02 dB-per-address-bit rule.
- Results are also emitted as structured JSON lines (`SYNTH_RESULT`,
  `SYNTH_SUMMARY`) with the failure message and a replay command, so a script
  can triage a regression. See `docs/verification.md`.

## Running the tests

Requires Verilator (5.x), Python 3 with cocotb 2.x, NumPy and SciPy, and
`yowasp-yosys` for synthesis reports.

```
python3 sim/run.py sine_rom                      # one module, default config
python3 sim/run.py phase_accumulator --config w24
python3 sim/run.py sine_rom --seed 1790588464    # replay a random run
python3 sim/regress.py                           # lint + every module, every config
python3 sim/synth.py sine_rom --target ice40     # resource use
```

`make help` lists the same as make targets. Waveforms are written to
`tb/dump.vcd` and can be viewed with [Surfer](https://surfer-project.org) or
GTKWave.

## Layout

```
rtl/          Verilog sources
rtl/mem/      generated ROM contents
tb/           cocotb testbenches
tb/synthtb/   shared test helpers (pitch/FFT, MIDI stimulus, slot monitor)
model/        Python reference models
sim/          runner, regression, synthesis scripts, module manifest
docs/         architecture, interfaces, verification, hardware
```

## Tools

AI tools were used for the simulation, regression and synthesis scripts, the
shared test helpers, the design documents in `docs/`, and
code review. All RTL, reference models and test checks were written by me.
