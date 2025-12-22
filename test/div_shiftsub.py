# top=div_shiftsub::div_shiftsub_fu

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
    s.i.set_op_a = "None"
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.i.rst = False
    await FallingEdge(dut.clk)
    return s

@cocotb.test()
async def test_basic_div(dut):
    """
    Test 100 / 10 = 10.
    Verifies the 32-cycle latency.
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. Load Dividend (A)
    s.i.set_op_a = "Some(100)"
    await FallingEdge(dut.clk)
    s.i.set_op_a = "None"

    # 2. Trigger with Divisor (B)
    s.i.trig = "Some(10)"
    await FallingEdge(dut.clk)
    s.i.trig = "None"
    
    # 3. Wait for calculation (Cycles 0..29)
    for i in range(30):
        await FallingEdge(dut.clk)
        s.o.assert_eq("None")
        
    # 4. Result valid at Cycle 31
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(10)")
    
    # 5. Return to Idle
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_overwrite_op_a(dut):
    """
    Test overwriting Dividend multiple times before trigger.
    Load 50, Load 200, Trigger 5 -> Expect 40.
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    s.i.set_op_a = "Some(50)"
    await FallingEdge(dut.clk)
    
    s.i.set_op_a = "Some(200)" # Should stick
    await FallingEdge(dut.clk)
    
    s.i.trig = "Some(5)"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.i.trig = "None"

    # Wait 31 cycles
    for _ in range(31):
        await FallingEdge(dut.clk)

    s.o.assert_eq("Some(40)")

@cocotb.test()
async def test_simultaneous_load_trigger(dut):
    """
    Test setting Dividend and Divisor in the same cycle.
    100 / 2 = 50.
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    s.i.set_op_a = "Some(100)"
    s.i.trig = "Some(2)"
    await FallingEdge(dut.clk)
    
    s.i.set_op_a = "None"
    s.i.trig = "None"

    # Wait 31 cycles
    for _ in range(31):
        await FallingEdge(dut.clk)

    s.o.assert_eq("Some(50)")

@cocotb.test()
async def test_random_vectors(dut):
    """
    Run 20 random divisions to verify logic.
    Handles Div-by-zero by ensuring B != 0 in test gen 
    (though hardware should output all 1s).
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    for i in range(20):
        a = random.randint(0, 0xFFFFFFFF)
        b = random.randint(1, 0xFFFFFFFF) # Avoid 0 for python check
        
        expected = int(a / b)
        
        # Drive inputs
        s.i.set_op_a = f"Some({a})"
        await FallingEdge(dut.clk)
        
        s.i.trig = f"Some({b})"
        s.i.set_op_a = "None"
        await FallingEdge(dut.clk)
        s.i.trig = "None"
        
        # Wait 31 cycles
        for _ in range(31):
            await FallingEdge(dut.clk)
            
        s.o.assert_eq(f"Some({expected})")
        
        await FallingEdge(dut.clk)

@cocotb.test()
async def test_divide_by_zero(dut):
    """
    Verify behavior when dividing by zero.
    Standard unsigned int logic usually results in MAX_INT (all 1s)
    because subtract always fails (rem < 0 is false), 
    so it shifts 1s into quotient? 
    Actually: if divisor is 0, (rem >= 0) is always true.
    So it subtracts 0 and shifts in 1.
    Result should be 0xFFFFFFFF.
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    s.i.set_op_a = "Some(12345)"
    s.i.trig = "Some(0)"
    await FallingEdge(dut.clk)
    s.i.set_op_a = "None"
    s.i.trig = "None"
    
    for _ in range(31):
        await FallingEdge(dut.clk)
        
    # Expect All 1s
    s.o.assert_eq("Some(4294967295)")