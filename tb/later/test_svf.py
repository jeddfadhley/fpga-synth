"""Tests for rtl/svf.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `svf`
Model:  model/svf.py: fixed-point Chamberlin with the RTL's widths
Run:    python3 sim/run.py svf

Assumption-breaking case: Maximum resonance with a full-scale input: states must saturate, never wrap.

TIER 3 (optional). Parked in tb/later/: move this file to tb/ when starting
the module, and set its status to "active" in sim/modules.py.

Every test below raises NotImplementedError until written. The module stays
out of the regression until its status in sim/modules.py is set to "active".
Write assert messages as key=value pairs (docs/verification.md).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

CLK_PERIOD_NS = 20            # 50 MHz
from synthtb.audio import measure_frequency


@cocotb.test()
async def test_bit_exact(dut):
    """Impulse and random input vs the model, per voice."""
    # TODO(you): write it
    raise NotImplementedError("test_bit_exact: not written yet")


@cocotb.test()
async def test_lowpass_response(dut):
    """Sine sweep: LP gain at fc/10 ~ 0 dB, at 10*fc down ~40 dB (2-pole)."""
    # TODO(you): write it
    raise NotImplementedError("test_lowpass_response: not written yet")


@cocotb.test()
async def test_saturation(dut):
    """Full-scale input at max resonance never wraps."""
    # TODO(you): write it
    raise NotImplementedError("test_saturation: not written yet")
