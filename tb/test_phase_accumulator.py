import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
from pexpect import expect
from phase_accumulator import next_phase

WIDTH = 32
INCREMENT = 0x1000_0000

@cocotb.test()
async def test_reset(dut):
    clock = Clock(dut.clk, 10 , unit = "ns")
    clock.start()

    #reset
    dut.rst.value = 1
    dut.en.value = 0
    dut.increment.value = 0
    for _ in range(2):
        await FallingEdge(dut.clk)

    #release reset and start counting
    dut.rst.value = 0
    dut.en.value = 1
    dut.increment.value = INCREMENT

    expected = 0

    for cycle in range(40):
        await FallingEdge(dut.clk)
        expected = next_phase(expected, INCREMENT, 1, 0, WIDTH)
        actual = int(dut.phase.value)
        assert actual == expected, f"cycle {cycle}: phase={actual:#x} expected={expected:#x}"
