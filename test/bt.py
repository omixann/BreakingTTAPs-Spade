#top=bt::bt_fu

import cocotb
from spade import SpadeExt
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge



@cocotb.test()
async def test_reset(dut):
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    s.i.rst = True
    s.i.jump_to = "None"
    s.i.condition_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_jump_true(dut):
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    s.i.rst = True
    s.i.jump_to = "None"
    s.i.condition_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.jump_to = "Some(10)"
    s.i.condition_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.jump_to = "None"
    s.i.condition_trig = "Some(1)"
    await FallingEdge(clk)
    s.o.assert_eq("Some(10)")
    

@cocotb.test()
async def test_jump_false(dut):
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    s.i.rst = True
    s.i.jump_to = "None"
    s.i.condition_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.jump_to = "Some(10)"
    s.i.condition_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.jump_to = "None"
    s.i.condition_trig = "Some(0)"
    await FallingEdge(clk)
    s.o.assert_eq("None")