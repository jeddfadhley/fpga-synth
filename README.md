# FPGA Synthesiser

A MIDI-controlled polyphonic synthesiser written in Verilog, played from a
Yamaha P-125 digital piano. The goal is a working synth on an FPGA, with
every module verified against an independent Python reference model.

## Status

| Block | Status |
|---|---|
| Phase accumulator (NCO) | Done: RTL, model, tests |
| Sine wavetable ROM | Next |
| Audio output (sigma-delta) | Planned |
| MIDI input (UART RX + parser) | Planned |
| Note to phase-increment ROM | Planned |
| ADSR envelope | Planned |
| Polyphony (time-multiplexed voices + allocator) | Planned |

Target board not yet chosen. The design is kept vendor-neutral.

## Signal chain

```
MIDI in -> UART RX -> MIDI parser -> note-to-increment ROM
                                              |
                                          increment
                                              v
audio out <- ADSR <- sine ROM <- phase <- phase accumulator
```

## Verification

Each module has a self-checking cocotb testbench, run on Verilator.

- Expected values come from a Python model in `model/`, not from the RTL.
- Tests combine directed cases (reset, counting) with randomised stimulus
  checked every clock cycle.
- Tests read parameters such as `WIDTH` from the design, and are re-run at
  non-default values to catch hard-coded assumptions.

## Running the tests

Requires Verilator (5.x), Python 3, and cocotb 2.x.

```
python3 sim/run.py phase_accumulator             # default parameters
python3 sim/run.py phase_accumulator -p WIDTH=24 # override a parameter
```

Waveforms are written to `tb/dump.vcd` and can be viewed with
[Surfer](https://surfer-project.org) or GTKWave.

## Layout

```
rtl/     Verilog sources
tb/      cocotb testbenches
model/   Python reference models
sim/     simulation runner
docs/    design notes
```

## Tools

AI tools were used for testbench scaffolding, the simulation runner, and code
review. All RTL was written by me.
