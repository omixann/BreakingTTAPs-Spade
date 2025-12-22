#top=bootloader::bootloader

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge
from spade import SpadeExt
import random

CLK_NS = 10

# --------------- Common helpers ---------------

async def start_clock(clk):
    await cocotb.start(Clock(clk, period=CLK_NS, units="ns").start())

async def reset_dut(dut):
    s = SpadeExt(dut)
    s.i.rst = True
    s.i.byte_valid = False
    s.i.byte = 0
    await FallingEdge(dut.clk)
    s.i.rst = False
    await FallingEdge(dut.clk)
    return s

async def drive_byte(s, clk, b: int, toggle_byte_valid: bool = False):
    """Drive one UART-decoded byte into the bootloader (1-cycle valid)."""
    s.i.byte = int(b & 0xFF)
    s.i.byte_valid = True
    await FallingEdge(clk)


    if toggle_byte_valid:
        s.i.byte_valid = False
        await FallingEdge(clk)

async def idle_cycles(clk, n: int):
    for _ in range(n):
        await FallingEdge(clk)

def le16(x): return [x & 0xFF, (x >> 8) & 0xFF]
def le32(x): return [x & 0xFF, (x >> 8) & 0xFF, (x >> 16) & 0xFF, (x >> 24) & 0xFF]

def build_image(instr_pairs, entry_pc: int, version: int = 1, instr_cnt_override: int | None = None):
    n = len(instr_pairs)
    hdr_n = n if instr_cnt_override is None else instr_cnt_override
    data = []
    data += [0x42, 0x54]       # 'B','T'
    data += le16(version)
    data += le16(hdr_n)
    data += le16(entry_pc)
    for w0, w1 in instr_pairs:
        data += le32(w0)
        data += le32(w1)
    return data

async def expect_commit_now(s, clk, idx: int, w0: int, w1: int):
    """
    Expect that *this cycle* the FSM is in Commit:
      - boot_active == True
      - wr_addr / wr_slot0 / wr_slot1 are Some with the expected values
      - and they return to None on the next cycle.
    """
    s.o.boot_active.assert_eq(True)

    #assert s.o.wr_addr != "None", "wr_addr should be Some during Commit"
    #assert s.o.wr_slot0 != "None", "wr_slot0 should be Some during Commit"
    #assert s.o.wr_slot1 != "None", "wr_slot1 should be Some during Commit"

    s.o.wr_addr.assert_eq(f"Some({idx})")
    s.o.wr_slot0.assert_eq(f"Some({(w0 & 0xFFFFFFFF)})")
    s.o.wr_slot1.assert_eq(f"Some({(w1 & 0xFFFFFFFF)})")

    # Next cycle: one-cycle pulse → all Nones
    await FallingEdge(clk)
    s.o.wr_addr.assert_eq("None")
    s.o.wr_slot0.assert_eq("None")
    s.o.wr_slot1.assert_eq("None")

async def expect_done_and_release(s, clk, entry_pc: int):
    """
    Expect we are in Done:
      - boot_active == False
      - release_pc == Some(entry_pc) (level-high while in Done)
    """
    s.o.boot_active.assert_eq(False)
    assert s.o.release_pc != "None", "release_pc should be Some(entry) in Done"
    s.o.release_pc.assert_eq(f"Some({(entry_pc & 0xFFFF)})")

    # Stays in Done on subsequent cycles
    await FallingEdge(clk)
    s.o.boot_active.assert_eq(False)
    assert s.o.release_pc != "None"

# --------------- Tests ---------------

@cocotb.test()
async def test_random_gaps_between_bytes(dut):
    """
    Random idle gaps between bytes shouldn't affect commit timing or values.
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    random.seed(1)
    instrs = [(0x11111111, 0x22222222), (0xA0A0A0A0, 0x0B0B0B0B), (0xDEADBEEF, 0xCAFEBABE)]
    entry = 7
    img = build_image(instrs, entry_pc=entry)

    # Stream with random gaps of 0..3 cycles between bytes
    for i, b in enumerate(img):
        await drive_byte(s, dut.clk, b)
        
        # Detect instruction boundaries: after each 8B payload
        if i in {8+8-1, 8+16-1, 8+24-1}:
            idx = (i - 8) // 8
            await expect_commit_now(s, dut.clk, idx, *instrs[idx])

        s.i.byte_valid = False
        await FallingEdge(dut.clk)

        await idle_cycles(dut.clk, random.randint(0, 3))

    await expect_done_and_release(s, dut.clk, entry)

@cocotb.test()
async def test_truncated_stream_stalls_safely(dut):
    """
    If the stream ends early (fewer payload bytes than header count),
    the FSM should not Commit or Done; it should just wait.
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    instrs = [(0x01020304, 0x05060708), (0x11121314, 0x15161718)]
    entry = 3
    full = build_image(instrs, entry_pc=entry)

    # Send header + only first instruction payload (8B), leave second instruction missing
    partial = full[:8 + 8]  # 8 header + 8 payload
    for (i, b) in enumerate(partial):
        await drive_byte(s, dut.clk, b, i != 15)
        

    # Expect exactly one Commit for instr 0
    await expect_commit_now(s, dut.clk, 0, *instrs[0])
    s.i.byte_valid = False
    await FallingEdge(dut.clk)

    # Now stop sending bytes: must remain active, no release_pc, no further commits
    for _ in range(10):
        s.o.boot_active.assert_eq(True)
        s.o.wr_addr.assert_eq("None")
        s.o.wr_slot0.assert_eq("None")
        s.o.wr_slot1.assert_eq("None")
        s.o.release_pc.assert_eq("None")
        await FallingEdge(dut.clk)

@cocotb.test()
async def test_reset_mid_stream(dut):
    """
    Reset during payload must return to WaitB and clear intents.
    Then a fresh valid image should start at wr_addr=0.
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    instrs1 = [(0xAAAABBBB, 0xCCCCDDDD)]
    img1 = build_image(instrs1, entry_pc=1)

    # Send header + first 4 payload bytes, then reset
    for b in img1[:8 + 4]:
        await drive_byte(s, dut.clk, b)

    # Assert reset
    s.i.rst = True
    await FallingEdge(dut.clk)
    s.i.rst = False
    await FallingEdge(dut.clk)

    # No commits leaked
    s.o.wr_addr.assert_eq("None")
    s.o.wr_slot0.assert_eq("None")
    s.o.wr_slot1.assert_eq("None")
    s.o.release_pc.assert_eq("None")

    # Send a new valid single-instr image; expect wr_addr=0
    instrs2 = [(0x11223344, 0x55667788)]
    img2 = build_image(instrs2, entry_pc=5)
    for i, b in enumerate(img2):
        await drive_byte(s, dut.clk, b)
        if i == 8 + 8 - 1:
            await expect_commit_now(s, dut.clk, 0, *instrs2[0])
    await expect_done_and_release(s, dut.clk, 5)

@cocotb.test()
async def test_resync_on_bad_magic_overlap(dut):
    """
    Sequence: 'B' 'X' 'B' 'T' ... should lock on the second 'B','T' and load normally.
    (Your FSM resets to WaitB on mismatch.)
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Noise / partial header
    for b in [0x42, 0x58]:  # 'B','X'
        await drive_byte(s, dut.clk, b)

    instrs = [(0xDEAD0001, 0xBEEF0002)]
    entry = 2
    img = build_image(instrs, entry_pc=entry)

    # Now stream a valid header+payload
    for i, b in enumerate(img):
        await drive_byte(s, dut.clk, b)
        if i == 8 + 8 - 1:
            await expect_commit_now(s, dut.clk, 0, *instrs[0])

    await expect_done_and_release(s, dut.clk, entry)

@cocotb.test()
async def test_ignore_bytes_after_done(dut):
    """
    After Done, any additional bytes must be ignored; wr_* remain None, release_pc stays Some(entry).
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    instrs = [(0x01010101, 0x02020202)]
    entry = 9
    img = build_image(instrs, entry_pc=entry)

    # Load normally
    for i, b in enumerate(img):
        await drive_byte(s, dut.clk, b)
        if i == 8 + 8 - 1:
            await expect_commit_now(s, dut.clk, 0, *instrs[0])
    await expect_done_and_release(s, dut.clk, entry)

    # Send more garbage: must remain in Done (one-shot)
    for b in [0x42, 0x54, 0x01, 0x00, 0x01, 0x00, 0xEF]:
        await drive_byte(s, dut.clk, b)
        s.o.boot_active.assert_eq(False)
        s.o.wr_addr.assert_eq("None")
        s.o.wr_slot0.assert_eq("None")
        s.o.wr_slot1.assert_eq("None")
        assert s.o.release_pc != "None"


@cocotb.test()
async def test_clamp_to_1024_and_done(dut):
    """
    If header instr_cnt > 1024, it must clamp to 1024.
    We send exactly 1024 instructions and expect last wr_addr==1023, then Done.
    """
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    N = 1024
    instrs = [(i, 0xFFFFFFFF ^ i) for i in range(N)]
    entry = 123
    img = build_image(instrs, entry_pc=entry, instr_cnt_override=1200)  # over-limit

    # Header
    for b in img[:8]:
        await drive_byte(s, dut.clk, b)

    # Stream all 1024 payloads and check some samples + last
    for idx in range(N):
        # 8 bytes per instruction payload
        base = 8 + idx * 8
        for b in img[base:base+8]:
            await drive_byte(s, dut.clk, b)
        await expect_commit_now(s, dut.clk, idx, instrs[idx][0], instrs[idx][1])

    # After 1024th commit, we should be Done; ignore any extra bytes
    await expect_done_and_release(s, dut.clk, entry)

    # Even if we push more bytes (which would have belonged to >1024), nothing should happen
    for _ in range(16):
        await drive_byte(s, dut.clk, 0x00)
        s.o.wr_addr.assert_eq("None")
        s.o.wr_slot0.assert_eq("None")
        s.o.wr_slot1.assert_eq("None")
