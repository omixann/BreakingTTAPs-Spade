# top=xorshift::xorshift_fu

import cocotb
from spade import SpadeExt
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

# Python reference implementation
def xorshift32_py(x):
    x = x & 0xFFFFFFFF
    x ^= (x << 13) & 0xFFFFFFFF
    x ^= (x >> 17) & 0xFFFFFFFF
    x ^= (x << 5) & 0xFFFFFFFF
    return x & 0xFFFFFFFF

CLK_PERIOD_NS = 10

async def start_clock(clk):
    await cocotb.start(Clock(clk, period=CLK_PERIOD_NS, units="ns").start())

async def reset_dut(dut):
    s = SpadeExt(dut)
    s.i.rst = True
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.i.rst = False
    await FallingEdge(dut.clk)
    return s

@cocotb.test()
async def test_reset_behavior(dut):
    """Verify reset state (1) and no output without trigger."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)
    
    # After reset, state is 1, but we always have output
    s.o.assert_eq("Some(270369)")
    
    # Trigger once to see the first value (xorshift32(1))
    s.i.trig = "Some(1)"
    await FallingEdge(dut.clk)
    s.i.trig = "None"
    
    # Expected: xorshift32(1)
    # 1 ^ (1<<13) = 8193
    # 8193 ^ (8193>>17) = 8193
    # 8193 ^ (8193<<5) = 8193 ^ 262176 = 270369
    expected = xorshift32_py(1)
    s.o.assert_eq(f"Some({expected})")
    
    await FallingEdge(dut.clk)
    expected = xorshift32_py(expected)
    s.o.assert_eq(f"Some({expected})")




@cocotb.test()
async def test_free_running(dut):
    """Verify continuous generation from default reset state (1)."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)
    
    # After reset released, the DUT sees trig=None and state=1.
    # It calculates next=xorshift(1) and outputs it at the end of the cycle.
    
    current_seed = 1
    
    # Check 10 consecutive values
    for i in range(10):
        # Expected value for this cycle
        expected = xorshift32_py(current_seed)
        s.o.assert_eq(f"Some({expected})")
        
        # Update seed for next expectation
        current_seed = expected
        
        # Advance clock (trig remains None)
        await FallingEdge(dut.clk)

@cocotb.test()
async def test_free_running_zero(dut):
    """Verify continuous generation from default reset state (1) when using 0 trigger"""
    await start_clock(dut.clk)
    s = await reset_dut(dut)
    
    # After reset released, the DUT sees trig=None and state=1.
    # It calculates next=xorshift(1) and outputs it at the end of the cycle.
    
    current_seed = 1
    s.i.trig = "Some(0)"
    
    # Check 10 consecutive values
    for i in range(10):
        # Expected value for this cycle
        expected = xorshift32_py(current_seed)
        s.o.assert_eq(f"Some({expected})")
        
        # Update seed for next expectation
        current_seed = expected
        
        # Advance clock (trig remains None)
        await FallingEdge(dut.clk)

@cocotb.test()
async def test_reseed(dut):
    """Verify reseeding with trig=Some(seed)."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)
    
    # 1. Let it run for a cycle (state becomes xorshift(1))
    await FallingEdge(dut.clk)
    
    # 2. Reseed with a new value
    seed = 0xDEADBEEF
    s.i.trig = f"Some({seed})"
    await FallingEdge(dut.clk)
    
    # Output should be xorshift(seed)
    expected = xorshift32_py(seed)
    s.o.assert_eq(f"Some({expected})")
    
    # 3. Stop reseeding (back to None), verify it continues from new sequence
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    
    expected_2 = xorshift32_py(expected)
    s.o.assert_eq(f"Some({expected_2})")

@cocotb.test()
async def test_continuous_reseeding(dut):
    """Verify behavior when trig is Some(v) multiple cycles in a row."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)
    
    seeds = [100, 200, 300]
    
    for seed in seeds:
        s.i.trig = f"Some({seed})"
        await FallingEdge(dut.clk)
        
        expected = xorshift32_py(seed)
        s.o.assert_eq(f"Some({expected})")