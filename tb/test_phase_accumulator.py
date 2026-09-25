import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge

@cocotb.test()
async def test_reset(dut):
    clock = Clock(dut.clk, 10 , unit = "ns")
    clock.start()
    dut.rst.value = 1
    dut.en.value = 0
    dut.increment.value = 0

    for _ in range(2):
        await FallingEdge(dut.clk)

    assert int(dut.phase.value) == 0, f"phase={int(dut.phase.value)} after reset"
