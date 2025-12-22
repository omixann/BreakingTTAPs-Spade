#top=lsu::lsu_fu

import cocotb
from spade import SpadeExt
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge

#entity lsu(_fu
#  clk: clock, rst: bool,
#  set_addr_a: Option<uint<32>>,
#  load_trig:  Option<uint<32>>,   // offset B; triggers LOAD
#  store_trig: Option<uint<32>>    // store data; triggers STORE
#) -> Option<uint<32>>

@cocotb.test()
async def test_reset(dut):
    """LSU is None after reset"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    
    s.i.rst = True
    s.i.set_addr_a = "None"
    s.i.load_trig = "None"
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_set_addr_and_load(dut):
    """Set an address in LSU and load mem"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    s.i.rst = True
    s.i.set_addr_a = "None"
    s.i.load_trig = "None"
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_addr_a = "Some(8)"
    s.i.load_trig = "Some(0)"
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("Some(0)") # empty data from the memory slot pre-store

    s.i.rst = False
    s.i.set_addr_a = "None"
    s.i.load_trig = "None"
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None") # gone

@cocotb.test()
async def test_set_addr_store_and_load(dut):
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    s.i.rst = True
    s.i.set_addr_a = "None"
    s.i.load_trig = "None"
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_addr_a = "Some(0)"
    s.i.load_trig = "None"
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_addr_a = "None"
    s.i.load_trig = "None"
    s.i.store_trig = "Some(19)"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_addr_a = "None"
    s.i.load_trig = "Some(0)"
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("Some(19)")

@cocotb.test()
async def test_set_non_zero_addr_store_and_load(dut):
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    s.i.rst = True
    s.i.set_addr_a = "None"
    s.i.load_trig = "None"
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_addr_a = "Some(8)" # set addr to 8
    s.i.load_trig = "None"
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_addr_a = "None"
    s.i.load_trig = "None"
    s.i.store_trig = "Some(19)" # stpre omtp addr 8
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_addr_a = "None"
    s.i.load_trig = "Some(0)"  # load from 8+0  
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("Some(19))") 


@cocotb.test()
async def test_set_addr_and_offset_store_and_load(dut):
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    s.i.rst = True
    s.i.set_addr_a = "None"
    s.i.load_trig = "None"
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_addr_a = "Some(8)"     # set address to 8
    s.i.load_trig = "None"
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_addr_a = "None"    
    s.i.load_trig = "None"
    s.i.store_trig = "Some(19)"    # Store the value (at 8)
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_addr_a = "Some(0)"     # set address back to zero
    s.i.load_trig = "None"      
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")    # empty data from the memory slot pre-store

    s.i.rst = False
    s.i.set_addr_a = "None"     
    s.i.load_trig = "Some(8)"      # load, but offset to 8
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("Some(19)")    # e19 on next clock

    s.i.rst = False
    s.i.set_addr_a = "None"
    s.i.load_trig = "None" # no instruction
    s.i.store_trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None") #  gone