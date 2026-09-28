"""Tests for rtl/voice_mixer.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `voice_mixer`
Model:  model/voice_mixer.py: mix(frame_samples, mix_shift) -> saturated sample
Run:    python3 sim/run.py voice_mixer [--config one_voice]

Assumption-breaking case: Every voice at +full scale, and every voice at -full scale.

Every test below raises NotImplementedError until written. The module stays
out of the regression until its status in sim/modules.py is set to "active".
Write assert messages as key=value pairs (docs/verification.md).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

CLK_PERIOD_NS = 20            # 50 MHz
import random


@cocotb.test()
async def test_sum_per_frame(dut):
    """One mix_valid per frame, value = model mix of that frame."""
    # TODO(you): write it
    raise NotImplementedError("test_sum_per_frame: not written yet")


@cocotb.test()
async def test_saturation_extremes(dut):
    """All voices +FS and all -FS saturate correctly."""
    # TODO(you): write it
    raise NotImplementedError("test_saturation_extremes: not written yet")
