import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from nco import FS, Nco, frequency_of, increment_for

NUM_RANDOM_CYCLES = 5000
RESET_PROBABILITY = 0.02
NUM_FREQ_SAMPLES = 4096
FREQ_HZ = 1000
NUM_HELD_CYCLES = 200


async def setup(dut):
    """starts clock, holds reset for 3 cycles with inputs at zero, then returns (phase_w, addr_w, data_w).
    3 cycles: phase is 0 after the first, and the ROM shows table[0] after the second."""
    clock = Clock(dut.clk, 10, unit="ns")
    clock.start()

    dut.rst.value = 1
    dut.en.value = 0
    dut.increment.value = 0
    for _ in range(3):
        await FallingEdge(dut.clk)
    dut.rst.value = 0

    return len(dut.increment), int(dut.ADDR_W.value), len(dut.sample)


async def step(dut, model, rst, en, inc, cycle, test):
    """drives one clock on the DUT and the model and checks both outputs"""
    dut.rst.value = rst
    dut.en.value = en
    dut.increment.value = inc
    await FallingEdge(dut.clk)
    exp_sample, exp_valid = model.step(rst, en, inc)
    got_sample = dut.sample.value.to_signed()
    got_valid = int(dut.sample_valid.value)
    assert got_valid == exp_valid, f"test={test} cycle={cycle} rst={rst} en={en} sig=sample_valid expected={exp_valid} got={got_valid}"
    assert got_sample == exp_sample, f"test={test} cycle={cycle} rst={rst} en={en} sig=sample expected={exp_sample} got={got_sample}"
    return got_sample, got_valid


@cocotb.test()
async def test_reset(dut):
    """after reset: sample_valid 0 and sample is table[0] = 0 (phase 0)"""
    await setup(dut)
    got_valid = int(dut.sample_valid.value)
    got_sample = dut.sample.value.to_signed()
    assert got_valid == 0, f"test=reset sig=sample_valid expected=0 got={got_valid}"
    assert got_sample == 0, f"test=reset sig=sample expected=0 got={got_sample}"


@cocotb.test()
async def test_en_pulse_latency(dut):
    """One en pulse with a quarter-cycle increment. Expected values worked out by hand, not from the
    model: sample goes from sin(0) = 0 to sin(pi/2) = +max exactly 2 clocks after en, with
    sample_valid high for that one clock only."""
    phase_w, addr_w, data_w = await setup(dut)
    full = 2**(data_w - 1) - 1
    quarter = 2**phase_w // 4

    dut.en.value = 1
    dut.increment.value = quarter
    await FallingEdge(dut.clk)                  # edge 0: phase <- quarter
    dut.en.value = 0
    expected = [(0, 0), (full, 1), (full, 0), (full, 0)]   # (sample, sample_valid) after edges 0, 1, 2, 3
    for edge, (exp_sample, exp_valid) in enumerate(expected):
        if edge > 0:
            await FallingEdge(dut.clk)
        got_sample = dut.sample.value.to_signed()
        got_valid = int(dut.sample_valid.value)
        assert got_valid == exp_valid, f"test=en_pulse edge={edge} sig=sample_valid expected={exp_valid} got={got_valid}"
        assert got_sample == exp_sample, f"test=en_pulse edge={edge} sig=sample expected={exp_sample} got={got_sample}"


@cocotb.test()
async def test_random(dut):
    """random rst, en and increment every clock, checked against the model every clock.
    Half the random increments are above half a cycle, so this also covers aliasing."""
    phase_w, addr_w, data_w = await setup(dut)
    model = Nco(phase_w, addr_w, data_w)
    for cycle in range(NUM_RANDOM_CYCLES):
        rst = 1 if random.random() < RESET_PROBABILITY else 0
        en = random.randint(0, 1)
        inc = random.getrandbits(phase_w)
        await step(dut, model, rst, en, inc, cycle, "random")


@cocotb.test()
async def test_en_held_high(dut):
    """Contradicts the assumption that en is a sparse tick (one clock in 2048): with en high every
    clock there is a new sample every clock, and sample_valid stays high from the second clock on."""
    phase_w, addr_w, data_w = await setup(dut)
    model = Nco(phase_w, addr_w, data_w)
    inc = increment_for(FREQ_HZ, phase_w)
    for cycle in range(NUM_HELD_CYCLES):
        _, got_valid = await step(dut, model, 0, 1, inc, cycle, "en_held")
        if cycle >= 1:
            assert got_valid == 1, f"test=en_held cycle={cycle} sig=sample_valid expected=1 got={got_valid}"


@cocotb.test()
async def test_frequency(dut):
    """Counts rising zero crossings over NUM_FREQ_SAMPLES samples at FREQ_HZ: checks
    f_out = increment * fs / 2**PHASE_W without using the model's per-clock values."""
    phase_w, addr_w, data_w = await setup(dut)
    inc = increment_for(FREQ_HZ, phase_w)
    dut.en.value = 1
    dut.increment.value = inc

    samples = []
    while len(samples) < NUM_FREQ_SAMPLES:
        await FallingEdge(dut.clk)
        if int(dut.sample_valid.value):
            samples.append(dut.sample.value.to_signed())

    crossings = sum(1 for a, b in zip(samples, samples[1:]) if a < 0 <= b)
    expected = frequency_of(inc, phase_w) * NUM_FREQ_SAMPLES / FS
    assert abs(crossings - expected) <= 1, f"test=frequency f_hz={FREQ_HZ} crossings expected={expected:.2f} got={crossings}"


@cocotb.test()
async def test_alias(dut):
    """Increment above half a cycle: 7/8 cycle per sample is really -1/8, so the output must be the
    1/8-cycle output negated (sin(-x) = -sin(x), and the table is odd-symmetric)."""
    phase_w, addr_w, data_w = await setup(dut)
    eighth = 2**phase_w // 8

    async def run(inc):
        model = Nco(phase_w, addr_w, data_w)
        dut.rst.value = 1
        for _ in range(3):
            await FallingEdge(dut.clk)
        model.step(1, 0, 0)
        model.step(1, 0, 0)
        model.step(1, 0, 0)
        out = []
        for cycle in range(32):
            sample, valid = await step(dut, model, 0, 1, inc, cycle, f"alias_inc={inc:#x}")
            if valid:
                out.append(sample)
        return out

    slow = await run(eighth)
    fast = await run(7 * eighth)
    for n, (s, f) in enumerate(zip(slow, fast)):
        assert f == -s, f"test=alias sample={n} expected={-s} got={f}"
