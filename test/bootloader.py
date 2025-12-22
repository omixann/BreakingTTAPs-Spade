#top=bootloader::bootloader

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge
from spade import SpadeExt

CLK_NS = 10

# -----------------------
# Helpers: clock & reset
# -----------------------

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

# -----------------------
# Helpers: drive the stream
# -----------------------

async def drive_byte(dut, s, clk, b: int, toggle_byte_valid: bool = False):
    """Drive one UART-decoded byte into the bootloader (1-cycle valid)."""
    s.i.byte = int(b & 0xFF)
    s.i.byte_valid = True
    await FallingEdge(clk)
    wr = (s.o.wr_addr == "None")
    dut._log.info(f"wr_addr is None: {wr}")


    if toggle_byte_valid:
        s.i.byte_valid = False
        await FallingEdge(clk)
        wr = (s.o.wr_addr == "None")
        dut._log.info(f"wr_addr is None: {wr}")

async def send_bytes(dut, s, clk, data):
    for b in data:
        await drive_byte(dut, s, clk, b)

# -----------------------
# Helpers: LE packers & image builder
# -----------------------

def le16(x: int): return [x & 0xFF, (x >> 8) & 0xFF]
def le32(x: int): return [x & 0xFF, (x >> 8) & 0xFF, (x >> 16) & 0xFF, (x >> 24) & 0xFF]

def build_image(instr_pairs, entry_pc: int, version: int = 1, instr_cnt_override: int | None = None):
    """
    instr_pairs: list[(w0_u32, w1_u32)]
    entry_pc: u16
    instr_cnt_override: write a different header count (e.g., to test clamping)
    """
    n = len(instr_pairs)
    hdr_n = n if instr_cnt_override is None else instr_cnt_override
    data = []
    data += [0x42, 0x54]         # 'B','T'
    data += le16(version)        # u16 version LE
    data += le16(hdr_n)          # u16 instr_cnt LE
    data += le16(entry_pc)       # u16 entry_pc LE
    for w0, w1 in instr_pairs:   # payload: slot0 then slot1, both LE
        data += le32(w0)
        data += le32(w1)
    return data

# -----------------------
# Assertions
# -----------------------

async def expect_commit_now(s, clk, idx: int, w0: int, w1: int):
    """
    Expect that *this cycle* the FSM is in Commit:
      - boot_active == True
      - wr_addr / wr_slot0 / wr_slot1 are Some with the expected values
      - and they return to None on the next cycle.
    """
    s.o.boot_active.assert_eq(True)

    assert s.o.wr_addr != "None", "wr_addr should be Some during Commit"
    assert s.o.wr_slot0 != "None", "wr_slot0 should be Some during Commit"
    assert s.o.wr_slot1 != "None", "wr_slot1 should be Some during Commit"

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

# ============================================================
# Tests
# ============================================================

@cocotb.test()
async def test_basic_single_instruction(dut):
    """One instruction: exactly one Commit at addr 0, then Done with release_pc."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    instrs = [(0x11223344, 0xAABBCCDD)]
    entry  = 2
    img = build_image(instrs, entry_pc=entry)

    dut._log.info(f"Img: {img}")

    # Stream the whole image; Commit occurs right after the last payload byte
    for i, b in enumerate(img):
        dut._log.info(f"{i}, {b}")
        await drive_byte(dut, s, dut.clk, b, False)
        if i == 8 + 8 - 1:   # header 8B + payload 8B - 1 (zero-based)
            await expect_commit_now(s, dut.clk, 0, *instrs[0])

    await expect_done_and_release(s, dut.clk, entry)

@cocotb.test()
async def test_two_instructions_sequence(dut):
    """Two instructions: Commit at addr 0 and 1, then Done."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    instrs = [(0x00000019, 0x00000000), (0xCAFEBABE, 0x12345678)]
    entry  = 4
    img = build_image(instrs, entry_pc=entry)

    # header
    for b in img[:8]:
        await drive_byte(dut, s, dut.clk, b)
        s.i.byte_valid = False
        await FallingEdge(dut.clk)

    # instr 0 payload (8 bytes)
    for j, b in enumerate(img[8:8+8]):
        await drive_byte(dut, s, dut.clk, b)
        if j == 7:
            await expect_commit_now(s, dut.clk, 0, *instrs[0])
        
        s.i.byte_valid = False
        await FallingEdge(dut.clk)

    # instr 1 payload
    for j, b in enumerate(img[16:24]):
        await drive_byte(dut, s, dut.clk, b)
        if j == 7:
            await expect_commit_now(s, dut.clk, 1, *instrs[1])
        
        s.i.byte_valid = False
        await FallingEdge(dut.clk)

    await expect_done_and_release(s, dut.clk, entry)

@cocotb.test()
async def test_n0_immediate_done(dut):
    """instr_cnt=0 → Done immediately after E1 with release_pc Some(entry)."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    entry = 9
    img = build_image([], entry_pc=entry, instr_cnt_override=0)

    # only 8 bytes (header)
    for b in img:
        await drive_byte(dut, s, dut.clk, b)
        s.i.byte_valid = False
        await FallingEdge(dut.clk)

    # No Commit should occur; we should be in Done now
    s.o.wr_addr.assert_eq("None")
    s.o.wr_slot0.assert_eq("None")
    s.o.wr_slot1.assert_eq("None")
    await expect_done_and_release(s, dut.clk, entry)

@cocotb.test()
async def test_bad_magic_then_good(dut):
    """Noise bytes first; then a valid image. Expect no Commit until valid header, then normal."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    for b in [0x00, 0xFF, 0x41, 0x41, 0x99]:
        await drive_byte(dut, s, dut.clk, b)
        s.i.byte_valid = False
        await FallingEdge(dut.clk)
        s.o.wr_addr.assert_eq("None")
        s.o.wr_slot0.assert_eq("None")
        s.o.wr_slot1.assert_eq("None")
        

    instrs = [(0xDEADBEEF, 0x0BADF00D)]
    entry  = 3
    img = build_image(instrs, entry_pc=entry)

    for i, b in enumerate(img):
        await drive_byte(dut, s, dut.clk, b)
        if i == 8 + 8 - 1:
            await expect_commit_now(s, dut.clk, 0, *instrs[0])

        s.i.byte_valid = False
        await FallingEdge(dut.clk)

    await expect_done_and_release(s, dut.clk, entry)

@cocotb.test()
async def test_bad_version_resets_to_waitB(dut):
    """Bad version image (ver=2) should never Commit; then a good image starts at addr 0."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    bad = build_image([(0x11111111, 0x22222222)], entry_pc=2, version=2)
    for b in bad:
        await drive_byte(dut, s, dut.clk, b)
        s.i.byte_valid = False
        await FallingEdge(dut.clk)
        s.o.wr_addr.assert_eq("None")
        s.o.wr_slot0.assert_eq("None")
        s.o.wr_slot1.assert_eq("None")

    good = build_image([(0xAAAA0001, 0x55550002)], entry_pc=5, version=1)
    for i, b in enumerate(good):
        await drive_byte(dut, s, dut.clk, b)
        if i == 8 + 8 - 1:
            await expect_commit_now(s, dut.clk, 0, 0xAAAA0001, 0x55550002)

        s.i.byte_valid = False
        await FallingEdge(dut.clk)

    await expect_done_and_release(s, dut.clk, 5)

@cocotb.test()
async def test_endianness_payload(dut):
    """Ensure payload words are written little-endian."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    w0 = 0x01020304  # wire: 04 03 02 01
    w1 = 0x0A0B0C0D  # wire: 0D 0C 0B 0A
    img = build_image([(w0, w1)], entry_pc=0)

    for i, b in enumerate(img):
        await drive_byte(dut, s, dut.clk, b)
        if i == 8 + 8 - 1:
            await expect_commit_now(s, dut.clk, 0, w0, w1)

        s.i.byte_valid = False
        await FallingEdge(dut.clk)

    await expect_done_and_release(s, dut.clk, 0)
