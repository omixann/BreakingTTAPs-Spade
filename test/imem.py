# top = imem::imem

import cocotb
from spade import SpadeExt
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge
import random
import re
import os

CLK_NS = 10

# =========================================================
# Dynamic Token Loading
# =========================================================

class TokenNamespace:
    """
    Helper to expose tokens as attributes (Src.ALU_Res) or methods (Src.RegisterFile(0)).
    """
    def __init__(self, name, general_map, rf_map, reverse_map):
        self.name = name
        self._map = general_map      # {"ALU_Res": 11, ...}
        self._rf_map = rf_map        # {0: 0, 1: 1, ...} (index -> token)
        self._rev_map = reverse_map  # {11: ("ALU_Res", None), 0: ("RegisterFile", 0), ...}

    def __getattr__(self, key):
        if key in self._map:
            return self._map[key]
        raise AttributeError(f"{self.name} has no token '{key}'")

    def RegisterFile(self, idx):
        if idx in self._rf_map:
            return self._rf_map[idx]
        raise ValueError(f"RegisterFile index {idx} not found in {self.name} map")

    def get_str(self, token, imm_val=0):
        """Reconstruct Spade string from token ID using reverse map."""
        if token not in self._rev_map:
            return f"{self.name}::Zero" # Fallback/Default
        
        name, arg = self._rev_map[token]
        
        if name == "RegisterFile":
            return f"{self.name}::{name}({arg})"
        elif name == "Immediate":
            return f"{self.name}::{name}({imm_val})"
        else:
            return f"{self.name}::{name}"

def parse_spade_tokens(filename):
    """
    Parses imem.spade to extract decode_src_tok and decode_dst_tok mappings.
    Returns (SrcNamespace, DstNamespace).
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Could not find {filename}")

    with open(filename, 'r') as f:
        content = f.read()

    def parse_func(func_name, namespace_prefix):
        general_map = {}
        rf_map = {}
        rev_map = {}

        # Regex to find match block inside specific function
        # Finds: fn name(...) -> ... { match t { ... } }
        func_regex = re.search(f"fn {func_name}.*?match t \{{(.*?)\}}", content, re.DOTALL)
        if not func_regex:
            print(f"Warning: Could not find function {func_name}")
            return TokenNamespace(namespace_prefix, {}, {}, {})

        block_content = func_regex.group(1)
        
        # Parse lines like: 10u8 => Src::Immediate(zext(imm16)),
        # Captures: (token_id, type_prefix, variant_name, args)
        # e.g. ('10', 'Src', 'Immediate', 'zext(imm16)')
        # e.g. ('00', 'Src', 'RegisterFile', '0u4')
        pattern = re.compile(r'(\d+)u8\s*=>\s*(\w+)::(\w+)(?:\((.*?)\))?')
        
        for line in block_content.split('\n'):
            line = line.split('//')[0].strip() # Remove comments
            m = pattern.search(line)
            if m:
                tok_id = int(m.group(1))
                variant = m.group(3)
                args = m.group(4)

                # Store for reverse lookup
                # Determine "arg type": None, index (for RF), or "imm" (for Immediate)
                rev_arg = None

                if variant == "RegisterFile":
                    # Extract index from "0u4" -> 0
                    idx_match = re.search(r'(\d+)', args if args else "0")
                    idx = int(idx_match.group(1)) if idx_match else 0
                    rf_map[idx] = tok_id
                    rev_arg = idx
                elif variant == "Immediate":
                    general_map[variant] = tok_id
                    rev_arg = "imm"
                else:
                    general_map[variant] = tok_id
                    rev_arg = None
                
                rev_map[tok_id] = (variant, rev_arg)

        return TokenNamespace(namespace_prefix, general_map, rf_map, rev_map)

    src = parse_func("decode_src_tok", "Src")
    dst = parse_func("decode_dst_tok", "Dst")
    return src, dst

    
def setup_token_maps():
    global Src
    global Dst
    # Load tokens relative to this test file
    if Src is None or Dst is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        spade_file = os.path.join(current_dir, "../../src/imem.spade")
        Src, Dst = parse_spade_tokens(spade_file)

# =========================================================
# Helpers
# =========================================================

def pack_move(guard, src_tok, dst_tok, Immediate):
    return ((guard & 1) << 31) | ((src_tok & 0x7F) << 24) | ((dst_tok & 0x7F) << 17) | (Immediate & 0xFFFF)

def fmt_move(guard, src_tok, dst_tok, imm):
    global Src
    global Dst
    # Use dynamic reverse lookup
    s_str = Src.get_str(src_tok, imm & 0xFFFF)
    d_str = Dst.get_str(dst_tok)
    return f"Move({s_str}, {d_str}, {'true' if guard else 'false'})"

def fmt_instr(m0, m1):
    (g0, s0, d0, i0) = m0
    (g1, s1, d1, i1) = m1
    return f"Some(Instr({fmt_move(g0, s0, d0, i0)}, {fmt_move(g1, s1, d1, i1)}))"

async def start_clock(clk):
    await cocotb.start(Clock(clk, period=CLK_NS, units="ns").start())

async def reset_dut(dut):
    s = SpadeExt(dut)
    s.i.rst = True
    s.i.boot_mode = True
    s.i.fetch_pc = 0
    s.i.wr_addr = "None"
    s.i.wr_slot0 = "None"
    s.i.wr_slot1 = "None"
    await FallingEdge(dut.clk)
    s.i.rst = False
    await FallingEdge(dut.clk)
    return s

async def write_instr(s, clk, addr: int, w0: int, w1: int):
    """Pulse a write for one cycle while boot_mode is True."""
    s.i.wr_addr  = f"Some({addr})"
    s.i.wr_slot0 = f"Some({(w0 & 0xFFFFFFFF)})"
    s.i.wr_slot1 = f"Some({(w1 & 0xFFFFFFFF)})"
    await FallingEdge(clk)


Src = None
Dst = None

# =========================================================
# Tests
# =========================================================

@cocotb.test()
async def test_write_then_fetch_addr0(dut):
    global Src
    global Dst
    setup_token_maps()


    """Write one instruction at addr 0, then fetch it in run mode."""
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Use Dynamic Enums
    # Move0: Immediate(19) -> ALU_OpA
    w0 = pack_move(0, Src.Immediate, Dst.ALU_OpA, 19)
    # Move1: RF0 -> ALU_Ashr_Trig
    w1 = pack_move(1, Src.RegisterFile(0), Dst.ALU_Ashr_Trig, 0)

    await write_instr(s, dut.clk, 0, w0, w1)

    # Switch to run mode
    s.i.boot_mode = False
    s.i.wr_addr  = "None"
    s.i.wr_slot0 = "None"
    s.i.wr_slot1 = "None"
    s.i.fetch_pc = 0
    await FallingEdge(dut.clk)
    await FallingEdge(dut.clk)  #one extra cycle for the read

    # Assertion uses dynamic fmt_instr to build string
    # Matches: Move(Src::Immediate(19), Dst::ALU_OpA, false), Move(Src::RegisterFile(0), Dst::ALU_Ashr_Trig, true)
    expected = fmt_instr((0, Src.Immediate, Dst.ALU_OpA, 19), (1, Src.RegisterFile(0), Dst.ALU_Ashr_Trig, 0))
    s.o.assert_eq(expected)

@cocotb.test()
async def test_write_two_addrs_then_fetch_each(dut):
    """Write addr 0 and 1, then fetch both and verify."""
    global Src
    global Dst
    setup_token_maps()
    
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Instr 0
    w0a = pack_move(0, Src.RegisterFile(2), Dst.ALU_OpA, 0x1234)
    w1a = pack_move(1, Src.RegisterFile(3), Dst.ALU_Add_Trig, 0)
    await write_instr(s, dut.clk, 0, w0a, w1a)

    # Instr 1
    w0b = pack_move(0, Src.Immediate, Dst.LSU_AddrA, 4)
    w1b = pack_move(1, Src.RegisterFile(1), Dst.LSU_Store_Trig, 0)
    await write_instr(s, dut.clk, 1, w0b, w1b)
    
    s.o.assert_eq("None")

    s.i.boot_mode = False
    s.i.wr_addr  = "None"
    s.i.wr_slot0 = "None"
    s.i.wr_slot1 = "None"
    s.i.fetch_pc = 0
    await FallingEdge(dut.clk)

    s.i.fetch_pc = 1
    await FallingEdge(dut.clk)  #one extra cycle for the read

    # Check Instr 0
    expected_0 = fmt_instr((0, Src.RegisterFile(2), Dst.ALU_OpA, 0x1234), (1, Src.RegisterFile(3), Dst.ALU_Add_Trig, 0))
    s.o.assert_eq(expected_0)
    
    # Check Instr 1 (next cycle)
    await FallingEdge(dut.clk)
    expected_1 = fmt_instr((0, Src.Immediate, Dst.LSU_AddrA, 4), (1, Src.RegisterFile(1), Dst.LSU_Store_Trig, 0))
    s.o.assert_eq(expected_1)


@cocotb.test()
async def test_overwrite_same_address(dut):
    """A later write to the same addr should overwrite previous contents."""
    global Src
    global Dst
    setup_token_maps()
    
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Old
    w0_old = pack_move(0, Src.RegisterFile(2), Dst.ALU_OpA, 0)
    w1_old = pack_move(1, Src.RegisterFile(3), Dst.ALU_Add_Trig, 0)
    await write_instr(s, dut.clk, 5, w0_old, w1_old)

    # New
    w0_new = pack_move(0, Src.Immediate, Dst.ALU_OpA, 19)
    w1_new = pack_move(1, Src.RegisterFile(0), Dst.ALU_Add_Trig, 0)
    await write_instr(s, dut.clk, 5, w0_new, w1_new)

    s.i.boot_mode = False
    s.i.wr_addr  = "None"
    s.i.wr_slot0 = "None"
    s.i.wr_slot1 = "None"
    s.i.fetch_pc = 5
    await FallingEdge(dut.clk)
    await FallingEdge(dut.clk)

    expected = fmt_instr((0, Src.Immediate, Dst.ALU_OpA, 19), (1, Src.RegisterFile(0), Dst.ALU_Add_Trig, 0))
    s.o.assert_eq(expected)

@cocotb.test()
async def test_imm_and_tokens_boundaries(dut):
    """
    Check edge token values and imm boundary cases pack and read back correctly.
    """
    global Src
    global Dst
    setup_token_maps()
    
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    # Use raw integers to test boundaries if they aren't exposed in enum
    # Maxing out 7-bit token field (0x7F) - assuming decoder maps unknown to Zero/OpA default
    w0 = pack_move(1, 0x7F, 0x7E, 0x0000)   
    w1 = pack_move(0, 0x7F, 0x7E, 0x0000)   
    await write_instr(s, dut.clk, 9, w0, w1)

    s.i.boot_mode = False
    s.i.wr_addr  = "None"
    s.i.wr_slot0 = "None"
    s.i.wr_slot1 = "None"
    s.i.fetch_pc = 9
    await FallingEdge(dut.clk)
    await FallingEdge(dut.clk)

    # Manual expected string because 0x7F maps to defaults in Spade match arms
    # 0x7F -> _ -> Src::Zero
    # 0x7E -> _ -> Dst::ALU_OpA
    # Note: Using fmt_instr with raw ints will use the dynamic lookup which should default correctly
    
    expected = fmt_instr((1, Src.Zero, Dst.ALU_OpA, 0), (0, Src.Zero, Dst.ALU_OpA, 0))
    s.o.assert_eq(expected)

@cocotb.test()
async def test_long_program_sequential_fetch(dut):
    """
    Load 1023 instructions, then sequentially fetch all of them and
    verify raw words and decoded Instr strings.
    """
    global Src
    global Dst
    setup_token_maps()
    
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    N = 1023 
    moves0, moves1, words0, words1 = [], [], [], []

    for i in range(N):
        m0 = (0, Src.Immediate, Dst.ALU_OpA, i)
        m1 = (1, Src.RegisterFile(i & 7), Dst.ALU_Add_Trig, 0)
        
        w0 = pack_move(*m0)
        w1 = pack_move(*m1)
        moves0.append(m0); moves1.append(m1)
        words0.append(w0); words1.append(w1)
        await write_instr(s, dut.clk, i, w0, w1)

    s.i.boot_mode = False
    s.i.wr_addr = "None"
    s.i.wr_slot0 = "None"
    s.i.wr_slot1 = "None"

    # Fetch and check
    for pc in range(N):
        s.i.fetch_pc = pc
        await FallingEdge(dut.clk)  
        await FallingEdge(dut.clk)
        #dut._log.info(pc)
        s.o.assert_eq(fmt_instr(moves0[pc], moves1[pc]))

@cocotb.test()
async def test_overwrite_stride_every_3(dut):
    """
    Write a small program, then overwrite every 3rd address with new data.
    Verify fetch returns the updated contents.
    """
    global Src
    global Dst
    setup_token_maps()
    
    await start_clock(dut.clk)
    s = await reset_dut(dut)

    N = 30
    base0, base1 = [], []
    for i in range(N):
        m0 = (0, Src.Immediate, Dst.ALU_OpA, i)
        m1 = (1, Src.RegisterFile(i & 7), Dst.ALU_Add_Trig, 0)
        await write_instr(s, dut.clk, i, pack_move(*m0), pack_move(*m1))
        base0.append(m0); base1.append(m1)

    # Overwrite every 3rd instruction
    for i in range(0, N, 3):
        m0 = (1, Src.PC_Val, Dst.PC_Trig, 0)        
        m1 = (0, Src.Zero, Dst.ALU_Or_Trig, 0)
        await write_instr(s, dut.clk, i, pack_move(*m0), pack_move(*m1))
        base0[i] = m0; base1[i] = m1

    s.i.boot_mode = False
    s.i.wr_addr = "None"
    s.i.wr_slot0 = "None"
    s.i.wr_slot1 = "None"
    s.i.fetch_pc = 0
    await FallingEdge(dut.clk)

    # Spot check
    for i in range(0, N, 3):
        s.i.fetch_pc = i
        await FallingEdge(dut.clk)
        await FallingEdge(dut.clk)

        s.o.assert_eq(fmt_instr(base0[i], base1[i]))
        if i+1 < N:
            s.i.fetch_pc = i+1
            await FallingEdge(dut.clk)
            await FallingEdge(dut.clk)
            s.o.assert_eq(fmt_instr(base0[i+1], base1[i+1]))

@cocotb.test()
async def test_random_program_spotchecks(dut):
    """
    Randomized long program; fetch random PCs and verify both raw words and decode strings.
    """
    global Src
    global Dst
    setup_token_maps()
    
    await start_clock(dut.clk)
    s = await reset_dut(dut)
    random.seed(42)

    N = 200
    # Use dynamic pools derived from the parsed maps
    # Filter out RF special handling for pool simplicity, or just add a few representative ones
    SRC_POOL = [Src.Immediate, Src.Zero, Src.PC_Val, Src.ALU_Res, Src.LSU_Res] + [Src.RegisterFile(i) for i in range(8)]
    DST_POOL = [Dst.ALU_OpA, Dst.ALU_Add_Trig, Dst.LSU_AddrA, Dst.PC_Trig] + [Dst.RegisterFile(i) for i in range(8)]

    moves = []
    for i in range(N):
        s0 = random.choice(SRC_POOL); d0 = random.choice(DST_POOL)
        s1 = random.choice(SRC_POOL); d1 = random.choice(DST_POOL)
        i0 = random.randint(0, 0xFFFF) if s0 == Src.Immediate else 0
        i1 = random.randint(0, 0xFFFF) if s1 == Src.Immediate else 0
        m0 = (random.randint(0,1), s0, d0, i0)
        m1 = (random.randint(0,1), s1, d1, i1)
        moves.append((m0, m1))
        await write_instr(s, dut.clk, i, pack_move(*m0), pack_move(*m1))

    s.i.boot_mode = False
    s.i.wr_addr = "None"
    s.i.wr_slot0 = "None"
    s.i.wr_slot1 = "None"
    
    for pc in random.sample(range(N), 20):
        s.i.fetch_pc = pc
        await FallingEdge(dut.clk)
        await FallingEdge(dut.clk)
        s.o.assert_eq(fmt_instr(moves[pc][0], moves[pc][1]))






def parse_match_arms(file_content, func_name):
    """
    Extracts the body of a specific function's match statement 
    and returns a list of tuples: (token_int, target_str).
    """
    global Src
    global Dst
    setup_token_maps()
    
    # 1. Find the function definition
    func_start_pattern = f"fn {func_name}\("
    match_start = re.search(func_start_pattern, file_content)
    
    if not match_start:
        raise ValueError(f"Function {func_name} not found in file.")
    
    # Locate the match block inside the function
    rest_of_file = file_content[match_start.start():]
    match_block_start = rest_of_file.find("match t {")
    
    if match_block_start == -1:
        raise ValueError(f"'match t {{' block not found inside {func_name}.")
        
    # Extract the block content
    block_content = ""
    brace_count = 0
    started = False
    
    scan_start = match_block_start + len("match t")
    
    for i, char in enumerate(rest_of_file[scan_start:]):
        if char == '{':
            if not started:
                started = True
                brace_count = 1
                continue
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if started and brace_count == 0:
                break
        
        if started:
            block_content += char

    # 2. Extract Token Numbers AND Targets
    # Pattern:  12u8 => Target::Thing,
    # Regex captures: Group 1 (digits), Group 2 (rest of line until comma or comment)
    
    # Matches: "  12u8 => Dst::Thing," or "  12u8 => Dst::Thing(x),"
    # Note: We need to be careful about the "Src::Immediate(zext(imm16))" case
    
    token_pattern = re.compile(r'(\d+)u8\s*=>\s*([^,\n]+)')
    
    mappings = []
    lines = block_content.split('\n')
    for line in lines:
        # Strip comments first
        clean_line = line.split('//')[0].strip()
        if not clean_line:
            continue
            
        # Check for match
        match = token_pattern.search(clean_line)
        if match:
            token_val = int(match.group(1))
            target_str = match.group(2).strip()
            mappings.append((token_val, target_str))
            
    return mappings

@cocotb.test()
async def test_imem_tokens_unique(dut):
    """
    Parses imem.spade and asserts that:
    1. Token IDs (u8) are unique.
    2. Token Targets (Dst::...) are unique (no two tokens map to same dest).
    """
    # Load file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(current_dir, "../../src/imem.spade")
    
    if not os.path.exists(filename):
        print(f"Error: {filename} not found.")
        assert False, f"File {filename} not found."

    with open(filename, 'r') as f:
        content = f.read()

    # --- Helper to run checks ---
    def check_uniqueness(name, mappings):
        print(f"\nChecking {name}...")
        
        # 1. Check Unique IDs
        seen_ids = set()
        dup_ids = set()
        
        # 2. Check Unique Targets
        seen_targets = set()
        dup_targets = set()
        
        # Target Ignore List (Things that are allowed to be duplicated or catch-alls)
        # We explicitly allow "Src::Zero" or reserved bands if that's the intent, 
        # but the prompt specifically asked to fail on "08u8 => Dst::ALU_OpA, 09u8 => Dst::ALU_OpA"
        # So we will enforce strict uniqueness.
        
        for token_id, target in mappings:
            # Check ID
            if token_id in seen_ids:
                dup_ids.add(token_id)
            seen_ids.add(token_id)
            
            # Check Target
            # Normalize target string (remove trailing parens/spaces if needed)
            # e.g. "Dst::RegisterFile(0u4)" vs "Dst::RegisterFile(1u4)" are different.
            if target in seen_targets:
                # Special Case: Allow Src::Zero to be reused? 
                # The prompt implies STRICT mapping. 
                # Ideally, reserved bands map to _ => Src::Zero, not explicit numbers.
                dup_targets.add(f"{target} (used by {token_id})")
            seen_targets.add(target)

        # Report IDs
        if dup_ids:
            print(f"FAIL: Duplicate {name} Token IDs found: {sorted(list(dup_ids))}")
        else:
            print(f"PASS: {len(mappings)} {name} token IDs are unique.")
            
        assert not dup_ids, f"Duplicate {name} IDs: {dup_ids}"

        # Report Targets
        if dup_targets:
            print(f"FAIL: Duplicate {name} Targets found: {sorted(list(dup_targets))}")
            # We assert here to fail the test as requested
            assert not dup_targets, f"Duplicate {name} Targets detected: {dup_targets}"
        else:
            print(f"PASS: All {name} targets are unique.")

    # --- Run Checks ---
    src_map = parse_match_arms(content, "decode_src_tok")
    check_uniqueness("Source", src_map)

    dst_map = parse_match_arms(content, "decode_dst_tok")
    check_uniqueness("Dest", dst_map)


def parse_enum_variants(spade_content, enum_name):
    """
    Parse an enum definition from Spade source and extract all variant names.
    Handles both simple variants (e.g., ALU_Res) and parameterized variants
    (e.g., RegisterFile{idx: uint<4>}).
    """
    pattern = rf'enum\s+{enum_name}\s*\{{'
    match = re.search(pattern, spade_content)
    if not match:
        raise ValueError(f"Could not find enum {enum_name}")

    start = match.end()
    brace_count = 1
    end = start
    while brace_count > 0 and end < len(spade_content):
        if spade_content[end] == '{':
            brace_count += 1
        elif spade_content[end] == '}':
            brace_count -= 1
        end += 1

    enum_body = spade_content[start:end-1]
    variant_pattern = r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\{[^}]*\})?\s*,?\s*(?://.*)?$'
    variants = []
    for line in enum_body.split('\n'):
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        m = re.match(variant_pattern, line)
        if m:
            variants.append(m.group(1))
    return variants


def get_mapped_variants_from_mappings(mappings):
    """
    Extract unique variant names from token mappings.
    mappings is a list of (token_id, target_str) tuples.
    Returns a set of variant names (e.g., 'ALU_Res', 'RegisterFile').
    """
    variants = set()
    for _, target in mappings:
        # Extract variant name from "Src::VariantName" or "Dst::VariantName(args)"
        m = re.match(r'(?:Src|Dst)::([A-Za-z_][A-Za-z0-9_]*)', target)
        if m:
            variants.add(m.group(1))
    return variants


@cocotb.test()
async def test_enum_coverage(dut):
    """
    Verify that all Src and Dst enum variants defined in tta.spade
    have corresponding token mappings in imem.spade.

    This is critical: if a variant has no token mapping, the instruction
    cannot be encoded and will not work in the final processor!
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Load tta.spade for enum definitions
    tta_file = os.path.join(current_dir, "../../src/tta.spade")
    if not os.path.exists(tta_file):
        assert False, f"File {tta_file} not found."
    with open(tta_file, 'r') as f:
        tta_content = f.read()

    # Load imem.spade for token mappings
    imem_file = os.path.join(current_dir, "../../src/imem.spade")
    if not os.path.exists(imem_file):
        assert False, f"File {imem_file} not found."
    with open(imem_file, 'r') as f:
        imem_content = f.read()

    # Parse enum variants from tta.spade
    src_variants = set(parse_enum_variants(tta_content, "Src"))
    dst_variants = set(parse_enum_variants(tta_content, "Dst"))

    # Parse token mappings from imem.spade
    src_mappings = parse_match_arms(imem_content, "decode_src_tok")
    dst_mappings = parse_match_arms(imem_content, "decode_dst_tok")

    src_mapped = get_mapped_variants_from_mappings(src_mappings)
    dst_mapped = get_mapped_variants_from_mappings(dst_mappings)

    # Check for missing Src mappings
    missing_src = src_variants - src_mapped
    if missing_src:
        print(f"\nFAIL: The following Src enum variants have NO token mapping:")
        for v in sorted(missing_src):
            print(f"  - {v}")
        print("\nThese instructions cannot be encoded in the final processor!")
    else:
        print(f"\nPASS: All {len(src_variants)} Src enum variants have token mappings.")

    # Check for missing Dst mappings
    missing_dst = dst_variants - dst_mapped
    if missing_dst:
        print(f"\nFAIL: The following Dst enum variants have NO token mapping:")
        for v in sorted(missing_dst):
            print(f"  - {v}")
        print("\nThese instructions cannot be encoded in the final processor!")
    else:
        print(f"\nPASS: All {len(dst_variants)} Dst enum variants have token mappings.")

    # Check for phantom mappings (mappings to variants that don't exist)
    extra_src = src_mapped - src_variants
    if extra_src:
        print(f"\nWARNING: These Src mappings reference non-existent variants: {sorted(extra_src)}")

    extra_dst = dst_mapped - dst_variants
    if extra_dst:
        print(f"\nWARNING: These Dst mappings reference non-existent variants: {sorted(extra_dst)}")

    # Fail the test if any coverage is missing
    assert not missing_src, f"Missing Src token mappings: {sorted(missing_src)}"
    assert not missing_dst, f"Missing Dst token mappings: {sorted(missing_dst)}"