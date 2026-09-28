"""Tests for rtl/voice_scheduler.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `voice_scheduler`
Model:  none needed beyond a small fake voice table in the test
Run:    python3 sim/run.py voice_scheduler [--config one_voice | v5]

Assumption-breaking case: NUM_VOICES=1 (last on every slot) and NUM_VOICES=5.

Every test below raises NotImplementedError until written. The module stays
out of the regression until its status in sim/modules.py is set to "active".
Write assert messages as key=value pairs (docs/verification.md).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

CLK_PERIOD_NS = 20            # 50 MHz
from synthtb.stream import SlotMonitor


@cocotb.test()
async def test_frame_order(dut):
    """After each tick: voices 0..N-1 in order, last only on N-1."""
    # TODO(you): pulse tick; SlotMonitor on out_*; check [s['voice'] for s in frame] == list(range(N))
    raise NotImplementedError("test_frame_order: not written yet")


@cocotb.test()
async def test_fields_aligned(dut):
    """Each slot carries its own voice's table fields."""
    # TODO(you): answer vt_rd_voice from a fake table with distinct values per voice (1-clock latency)
    # TODO(you): check out_increment etc. match the slot's out_voice, not a neighbour's
    raise NotImplementedError("test_fields_aligned: not written yet")


@cocotb.test()
async def test_tick_too_early(dut):
    """Simulation-only check fires if a tick arrives mid-frame."""
    # TODO(you): only meaningful with ISSUE_INTERVAL large; expect the check to report (decide how: $error)
    raise NotImplementedError("test_tick_too_early: not written yet")
