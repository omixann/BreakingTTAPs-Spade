#top=bit::bit_fu

import cocotb
from spade import SpadeExt
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge



CLK_NS = 10

async def start_clock(clk):
    await cocotb.start(Clock(clk, period=CLK_NS, units='ns').start())

async def reset_dut(dut):
    s = SpadeExt(dut)
    s.i.rst = True
    s.i.set_op_a = "None"
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")
    s.i.rst = False
    await FallingEdge(dut.clk)
    return s



@cocotb.test()
async def test_clz(dut):
    """Count Leading Zeros."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. 0x0000000F -> 28 zeros
    s.i.set_op_a = "Some(15)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    
    s.i.trig = "Some((BitOp::Clz, 0))" # Operand B ignored for CLZ
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(28)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # 2. 0xFFFFFFFF -> 0 zeros
    s.i.set_op_a = "Some(4294967295)"
    await FallingEdge(dut.clk)
    
    s.i.trig = "Some((BitOp::Clz, 0))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(0)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_ctz(dut):
    """Count Trailing Zeros."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. 0xF0000000 -> 28 zeros at end
    s.i.set_op_a = "Some(4026531840)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((BitOp::Ctz, 0))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(28)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # 2. 0x00000008 -> 3 zeros
    s.i.set_op_a = "Some(8)"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((BitOp::Ctz, 0))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(3)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_popcnt(dut):
    """Population Count."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. 0x0000FFFF -> 16 bits
    s.i.set_op_a = "Some(65535)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((BitOp::Popcnt, 0))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(16)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # 2. 0xAAAAAAAA -> 16 bits
    s.i.set_op_a = "Some(2863311530)"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((BitOp::Popcnt, 0))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(16)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_brev(dut):
    """Bit Reverse."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 0x00000001 -> 0x80000000
    s.i.set_op_a = "Some(1)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((BitOp::Brev, 0))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(2147483648)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_bset(dut):
    """Bit Set."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Set bit 4 of 0 -> 16
    s.i.set_op_a = "Some(0)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((BitOp::Bset, 4))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(16)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_bclr(dut):
    """Bit Clear."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Clear bit 0 of 1 -> 0
    s.i.set_op_a = "Some(1)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((BitOp::Bclr, 0))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(0)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_bext(dut):
    """Bitfield Extract."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Extract nibble at offset 4.
    # Pattern: 0xBA (10111010). Offset 4 is 'B' (1011).
    # Width=4 (encoded as 3 in upper bits). LSB=4.
    # Control = (3 << 5) | 4 = 96 | 4 = 100
    s.i.set_op_a = "Some(186)" # 0xBA
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((BitOp::Bext, 100))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(11)") # 0xB
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_bins(dut):
    """Bitfield Insert."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Deposit 0xF into position 8.
    # Val=0xFF (take low 4 bits -> 0xF). LSB=8. Width=4.
    # Control = (3 << 5) | 8 = 96 | 8 = 104
    s.i.set_op_a = "Some(255)" # 0xFF
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((BitOp::Bins, 104))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(3840)") # 0xF00
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

