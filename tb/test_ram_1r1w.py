import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge


@cocotb.test()
async def test_full_sweep(dut):
    """Writes a value to every address, then tries to overwrite them with wr_en off, then reads back and checks the first values survived."""
    depth = int(dut.DEPTH.value)

    clock = Clock(dut.clk, 10, unit="ns")
    clock.start()

    for addr in range(depth):
        dut.wr_addr.value = addr
        dut.wr_en.value = 1
        dut.wr_data.value = addr * 1000 + 7
        await FallingEdge(dut.clk)

    for addr in range(depth):
        dut.wr_addr.value = addr
        dut.wr_en.value = 0
        dut.wr_data.value = addr * 1000 + 5
        await FallingEdge(dut.clk)

    for addr in range(depth):
        dut.rd_addr.value = addr
        await FallingEdge(dut.clk)
        output = int(dut.rd_data.value)
        assert output == addr * 1000 + 7 , f"addr {addr}: output={output} expected={addr * 1000 + 7}"


@cocotb.test()
async def test_same_box_same_clock(dut):
    """Writing and reading the same box in one clock returns the old value; the new value is there on the next clock."""
    depth = int(dut.DEPTH.value)

    clock = Clock(dut.clk, 10, unit="ns")
    clock.start()

    for addr in range(depth):
        old = addr * 1000 + 1
        new = addr * 1000 + 2

        #step 1: put known old value in the box
        dut.wr_addr.value = addr
        dut.wr_en.value = 1
        dut.wr_data.value = old
        await FallingEdge(dut.clk)

        #step 2: write new and read the same box in the same clock
        dut.wr_addr.value = addr
        dut.rd_addr.value = addr

        dut.wr_en.value = 1
        dut.wr_data.value = new
        await FallingEdge(dut.clk)

        output = int(dut.rd_data.value)
        assert output == old , f"addr {addr}: output={output} expected={old}"

        #step 3: stop writing and read again
        dut.wr_en.value = 0
        await FallingEdge(dut.clk)
        output = int(dut.rd_data.value)
        assert output == new , f"addr {addr}: output={output} expected={new}"
