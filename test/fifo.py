# top=fifo::fifo_u8

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from spade import SpadeExt
import random

CLK_PERIOD_NS = 10

async def start_clock(clk):
    await cocotb.start(Clock(clk, period=CLK_PERIOD_NS, units="ns").start())

async def reset_dut(dut):
    s = SpadeExt(dut)
    s.i.rst = True
    s.i.push = "None"
    s.i.pop = False
    await FallingEdge(dut.clk)
    s.i.rst = False
    await FallingEdge(dut.clk)
    return s

@cocotb.test()
async def test_fifo_basic(dut):
    """Verify basic push and pop behavior."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. Check Empty
    s.o.empty.assert_eq(True)
    s.o.full.assert_eq(False)
    s.o.count.assert_eq(0)
    s.o.val.assert_eq("None")

    # 2. Push 10, 20, 30
    dut._log.info("Pushing 10, 20, 30")
    for val in [10, 20, 30]:
        s.i.push = f"Some({val})"
        await FallingEdge(dut.clk)
    s.i.push = "None"

    # Check state
    s.o.empty.assert_eq(False)
    s.o.count.assert_eq(3)
    s.o.val.assert_eq("Some(10)") # Should show head immediately (FWFT)

    # 3. Pop 10
    dut._log.info("Popping 10")
    s.i.pop = True
    await FallingEdge(dut.clk) # Pops 10, head becomes 20
    s.i.pop = False

    s.o.val.assert_eq("Some(20)")
    s.o.count.assert_eq(2)

    # 4. Pop remaining
    await FallingEdge(dut.clk) # Wait a cycle
    s.i.pop = True
    await FallingEdge(dut.clk) # Pops 20
    s.o.val.assert_eq("Some(30)")
    
    await FallingEdge(dut.clk) # Pops 30
    s.i.pop = False
    
    # Check Empty
    s.o.empty.assert_eq(True)
    s.o.val.assert_eq("None")

@cocotb.test()
async def test_fifo_full_wrap(dut):
    """Verify filling the FIFO and wrapping around."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Fill FIFO (Depth 8)
    for i in range(8):
        s.i.push = f"Some({i})"
        await FallingEdge(dut.clk)
    s.i.push = "None"

    s.o.full.assert_eq(True)
    s.o.count.assert_eq(8)
    s.o.val.assert_eq("Some(0)")

    # Try to push when full (should be ignored or handled? 
    # Our logic: do_push = !full || pop. So it should ignore.)
    s.i.push = "Some(99)"
    await FallingEdge(dut.clk)
    s.i.push = "None"

    # Verify 99 was NOT added and count is still 8
    s.o.count.assert_eq(8)
    
    # Drain FIFO
    s.i.pop = True
    for i in range(8):
        s.o.val.assert_eq(f"Some({i})")
        await FallingEdge(dut.clk)
    s.i.pop = False

    s.o.empty.assert_eq(True)

@cocotb.test()
async def test_simultaneous_push_pop(dut):
    """Verify simultaneous push and pop works (count stays same)."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Push 100
    s.i.push = "Some(100)"
    await FallingEdge(dut.clk)
    
    # Push 200 AND Pop (100) same cycle
    s.i.push = "Some(200)"
    s.i.pop = True
    await FallingEdge(dut.clk)
    
    # Should now contain 200 (1 item), 100 is gone
    s.i.push = "None"
    s.i.pop = False
    
    s.o.count.assert_eq(1)
    s.o.val.assert_eq("Some(200)")