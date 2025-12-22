# top=stack_lsu::stack_lsu_fu

import cocotb
from spade import SpadeExt
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

CLK_PERIOD_NS = 10

async def start_clock(clk):
    await cocotb.start(Clock(clk, period=CLK_PERIOD_NS, units="ns").start())

async def reset_dut(dut):
    s = SpadeExt(dut)
    s.i.rst = True
    s.i.set_sp = "None"
    s.i.pop_trig = False
    s.i.push_trig = "None"
    await FallingEdge(dut.clk)
    s.i.rst = False
    await FallingEdge(dut.clk)
    return s

@cocotb.test()
async def test_push_pop_sequence(dut):
    """Test pushing 3 values and popping them back (LIFO order)."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. Initialize SP to 100
    # Stack grows down, so 100 is the "start" (empty).
    s.i.set_sp = "Some(100)"
    await FallingEdge(dut.clk)
    s.i.set_sp = "None"

    # 2. Push 0xA (Expected Addr: 99)
    s.i.push_trig = "Some(10)"
    await FallingEdge(dut.clk)
    s.i.push_trig = "None"

    # 3. Push 0xB (Expected Addr: 98)
    s.i.push_trig = "Some(11)"
    await FallingEdge(dut.clk)
    s.i.push_trig = "None"

    # 4. Push 0xC (Expected Addr: 97)
    s.i.push_trig = "Some(12)"
    await FallingEdge(dut.clk)
    s.i.push_trig = "None"

    # Current SP should be 97. Data at 97=12, 98=11, 99=10.

    # 5. Pop 1 (Should get 0xC / 12)
    # Read addr 97, SP becomes 98
    s.i.pop_trig = True
    await FallingEdge(dut.clk)
    s.i.pop_trig = False
    s.o.assert_eq("Some(12)")

    # 6. Pop 2 (Should get 0xB / 11)
    # Read addr 98, SP becomes 99
    s.i.pop_trig = True
    await FallingEdge(dut.clk)
    s.i.pop_trig = False
    s.o.assert_eq("Some(11)")

    # 7. Pop 3 (Should get 0xA / 10)
    # Read addr 99, SP becomes 100
    s.i.pop_trig = True
    await FallingEdge(dut.clk)
    s.i.pop_trig = False
    s.o.assert_eq("Some(10)")

@cocotb.test()
async def test_interleaved_push_pop(dut):
    """Test mixed push/pop operations."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Start at 50
    s.i.set_sp = "Some(50)"
    await FallingEdge(dut.clk)
    s.i.set_sp = "None"

    # Push 100
    s.i.push_trig = "Some(100)"
    await FallingEdge(dut.clk)
    s.i.push_trig = "None"

    # Pop 100
    s.i.pop_trig = True
    await FallingEdge(dut.clk)
    s.i.pop_trig = False
    s.o.assert_eq("Some(100)")

    # Push 200
    s.i.push_trig = "Some(200)"
    await FallingEdge(dut.clk)
    
    # Push 300 immediately after
    s.i.push_trig = "Some(300)"
    await FallingEdge(dut.clk)
    s.i.push_trig = "None"

    # Pop (should be 300)
    s.i.pop_trig = True
    await FallingEdge(dut.clk)
    s.i.pop_trig = False
    s.o.assert_eq("Some(300)")