# top=tanh::tanh_pwl_fu

import cocotb
from spade import SpadeExt
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge

CLK_PERIOD_NS = 10
SCALE = 32768  # Q1.15 Scale

def to_fixed_u32(f):
    """Converts float to clamped 16-bit int, then masks to uint32."""
    val = int(f * SCALE)
    if val > 32767: val = 32767
    if val < -32768: val = -32768
    return val & 0xFFFFFFFF

def from_fixed_u32(u32_val):
    """Converts uint32 (sign-extended 16-bit) back to signed int."""
    # Treat as 32-bit signed
    if u32_val >= 0x80000000:
        return u32_val - 0x100000000
    return u32_val

def parse_spade_option(val_str):
    """Parses 'Some(1234)' -> 1234 or 'None' -> None."""
    # Convert to string just in case it's a wrapper object
    s = str(val_str).strip()
    
    if s == "None":
        return None
    
    if s.startswith("Some(") and s.endswith(")"):
        # Extract content between Some( and )
        inner = s[5:-1]
        return int(inner)
        
    raise ValueError(f"Unexpected Spade output format: {s}")

async def start_clock(clk):
    await cocotb.start(Clock(clk, period=CLK_PERIOD_NS, units="ns").start())

async def reset_dut(dut):
    s = SpadeExt(dut)
    s.i.rst = True
    s.i.trig = "None"
    await FallingEdge(dut.clk)
    s.i.rst = False
    await FallingEdge(dut.clk)
    return s

async def check_val(dut, s, input_float, expected_float):
    in_u32 = to_fixed_u32(input_float)
    expected_signed = int(to_fixed_u32(expected_float))
    # Adjust expected if it was masked to unsigned by helper
    if expected_signed >= 0x80000000: expected_signed -= 0x100000000
    
    s.i.trig = f"Some({in_u32})"
    await FallingEdge(dut.clk)
    
    # 1. Get raw string from SpadeExt
    raw_str = s.o.value()
    
    # 2. Parse "Some(12345)" to integer 12345
    raw_out = parse_spade_option(raw_str)
    
    # Ensure we actually got a value
    assert raw_out is not None, f"Expected Some(...), got None for input {input_float}"

    # 3. Interpret as signed 32-bit
    got_signed = from_fixed_u32(raw_out)
    
    # Tolerance of +/- 1 LSB
    diff = abs(got_signed - expected_signed)
    assert diff <= 1, \
        f"In: {input_float}. Exp: {expected_float} ({expected_signed}). Got: {got_signed} (Raw: {raw_str})"

@cocotb.test()
async def test_identity_region(dut):
    """Region 1: |x| < 0.5 -> y = x"""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    await check_val(dut, s, 0.0, 0.0)
    await check_val(dut, s, 0.25, 0.25)
    await check_val(dut, s, -0.4, -0.4)

    s.i.trig = "None"
    await FallingEdge(dut.clk)

@cocotb.test()
async def test_compressed_region(dut):
    """Region 2: 0.5 <= |x| <= 1.0 -> y = 0.5x + 0.25"""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # 0.5 -> 0.5
    await check_val(dut, s, 0.5, 0.5)

    # 0.8 -> 0.5(0.8) + 0.25 = 0.65
    await check_val(dut, s, 0.8, 0.65)
    
    # -0.8 -> -0.65
    await check_val(dut, s, -0.8, -0.65)

@cocotb.test()
async def test_full_range_limits(dut):
    """Verify behavior at 16-bit limits passed as 32-bit values."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)
    
    # Max Positive (32767)
    s.i.trig = "Some(32767)"
    await FallingEdge(dut.clk)
    
    # Parse output manually for this specific test case
    raw_val = parse_spade_option(s.o.value())
    got = from_fixed_u32(raw_val)
    
    expected = 24575 # approx 0.75
    assert got == expected, f"Max Pos failed. Got {got}"

    # Max Negative (-32768) -> passed as 0xFFFF8000
    neg_input = (-32768) & 0xFFFFFFFF
    s.i.trig = f"Some({neg_input})"
    await FallingEdge(dut.clk)
    
    raw_val_neg = parse_spade_option(s.o.value())
    got_neg = from_fixed_u32(raw_val_neg)
    
    expected_neg = -24576
    assert got_neg == expected_neg, f"Max Neg failed. Got {got_neg}"