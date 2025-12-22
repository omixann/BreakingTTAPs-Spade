# top=sel::sel_fu

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
    s.i.set_cond = "None"
    s.i.set_a = "None"
    s.i.trig_b = "None"
    await FallingEdge(dut.clk)
    s.i.rst = False
    await FallingEdge(dut.clk)
    return s

@cocotb.test()
async def test_sel_true(dut):
    """Test Condition = True (Select A)."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. Setup Cond=True, A=0xAAAA
    s.i.set_cond = "Some(true)"
    s.i.set_a = "Some(43690)" # 0xAAAA
    await FallingEdge(dut.clk)

    # 2. Trigger with B=0xBBBB
    s.i.set_cond = "None"
    s.i.set_a = "None"
    s.i.trig_b = "Some(48059)" # 0xBBBB
    await FallingEdge(dut.clk)

    # 3. Expect A (0xAAAA)
    s.o.assert_eq("Some(43690)")
    s.i.trig_b = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_sel_false(dut):
    """Test Condition = False (Select B)."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. Setup Cond=False, A=0xAAAA
    s.i.set_cond = "Some(false)"
    s.i.set_a = "Some(43690)"
    await FallingEdge(dut.clk)

    # 2. Trigger with B=0xBBBB
    s.i.set_cond = "None"
    s.i.set_a = "None"
    s.i.trig_b = "Some(48059)"
    await FallingEdge(dut.clk)

    # 3. Expect B (0xBBBB)
    s.o.assert_eq("Some(48059)")
    s.i.trig_b = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_toggle_condition(dut):
    """Test toggling condition between triggers."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)
    
    val_a = 100
    val_b = 200

    # Load A=100 once
    s.i.set_a = f"Some({val_a})"
    await FallingEdge(dut.clk)
    s.i.set_a = "None"

    # Loop: Toggle True/False
    for cond_state in [True, False, True]:
        # Set Condition
        s.i.set_cond = f"Some({'true' if cond_state else 'false'})"
        await FallingEdge(dut.clk)
        
        # Trigger
        s.i.set_cond = "None"
        s.i.trig_b = f"Some({val_b})"
        await FallingEdge(dut.clk)
        
        # Check
        expected = val_a if cond_state else val_b
        s.o.assert_eq(f"Some({expected})")
        
        s.i.trig_b = "None"
        await FallingEdge(dut.clk)