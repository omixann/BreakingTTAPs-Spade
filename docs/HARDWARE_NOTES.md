# TTA ASIC Hardware Notes

This document describes hardware behaviors that programmers and compiler authors must account for when targeting this TTA architecture.

NOTE: this document needs to be audited, I'm not sure it's current anymore (especially after the last-minute Christmas bug fix). The rest of the instructions need to be documented too. Will update soon!

---

## Table of Contents

1. [Memory and Addressing](#memory-and-addressing)
2. [Functional Unit Latencies and Conflicts](#functional-unit-latencies-and-conflicts)
3. [Arithmetic Limitations](#arithmetic-limitations)
4. [I/O Considerations](#io-considerations)
5. [Boot Sequence](#boot-sequence)

---

## Memory and Addressing

### Instruction Memory (IMEM)

| Property | Value |
|----------|-------|
| Size | 1024 instructions |
| Instruction Width | 2 x 32-bit move words (slot0, slot1) |
| Address Range | 0 - 1023 |

**PC Wraparound:** The program counter wraps silently from 1023 to 0. Ensure your program fits within IMEM or explicitly handles the boundary.

### Data Memory (DMEM via LSU)

| Property | Value |
|----------|-------|
| Size | 1024 x 32-bit words |
| Address Range | 0 - 1023 |
| LSU Count | 2 (LSU, LSU2) |

**Address Overflow:** LSU addresses are 10 bits. Values > 1023 wrap silently (e.g., address 1025 accesses word 1).

### Stack

| Property | Value |
|----------|-------|
| Depth | 256 entries |
| Entry Width | 32 bits |
| Stack Pointer Range | 0 - 255 |

**Stack Pointer Wraparound:** The stack pointer is 8 bits and wraps silently. Pushing beyond 256 entries overwrites the bottom of the stack. Popping an empty stack wraps SP to 255. **Software must track stack depth.**

**Push/Pop Conflict:** If both `Stack_Push_Trig` and `Stack_Pop_Trig` are written in the same cycle, **push wins** and pop is suppressed.

---

## Functional Unit Latencies and Conflicts

### Register File

| Property | Value |
|----------|-------|
| Registers | 16 x 32-bit (r0 - r15) |
| Read Ports | 2 (one per bus) |
| Write Ports | 2 (one per bus) |

**Dual-Write Conflict:** If both slots write to the same register in one instruction, **slot1 wins**. The slot0 write is lost.

**Invalid Register Index:** Register indices outside 0-15 default to r15.

### Load-Store Units (LSU, LSU2)

| Operation | Latency |
|-----------|---------|
| Load | 2 cycles (result available on 3rd cycle) |
| Store | 1 cycle |

**Overlapped Loads:** Each LSU can only have **one load pending** at a time. You must wait 2 cycles between issuing consecutive loads to the same LSU. Issuing a second load before the first completes produces undefined results.

```
Cycle 0: LSU_Load_Trig <- addr1   ; Start load 1
Cycle 1: (wait)
Cycle 2: r0 <- LSU_Res            ; Load 1 result ready
Cycle 2: LSU_Load_Trig <- addr2   ; Safe to start load 2
```

**Load/Store Conflict:** If `LSU_Load_Trig` and `LSU_Store_Trig` are written in the same cycle, **store wins** and the load is suppressed.

### ALU

| Operation | Latency |
|-----------|---------|
| All operations | 1 cycle |

**Shift Amounts:** Shift operations (Shl, Shr, Ashr, Rotl, Rotr) mask the shift amount to 5 bits (0-31). Shifting by 32 or more is equivalent to shifting by `amount mod 32`.

### Comparators (Cmp, Cmpz)

| Operation | Latency |
|-----------|---------|
| All comparisons | 1 cycle |

Results are 1 (true) or 0 (false).

### Multiplier (MUL)

| Operation | Latency |
|-----------|---------|
| 32x32 multiply | 32 cycles |

**Precision:** Result is truncated to 32 bits. Upper bits of the 64-bit product are lost. This is by design for this chip's use case.

### Multiply-Accumulate (MAC)

| Operation | Latency |
|-----------|---------|
| MAC operation | 32 cycles |

**Precision:** Accumulator and result are 32 bits. Overflow wraps silently. Use `MAC_Clear` to reset the accumulator.

### Divider (DIV)

| Operation | Latency |
|-----------|---------|
| 32-bit divide | 32 cycles |

**Division by Zero:** Produces undefined/garbage output. **Software must check for zero divisor before triggering division.**

### Xorshift PRNG

| Operation | Latency |
|-----------|---------|
| Generate next | 1 cycle |

**Seed Value:** The PRNG state is initialized to 1 on reset. Writing 0 as a seed keeps the state unchanged (0 would break the algorithm). The xorshift32 algorithm never produces 0 as output.

### Tanh Approximation (TNH)

| Operation | Latency |
|-----------|---------|
| Tanh lookup | 1 cycle |

**Input Range:** Optimized for inputs in the range [-0.75, +0.75]. Values outside this range are clamped.

### Select Unit (SEL)

| Operation | Latency |
|-----------|---------|
| Conditional select | 1 cycle |

Selects between two values based on a condition. Set condition first, then operand A, then trigger with operand B.

---

## Arithmetic Limitations

### Saturating Arithmetic

The ALU provides saturating add/subtract for both signed and unsigned:

| Operation | Overflow Behavior |
|-----------|-------------------|
| USadd | Clamps to 0xFFFFFFFF |
| USsub | Clamps to 0x00000000 |
| SSadd | Clamps to 0x7FFFFFFF (max) or 0x80000000 (min) |
| SSsub | Clamps to 0x7FFFFFFF (max) or 0x80000000 (min) |

### Min/Max

Min and Max operations are **unsigned** comparisons.

---

## I/O Considerations

### General Purpose Input (GPI)

| Property | Value |
|----------|-------|
| Width | 32 bits |
| Synchronization | 2-stage flip-flop |

**Input Latency:** External signals pass through a 2-FF synchronizer, adding **2 cycles of latency** before the value is visible to the CPU via `GPI_In`.

### General Purpose Output (GPO)

| Property | Value |
|----------|-------|
| Width | 32 bits |
| Synchronization | None |

**No Output Synchronization:** GPO directly drives external pins. If the receiving domain uses a different clock, that domain must handle synchronization.

### UART

| Property | Value |
|----------|-------|
| TX/RX Width | 8 bits |
| FIFO Depth | Implementation-defined |

**FIFO Overflow:** If the RX FIFO overflows, new bytes are lost. Software must read `UART_In` and issue `UART_InPop_Trig` frequently enough to prevent overflow.

### SPI

| Property | Value |
|----------|-------|
| Width | 8 bits |
| FIFO Depth | Implementation-defined |

**FIFO Overflow:** Similar to UART, the RX FIFO can overflow if not serviced promptly.

---

## Boot Sequence

### Bootloader Behavior

The system boots in **boot mode** with the PC held at 0. During boot mode:

1. External programmer writes instructions to IMEM via `wr_addr`, `wr_slot0`, `wr_slot1`
2. Boot mode is cleared by external signal
3. Execution begins at **PC = 0**

**Entry Point:** The bootloader's entry point field is non-functional in the current design. Code always starts executing at address 0 regardless of any configured entry point.

**Instruction Count:** The bootloader accepts an instruction count, but values > 1024 are silently clamped to 1024.

---

## Quick Reference: Conflict Resolution

| Conflict | Winner |
|----------|--------|
| Slot0 + Slot1 write same register | Slot1 |
| LSU Load + Store same cycle | Store |
| Stack Push + Pop same cycle | Push |

---

## Quick Reference: Latencies

| Unit | Operation | Cycles |
|------|-----------|--------|
| ALU | All | 1 |
| Cmp/Cmpz | All | 1 |
| LSU | Load | 2 |
| LSU | Store | 1 |
| MUL | Multiply | 32 |
| MAC | MAC | 32 |
| DIV | Divide | 32 |
| Xorshift | Next | 1 |
| TNH | Tanh | 1 |
| SEL | Select | 1 |
| GPI | Sync delay | 2 |
