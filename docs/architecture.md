# Architecture

A MIDI-driven polyphonic synthesiser: one shared voice pipeline,
time-multiplexed across `NUM_VOICES` (8–16) notes.

The module plan was inspired by
[UA3MQJ/fpga-synth](https://github.com/UA3MQJ/fpga-synth) (GPL-3.0; ideas only,
no code is used). Its chain is: UART MIDI in → held-key bitmap with
highest-note priority → note to phase increment → 32-bit DDS → waveforms
from phase bits → linear ADSR → VCA → 1-bit delta-sigma or I²S. This design
keeps that shape. [Changes from the reference](#changes-from-the-reference)
lists what it does differently.

## Clock and sample budget

| Quantity | Value | Notes |
|---|---|---|
| `CLK_HZ` | 50 MHz (default) | 49.152 MHz = 1024 × 48 kHz divides exactly, if the board's PLL can make it |
| `SAMPLE_HZ` | 48 kHz | |
| Clocks per sample | 1041.67 | `sample_tick` averages this exactly (fractional divider) |
| `NUM_VOICES` | 16 (default) | 1 for bring-up, the same RTL |

At one voice per clock, 16 voices take 16 clocks of the ~1042 in a sample
period. **Extra voices are nearly free.** The pipeline's logic and multipliers
are shared, so they don't grow with `NUM_VOICES`. Only the per-voice state
RAMs grow (roughly 50–100 bits a voice), plus log2(N) bits in the mixer. The
hard ceiling is cycles: about `1042 / ISSUE_INTERVAL` minus the pipeline
latency, so around 1000 voices. In practice the mix level and musical need
set it at 16–32.

The resource trade-off is multipliers against clocks, set by
`ISSUE_INTERVAL` in `voice_scheduler`:

- **1 (default): fully pipelined.** Each stage owns its multiplier. The
  fewest clocks, the most DSP blocks.
- **k > 1: a voice every k clocks.** Stages can share one multiplier over k
  cycles. Fewer DSPs, more control logic.

The spare cycles also make 2× oversampling of the filter free (see `svf`).

## Block diagram

```
                     control plane (event-driven)
 midi_rx ─► midi_uart_rx ─► midi_parser ─► voice_allocator ◄── voice_active[N]
  (async)    (sync+8N1)      (events)      │  voice table:           ▲
                                           │  gate, trig, note, vel, │
                          note_inc_rom ◄───┤  increment, inc_recip   │
                                           ▼ read port               │
                     datapath (one slot per voice per sample)        │
 sample_tick ─► voice_scheduler ─► osc_phase ─► waveform_gen ─► envelope_exp ─► vca ─► svf ─► voice_mixer
   (48 kHz)     slots 0..N-1       phase RAM    sine_rom,        level RAM                 state   sum N,
                + voice fields                  polyblep                                   RAM     saturate
                                                                                                    │ one sample
                                                                                 dac_delta_sigma ◄──┤ per frame
                                                                                 i2s_tx ◄───────────┘
```

## The voice slot

Every datapath stage has the same shape: it takes one **slot** per clock and
gives one slot per clock, `LATENCY` clocks later. A slot carries:

- `valid`: this cycle carries a slot
- `voice`: which voice, `0..NUM_VOICES-1`
- `last`: the last voice of this sample frame
- the stage's data

Per-voice state (phase, envelope level, filter state) lives in a small RAM
indexed by `voice`. It is read when the slot enters the stage and written back
when it leaves. Because each voice appears once per frame and a frame is far
shorter than the sample period, a voice's read never overlaps its own
write-back. The pipeline has no hazards by construction. Say why in the
interview: that is the whole argument for time-multiplexing.

Consequences:

- **Mono is `NUM_VOICES = 1`**, the same RTL. There is no separate mono
  design to throw away.
- **No backpressure.** The scheduler's fixed timetable guarantees every stage
  can accept every slot, so there is no `ready` signal. A simulation-only check
  in `voice_scheduler` asserts that a frame finishes before the next tick.
- **`valid`, `voice` and `last` are delayed alongside the data** through every
  stage's latency. Misaligning them is the classic bug, and
  `tb/synthtb/stream.py` checks for it.

## Control plane

- **`midi_uart_rx`** synchronises the asynchronous input (two flip-flops,
  because metastability is real) and decodes 8N1 at `BAUD` (31 250 for DIN
  MIDI; the PC bridge may run faster).
- **`midi_parser`** handles running status, real-time bytes (0xF8–0xFF) that
  can arrive between the bytes of a message, SysEx skipping, note-on with
  velocity 0 treated as note-off, and control changes. It emits one event per
  complete message.
- **`voice_allocator`** owns the voice table:
  - **note-on:** reuse a voice already playing that note (retrigger); else take
    a free voice (gate off, envelope idle); else **steal**, preferring the
    oldest released voice, then the oldest held one.
  - **sustain (CC64 ≥ 64):** note-offs mark the voice *sustained* instead of
    dropping the gate. Pedal up releases every sustained voice.
  - A **trig toggle** per voice tells the envelope about a new note-on even when
    the gate stays high (retrigger, steal). The envelope compares it with the
    last value it saw, so there is no pulse to lose.
- **`voice_active[N]`** comes back from `envelope_exp`: a voice is free only
  once its release has actually finished.

## Changes from the reference

| Reference | This design | Why |
|---|---|---|
| `initial` blocks for state | Synchronous active-high `rst` on all state; per-voice RAMs cleared by a valid-bit vector | ASIC-friendly; FPGA-portable. `initial $readmemh` stays only for ROM contents, isolated in the ROM modules |
| Monophonic, highest-note priority | `NUM_VOICES` time-multiplexed through one pipeline, with allocation and stealing | The resource-sharing problem is the point of the project |
| 12 increment constants shifted per octave | 128-entry note→increment ROM from Python | No divide-by-12 or shifter in hardware; allows retuning (A4 calibration, stretch tuning). Both are accurate enough at 32 bits; this one is simpler |
| Naive saw and square | PolyBLEP-corrected saw and square *(tier 3)* | Naive edges alias badly at high notes. PolyBLEP needs `t/dt`, so the ROM also stores `1/increment` per note, avoiding a hardware divider |
| Linear ADSR | Exponential (one-pole) ADSR | Sounds natural. The attack aims past full scale so it reaches 1.0 in finite time; the release has a floor so it actually ends and frees the voice |
| No filter | Chamberlin state-variable filter per voice (LP/BP/HP) *(tier 3)* | State wider than the audio to avoid low-cutoff dead-band; optional 2× oversampling for stability |
| Eyeballed or ad-hoc tests | Self-checking cocotb against Python models, pitch/FFT checks, structured logs, regression | See `docs/verification.md` |
| No sustain | CC64 sustain | The P-125 has a pedal |

## Tiers and bring-up order

Each tier ends with a result you can put on a CV. Stop after any of them and
the project is still complete.

**Tier 1: playable mono synth** (`NUM_VOICES = 1`)

1. `ram_1r1w`, `sample_tick`, `voice_scheduler`: small, and everything else
   sits on them.
2. **First sound:** `osc_phase` + `waveform_gen` (sine, naive saw/square) +
   `voice_mixer` + `dac_delta_sigma`, with a hardcoded increment. Pitch-checked
   by FFT in simulation. *CV: "oscillator pitch and spur level verified by FFT
   against a Python model"*, with the measured numbers.
3. **MIDI:** `midi_uart_rx`, `midi_parser`, `note_inc_rom`, `voice_allocator`
   (one voice). Play it from the P-125.
4. **Shape:** `envelope_exp`, `vca`. *CV: "MIDI-controlled synthesiser on an
   FPGA, played from a keyboard"*, plus a video.

**Tier 2: polyphony.** The main interview talking point.

5. `NUM_VOICES` = 8–16, allocator stealing and CC64 sustain. Mostly parameters
   and allocator logic, since the datapath is already slot-based. *CV:
   "16-voice polyphony by time-multiplexing one pipeline, with voice
   allocation and stealing"*, plus the utilisation numbers.

**Tier 3: polish (optional).** Only if time allows.

6. `polyblep` (anti-aliased saw/square), triangle, `svf`, `i2s_tx`.

`phase_accumulator` and `sine_rom` (done) carry over: the accumulator's adder
is the core of `osc_phase` and it stays as the tested mono reference;
`sine_rom` is used unchanged inside `waveform_gen`.

## Hardware

See `docs/hardware.md`: board choice, MIDI input from a USB-only P-125, and
audio output.
