# top=mul_shiftadd::mul_shiftadd_fu

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
async def test_basic_mult(dut):
    """
    Test 10 * 20 = 200. 
    Verifies the 32-cycle latency.
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. Load Operand A
    s.i.set_op_a = "Some(10)"
    await FallingEdge(dut.clk)
    s.i.set_op_a = "None"

    # 2. Trigger with Operand B
    s.i.trig = "Some(20)"
    await FallingEdge(dut.clk)
    s.i.trig = "None"
    
    # State is now Calc, cnt=0. Output should be None.
    s.o.assert_eq("None")

    # 3. Wait for calculation
    # We are at cnt=0. We need 31 edges to reach cnt=31.
    # The first 30 edges (cnt increments to 1..30) should produce None.
    for i in range(30):
        await FallingEdge(dut.clk)
        s.o.assert_eq("None")
        
    # The 31st edge reaches cnt=31. The output becomes valid HERE.
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(200)")
    
    # 4. Verify return to Idle
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_overwrite_op_a(dut):
    """
    Test that Op A can be overwritten multiple times before trigger.
    Scenario: Load 5, Load 50, Load 100 -> Trigger with 2. Result should be 200.
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    s.i.set_op_a = "Some(5)"
    await FallingEdge(dut.clk)
    
    s.i.set_op_a = "Some(50)"
    await FallingEdge(dut.clk)
    
    s.i.set_op_a = "Some(100)" # This is the one that should stick
    await FallingEdge(dut.clk)
    
    # Trigger with B=2, while clearing set_op_a
    s.i.set_op_a = "None" 
    s.i.trig = "Some(2)"
    await FallingEdge(dut.clk)
    s.i.trig = "None"

    # Wait 31 cycles
    for _ in range(31):
        await FallingEdge(dut.clk)

    # Check result: 100 * 2 = 200
    s.o.assert_eq("Some(200)")

@cocotb.test()
async def test_simultaneous_load_trigger(dut):
    """
    Test setting Op A and Triggering in the SAME cycle.
    Your logic: `let next_a = match set_op_a ...; match trig ...`
    allows immediate use of the new A.
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Set A=10 and B=10 simultaneously
    s.i.set_op_a = "Some(10)"
    s.i.trig = "Some(10)"
    await FallingEdge(dut.clk)
    
    s.i.set_op_a = "None"
    s.i.trig = "None"

    # Wait 31 cycles
    for _ in range(31):
        await FallingEdge(dut.clk)

    # Check result: 10 * 10 = 100
    s.o.assert_eq("Some(100)")

@cocotb.test()
async def test_random_vectors(dut):
    """
    Run 50 random multiplications to verify logic and overflow behavior.
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    for i in range(50):
        # Use full 32-bit range to test overflow behavior (wrapping)
        a = random.randint(0, 0xFFFFFFFF)
        b = random.randint(0, 0xFFFFFFFF)
        
        # Expected result modulo 2^32
        expected = (a * b) & 0xFFFFFFFF
        
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
            
        # Check result
        s.o.assert_eq(f"Some({expected})")
        
        # Wait one cycle for Idle before next loop
        await FallingEdge(dut.clk)

@cocotb.test()
async def test_simultaneous_load_trigger(dut):
    """
    Test setting Op A and Triggering in the SAME cycle.
    Your logic: `let next_a = match set_op_a ...; match trig ...`
    allows immediate use of the new A.
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Set A=10 and B=10 simultaneously
    s.i.set_op_a = "Some(10)"
    s.i.trig = "Some(10)"
    await FallingEdge(dut.clk)
    
    s.i.set_op_a = "None"
    s.i.trig = "None"

    # Wait 31 cycles
    for _ in range(31):
        await FallingEdge(dut.clk)

    # Check result: 10 * 10 = 100
    s.o.assert_eq("Some(100)")

@cocotb.test()
async def test_ignore_inputs_during_calc(dut):
    """
    Requested Test: start a multiplication, then set opA and trigger 
    while running, to show that they don't affect the final result.
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. Start clean multiplication 10 * 10 = 100
    s.i.set_op_a = "Some(10)"
    await FallingEdge(dut.clk)
    s.i.trig = "Some(10)"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.i.trig = "None"

    # We are now in Calc state.
    # Wait 5 cycles to be well inside calculation
    for _ in range(5):
        await FallingEdge(dut.clk)
        
    # 2. Try to sabotage the calculation
    # These inputs should be IGNORED by the state machine in State::Calc
    s.i.set_op_a = "Some(999999)"
    s.i.trig     = "Some(999999)"
    await FallingEdge(dut.clk)
    
    # 3. Clear inputs and finish wait
    s.i.set_op_a = "None"
    s.i.trig     = "None"
    
    # We waited 5 cycles, then 1 cycle sabotage. Total 6. 
    # Need to wait 31 - 6 = 25 more cycles.
    for _ in range(25):
        await FallingEdge(dut.clk)

    # 4. Check result. If sabotage worked, result would be massive or incorrect.
    # It should remain 100.
    s.o.assert_eq("Some(100)")