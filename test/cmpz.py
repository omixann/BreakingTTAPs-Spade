#top=cmpz::cmpz_fu

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
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")
    s.i.rst = False
    await FallingEdge(dut.clk)
    return s

@cocotb.test()
async def test_eqz_Neqz(dut):
    """EQZ/Neqz basic correctness and 1-cycle latency using value in trigger."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    s.i.trig = "Some((CmpzOp::Eqz, 0))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    s.i.trig = "Some((CmpzOp::Neqz, 0))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(0)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")


    s.i.trig = "Some((CmpzOp::Eqz, 5))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(0)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    s.i.trig = "Some((CmpzOp::Neqz, 5))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_signed_boundaries(dut):
    """Signed Sltz/Slez/Sgtz/Sgez around negatives."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    neg2 = 4294967294  # -2
    neg1 = 4294967295  # -1


    s.i.trig = f"Some((CmpzOp::Sltz, {neg2}))"
    await FallingEdge(dut.clk); s.o.assert_eq("Some(1)")
    s.i.trig = "None"; await FallingEdge(dut.clk); s.o.assert_eq("None")

    s.i.trig = f"Some((CmpzOp::Slez, {neg2}))"
    await FallingEdge(dut.clk); s.o.assert_eq("Some(1)")
    s.i.trig = "None"; await FallingEdge(dut.clk); s.o.assert_eq("None")

    s.i.trig = f"Some((CmpzOp::Sgtz, {neg2}))"
    await FallingEdge(dut.clk); s.o.assert_eq("Some(0)")
    s.i.trig = "None"; await FallingEdge(dut.clk); s.o.assert_eq("None")

    s.i.trig = f"Some((CmpzOp::Sgez, {neg2}))"
    await FallingEdge(dut.clk); s.o.assert_eq("Some(0)")
    s.i.trig = "None"; await FallingEdge(dut.clk); s.o.assert_eq("None")

    # A = -1: Sgez should be 0; Slez should be 1
    s.i.trig = f"Some((CmpzOp::Sgez, {neg1}))"
    await FallingEdge(dut.clk); s.o.assert_eq("Some(0)")
    s.i.trig = "None"; await FallingEdge(dut.clk); s.o.assert_eq("None")

    s.i.trig = f"Some((CmpzOp::Slez, {neg1}))"
    await FallingEdge(dut.clk); s.o.assert_eq("Some(1)")
    s.i.trig = "None"; await FallingEdge(dut.clk); s.o.assert_eq("None")

@cocotb.test()
async def test_zero_corner_cases(dut):
    """At zero: Eqz=1, Neqz=0, Slez=1, Sgez=1, Sltz=0, Sgtz=0."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    for op, expect in [
        ("Eqz", 1), ("Neqz", 0), ("Slez", 1),
        ("Sgez", 1), ("Sltz", 0), ("Sgtz", 0),
    ]:
        s.i.trig = f"Some((CmpzOp::{op}, 0))"
        await FallingEdge(dut.clk)
        s.o.assert_eq(f"Some({expect})")
        s.i.trig = "None"
        await FallingEdge(dut.clk)
        s.o.assert_eq("None")

@cocotb.test()
async def test_positive_values(dut):
    """Positive A: Sgtz/Sgez=1, Sltz/Slez=0, Eqz=0, Neqz=1."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    val = 1234

    s.i.trig = f"Some((CmpzOp::Sgtz, {val}))"
    await FallingEdge(dut.clk); s.o.assert_eq("Some(1)")
    s.i.trig = "None"; await FallingEdge(dut.clk); s.o.assert_eq("None")

    s.i.trig = f"Some((CmpzOp::Sgez, {val}))"
    await FallingEdge(dut.clk); s.o.assert_eq("Some(1)")
    s.i.trig = "None"; await FallingEdge(dut.clk); s.o.assert_eq("None")

    s.i.trig = f"Some((CmpzOp::Sltz, {val}))"
    await FallingEdge(dut.clk); s.o.assert_eq("Some(0)")
    s.i.trig = "None"; await FallingEdge(dut.clk); s.o.assert_eq("None")

    s.i.trig = f"Some((CmpzOp::Slez, {val}))"
    await FallingEdge(dut.clk); s.o.assert_eq("Some(0)")
    s.i.trig = "None"; await FallingEdge(dut.clk); s.o.assert_eq("None")

    s.i.trig = f"Some((CmpzOp::Eqz, {val}))"
    await FallingEdge(dut.clk); s.o.assert_eq("Some(0)")
    s.i.trig = "None"; await FallingEdge(dut.clk); s.o.assert_eq("None")

    s.i.trig = f"Some((CmpzOp::Neqz, {val}))"
    await FallingEdge(dut.clk); s.o.assert_eq("Some(1)")
    s.i.trig = "None"; await FallingEdge(dut.clk); s.o.assert_eq("None")

@cocotb.test()
async def test_back_to_back_triggers(dut):
    """Back-to-back triggers yield back-to-back results on subsequent cycles."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Cycle 0 (after reset edge): queue Eqz(0)
    s.i.trig = "Some((CmpzOp::Eqz, 0))"
    await FallingEdge(dut.clk)        # Cycle 1: result for Eqz(0)
    s.o.assert_eq("Some(1)")

    # Immediately queue Neqz(0) for next cycle
    s.i.trig = "Some((CmpzOp::Neqz, 0))"
    await FallingEdge(dut.clk)        # Cycle 2: result for Neqz(0)
    s.o.assert_eq("Some(0)")

    # Immediately queue Sltz(-1) for next cycle
    s.i.trig = "Some((CmpzOp::Sltz, 4294967295))"
    await FallingEdge(dut.clk)        # Cycle 3: result for Sltz(-1) → 1
    s.o.assert_eq("Some(1)")

    # Clear
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")
