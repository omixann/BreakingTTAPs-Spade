# top=modadd::modadd_fu

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
    s.i.set_base = "None"
    s.i.set_mask = "None"
    s.i.set_ptr = "None"
    s.i.trig_stride = "None"
    await FallingEdge(dut.clk)
    s.i.rst = False
    await FallingEdge(dut.clk)
    return s

@cocotb.test()
async def test_basic_wrap(dut):
    """Test basic wrapping: 0..3 (Mask=3). Stride=1."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Config: Base=0, Mask=3
    s.i.set_base = "Some(0)"
    s.i.set_mask = "Some(3)"
    s.i.set_ptr  = "Some(0)"
    await FallingEdge(dut.clk)
    s.i.set_base = "None"
    s.i.set_mask = "None"
    s.i.set_ptr  = "None"

    # Step 1: 0 -> 1
    s.i.trig_stride = "Some(1)"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1)")

    # Step 2: 1 -> 2
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(2)")

    # Step 3: 2 -> 3
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(3)")

    # Step 4: 3 -> 0 (Wrap)
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(0)")

    s.i.trig_stride = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_base_offset(dut):
    """Test with Base=0x100, Mask=0xF. ptr should stay in 0x100..0x10F."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    s.i.set_base = "Some(256)" # 0x100
    s.i.set_mask = "Some(15)"  # 0x0F
    s.i.set_ptr  = "Some(270)" # 0x10E (Start near end)
    await FallingEdge(dut.clk)
    s.i.set_base = "None"
    s.i.set_mask = "None"
    s.i.set_ptr  = "None"

    # Step 1: 0x10E + 1 -> 0x10F
    s.i.trig_stride = "Some(1)"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(271)") # 0x10F

    # Step 2: 0x10F + 1 -> 0x100 (Wrap relative to base)
    # Calculation: (0x10F + 1) & 0xF = 0x0. Base | 0 = 0x100.
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(256)") # 0x100

    s.i.trig_stride = "None"
    await FallingEdge(dut.clk)

@cocotb.test()
async def test_simultaneous_load_step(dut):
    """Test setting ptr and stepping in the same cycle."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    s.i.set_base = "Some(0)"
    s.i.set_mask = "Some(255)"
    # Don't set ptr yet, internal is 0.
    await FallingEdge(dut.clk)

    # Set ptr=100 AND Stride=10
    # Expected: (100 + 10) & 255 = 110
    s.i.set_ptr = "Some(100)"
    s.i.trig_stride = "Some(10)"
    s.i.set_base = "None"
    s.i.set_mask = "None"
    await FallingEdge(dut.clk)
    
    s.o.assert_eq("Some(110)")
    
    # Next step: 110 + 10 = 120
    s.i.set_ptr = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(120)")