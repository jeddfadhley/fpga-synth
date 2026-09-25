# FPGA Synthesiser

MIDI-driven polyphonic synthesiser in Verilog RTL, played from a Yamaha P-125.
Portfolio project for ASIC/FPGA internship applications. Design intent and
conventions live in [CLAUDE.md](CLAUDE.md).

## Toolchain

| Role | Tool | Notes |
|------|------|-------|
| Simulator | **Verilator 5.052** | Installed via conda-forge into `radioconda`. Chosen over Icarus because Homebrew has no arm64 bottle for this macOS and the source build needs a newer Xcode CLT; conda-forge has no `iverilog` for osx-arm64 either. Verilator is 2-state, cycle-based, and industry-standard. |
| Testbenches | **cocotb 2.0.1** | Python testbenches. Same language as the reference models: the model produces expected values and the testbench checks the DUT against them. |
| Reference models | **Python** (NumPy/SciPy) | Under `model/`. |
| Waveform viewer | Surfer | Installed via Homebrew. Only for debugging — a passing run never depends on eyeballing waves. |

Python interpreter is the radioconda one: `/Users/jedd/radioconda/bin/python3`
(cocotb and Verilator live there). Verilator needs `radioconda/bin` on `PATH`.

> **Path must not contain spaces.** Verilator + GNU Make cannot build in a
> directory with a space in its path. This project lives at
> `~/IdeaProjects/FPGA_synth` for that reason.

## Layout

```
rtl/          Verilog sources (module per file, filename = module name)
tb/           cocotb testbenches (test_<module>.py)
model/        Python reference models
sim/          simulation runner
docs/         design notes, fixed-point formats, block diagrams
```

## Running a testbench

```sh
export PATH="/Users/jedd/radioconda/bin:$PATH"
python3 sim/run.py <module> [test_module]
# e.g. python3 sim/run.py counter
```

`sim/run.py` builds `rtl/<module>.v` with Verilator and runs the cocotb tests
in `tb/test_<module>.py`.

Plain-Verilog testbenches (`tb/<module>_tb.v`) run directly under Verilator:

```sh
mkdir -p sim_build/phase_accumulator_tb
verilator --binary --timing --trace --top-module phase_accumulator_tb \
    rtl/phase_accumulator.v tb/phase_accumulator_tb.v \
    --Mdir sim_build/phase_accumulator_tb -o sim
./sim_build/phase_accumulator_tb/sim          # prints PASS / FAIL
surfer phase_accumulator_tb.vcd               # view waveforms
```

## Status

- [x] Phase 0 — toolchain + verification flow proven (throwaway `counter` module
      passes a self-checking cocotb test against a Python model)
- [ ] Phase 1 — NCO (phase accumulator + wavetable)
- [ ] Phase 2 — audio output (PWM / sigma-delta)
- [ ] Phase 3 — MIDI input (UART RX + note parser)
- [ ] Phase 4 — ADSR envelope  → monophonic chain complete
- [ ] Phase 5 — polyphony (time-multiplexed voice + allocator)

### Results to record as they land

Resource utilisation, max clock frequency after synthesis, voice count, test
coverage.
