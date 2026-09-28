# Verification

Every module has a self-checking cocotb testbench on Verilator. A module is
not done until its testbench passes at every config in `sim/modules.py`.

## Principles

1. **Expected values come from `model/`**, an independent Python model, never
   from the RTL. When a test and the model both derive from the same function
   (e.g. `sine_table()` produces the ROM file *and* the expected values), test
   the model separately against first principles (`math.sin`, the MIDI spec).
2. **Check timing as well as values.** Every stage has a stated `LATENCY`. A
   test must fail if the latency changes: see `test_sine_rom.test_latency`,
   which was confirmed to fail against a combinational ROM.
3. **At least one case per module contradicts an assumption the design was
   written under.** Each module's case is listed in `docs/interfaces.md`, and
   in its test skeleton.
4. **Read parameters from the design**, never hardcode them, so the same test
   runs at every config. Widths: `len(dut.port)`. Any integer parameter:
   `int(dut.NAME.value)` (run.py builds with Verilator `--public-params`).
5. **Randomised tests log their seed**, and `run.py --seed N` replays them.

## Running

```
python3 sim/run.py sine_rom                    # default config
python3 sim/run.py sine_rom --config a8_d12    # named config (sim/modules.py)
python3 sim/run.py sine_rom -t test_latency    # one test
python3 sim/run.py sine_rom --seed 1790588464  # replay a random run
python3 sim/regress.py                         # lint + every module, every config
python3 sim/synth.py sine_rom --target ice40   # resource use
```

`make` wraps these; see `Makefile`.

## Structured results (for scripts and triage agents)

`run.py` prints the normal cocotb log, then JSON lines behind fixed prefixes.
Every field is always present.

```
SYNTH_RESULT  {"schema": 1, "module": "sine_rom", "config": "default",
               "test_module": "test_sine_rom", "test": "test_latency",
               "status": "PASS" | "FAIL" | "SKIP",
               "message": null | "AssertionError: <your assert message>",
               "seed": 1790588464, "params": {...}, "sim_time_ns": 50005.0,
               "file": "tb/test_sine_rom.py", "line": 31}

SYNTH_SUMMARY {"schema": 1, "module": ..., "config": ..., "params": {...},
               "status": "PASS" | "FAIL" | "ERROR",
               "passed": 2, "failed": 0, "skipped": 0, "seed": ...,
               "error": null | "build failed" | "timeout after 600 s" | ...,
               "error_details": ["%Error: ...", ...],
               "replay": "python3 sim/run.py sine_rom --config default --seed ..."}
```

- **FAIL**: a test's assert fired. `message` has the text.
- **ERROR**: nothing meaningful ran. This covers a build failure, a simulator
  abort (e.g. `$readmem` out of bounds; `error_details` has Verilator's lines),
  a missing source, or a timeout.
- Exit codes: 0 pass, 1 fail, 2 error.

The same record goes to `sim/results/<module>/<config>/summary.json`.
`regress.py` collects them all into `sim/results/regression.json` and prints
`SYNTH_REGRESSION {...}`. `synth.py` prints `SYNTH_UTIL {...}`.

**Write assert messages as `key=value` pairs**, so a failure can be
triaged from `message` alone:

```python
assert actual == exp, f"cycle={cycle} voice={v} addr={a} got={actual} exp={exp}"
```

## Helpers: `tb/synthtb/`

These are measurement and stimulus only. They never produce expected values.

| Helper | Use |
|---|---|
| `audio.measure_frequency(samples, fs)` | pitch, better than 0.001 cent on clean tones, low notes included |
| `audio.check_pitch(samples, fs, hz, tol_cents)` | returns a dict for the assert message |
| `audio.sfdr_db(samples, fs)` | largest spur below the carrier. Measured 60.1 dB for the 10-bit sine ROM, matching 6.02 dB/bit |
| `audio.note_hz(note)` | equal-tempered reference |
| `midi.note_on / note_off / sustain / encode` | messages; `encode` applies running status |
| `midi.insert_realtime` | puts 0xF8 between bytes, including mid-message |
| `midi.uart_send(pin, bytes, baud, baud_error_ppm)` | drives 8N1 bits; the skew tests the ±1% tolerance |
| `stream.SlotMonitor` | records `valid/voice/last` + data per clock and groups them into frames |

## What each level checks

| Level | Checks |
|---|---|
| Unit (each module) | Cycle-exact against the model: values, latency, reset, every config |
| Stream (datapath stages) | Slot order 0..N-1, `last` on the final slot, voice/data alignment, per-voice state isolation (voice 3's phase is unaffected by voice 5's increment) |
| Integration (`synth_core`) | MIDI bytes in → `mix_sample` out: pitch per note (FFT, within cents), polyphony (N notes → N spectral peaks), stealing (N+1 notes), sustain (note-off during pedal keeps sounding), release frees the voice (`voice_active`) |
| Synthesis | `synth.py` per module: memories map to BRAM, multipliers to DSP; numbers go in the README |

## Models to write (`model/`)

Yours to write. One per module with a non-trivial function. The expected
shapes are:

| Model | Function |
|---|---|
| `sample_tick.py` | tick times for a given `CLK_HZ` and `SAMPLE_HZ` |
| `midi_uart_rx.py` | not needed: the stimulus bytes are the expected values |
| `midi_parser.py` | byte stream → list of events (running status, real-time, SysEx) |
| `note_inc_rom.py` | `increment(note)`, `write_hex(...)`; `inc_recip(note)` in tier 3 |
| `voice_allocator.py` | event list → voice-table state after each event (the stealing policy) |
| `osc_phase.py` | per-voice phase sequence (reuse `phase_accumulator.next_phase`) |
| `polyblep.py` *(tier 3)* | correction(t, dt) in fixed point |
| `waveform_gen.py` | sample(phase, wave_sel, recip) |
| `envelope_exp.py` | level sequence for a gate/trig pattern |
| `vca.py`, `voice_mixer.py` | multiply / sum-shift-saturate with the RTL's rounding |
| `svf.py` *(tier 3)* | fixed-point Chamberlin, bit-exact with the RTL's widths |
| `dac_delta_sigma.py` | bitstream for an input sequence (or check the mean only) |
