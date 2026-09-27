
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, Timer
from sine_rom import sine_table


NUM_LATENCY_CYCLES = 5000

@cocotb.test()
async def test_full_sweep(dut):
    """Every address reads back its sine_table() value. One clock per address, so it does not check latency."""
    addr_w = len(dut.address_input)
    data_w = len(dut.sample_output)
    num_addresses = 2**addr_w

    clock = Clock(dut.clk, 10, unit="ns")
    clock.start()

    expected = sine_table(addr_w, data_w)

    for addr in range(num_addresses):
        dut.address_input.value = addr
        await FallingEdge(dut.clk)
        actual = dut.sample_output.value.to_signed()
        expected_value = expected[addr]
        assert actual == expected_value, f"addr {addr}: output={actual} expected={expected_value}"


@cocotb.test()
async def test_latency(dut):
    """The output holds the previous address's value until the next rising edge,
     then changes to the new one. Checks the read is exactly one cycle, which catches a combinational read."""
    addr_w = len(dut.address_input)
    data_w = len(dut.sample_output)

    clock = Clock(dut.clk, 10, unit="ns")
    clock.start()

    expected = sine_table(addr_w, data_w)
    prev = random.getrandbits(addr_w)
    dut.address_input.value = prev
    await FallingEdge(dut.clk)

    for cycle in range(NUM_LATENCY_CYCLES):
        random_input = random.getrandbits(addr_w)
        dut.address_input.value = random_input
        await Timer(1, unit="ns")

        actual_prev = dut.sample_output.value.to_signed()
        expected_prev = expected[prev]
        assert actual_prev == expected_prev, f"addr {prev}: output={actual_prev} expected={expected_prev}"

        await FallingEdge(dut.clk)
        prev = random_input
        actual = dut.sample_output.value.to_signed()
        expected_value = expected[random_input]
        assert actual == expected_value, f"addr {random_input}: output={actual} expected={expected_value}"

