import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from phase_accumulator import next_phase

WIDTH = 32
INCREMENT = 0x1000_0000
NUM_CYCLES = 100
NUM_RANDOM_CYCLES = 5000
RESET_PROBABILITY = 0.02

@cocotb.test()
async def test_reset(dut):
    clock = Clock(dut.clk, 10 , unit="ns")
    clock.start()

    # reset
    dut.rst.value = 1
    dut.en.value = 0
    dut.increment.value = 0
    for _ in range(2):
        await FallingEdge(dut.clk)

    # check
    actual = int(dut.phase.value)
    assert actual == 0, f"phase={actual:#x} after reset"


@cocotb.test()
async def test_count(dut):
    clock = Clock(dut.clk, 10 , unit = "ns")
    clock.start()

    # reset
    dut.rst.value = 1
    dut.en.value = 0
    dut.increment.value = 0
    for _ in range(2):
        await FallingEdge(dut.clk)

    # release reset and start counting
    dut.rst.value = 0
    dut.en.value = 1
    dut.increment.value = INCREMENT

    expected = 0

    for cycle in range(NUM_CYCLES):
        await FallingEdge(dut.clk)
        expected = next_phase(expected, INCREMENT, 1, 0, WIDTH)
        actual = int(dut.phase.value)
        assert actual == expected, f"cycle {cycle}: phase={actual:#x} expected={expected:#x}"

@cocotb.test()
async def test_random(dut):
    clock = Clock(dut.clk, 10 , unit = "ns")
    clock.start()

    # reset
    dut.rst.value = 1
    dut.en.value = 0
    dut.increment.value = 0
    for _ in range(2):
        await FallingEdge(dut.clk)

    expected = 0

    for cycle in range(NUM_RANDOM_CYCLES):
        # pick random inputs
        rst = 1 if random.random() < RESET_PROBABILITY else 0
        en = random.randint(0,1)
        inc = random.getrandbits(WIDTH)

        #drive onto the DUT
        dut.rst.value = rst
        dut.en.value = en
        dut.increment.value = inc

        #pass one clock cycle
        await FallingEdge(dut.clk)

        #do it with model
        expected = next_phase(expected, inc, en, rst, WIDTH)
        actual = int(dut.phase.value)
        assert actual == expected, f"cycle {cycle}: rst={rst} en={en} inc={inc:#x}"

