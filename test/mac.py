# top=mac::mac_fu

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
    s.i.set_op_a = "None"
    s.i.trig = "None"
    s.i.clr = False
    await FallingEdge(dut.clk)
    s.i.rst = False
    await FallingEdge(dut.clk)
    return s

@cocotb.test()
async def test_basic_mac(dut):
    """Test basic Multiply-Accumulate: 2*3 + 4*5 = 6 + 20 = 26."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. Load A=2
    s.i.set_op_a = "Some(2)"
    await FallingEdge(dut.clk)
    
    # 2. Trigger B=3 (Acc += 2*3 = 6)
    s.i.set_op_a = "None"
    s.i.trig = "Some(3)"
    await FallingEdge(dut.clk)
    
    # Check Result (Latency 1)
    s.o.assert_eq("Some(6)")
    s.i.trig = "None"
    
    # 3. Load A=4
    s.i.set_op_a = "Some(4)"
    await FallingEdge(dut.clk)
    
    # 4. Trigger B=5 (Acc += 4*5 = 20 -> Total 26)
    s.i.set_op_a = "None"
    s.i.trig = "Some(5)"
    await FallingEdge(dut.clk)
    
    # Check Result
    s.o.assert_eq("Some(26)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_clr(dut):
    """Verify synchronous clear."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Accumulate 10*10 = 100
    s.i.set_op_a = "Some(10)"
    await FallingEdge(dut.clk)
    s.i.trig = "Some(10)"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(100)")

    # Assert Clear
    s.i.trig = "None"
    s.i.clr = True
    await FallingEdge(dut.clk)
    
    # Output should confirm 0
    s.o.assert_eq("Some(0)")
    
    # Verify internal state is 0 by adding 5*2
    s.i.clr = False
    s.i.set_op_a = "Some(5)"
    await FallingEdge(dut.clk)
    s.i.trig = "Some(2)"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    
    # Should be 0 + 10 = 10 (not 110)
    s.o.assert_eq("Some(10)")

@cocotb.test()
async def test_read_without_modify(dut):
    """Verify reading accumulator by multiplying by 0."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Set Acc = 50
    s.i.set_op_a = "Some(50)"
    await FallingEdge(dut.clk)
    s.i.trig = "Some(1)"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(50)")
    
    # Read without changing (Acc += 0*0)
    s.i.set_op_a = "Some(0)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    
    s.i.trig = "Some(0)"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(50)")