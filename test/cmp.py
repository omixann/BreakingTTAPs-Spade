#top=cmp::cmp_fu

import cocotb
from spade import SpadeExt
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

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
async def test_eq_true_false(dut):
    """Set A, then EQ true then false; result visible for 1 cycle."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Set A = 10
    s.i.set_op_a = "Some(10)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # Trigger EQ with B=10 -> 1 next cycle
    s.i.set_op_a = "None"
    s.i.trig = "Some((CmpOp::Eq, 10))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1)")
    # Then clears back to None
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # Trigger EQ with B=9 -> 0 next cycle
    s.i.trig = "Some((CmpOp::Eq, 9))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(0)")
     # Then clears back to None
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_neq(dut):
    """NEQ produces 0 when equal and 1 when not equal."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 7
    s.i.set_op_a = "Some(7)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # NEQ 7 -> 0
    s.i.set_op_a = "None"
    s.i.trig = "Some((CmpOp::Neq, 7))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(0)")
     # Then clears back to None
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # NEQ 5 -> 1
    s.i.trig = "Some((CmpOp::Neq, 5))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1)")
    # Then clears back to None
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_signed_lt_le(dut):
    """Signed comparisons across negative/positive boundary."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0xFFFF_FFFE (-2)
    s.i.set_op_a = "Some(4294967294)"  # -2 in two's complement
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # SLT A(-2) < B(1) -> 1
    s.i.trig = "Some((CmpOp::Slt, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1)")
    # Then clears back to None
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # SLE A(-2) <= B(-1) -> 1
    s.i.trig = "Some((CmpOp::Sle, 4294967295))"  # -1
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1)")
    # Then clears back to None
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # SLT A(-2) < B(-3) -> 0 (since -2 !< -3)
    s.i.trig = "Some((CmpOp::Slt, 4294967293))"  # -3
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(0)")
    # Then clears back to None
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_unsigned_lt_le(dut):
    """Unsigned < and <= with high MSB values."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0xFFFF_FFFF (4294967295)
    s.i.set_op_a = "Some(4294967295)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # ULT A < 1 -> 0 (since 0xFFFF_FFFF > 1 unsigned)
    s.i.trig = "Some((CmpOp::Ult, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(0)")
    # Then clears back to None
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # ULE A <= 0xFFFF_FFFF -> 1
    s.i.trig = "Some((CmpOp::Ule, 4294967295))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1)")
    # Then clears back to None
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_latency_and_persistence(dut):
    """Result appears exactly next cycle, then clears; A persists until overwritten."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Set A = 123
    s.i.set_op_a = "Some(123)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # Wait a couple cycles (no new set_op_a), then trigger EQ with B=123 => still uses latched A
    await FallingEdge(dut.clk)
    await FallingEdge(dut.clk)
    s.i.trig = "Some((CmpOp::Eq, 123))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1)")
    # Then clears back to None
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # Back-to-back triggers produce back-to-back outputs on subsequent cycles
    s.i.trig = "Some((CmpOp::Eq, 0))"  # false
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(0)")
    # queue another trigger immediately
    s.i.trig = "Some((CmpOp::Neq, 999))"  # true
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1)")
    # clear
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")
