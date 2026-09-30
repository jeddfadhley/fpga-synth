# Module interfaces

The spec to write the RTL against. The bring-up order is in
`docs/architecture.md`: **tier 1** is the playable mono synth (`nco`,
`i2s_tx`, MIDI, envelope), **tier 2** is polyphony (the slot-based modules
below), and stretch items are optional. Stretch sections and ports are marked
*(tier 3)*; leave them out until then.

For each module: parameters, ports with
fixed-point formats, latency, and the behaviour that must hold. The internals
are yours. Where there is a real design choice, it is listed as open rather
than decided here.

Conventions (from CLAUDE.md): `clk`, synchronous active-high `rst`,
`snake_case` signals, `UPPER_CASE` parameters, registered outputs, and a
format comment on every port. No `initial` blocks for state; `initial
$readmemh` only for ROM contents.

Formats: `UQm.n` is unsigned with m integer and n fraction bits; `Qm.n` is
two's complement with m integer bits including the sign.

## Shared parameters

| Parameter | Default | Meaning |
|---|---|---|
| `CLK_HZ` | 100_000_000 | system clock (Basys 3) |
| `BCLK_DIV` | 32 | system clocks per I²S bit clock |
| `SLOT_W` | 32 | bits per I²S slot; a frame is 2 slots |

The sample rate, `CLK_HZ / (BCLK_DIV × 2 × SLOT_W)` = 48 828.125 Hz, isn't
an integer, so it is never a Verilog parameter. It exists in the RTL only as
"one `i2s_tx` tick per 2048 clocks". Python models use 48828.125 exactly.
| `NUM_VOICES` | 16 | voices; 1 for mono bring-up |
| `VOICE_W` | `$clog2(NUM_VOICES)` | **careful:** 0 when `NUM_VOICES = 1`. Use `(NUM_VOICES > 1) ? $clog2(NUM_VOICES) : 1` |
| `PHASE_W` | 32 | phase and increment, UQ0.PHASE_W |
| `ADDR_W` | 10 | wavetable address bits (top bits of the phase) |
| `DATA_W` | 16 | audio samples, Q1.(DATA_W-1) |
| `ENV_W` | 16 | envelope level, UQ0.ENV_W |
| `RECIP_W` | 24 | `inc_recip` *(tier 3, PolyBLEP only)*; format under `note_inc_rom` |

## The slot interface

Every datapath stage uses this on its input (`in_`) and output (`out_`):

| Signal | Width | Meaning |
|---|---|---|
| `*_valid` | 1 | a slot is present this cycle |
| `*_voice` | `VOICE_W` | voice index |
| `*_last` | 1 | last slot of this sample frame |
| `*_<data>` | per stage | the stage's payload |

Rules:

- `out_*` equals the input slot delayed by exactly `LATENCY` clocks. Declare
  it as a `localparam` and state it in the header comment.
- `valid`, `voice` and `last` travel alongside the data.
- There is no `ready`: a stage must accept a slot every cycle.
- On `rst`, `out_valid` goes to 0. The data outputs need no reset.
- Per-voice state RAM is **not** reset in one cycle (it can't be). Keep a
  `NUM_VOICES`-bit "written" vector, reset to 0: an unwritten entry reads as
  zero. This is cheap at 16 voices and ASIC-friendly.

---

## Infrastructure

### `ram_1r1w`: generic simple dual-port RAM

The only place memories are inferred, so a vendor or ASIC macro can replace
it later (CLAUDE.md: isolate anything vendor-specific).

| Parameter | Meaning |
|---|---|
| `WIDTH` | word width |
| `DEPTH` | number of words (may be 1, and may be a non-power of two) |

| Port | Dir | Width | Notes |
|---|---|---|---|
| `clk` | in | 1 | |
| `wr_en` | in | 1 | |
| `wr_addr` | in | `max(1, $clog2(DEPTH))` | |
| `wr_data` | in | `WIDTH` | |
| `rd_addr` | in | `max(1, $clog2(DEPTH))` | |
| `rd_data` | out | `WIDTH` | registered; valid 1 clock after `rd_addr` |

**Latency:** 1. **Read-during-write to the same address:** return the *old*
data, and document it. The datapath never does this; the test checks the
documented behaviour anyway. **No reset** (see the slot rules above).
**Assumption-breaking cases:** `DEPTH = 1` (zero-width address trap) and
`DEPTH = 5`.

### `nco`: mono oscillator for first sound (tier 1)

Your `phase_accumulator` and `sine_rom` wired together: your first module
that instantiates others. It stays as the tested mono reference once the
slot pipeline replaces it.

| Parameter | Meaning |
|---|---|
| `PHASE_W`, `ADDR_W`, `DATA_W`, `INIT_FILE` | passed down to the submodules; `ADDR_W <= PHASE_W` |

| Port | Dir | Width | Notes |
|---|---|---|---|
| `clk`, `rst` | in | 1 | `rst` resets the accumulator only |
| `en` | in | 1 | advance one sample: the `i2s_tx` tick |
| `increment` | in | `PHASE_W` | UQ0.PHASE_W, fraction of a cycle per sample |
| `sample` | out | `DATA_W` | Q1.(DATA_W−1) |
| `sample_valid` | out | 1 | *(optional)* `en` delayed to line up with `sample` |

The address is `phase[PHASE_W-1 -: ADDR_W]`. **Latency:** 2 clocks from `en`
(the accumulator register, then the ROM register). `f_out = increment × fs /
2^PHASE_W`. **Assumption-breaking:** increment above half a cycle (it aliases,
and the model must still match); `PHASE_W = 24`.

### `voice_scheduler`: issue one slot per voice per sample

| Parameter | Meaning |
|---|---|
| `NUM_VOICES`, `VOICE_W` | |
| `ISSUE_INTERVAL` | clocks between slots (1 = fully pipelined) |

| Port | Dir | Width | Notes |
|---|---|---|---|
| `clk`, `rst` | in | 1 | |
| `tick` | in | 1 | from `i2s_tx` |
| `vt_rd_voice` | out | `VOICE_W` | voice-table read address |
| `vt_rd_*` | in | per field | voice-table fields, 1 clock after `vt_rd_voice` |
| `out_valid/voice/last` | out | slot | voices 0..N-1 in order after each `tick` |
| `out_increment` | out | `PHASE_W` | UQ0.PHASE_W |
| `out_inc_recip` | out | `RECIP_W` | *(tier 3)* see `note_inc_rom` |
| `out_gate`, `out_trig` | out | 1 | |
| `out_velocity` | out | 7 | MIDI velocity 0..127 |

It reads each voice's fields from the voice table as it issues the slot, so
later stages get them in the slot rather than needing their own read ports.
Account for the table's 1-clock read latency when aligning. **Simulation-only
check** (inside `` `ifndef SYNTHESIS ``): a `tick` arriving before the previous
frame is issued is an error. **Assumption-breaking:** `NUM_VOICES = 1`
(`last` on every slot) and 5 (not a power of two).

---

## Control plane

### `midi_uart_rx`

| Parameter | Meaning |
|---|---|
| `CLK_HZ`, `BAUD` | 31 250 for DIN MIDI; a PC/Pi bridge may use 115 200 |

| Port | Dir | Width | Notes |
|---|---|---|---|
| `clk`, `rst` | in | 1 | |
| `rx` | in | 1 | **asynchronous**: synchronise with two flip-flops first |
| `byte_valid` | out | 1 | one-clock pulse |
| `byte_data` | out | 8 | |
| `framing_error` | out | 1 | pulse: stop bit was 0; the byte is dropped |

Detect the start bit, re-check it at mid-bit (to reject glitches), then sample
each bit at its centre. **Must tolerate ±1% baud error** (MIDI spec), and the
test skews the sender. **Assumption-breaking:** back-to-back bytes with no idle
gap; a glitch shorter than half a bit on an idle line.

### `midi_parser`

| Parameter | Meaning |
|---|---|
| `OMNI` | 1: accept all channels; 0: only `CHANNEL` |
| `CHANNEL` | 0..15 when `OMNI = 0` |

| Port | Dir | Width | Notes |
|---|---|---|---|
| `clk`, `rst` | in | 1 | |
| `byte_valid`, `byte_data` | in | 1, 8 | from `midi_uart_rx` |
| `ev_valid` | out | 1 | one-clock pulse per complete message |
| `ev_type` | out | 2 | 0 NOTE_ON, 1 NOTE_OFF, 2 CONTROL_CHANGE |
| `ev_channel` | out | 4 | |
| `ev_key` | out | 7 | note number, or controller number |
| `ev_value` | out | 7 | velocity, or controller value |

Must handle:
- **running status**: data bytes after a message reuse its status
- **real-time bytes** 0xF8–0xFF: ignore them, even between a status and its
  data, without disturbing running status
- **SysEx** (0xF0 … 0xF7): skip it
- **system common** messages: cancel running status
- **note-on with velocity 0**: emit NOTE_OFF
- **other channel messages** (aftertouch, program change, pitch bend): consume
  the right number of data bytes and emit nothing

Pitch bend could be added later as a new `ev_type`.

### `note_inc_rom`

| Parameter | Meaning |
|---|---|
| `PHASE_W`, `RECIP_W` | |
| `INIT_FILE` | hex table generated by `model/note_inc_rom.py` (yours to write) |

| Port | Dir | Width | Notes |
|---|---|---|---|
| `clk` | in | 1 | |
| `note` | in | 7 | MIDI note 0..127 |
| `increment` | out | `PHASE_W` | UQ0.PHASE_W: `round(f × 2^PHASE_W / 48828.125)`, f = 440·2^((n−69)/12) |
| `inc_recip` | out | `RECIP_W` | *(tier 3)* `2^PHASE_W / increment`, for PolyBLEP's `t/dt` |

**Latency:** 1 (same as `sine_rom`). The range of `inc_recip` sets its
format: about 3.9 at note 127 and about 5970 at note 0 (fs = 48 828.125 Hz). So it needs
13 integer bits; decide the fraction bits from PolyBLEP's accuracy (**open**:
suggest UQ13.11). Note 127 (12.5 kHz) is above fs/4, and the model should
still produce a correct value.

### `voice_allocator`

Tier 1 needs only `NUM_VOICES = 1`: every note-on takes voice 0 and every
note-off for that note clears its gate. Stealing, sustain and the age
tracking are **tier 2**.

| Parameter | Meaning |
|---|---|
| `NUM_VOICES`, `VOICE_W`, `PHASE_W`, `RECIP_W` | |

| Port | Dir | Width | Notes |
|---|---|---|---|
| `clk`, `rst` | in | 1 | |
| `ev_*` | in | | from `midi_parser` |
| `voice_active` | in | `NUM_VOICES` | from `envelope_exp`: bit v = voice v still sounding |
| `vt_rd_voice` | in | `VOICE_W` | datapath read port |
| `vt_rd_gate`, `vt_rd_trig` | out | 1 | registered, 1 clock |
| `vt_rd_increment` | out | `PHASE_W` | |
| `vt_rd_inc_recip` | out | `RECIP_W` | *(tier 3)* |
| `vt_rd_velocity` | out | 7 | |
| `vt_rd_note` | out | 7 | for debug and the tests |
| `sustain` | out | 1 | pedal state, for visibility |

Per voice: `note`, `gate`, `sustained`, `trig` (toggle), `velocity`, `age`,
plus `increment` and `inc_recip` from its own `note_inc_rom` instance.

- **Note-on n:**
  1. If a voice already has note n (held, sustained or releasing), retrigger
     it.
  2. Else take a free voice (`!gate && !voice_active`).
  3. Else steal: the oldest released voice (`!gate && voice_active`), else the
     oldest held one.

  Set `gate`, toggle `trig`, record `velocity` and `age`.
- **Note-off n:** for the voice holding n, set `sustained` if the pedal is
  down, else clear `gate`.
- **CC64:** value ≥ 64 is pedal down. On pedal up, clear `gate` on every
  `sustained` voice.
- **CC123 (all notes off):** clear every `gate`. Optional but cheap.

A note-on takes several clocks (a search over the voices plus the ROM
lookup). That's fine, since MIDI bytes arrive about 320 µs apart. Make it a
small state machine, and say why it can be slow. **Assumption-breaking:**
`NUM_VOICES = 1` (every note-on steals); note-off for a note that isn't held;
the same note twice without a note-off.

---

## Voice datapath

### `osc_phase`: per-voice phase accumulator

| Parameter | Meaning |
|---|---|
| `NUM_VOICES`, `VOICE_W`, `PHASE_W` | |

| Port | Dir | Width | Notes |
|---|---|---|---|
| `clk`, `rst` | in | 1 | |
| `in_valid/voice/last` | in | slot | |
| `in_increment` | in | `PHASE_W` | UQ0.PHASE_W |
| `in_*` pass-through | in | | `inc_recip`, `gate`, `trig`, `velocity` carried on |
| `out_valid/voice/last` | out | slot | |
| `out_phase` | out | `PHASE_W` | UQ0.PHASE_W: this voice's phase for this sample |
| `out_*` pass-through | out | | |

Phase in an `ram_1r1w` (DEPTH = `NUM_VOICES`): read on entry; `phase +
increment` (wraps); write back; output. Define whether `out_phase` is the
value *before* or *after* the add, and match the model. **Open:** reset the
phase on `trig`? Resetting gives consistent attacks but clicks on a steal.
Suggest *don't reset*. **Assumption-breaking:** `NUM_VOICES = 1`; an increment
above half a cycle (aliasing, but the arithmetic must still match).

### `polyblep`: band-limited step correction *(tier 3, optional)*

| Port | Dir | Width | Notes |
|---|---|---|---|
| `clk` | in | 1 | |
| `phase` | in | `PHASE_W` | UQ0.PHASE_W, t |
| `inc_recip` | in | `RECIP_W` | 1/dt |
| `correction` | out | `DATA_W` | Q1.(DATA_W−1), to subtract from a naive unit step |

With x = t/dt (a multiply by `inc_recip`, no divider):
- t < dt: `x = t/dt`, correction = 2x − x² − 1
- t > 1 − dt: `x = (t − 1)/dt`, correction = x² + 2x + 1
- else: 0

**Latency:** fixed, your choice (it is pipelined around the multiplies).
**Assumption-breaking:** dt > 0.5 (both regions overlap at the highest notes;
define which wins).

### `waveform_gen`

| Parameter | Meaning |
|---|---|
| `PHASE_W`, `ADDR_W`, `DATA_W`, `RECIP_W`, `INIT_FILE` | |

| Port | Dir | Width | Notes |
|---|---|---|---|
| slot in | in | | `in_phase`, `in_inc_recip`, pass-through fields |
| `wave_sel` | in | 2 | 0 sine, 1 saw, 2 square, 3 triangle (global) |
| slot out | out | | `out_sample`: Q1.(DATA_W−1) |

**Tier 1:** sine, naive saw and naive square. The naive waveforms alias on
high notes, which is audible but acceptable for a first version.

- **Sine:** `sine_rom` at `phase[PHASE_W-1 -: ADDR_W]`.
- **Saw:** the top `DATA_W` phase bits, recentred. *(tier 3: minus
  `polyblep(t)`)*
- **Square:** the MSB. *(tier 3: steps at t = 0 and t = 0.5, so two
  corrections)*
- **Triangle** *(tier 3)*: folded saw. It is naive but acceptable: its
  harmonics fall at 12 dB/octave.

Every select path has the same latency, so switching doesn't misalign.

### `envelope_exp`: exponential ADSR per voice

| Parameter | Meaning |
|---|---|
| `NUM_VOICES`, `VOICE_W`, `ENV_W` | |
| `ATTACK_TARGET` | overshoot target, e.g. 1.25 in UQ1.(ENV_W−1) |
| `FLOOR` | release ends below this level |

| Port | Dir | Width | Notes |
|---|---|---|---|
| slot in | in | | `in_gate`, `in_trig`, `in_velocity`, pass-through `in_sample` |
| `attack_coef`, `decay_coef`, `release_coef` | in | `ENV_W` | UQ0.ENV_W per-sample fraction |
| `sustain_level` | in | `ENV_W` | UQ0.ENV_W |
| slot out | out | | `out_level` UQ0.ENV_W, pass-through `out_sample` |
| `voice_active` | out | `NUM_VOICES` | registered; bit v = stage ≠ IDLE |

State per voice in RAM: `level`, `stage` (IDLE/ATTACK/DECAY/SUSTAIN/RELEASE)
and `last_trig`. Per sample: `level += (target − level) × coef`.
- **Attack** aims at `ATTACK_TARGET` and ends at 1.0.
- **Decay** aims at `sustain_level`.
- **Release** aims at 0 and ends below `FLOOR`, which frees the voice.

A trig toggle (`in_trig != last_trig`) restarts the attack **from the current
level**, with no reset to 0, so a retrigger or steal doesn't click. Velocity
scales the peak (**open:** linear or via a curve). **Assumption-breaking:**
release must terminate (a pure exponential never reaches 0); `coef = 0` and
full scale; retrigger during release.

### `vca`

| Port | Dir | Width | Notes |
|---|---|---|---|
| slot in | in | | `in_sample` Q1.(DATA_W−1), `in_level` UQ0.ENV_W |
| slot out | out | | `out_sample` Q1.(DATA_W−1) |

`sample × level`, rounded (**open:** truncate or round; the model must match).
Signed × unsigned: extend the level with a 0 sign bit before a signed
multiply. That's the classic bug here. **Latency:** 1–2, enough to use a
registered DSP.

### `svf`: Chamberlin state-variable filter per voice *(tier 3, optional)*

| Parameter | Meaning |
|---|---|
| `NUM_VOICES`, `VOICE_W`, `DATA_W` | |
| `STATE_W` | internal state width, > `DATA_W` (e.g. 24) |
| `OVERSAMPLE` | 1 or 2 iterations per sample |

| Port | Dir | Width | Notes |
|---|---|---|---|
| slot in / out | | | `in_sample` / `out_sample`, Q1.(DATA_W−1) |
| `cutoff_f` | in | 16 | f = 2·sin(π·fc/fs_eff), UQ1.15 |
| `damping_q` | in | 16 | q = 1/Q, UQ1.15 (2 = no resonance) |
| `mode` | in | 2 | 0 LP, 1 BP, 2 HP, 3 bypass |

Per iteration: `low += f·band; high = in − low − q·band; band += f·high`, with
`low` and `band` in RAM per voice. Stability degrades as fc approaches about
fs/6 at high resonance; `OVERSAMPLE = 2` uses the spare cycles to double
fs_eff. The state is wider than the audio because f·band is tiny at low
cutoff and would truncate to zero (dead-band, limit cycles). **Saturate** the
states, never wrap them. **Assumption-breaking:** maximum resonance with a
full-scale input; cutoff near Nyquist.

### `voice_mixer`

| Parameter | Meaning |
|---|---|
| `NUM_VOICES`, `DATA_W` | |
| `MIX_SHIFT` | right shift after summing (0..$clog2(NUM_VOICES)) |

| Port | Dir | Width | Notes |
|---|---|---|---|
| slot in | in | | `in_sample` Q1.(DATA_W−1) |
| `mix_valid` | out | 1 | one pulse per frame, after the slot with `in_last` |
| `mix_sample` | out | `DATA_W` | Q1.(DATA_W−1), saturated |

The accumulator needs `DATA_W + $clog2(NUM_VOICES)` bits so the sum itself
can't overflow. Then shift by `MIX_SHIFT` and saturate. The trade-off: a full
shift can never clip but makes one note quiet; a smaller shift is louder but
clips on big chords. **Assumption-breaking:** every voice at +full scale, and
every voice at −full scale.

---

## Audio out

### `dac_delta_sigma` *(stretch: replaced by the I²S amp)*

| Parameter | Meaning |
|---|---|
| `DATA_W` | |
| `ORDER` | 1 or 2 (second-order recommended: less idle-tone noise) |

| Port | Dir | Width | Notes |
|---|---|---|---|
| `clk`, `rst` | in | 1 | runs every clock (oversampling ratio ≈ 1000) |
| `sample` | in | `DATA_W` | Q1.(DATA_W−1), held between `mix_valid` pulses |
| `dac_out` | out | 1 | to the pin, then the RC filter |

Registered output (it drives a pin). Second-order loops can go unstable near
full scale, so **limit the input** (e.g. to ±0.8) and test that. The check
works by averaging `dac_out` over a window: the mean must track the input.
**Assumption-breaking:** ±full-scale input; zero input (the idle pattern must
stay bounded).

### `i2s_tx`: I²S transmitter and sample tick (tier 1)

Drives the MAX98357A amp and defines the sample rate for the whole synth.

| Parameter | Meaning |
|---|---|
| `BCLK_DIV` | system clocks per BCLK (32 → 3.125 MHz); even |
| `SLOT_W` | bits per slot (32) |
| `DATA_W` | sample width (16) |

| Port | Dir | Width | Notes |
|---|---|---|---|
| `clk`, `rst` | in | 1 | |
| `sample_l`, `sample_r` | in | `DATA_W` | Q1.(DATA_W−1), captured at `tick` (mono: the same sample on both) |
| `tick` | out | 1 | one-clock pulse per frame (every `BCLK_DIV × 2 × SLOT_W` = 2048 clocks): the synth's sample tick |
| `i2s_bclk`, `i2s_lrclk`, `i2s_data` | out | 1 | registered; to Pmod JA1–3 |

Standard (Philips) I²S:
- `i2s_lrclk` is low for the left slot and high for the right; it changes on
  a BCLK falling edge.
- The **MSB appears one BCLK after the LRCLK edge**.
- Data changes on BCLK falling edges; the amp samples on rising edges.
- The 16-bit sample is MSB-aligned in the 32-bit slot; the rest are zeros.

`i2s_bclk` is an ordinary registered output toggling every `BCLK_DIV/2`
clocks. It drives a pin only and is never used as a clock inside the FPGA, so
everything stays in the one 100 MHz domain.

**Open:** capture both samples at `tick`, or each at its own slot start.
Capturing at `tick` means a new sample can never tear across a frame.

The test decodes the waveform from the pins: bit order, MSB timing, frame
period (2048 clocks), and that left and right carry what was loaded.
**Assumption-breaking:** the most negative sample `0x8000` (MSB first, sign
kept); `SLOT_W = 16` or `BCLK_DIV = 4`, so nothing assumes 32/32.

---

## Integration: `synth_core`

A board-independent top level: control plane, datapath and outputs.
`top_basys3.v` wraps it with the pin names from `docs/hardware.md`. Any
vendor primitive lives only there.

| Port | Dir | Notes |
|---|---|---|
| `clk`, `rst` | in | |
| `uart_rx` | in | asynchronous; from the Mac bridge via the USB-UART |
| `wave_sel`, envelope coefs | in | constants at first; later from CCs. *(tier 3: `cutoff_f`, `damping_q`, `filter_mode`)* |
| `i2s_bclk`, `i2s_lrclk`, `i2s_data` | out | to the amp |
| `mix_valid`, `mix_sample` | out | for the testbench (pitch/FFT checks) |
| `voice_active` | out | for the testbench and debug LEDs |
