"""Module manifest: sources, parameter sets and status for every module.

run.py uses it to find a module's sources and default parameters; regress.py
runs every "active" module at every config. Paths are relative to the repo root.

To bring a planned module into the regression once its RTL and testbench
exist, set status="active" and check its sources and configs.

Fields:
  sources  RTL files to compile, dependencies first; the toplevel file last
  configs  name -> parameter overrides. "default" is used when none is named.
           String values that name an existing file are made absolute by run.py.
  requires files that must exist for a config to run (e.g. a generated table);
           regress.py reports the config as SKIP with the reason if one is missing
  status   "active" (in the regression), "planned" (spec only, see
           docs/interfaces.md) or "optional" (tier 3: only if
           time allows)
  tier     1 playable mono synth, 2 polyphony, 3 polish (optional)
"""

from dataclasses import dataclass, field


@dataclass
class Module:
    sources: list[str]
    configs: dict[str, dict] = field(default_factory=lambda: {"default": {}})
    requires: dict[str, list[str]] = field(default_factory=dict)
    status: str = "planned"
    tier: int = 1


def rtl(*names: str) -> list[str]:
    return [f"rtl/{n}.v" for n in names]


SINE_1024x16 = "rtl/mem/sine_1024x16.hex"
SINE_256x12 = "rtl/mem/sine_256x12.hex"

MODULES: dict[str, Module] = {
    # ---- done ------------------------------------------------------------
    "phase_accumulator": Module(
        sources=rtl("phase_accumulator"),
        configs={"default": {}, "w24": {"WIDTH": 24}},
        status="active",
    ),
    "sine_rom": Module(
        sources=rtl("sine_rom"),
        configs={
            "default": {"INIT_FILE": SINE_1024x16},
            "a8_d12": {"ADDR_W": 8, "DATA_W": 12, "INIT_FILE": SINE_256x12},
        },
        requires={"a8_d12": [SINE_256x12]},
        status="active",
    ),
    # ---- tier 1: mono first sound ------------------------------------------
    "i2s_tx": Module(
        sources=rtl("i2s_tx"),
        configs={"default": {}, "slot16": {"SLOT_W": 16}, "fast_bclk": {"BCLK_DIV": 4}},
        status="active",
    ),
    "nco": Module(
        sources=rtl("phase_accumulator", "sine_rom", "nco"),
        configs={"default": {"INIT_FILE": SINE_1024x16},
                 "p24": {"PHASE_W": 24, "INIT_FILE": SINE_1024x16}},
    ),
    # ---- infrastructure --------------------------------------------------
    "voice_scheduler": Module(
        sources=rtl("voice_scheduler"),
        configs={"default": {}, "one_voice": {"NUM_VOICES": 1}, "v5": {"NUM_VOICES": 5}},
    ),
    "ram_1r1w": Module(
        sources=rtl("ram_1r1w"),
        configs={"default": {}, "d1": {"DEPTH": 1}, "d5": {"DEPTH": 5}},
        status="active",
    ),
    # ---- control plane ---------------------------------------------------
    "midi_uart_rx": Module(
        sources=rtl("midi_uart_rx"),
        configs={"default": {}, "fast_bridge": {"BAUD": 115_200}},
    ),
    "midi_parser": Module(sources=rtl("midi_parser")),
    "note_inc_rom": Module(sources=rtl("note_inc_rom")),
    "voice_allocator": Module(
        sources=rtl("voice_allocator"),
        configs={"default": {}, "one_voice": {"NUM_VOICES": 1}},
    ),  # tier 1 at NUM_VOICES=1; stealing and sustain are tier 2
    # ---- voice datapath --------------------------------------------------
    "osc_phase": Module(
        sources=rtl("ram_1r1w", "osc_phase"),
        configs={"default": {}, "one_voice": {"NUM_VOICES": 1}},
    ),
    "polyblep": Module(sources=rtl("polyblep"), status="optional", tier=3),
    "waveform_gen": Module(
        sources=rtl("sine_rom", "waveform_gen"),      # + "polyblep" in tier 3
        configs={"default": {"INIT_FILE": SINE_1024x16}},
    ),
    "envelope_exp": Module(
        sources=rtl("ram_1r1w", "envelope_exp"),
        configs={"default": {}, "one_voice": {"NUM_VOICES": 1}},
    ),
    "vca": Module(sources=rtl("vca")),
    "svf": Module(sources=rtl("ram_1r1w", "svf"), status="optional", tier=3),
    "voice_mixer": Module(
        sources=rtl("voice_mixer"),
        configs={"default": {}, "one_voice": {"NUM_VOICES": 1}},
    ),
    # ---- audio out -------------------------------------------------------
    "dac_delta_sigma": Module(sources=rtl("dac_delta_sigma"), status="optional", tier=3),
    # ---- integration -----------------------------------------------------
    "synth_core": Module(
        sources=rtl(
            "ram_1r1w", "i2s_tx", "voice_scheduler",
            "midi_uart_rx", "midi_parser", "note_inc_rom", "voice_allocator",
            "osc_phase", "sine_rom", "waveform_gen",
            "envelope_exp", "vca", "voice_mixer", "synth_core",
        ),  # stretch adds "polyblep", "svf"
        configs={"default": {"INIT_FILE": SINE_1024x16}},
    ),
}
