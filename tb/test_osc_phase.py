"""Tests for rtl/osc_phase.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `osc_phase`
Model:  model/osc_phase.py: per-voice phase sequences (reuse phase_accumulator.next_phase)
Run:    python3 sim/run.py osc_phase [--config one_voice]

Assumption-breaking case: NUM_VOICES=1; increment above half a cycle.

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
async def test_per_voice_phase(dut):
    """Each voice accumulates its own increment, frame after frame."""
    # TODO(you): drive frames of slots (voice 0..N-1, last on N-1) with a distinct increment per voice
    # TODO(you): SlotMonitor.voice_series(v, 'phase') must equal the model's sequence for voice v
    raise NotImplementedError("test_per_voice_phase: not written yet")


@cocotb.test()
async def test_voice_isolation(dut):
    """Changing voice 3's increment never affects any other voice."""
    # TODO(you): write it
    raise NotImplementedError("test_voice_isolation: not written yet")


@cocotb.test()
async def test_latency_and_alignment(dut):
    """out_voice/out_last/out_valid are the inputs delayed by LATENCY."""
    # TODO(you): write it
    raise NotImplementedError("test_latency_and_alignment: not written yet")


@cocotb.test()
async def test_reset_clears_phase(dut):
    """After rst every voice's phase starts from 0 (written-vector, not a RAM sweep)."""
    # TODO(you): write it
    raise NotImplementedError("test_reset_clears_phase: not written yet")
