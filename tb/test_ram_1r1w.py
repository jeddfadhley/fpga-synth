"""Tests for rtl/ram_1r1w.v. SKELETON: the outline is here; the checks are yours.

Spec:   docs/interfaces.md, section `ram_1r1w`
Model:  none needed: a Python dict of written values is the reference
Run:    python3 sim/run.py ram_1r1w [--config d1 | d5]

Assumption-breaking case: DEPTH=1 (the address width must not collapse to zero) and DEPTH=5 (not a power of two).

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
async def test_write_then_read(dut):
    """Every address holds what was last written to it; read data is 1 clock late."""
    # TODO(you): DEPTH = int(dut.DEPTH.value) (not 2**len(dut.rd_addr): wrong for DEPTH=5)
    # TODO(you): write a distinct value to each address, then read each back one clock later
    raise NotImplementedError("test_write_then_read: not written yet")


@cocotb.test()
async def test_random_traffic(dut):
    """Random reads and writes against a dict model, checked every cycle."""
    # TODO(you): drive random wr_en/wr_addr/wr_data/rd_addr each falling edge
    # TODO(you): expected rd_data = the model's value for the rd_addr sampled one edge earlier
    raise NotImplementedError("test_random_traffic: not written yet")


@cocotb.test()
async def test_read_during_write(dut):
    """Same-address read and write returns the documented (old) data."""
    # TODO(you): write A to addr 0, then in one cycle write B to addr 0 and read addr 0; expect A
    raise NotImplementedError("test_read_during_write: not written yet")
