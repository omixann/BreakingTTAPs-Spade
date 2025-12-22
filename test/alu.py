#top=alu::alu_fu

import cocotb
from spade import SpadeExt
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge

#//============================================================
#// ALU functional unit
#// - Write ALU_OpA to set operand A
#// - Write *_Trig (with a value) to trigger op(BusValue) with opA
#// - One-cycle latency: result visible as ALU_Res in the *next* cycle
#//============================================================
#entity alu(
#  clk: clock, rst: bool,
#  set_op_a: Option<uint<32>>,
#  trig:    Option<(AluOp, uint<32>)>
#) -> Option<uint<32>>


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
    s.i.trig = "Some((AluOp::Add, 1))"
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
    s.i.trig = "Some((AluOp::Sub, 1))"
    await FallingEdge(clk)
    s.o.assert_eq("Some(18)")

    s.i.rst = False
    s.i.set_op_a = "None"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None") # resets back to None after 2 cycles

@cocotb.test()
async def test_set_op_a_and_trigger_and(dut):
    """Set OPA then trigger an AND operation"""
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
    s.i.set_op_a = "Some(6)"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_op_a = "None"
    s.i.trig = "Some((AluOp::And, 10))"
    await FallingEdge(clk)
    s.o.assert_eq("Some(2)")

    s.i.rst = False
    s.i.set_op_a = "None"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None") # resets back to None after 2 cycles

@cocotb.test()
async def test_set_op_a_and_trigger_or(dut):
    """Set OPA then trigger an OR operation"""
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
    s.i.set_op_a = "Some(6)"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_op_a = "None"
    s.i.trig = "Some((AluOp::Or, 10))"
    await FallingEdge(clk)
    s.o.assert_eq("Some(14)")

    s.i.rst = False
    s.i.set_op_a = "None"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None") # resets back to None after 2 cycles

@cocotb.test()
async def test_set_op_a_and_trigger_xor(dut):
    """Set OPA then trigger an XOR operation"""
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
    s.i.set_op_a = "Some(6)"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None")

    s.i.rst = False
    s.i.set_op_a = "None"
    s.i.trig = "Some((AluOp::Xor, 10))"
    await FallingEdge(clk)
    s.o.assert_eq("Some(12)")

    s.i.rst = False
    s.i.set_op_a = "None"
    s.i.trig = "None"
    await FallingEdge(clk)
    s.o.assert_eq("None") # resets back to None after 2 cycles


# ------------ Logical shift left/right ------------


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
async def test_left_basic(dut):
    """Set A then Left shift by various amounts; 1-cycle latency."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0x0000_0003
    s.i.set_op_a = "Some(3)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # << 1 => 6
    s.i.set_op_a = "None"
    s.i.trig = "Some((AluOp::Shl, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(6)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # << 4 => 3 << 4 = 48
    s.i.trig = "Some((AluOp::Shl, 4))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(48)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_right_basic(dut):
    """Set A then Right shift by various amounts; zero-fill on the left."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0x8000_0001
    s.i.set_op_a = "Some(2147483649)"  # 0x80000001
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # >> 1 => 0x4000_0000 (logical)
    s.i.trig = "Some((AluOp::Shr, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1073741824)")  # 0x40000000
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # >> 31 => 1
    s.i.trig = "Some((AluOp::Shr, 31))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_zero_and_max_shift(dut):
    """Shift by 0 (no-op) and by 31 (boundary)."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0x1234_5678
    s.i.set_op_a = "Some(305419896)"  # 0x12345678
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # << 0 => same
    s.i.trig = "Some((AluOp::Shl, 0))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(305419896)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # >> 31 => MSB only
    s.i.trig = "Some((AluOp::Shr, 31))"
    await FallingEdge(dut.clk)
    # 0x12345678 MSB=0 -> result 0
    s.o.assert_eq("Some(0)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_left_overflow_truncates(dut):
    """Left shift overflow drops high bits (trunc to 32)."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0xF000_0001
    s.i.set_op_a = "Some(4026531841)"  # 0xF0000001
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # << 4 => 0x0000_0010 (top nybble falls off)
    s.i.trig = "Some((AluOp::Shl, 4))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(16)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_back_to_back_triggers(dut):
    """Two triggers in consecutive cycles produce two consecutive results next cycles."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0x0000_00FF
    s.i.set_op_a = "Some(255)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # Queue <<2
    s.i.trig = "Some((AluOp::Shl, 2))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1020)")  # 0x3FC
    # Immediately queue >>3
    s.i.trig = "Some((AluOp::Shr, 3))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(31)")
    # Clear
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_op_a_persistence_and_overwrite(dut):
    """OpA persists until overwritten; setting new A takes effect on next trigger."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Set A = 0xAAAA_AAAA
    s.i.set_op_a = "Some(2863311530)"  # 0xAAAA_AAAA
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # >> 1 => 0x5555_5555
    s.i.trig = "Some((AluOp::Shr, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1431655765)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # Overwrite A = 0x0000_0001
    s.i.set_op_a = "Some(1)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # << 31 => 0x8000_0000
    s.i.trig = "Some((AluOp::Shl, 31))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(2147483648)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")



# ------------ Arithmetic shift right ------------



@cocotb.test()
async def test_ashr_positive_basic(dut):
    """Arithmetic right shift of positive numbers == logical right shift."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0x0000_0040 (64)
    s.i.set_op_a = "Some(64)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # >> 1 => 32
    s.i.trig = "Some((AluOp::Ashr, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(32)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # >> 4 => 4
    s.i.trig = "Some((AluOp::Ashr, 4))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(4)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_ashr_negative_sign_extend(dut):
    """Arithmetic right shift sign-extends for negatives."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0xFFFF_FF80 (-128)
    s.i.set_op_a = "Some(4294967168)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # >> 1 => 0xFFFF_FFC0 (-64)
    s.i.trig = "Some((AluOp::Ashr, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(4294967232)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # >> 7 => 0xFFFF_FFFF (-1)
    s.i.trig = "Some((AluOp::Ashr, 7))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(4294967295)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_ashr_extreme_amounts(dut):
    """Shift by 0 (no-op) and by 31 (all sign bits)."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0x8000_0000 (negative)
    s.i.set_op_a = "Some(2147483648)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # >> 0 => same
    s.i.trig = "Some((AluOp::Ashr, 0))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(2147483648)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # >> 31 => 0xFFFF_FFFF (-1)
    s.i.trig = "Some((AluOp::Ashr, 31))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(4294967295)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # A = 0x7FFF_FFFF (positive) >> 31 => 0
    s.i.set_op_a = "Some(2147483647)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.i.trig = "Some((AluOp::Ashr, 31))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(0)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_ashr_back_to_back(dut):
    """Back-to-back ASHR triggers yield consecutive results on subsequent cycles."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0x8000_0001 (negative with LSB=1)
    s.i.set_op_a = "Some(2147483649)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # >> 1 => 0xC000_0000 (3221225472)
    s.i.trig = "Some((AluOp::Ashr, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(3221225472)")

    # Immediately queue >>31 (still uses latched A)
    s.i.trig = "Some((AluOp::Ashr, 31))"
    await FallingEdge(dut.clk)
    # 0x8000_0001 >> 31 (arith) => 0xFFFF_FFFF
    s.o.assert_eq("Some(4294967295)")

    # Clear
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")



# ------------ Rotate left / Rotate right ------------


@cocotb.test()
async def test_rotl_basic(dut):
    """Rotate-left simple patterns; next-cycle visibility."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0x8000_0001
    s.i.set_op_a = "Some(2147483649)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # rotl 1 => 0x0000_0003
    s.i.trig = "Some((AluOp::Rotl, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(3)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # rotl 31 == rotr 1 => 0xC000_0000
    s.i.trig = "Some((AluOp::Rotl, 31))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(3221225472)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_rotr_basic(dut):
    """Rotate-right simple patterns; next-cycle visibility."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0x8000_0001
    s.i.set_op_a = "Some(2147483649)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # rotr 1 => 0xC000_0000
    s.i.trig = "Some((AluOp::Rotr, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(3221225472)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # rotr 31 == rotl 1 => 0x0000_0003
    s.i.trig = "Some((AluOp::Rotr, 31))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(3)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_symmetry_16(dut):
    """rotl 16 and rotr 16 on 0x00FF00FF both return original."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0x00FF_00FF
    s.i.set_op_a = "Some(16711935)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # rotl 16 => same
    s.i.trig = "Some((AluOp::Rotl, 16))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(16711935)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # rotr 16 => same
    s.i.trig = "Some((AluOp::Rotr, 16))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(16711935)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_overflow_wrap(dut):
    """Check wrap-around bits with nibble-aligned rotations."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0xF000_000F
    s.i.set_op_a = "Some(4026531855)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # rotl 4 => 0x0000_00FF
    s.i.trig = "Some((AluOp::Rotl, 4))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(255)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # rotr 4 => 0xFF00_0000
    s.i.trig = "Some((AluOp::Rotr, 4))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(4278190080)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_checkerboard(dut):
    """Rotate a checkerboard pattern by 1."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0xAAAA_AAAA
    s.i.set_op_a = "Some(2863311530)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # rotl 1 => 0x5555_5555
    s.i.trig = "Some((AluOp::Rotl, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(1431655765)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # A = 0x5555_5555
    s.i.set_op_a = "Some(1431655765)"
    await FallingEdge(dut.clk)

    # rotr 1 => 0xAAAA_AAAA
    s.i.trig = "Some((AluOp::Rotr, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(2863311530)")
    # clears
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_back_to_back_triggers_rotate(dut):
    """Two consecutive rotations produce two consecutive results on following cycles."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A = 0x0000_00FF
    s.i.set_op_a = "Some(255)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    # rotl 8 => 0x0000_FF00 (65280)
    s.i.trig = "Some((AluOp::Rotl, 8))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(65280)")

    # immediately queue rotr 8 => 0xFF00_0000 (4278190080)
    s.i.trig = "Some((AluOp::Rotr, 8))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(4278190080)")

    # clear
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")


# ------------ Min/Max ------------


@cocotb.test()
async def test_min(dut):
    """Unsigned Minimum."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A=10, B=20 -> 10
    s.i.set_op_a = "Some(10)"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((AluOp::Min, 20))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(10)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # A=30, B=20 -> 20
    s.i.set_op_a = "Some(30)"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((AluOp::Min, 20))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(20)")

@cocotb.test()
async def test_max(dut):
    """Unsigned Maximum."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # A=10, B=20 -> 20
    s.i.set_op_a = "Some(10)"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((AluOp::Max, 20))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(20)")
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

    # A=30, B=20 -> 30
    s.i.set_op_a = "Some(30)"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((AluOp::Max, 20))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(30)")


# ------------ Saturating Arithmetic Tests ------------

@cocotb.test()
async def test_ssadd(dut):
    """Signed Saturating Add."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. Normal Add: 100 + 200 = 300
    s.i.set_op_a = "Some(100)"
    await FallingEdge(dut.clk)
    s.i.trig = "Some((AluOp::SSadd, 200))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(300)")

    # 2. Positive Saturation: MAX_INT + 1 -> MAX_INT
    s.i.set_op_a = "Some(2147483647)" # 0x7FFFFFFF
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    
    s.i.trig = "Some((AluOp::SSadd, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(2147483647)") # Saturation at MAX

    # 3. Negative Saturation: MIN_INT + (-1) -> MIN_INT
    s.i.set_op_a = "Some(2147483648)" # 0x80000000 (Min Int in unsigned representation)
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((AluOp::SSadd, 4294967295))" # -1 in u32
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(2147483648)") # Saturation at MIN

@cocotb.test()
async def test_sssub(dut):
    """Signed Saturating Subtract."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. Normal Sub: 300 - 100 = 200
    s.i.set_op_a = "Some(300)"
    await FallingEdge(dut.clk)
    s.i.trig = "Some((AluOp::SSsub, 100))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(200)")

    # 2. Positive Saturation: MAX_INT - (-1) -> MAX_INT
    s.i.set_op_a = "Some(2147483647)" # MAX
    s.i.trig = "None"
    await FallingEdge(dut.clk)

    s.i.trig = "Some((AluOp::SSsub, 4294967295))" # -1
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(2147483647)")

    # 3. Negative Saturation: MIN_INT - 1 -> MIN_INT
    s.i.set_op_a = "Some(2147483648)" # MIN
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    
    s.i.trig = "Some((AluOp::SSsub, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(2147483648)")

@cocotb.test()
async def test_usadd(dut):
    """Unsigned Saturating Add."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. Normal Add
    s.i.set_op_a = "Some(100)"
    await FallingEdge(dut.clk)
    s.i.trig = "Some((AluOp::USadd, 100))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(200)")

    # 2. Saturation: MAX_UINT + 1 -> MAX_UINT
    s.i.set_op_a = "Some(4294967295)" # 0xFFFFFFFF
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    
    s.i.trig = "Some((AluOp::USadd, 1))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(4294967295)")

@cocotb.test()
async def test_ussub(dut):
    """Unsigned Saturating Subtract."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 1. Normal Sub
    s.i.set_op_a = "Some(200)"
    await FallingEdge(dut.clk)
    s.i.trig = "Some((AluOp::USsub, 100))"
    s.i.set_op_a = "None"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(100)")

    # 2. Saturation: 100 - 200 -> 0 (Underflow clamped)
    s.i.set_op_a = "Some(100)"
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    
    s.i.trig = "Some((AluOp::USsub, 200))"
    await FallingEdge(dut.clk)
    s.o.assert_eq("Some(0)")