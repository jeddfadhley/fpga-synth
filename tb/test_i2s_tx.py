import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge

NUM_RANDOM_FRAMES = 20
NUM_TIMING_FRAMES = 4


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


def drive(dut, left, right, data_w):
    """puts signed left/right samples on the inputs as two's complement"""
    mask = (1 << data_w) - 1
    dut.sample_l.value = left & mask
    dut.sample_r.value = right & mask


async def wait_tick(dut, frame_clks):
    """waits for the falling edge where tick is high; fails if none within a frame"""
    for _ in range(frame_clks + 1):
        await FallingEdge(dut.clk)
        if int(dut.tick.value) == 1:
            return
    assert False, f"tick_missing wait_clks={frame_clks + 1} expected=1 got=0"


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


class I2sReceiver:
    """Listens to the pins the way the amp does: lrclk and data sampled on each BCLK rising edge.
    Collects finished slots as (lr, bits), bits MSB first. Philips format: the bit sampled at the
    edge where LRCLK has just changed is the last bit of the old slot. Everything before the
    first LRCLK change is dropped, since listening starts partway into a slot."""

    def __init__(self, dut):
        self.dut = dut
        self.slots = []

    def start(self):
        cocotb.start_soon(self._run())

    async def _run(self):
        prev_lr = None
        bits = None                         # None until the first LRCLK change
        while True:
            await RisingEdge(self.dut.i2s_bclk)
            lr = int(self.dut.i2s_lrclk.value)
            d = int(self.dut.i2s_data.value)
            if bits is not None:
                bits.append(d)
            if prev_lr is not None and lr != prev_lr:
                if bits is not None:
                    self.slots.append((prev_lr, bits))
                bits = []
            prev_lr = lr

    def frames(self, slot_w, data_w):
        """pairs each left slot with the right slot after it; a right slot with no left before it is dropped"""
        frames = []
        left = None
        for lr, bits in self.slots:
            name = f"{'right' if lr else 'left'}{len(frames)}"
            value = decode_slot(bits, slot_w, data_w, name)
            if lr == 0:
                left = value
            elif left is not None:
                frames.append((left, value))
                left = None
        return frames


async def send_and_check(dut, pairs, garbage_mid_frame=False):
    """Drives pairs[k] so it is captured at tick k+1, then checks the frames decoded from the pins
    equal pairs in order. Frame 1 after reset carries the reset zeros and is dropped by the receiver
    (its left slot starts before the first LRCLK change), so decoded frame k is pairs[k].
    garbage_mid_frame: right after each tick drive the inverse of the next pair, then the real pair at a
    random clock before the next capture; only the value present at the capture may reach the pins."""
    bclk_div, slot_w, data_w = await setup(dut)
    frame_clks = bclk_div * 2 * slot_w
    rx = I2sReceiver(dut)
    rx.start()

    drive(dut, *pairs[0], data_w)
    for k in range(len(pairs)):
        await wait_tick(dut, frame_clks)
        nxt = pairs[k + 1] if k + 1 < len(pairs) else (0, 0)
        if garbage_mid_frame:
            drive(dut, ~nxt[0], ~nxt[1], data_w)
            for _ in range(random.randrange(1, frame_clks - 1)):   # latest: frame_clks-2, one clock before capture
                await FallingEdge(dut.clk)
        drive(dut, *nxt, data_w)

    # the last frame's right slot ends at the first BCLK edge of the frame after it
    for _ in range(2 * frame_clks):
        await FallingEdge(dut.clk)

    frames = rx.frames(slot_w, data_w)
    assert len(frames) >= len(pairs), f"frames_decoded expected>={len(pairs)} got={len(frames)}"
    for k, (exp, got) in enumerate(zip(pairs, frames)):
        assert got[0] == exp[0], f"frame={k} ch=left expected={exp[0]} got={got[0]}"
        assert got[1] == exp[1], f"frame={k} ch=right expected={exp[1]} got={got[1]}"


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
async def test_random_frames(dut):
    """random samples, a new pair every frame, come out of the pins in order"""
    data_w = int(dut.DATA_W.value)
    lo, hi = -(1 << (data_w - 1)), (1 << (data_w - 1)) - 1
    pairs = [(random.randint(lo, hi), random.randint(lo, hi)) for _ in range(NUM_RANDOM_FRAMES)]
    await send_and_check(dut, pairs)


@cocotb.test()
async def test_edge_values(dut):
    """full-scale negative and positive, zero, -1 (all ones) and 1: catches sign, MSB and LSB bugs"""
    data_w = int(dut.DATA_W.value)
    lo, hi = -(1 << (data_w - 1)), (1 << (data_w - 1)) - 1
    pairs = [(lo, hi), (hi, lo), (0, -1), (-1, 0), (1, lo + 1), (lo, lo), (hi, hi)]
    await send_and_check(dut, pairs)


@cocotb.test()
async def test_inputs_change_mid_frame(dut):
    """Contradicts the assumption that inputs only change at tick: the upstream voice datapath
    updates them whenever it likes. Only the value present at the capture may reach the pins."""
    data_w = int(dut.DATA_W.value)
    lo, hi = -(1 << (data_w - 1)), (1 << (data_w - 1)) - 1
    pairs = [(random.randint(lo, hi), random.randint(lo, hi)) for _ in range(NUM_RANDOM_FRAMES)]
    await send_and_check(dut, pairs, garbage_mid_frame=True)


@cocotb.test()
async def test_pin_timing(dut):
    """BCLK is BCLK_DIV/2 clocks low then BCLK_DIV/2 high. LRCLK and data change only on a BCLK
    falling edge, so they are stable at every rising edge where the amp samples them. LRCLK changes
    every SLOT_W bits."""
    bclk_div, slot_w, data_w = await setup(dut)
    frame_clks = bclk_div * 2 * slot_w
    slot_clks = bclk_div * slot_w
    lo, hi = -(1 << (data_w - 1)), (1 << (data_w - 1)) - 1

    prev = None
    bclk_run = 0                # clocks the current BCLK level has lasted
    bclk_changes = 0
    last_lr_change = None
    for t in range(NUM_TIMING_FRAMES * frame_clks):
        await FallingEdge(dut.clk)
        if int(dut.tick.value) == 1:
            drive(dut, random.randint(lo, hi), random.randint(lo, hi), data_w)

        bclk = int(dut.i2s_bclk.value)
        lr = int(dut.i2s_lrclk.value)
        d = int(dut.i2s_data.value)
        if prev is not None:
            p_bclk, p_lr, p_d = prev
            bclk_fell = p_bclk == 1 and bclk == 0
            if lr != p_lr:
                assert bclk_fell, f"pin=lrclk clk={t} change_on expected=bclk_fall got=bclk_{p_bclk}{bclk}"
                if last_lr_change is not None:
                    assert t - last_lr_change == slot_clks, f"pin=lrclk clk={t} half_period_clks expected={slot_clks} got={t - last_lr_change}"
                last_lr_change = t
            if d != p_d:
                assert bclk_fell, f"pin=data clk={t} change_on expected=bclk_fall got=bclk_{p_bclk}{bclk}"
            if bclk != p_bclk:
                if bclk_changes > 0:    # the first level started at reset, so its length is not a half period
                    assert bclk_run == bclk_div // 2, f"pin=bclk clk={t} level={p_bclk} run_clks expected={bclk_div // 2} got={bclk_run}"
                bclk_changes += 1
                bclk_run = 0
        bclk_run += 1
        prev = (bclk, lr, d)

    assert last_lr_change is not None, f"pin=lrclk changes expected>=1 got=0"
