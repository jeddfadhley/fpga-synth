import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge ,with_timeout

async def setup(dut):
    """starts clock holds reset for 2 cycles, inputs at zero then returns parameters"""
    clock = Clock(dut.clk, 10 , unit = "ns")
    clock.start()

    #reset
    dut.rst.value = 1
    dut.sample_r.value = 0
    dut.sample_l.value = 0

    for _ in range(2):
        await FallingEdge(dut.clk)
    dut.rst.value = 0

    #parameters
    return int(dut.BCLK_DIV.value) , int(dut.SLOT_W.value), int(dut.DATA_W.value)

@cocotb.test()
async def test_tick_period(dut):
    bclk_div, slot_w, data_w = await setup(dut)
    frame_clks = bclk_div * 2 * slot_w

    count = 0
    ticks_seen = 0

    for _ in range(6* frame_clks):
        await FallingEdge(dut.clk)
        count = count + 1
        if int(dut.tick.value) == 1:
            if ticks_seen > 0:
                assert count == frame_clks, f"tick={ticks_seen} gap_clks expected={frame_clks} got={count}"
            count = 0
            ticks_seen = ticks_seen + 1
    assert ticks_seen >= 5, f"min ticks expected=5  got={ticks_seen} count={count}"



