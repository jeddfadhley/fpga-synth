# FPGA Synthesiser

A MIDI-controlled polyphonic synthesiser written in Verilog, played from a
Yamaha P-125 digital piano. The goal is a working synth on an FPGA, with
every module verified against an independent Python reference model.

## Status

| Tier | Block | Status |
|---|---|---|
| 1 | Phase accumulator (mono reference) | Done: RTL, model, tests |
| 1 | Sine wavetable ROM | Done: RTL, model, tests (non-default width run pending) |
| 1 | RAM, sample tick, voice scheduler | Next |
| 1 | Per-voice oscillator, waveforms (sine, saw, square), mixer | Planned |
| 1 | Delta-sigma audio output | Planned |
| 1 | MIDI input (UART RX, parser, note-to-increment ROM) | Planned |
| 1 | Exponential ADSR, VCA | Planned |
| 2 | Polyphony: 8–16 voices, voice stealing, sustain pedal | Planned |
| 3 | PolyBLEP anti-aliasing, state-variable filter, I²S DAC | Optional |

Tier 1 is a playable mono synth, tier 2 adds polyphony, and tier 3 is
optional polish.

Target board not yet chosen; the design is kept vendor-neutral. Measured so far
(Yosys): the 1024×16 sine ROM maps to one block RAM on Gowin and Xilinx 7-series
and four on iCE40, with no logic.

## Architecture

One voice pipeline, time-multiplexed across up to 16 voices: at 50 MHz there
are about 1042 clocks per 48 kHz sample, and the pipeline handles one voice per
clock. Per-voice state (phase, envelope, filter) lives in small RAMs indexed by
voice number. Mono bring-up is the same RTL with `NUM_VOICES = 1`.

```
MIDI in -> UART RX -> parser -> voice allocator (voice table, stealing, sustain)
                                        | per-voice increment, gate, velocity
                                        v
48 kHz tick -> scheduler -> phase -> waveform -> envelope -> VCA -> filter -> mixer -> DAC
                            (slot per voice per sample: valid, voice, last, data)
```

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
shared test helpers, testbench skeletons, the design documents in `docs/`, and
code review. All RTL, reference models and test checks were written by me.
