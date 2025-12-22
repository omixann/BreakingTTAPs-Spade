#top=regfile::regfile8_fu

import cocotb
from spade import SpadeExt
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge

#entity regfile8(
#  clk: clock, rst: bool,
#  // write intents for this cycle (applied on next edge)
#  wr0: Option<(uint<3>, uint<32>)>,
#  wr1: Option<(uint<3>, uint<32>)>,
#  // read addresses for this cycle
#  ra0: uint<3>, ra1: uint<3>
#) -> (uint<32>, uint<32>) // (rd0, rd1)

@cocotb.test()
async def test_reset(dut):
    """Registry is zero after reset"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    
    s.i.rst = True
    s.i.wr0 = "None"
    s.i.wr1 = "None"
    s.i.ra0 = 0
    s.i.ra1 = 1
    await FallingEdge(clk)
    s.o.rd0.assert_eq(0)
    s.o.rd1.assert_eq(0)

@cocotb.test()
async def test_store_wr0_get_rd0(dut):
    """Register R0 is one after wr0 set to one"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    
    s.i.rst = True
    s.i.wr0 = "None"
    s.i.wr1 = "None"
    s.i.ra0 = 0
    s.i.ra1 = 1
    await FallingEdge(clk)
    s.o.rd0.assert_eq(0)
    s.o.rd1.assert_eq(0)

    # now set R0 to one
    s.i.rst = False
    s.i.wr0 = "Some((0,1))"
    s.i.wr1 = "None"
    s.i.ra0 = 0
    s.i.ra1 = 1

    await FallingEdge(clk)
    s.o.rd0.assert_eq(1)    #now set to one
    s.o.rd1.assert_eq(0)

@cocotb.test()
async def test_store_all_registers_using_wr0_read_r0(dut):
    """Registers are one after beging set to one, setting with wr0 and reading with r0"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    for i in range(8):
        dut._log.info(f"Register {i}")

        s.i.rst = True
        s.i.wr0 = "None"
        s.i.wr1 = "None"
        s.i.ra0 = 0
        s.i.ra1 = 1
        await FallingEdge(clk)
        s.o.rd0.assert_eq(0)
        s.o.rd1.assert_eq(0)

        # now set R0 to one
        s.i.rst = False
        s.i.wr0 = f"Some(({i},1))"
        s.i.wr1 = "None"
        s.i.ra0 = i
        s.i.ra1 = 1

        await FallingEdge(clk)
        s.o.rd0.assert_eq(1)   


@cocotb.test()
async def test_store_all_registers_using_wr1_read_r0(dut):
    """Registers are one after beging set to one, setting with wr1 and reading with r0"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    for i in range(8):
        dut._log.info(f"Register {i}")

        s.i.rst = True
        s.i.wr0 = "None"
        s.i.wr1 = "None"
        s.i.ra0 = 0
        s.i.ra1 = 1
        await FallingEdge(clk)
        s.o.rd0.assert_eq(0)
        s.o.rd1.assert_eq(0)

        # now set R0 to one
        s.i.rst = False
        s.i.wr0 = "None"
        s.i.wr1 = f"Some(({i},1))"
        s.i.ra0 = i
        s.i.ra1 = 1

        await FallingEdge(clk)
        s.o.rd0.assert_eq(1) 

@cocotb.test()
async def test_store_all_registers_using_wr0_read_r1(dut):
    """Registers are one after beging set to one, setting with wr0 and reading with r1"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    for i in range(8):
        dut._log.info(f"Register {i}")

        s.i.rst = True
        s.i.wr0 = "None"
        s.i.wr1 = "None"
        s.i.ra0 = 0
        s.i.ra1 = 1
        await FallingEdge(clk)
        s.o.rd0.assert_eq(0)
        s.o.rd1.assert_eq(0)

        # now set R0 to one
        s.i.rst = False
        s.i.wr0 = f"Some(({i},1))"
        s.i.wr1 = "None"
        s.i.ra0 = 0
        s.i.ra1 = i

        await FallingEdge(clk)
        s.o.rd1.assert_eq(1)   


@cocotb.test()
async def test_store_all_registers_using_wr1_read_r1(dut):
    """Registers are one after beging set to one, setting with wr1 and reading with r1"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    for i in range(8):
        dut._log.info(f"Register {i}")

        s.i.rst = True
        s.i.wr0 = "None"
        s.i.wr1 = "None"
        s.i.ra0 = 0
        s.i.ra1 = 1
        await FallingEdge(clk)
        s.o.rd0.assert_eq(0)
        s.o.rd1.assert_eq(0)

        # now set R0 to one
        s.i.rst = False
        s.i.wr0 = "None"
        s.i.wr1 = f"Some(({i},1))"
        s.i.ra0 = 0
        s.i.ra1 = i

        await FallingEdge(clk)
        s.o.rd1.assert_eq(1) 

@cocotb.test()
async def test_read_same_register(dut):
    """Read same register in both instruction slots"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    
    s.i.rst = True
    s.i.wr0 = "None"
    s.i.wr1 = "None"
    s.i.ra0 = 0
    s.i.ra1 = 1
    await FallingEdge(clk)
    s.o.rd0.assert_eq(0)
    s.o.rd1.assert_eq(0)

    # now set R0 and R1 to one
    s.i.rst = False
    s.i.wr0 = "Some((0,1))"
    s.i.wr1 = "None"
    
    s.i.ra0 = 0     #read same registers in both slots
    s.i.ra1 = 0

    await FallingEdge(clk)
    s.o.rd0.assert_eq(1)
    s.o.rd1.assert_eq(1)


@cocotb.test()
async def test_read_after_several_clocks(dut):
    """Register R0 is one after several clock cycles"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    
    s.i.rst = True
    s.i.wr0 = "None"
    s.i.wr1 = "None"
    s.i.ra0 = 0
    s.i.ra1 = 1
    await FallingEdge(clk)
    s.o.rd0.assert_eq(0)
    s.o.rd1.assert_eq(0)

    s.i.rst = False
    s.i.wr0 = "Some((0,1))"
    s.i.wr1 = "None"
    s.i.ra0 = 0     #read same registers in both slots
    s.i.ra1 = 0

    await FallingEdge(clk)
    s.o.rd0.assert_eq(1)
    s.o.rd1.assert_eq(1)

    s.i.rst = False
    s.i.wr0 = "None" # Both writes are NOP
    s.i.wr1 = "None"
    s.i.ra0 = 0     #read same registers in both slots
    s.i.ra1 = 0

    await FallingEdge(clk)
    s.o.rd0.assert_eq(1) #Should not have changed
    s.o.rd1.assert_eq(1)

    s.i.rst = False
    s.i.wr0 = "None" # Both writes are NOP
    s.i.wr1 = "None"
    s.i.ra0 = 0     #read same registers in both slots
    s.i.ra1 = 0

    await FallingEdge(clk)
    s.o.rd0.assert_eq(1) #Should not have changed
    s.o.rd1.assert_eq(1)


@cocotb.test()
async def test_wr1_priority_over_wr0(dut):
    """WR1 slot has priority over WR0 slot"""
    s = SpadeExt(dut) # Wrap the dut in the Spade wrapper

    clk = dut.clk

    await cocotb.start(Clock(
        clk,
        period=10,
        units='ns'
    ).start())

    
    s.i.rst = True
    s.i.wr0 = "None"
    s.i.wr1 = "None"
    s.i.ra0 = 0
    s.i.ra1 = 1
    await FallingEdge(clk)
    s.o.rd0.assert_eq(0)
    s.o.rd1.assert_eq(0)

    s.i.rst = False
    s.i.wr0 = "Some((0,1))"
    s.i.wr1 = "Some((0,5))"
    
    s.i.ra0 = 0
    s.i.ra1 = 0

    await FallingEdge(clk)
    s.o.rd0.assert_eq(5)    #should be 5 because WR1 has priority