"""Phase-0 cocotb testbench for the throwaway counter.

Proves the verification flow: an independent Python model computes the expected
value each cycle, and the testbench asserts the DUT matches it. Every real
module from the NCO onward follows this same shape.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


def model_count(prev, width):
    """Independent reference: next counter value after a non-reset cycle."""
    return (prev + 1) % (1 << width)


@cocotb.test()
async def test_reset_then_count(dut):
    width = 8  # matches the default WIDTH parameter

    # 10 ns period clock on clk
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # Apply synchronous reset for a couple of cycles.
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")  # let the registered output settle past the edge
    assert dut.count.value == 0, f"reset failed: count={dut.count.value}"

    # Release reset and check the DUT against the model for many cycles.
    dut.rst.value = 0
    expected = 0
    for _ in range(3 * (1 << width)):  # wrap around a few times
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        expected = model_count(expected, width)
        got = int(dut.count.value)
        assert got == expected, f"mismatch: got {got}, expected {expected}"
