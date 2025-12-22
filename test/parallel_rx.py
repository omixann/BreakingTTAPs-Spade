# top=parallel_rx::parallel_boot

import cocotb
from spade import SpadeExt
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

CLK_PERIOD_NS = 10
EXT_CLK_PERIOD_NS = 40 # Slower external clock (e.g. 25MHz vs 100MHz)

async def start_system_clock(clk):
    await cocotb.start(Clock(clk, period=CLK_PERIOD_NS, units="ns").start())

async def start_external_clock(clk_pin):
    # Start the external clock pin (simulating the MCU clock)
    await cocotb.start(Clock(clk_pin, period=EXT_CLK_PERIOD_NS, units="ns").start())

async def reset_dut(dut):
    s = SpadeExt(dut)
    s.i.rst = True
    s.i.data_in = 0
    s.i.strobe = False
    s.i.clk_pin = False 
    await FallingEdge(dut.clk)
    s.i.rst = False
    await FallingEdge(dut.clk)
    return s


async def wait_for_data(s, dut, expected_val):
    """
    Helper to poll for expected data on s.o.
    Since the DUT output is a 1-cycle pulse in the fast system domain,
    we must poll fast enough or wait for the specific condition.
    """
    # Look for the pulse in the system domain within a reasonable timeout
    # (e.g., slightly more than one external clock period)
    found = False
    for _ in range(8): # Scan ~8 system cycles (covers sync delay + margin)
        await FallingEdge(dut.clk)
        if s.o.value() == f"Some({expected_val})":
            found = True
            break
    
    if not found:
        # If we didn't find it, check if it's currently asserted (just in case)
        if s.o.value() == f"Some({expected_val})":
            found = True

    assert found, f"Failed to detect output pulse for value {expected_val}"


@cocotb.test()
async def test_single_byte_transfer(dut):
    """Test latching a single byte on clk_pin rising edge when strobe is high."""
    await start_system_clock(dut.clk)
    await start_external_clock(dut.clk_pin)

    s = await reset_dut(dut)

    # 1. Align to External Clock
    # We change inputs on the Falling Edge of the external clock
    # so they are stable for the Rising Edge (setup time).
    await FallingEdge(dut.clk_pin)

    # 2. Setup Data & Assert Strobe
    test_val = 0xA5
    dut._log.info(f"Setting Data: {test_val} and Strobe")
    s.i.data_in = test_val
    s.i.strobe = True
    
    # 3. Wait for External Clock Rising Edge (Data Capture point)
    await RisingEdge(dut.clk_pin)
    dut._log.info("External Clock Rising Edge (Capture)")

    # 4. Wait for System Clock to process the captured data
    # The synchronizer chain in the DUT takes 2 system cycles
    await FallingEdge(dut.clk)
    await FallingEdge(dut.clk)
    
    # Check output
    s.o.assert_eq(f"Some({test_val})")
    
    # 5. Deassert Strobe (on next falling edge of ext clock)
    await FallingEdge(dut.clk_pin)
    s.i.strobe = False
    
    # Wait for system to settle
    await FallingEdge(dut.clk)
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_burst_transfer(dut):
    """Test transferring multiple bytes synchronized to clk_pin."""
    await start_system_clock(dut.clk)
    await start_external_clock(dut.clk_pin)
    s = await reset_dut(dut)
    
    vals = [10, 20, 30]
    
    for val in vals:
        # Change data on Falling Edge of external clock
        await FallingEdge(dut.clk_pin)
        s.i.data_in = val
        s.i.strobe = True
        
        # Data is captured on the next Rising Edge of clk_pin
        # We wait for the system to output it (latency)
        
        # Wait for capture edge
        await RisingEdge(dut.clk_pin)
        
        # Wait for system processing (sync delay)
        # We need to sample the output *before* the next capture might occur,
        # but since our ext clock is slow (40ns) vs sys clock (10ns), 
        # the output will appear and disappear (it's a 1-cycle pulse in sys domain)
        # well before the next external edge.
        
        # We look for the pulse in the system domain
        found = False
        for _ in range(5): # Scan a few system cycles
            await FallingEdge(dut.clk)
            if s.o.value() == f"Some({val})":
                found = True
                break
        
        assert found, f"Failed to detect output pulse for value {val}"
        
    # Finish
    await FallingEdge(dut.clk_pin)
    s.i.strobe = False
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_long_burst(dut):
    """
    Stress test: Transfer 256 bytes sequentially (0..255).
    Ensures stability over long transfers.
    """
    await start_system_clock(dut.clk)
    await start_external_clock(dut.clk_pin)
    s = await reset_dut(dut)
    
    s.i.strobe = True
    
    for i in range(256):
        # Setup data
        await FallingEdge(dut.clk_pin)
        s.i.data_in = i
        
        # Capture happens at RisingEdge internally
        await RisingEdge(dut.clk_pin)
        
        # Check result
        await wait_for_data(s, dut, i)

    s.i.strobe = False
    await FallingEdge(dut.clk)
    s.o.assert_eq("None")

@cocotb.test()
async def test_interrupted_transfer(dut):
    """
    Edge Case: Data ignores clock edges when Strobe is Low.
    Sequence: Send 0xAA -> Strobe Low (Input 0xBB) -> Strobe High (Input 0xCC).
    Expected: Receive 0xAA, then 0xCC. 0xBB should be ignored.
    """
    await start_system_clock(dut.clk)
    await start_external_clock(dut.clk_pin)
    s = await reset_dut(dut)

    # 1. Send Valid Byte 0xAA
    await FallingEdge(dut.clk_pin)
    s.i.strobe = True
    s.i.data_in = 0xAA
    
    await RisingEdge(dut.clk_pin)
    await wait_for_data(s, dut, 0xAA)
    
    # 2. Deassert Strobe, Put Invalid Data 0xBB
    await FallingEdge(dut.clk_pin)
    s.i.strobe = False
    s.i.data_in = 0xBB
    
    await RisingEdge(dut.clk_pin)
    
    # 3. Verify Silence
    # Wait ~1 full external cycle to be sure no data appears
    for _ in range(int(EXT_CLK_PERIOD_NS / CLK_PERIOD_NS) + 2):
        await FallingEdge(dut.clk)
        s.o.assert_eq("None")
        
    # 4. Resume Valid Byte 0xCC
    await FallingEdge(dut.clk_pin)
    s.i.strobe = True
    s.i.data_in = 0xCC
    
    await RisingEdge(dut.clk_pin)
    await wait_for_data(s, dut, 0xCC)