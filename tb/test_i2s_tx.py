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

@cocotb.test()
async def test_watch_pins(dut):
    bclk_div, slot_w, data_w = await setup(dut)
    dut.sample_l.value = 0x8001
    dut.sample_r.value = 0x00FF

    for i in range(150):
        await RisingEdge(dut.i2s_bclk)
        lr = int(dut.i2s_lrclk.value)
        d = int(dut.i2s_data.value)
        print(i, lr, d)


# @cocotb.test()
# async def test_constant_frame(dut):
#     bclk_div, slot_w, data_w = await setup(dut)
#     frame_clks = bclk_div * 2 * slot_w



def decode_slot(bits, slot_w, data_w, name):
    """function to decode the slot"""
    assert len(bits) == slot_w, f"slot={name} bits expected={slot_w} got={len(bits)}"
    assert not any(bits[data_w:]) , f"slot={name} padding expected={0} got={bits[data_w:]}"
    value = 0
    for bit in bits[:data_w]:
        value = (value << 1) | bit
    if value & (1 << (data_w - 1)):
        value -= 1 << data_w
    return value

# class I2sReceiver:
#     def __init__(self, bclk, lrclk, data, slot_w, data_w):
#
#     def start(self):
#
#     async def _run(self):
