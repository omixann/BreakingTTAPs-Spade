#top=lalu::lalu_fu

import cocotb
from spade import SpadeExt
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge

# tests for Lightweight ALU (add/sub)

@cocotb.test()
async def test_reset(dut):
    """Alu is None after reset"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    
    s.i.rst = True
    s.i.set_op_a = "None"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_set_op_a(dut):
    """Set OPA but without triggering"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    
    s.i.rst = True
    s.i.set_op_a = "None"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_op_a = "Some(19)"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_set_op_a_and_trigger_add(dut):
    """Set OPA then trigger an add operation"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    
    s.i.rst = True
    s.i.set_op_a = "None"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_op_a = "Some(19)"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_op_a = "None"
    s.i.trig = "Some((LAluOp::Add, 1))"
    await FallingEdge(clk)
    s.o.assert_eq("Some(20)")

    s.i.rst = False
    s.i.set_op_a = "None"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None") # resets back to None after 2 cycles

@cocotb.test()
async def test_set_op_a_and_trigger_sub(dut):
    """Set OPA then trigger an subtract operation"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    
    s.i.rst = True
    s.i.set_op_a = "None"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_op_a = "Some(19)"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_op_a = "None"
    s.i.trig = "Some((LAluOp::Sub, 1))"
    await FallingEdge(clk)
    s.o.assert_eq("Some(18)")

    s.i.rst = False
    s.i.set_op_a = "None"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None") # resets back to None after 2 cycles

