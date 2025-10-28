import cocotb
import os
import json
import logging
from cocotb.triggers import RisingEdge, FallingEdge, Timer, First
from cocotb.clock import Clock
from regfile_signal_finder import find_regfile_write_signals, load_regfile_interface


# Pipeline measurement program with cache pre-warming strategy
# Strategy: Execute through addresses twice - first pass fills cache, second pass measures
# PASS 1: Cache warmup (0x00-0x7C) - fills instruction cache
# PASS 2: Measurement window (0x80-0xD4) - should hit in cache
# PASS 3: Loop back to PASS 2 for sustained throughput measurement

prog = {}

# === PASS 1: Cache Warmup (32 NOPs) ===
# These addresses will MISS in cache the first time, filling the cache
for i in range(32):
    prog[i * 4] = 0x00000013  # NOP (addi x0, x0, 0)

# === PASS 2: Measurement Window ===
# After warmup, these should be cache HITs (if cache is large enough)
# Or at least the access pattern is established

prog[0x00000080] = 0x00200113  # addi x2, x0, 2
prog[0x00000084] = 0x00300193  # addi x3, x0, 3
prog[0x00000088] = 0x00400213  # addi x4, x0, 4
prog[0x0000008c] = 0x00500293  # addi x5, x0, 5
prog[0x00000090] = 0x00600313  # addi x6, x0, 6
prog[0x00000094] = 0x00700393  # addi x7, x0, 7
prog[0x00000098] = 0x00800413  # addi x8, x0, 8
prog[0x0000009c] = 0x00900493  # addi x9, x0, 9
prog[0x000000a0] = 0x00a00513  # addi x10, x0, 10
prog[0x000000a4] = 0x00b00593  # addi x11, x0, 11

# === TEST INSTRUCTION (for pipeline depth measurement) ===
prog[0x000000a8] = 0x00500093  # addi x1, x0, 5 ← THE TEST INSTRUCTION

# === PASS 3: More NOPs then loop ===
prog[0x000000ac] = 0x00000013  # NOP
prog[0x000000b0] = 0x00000013  # NOP
prog[0x000000b4] = 0x00000013  # NOP
prog[0x000000b8] = 0x00000013  # NOP
prog[0x000000bc] = 0x00000013  # NOP
prog[0x000000c0] = 0x00000013  # NOP
prog[0x000000c4] = 0x00000013  # NOP
prog[0x000000c8] = 0x00000013  # NOP
prog[0x000000cc] = 0x00000013  # NOP
prog[0x000000d0] = 0x00000013  # NOP

# Jump back to 0x80 to create infinite loop (for Phase 2 observation of warm cache)
prog[0x000000d4] = 0xfadff06f  # jal x0, -84 (jump to 0x80)
# After this jump, all instructions 0x80-0xD4 should be in cache and execute at full pipeline speed


async def instr_mem_driver(dut):
    """
    Zero-wait-state memory driver that responds immediately.
    For cores that check valid/ack before asserting request (like AUK-V),
    we keep ACK high and data ready at all times.
    """
    dut.core_data_in.value = 0
    dut.core_ack.value = 1  # Keep ACK high - zero wait state memory
    cycle_count = 0
    while True:
        await RisingEdge(dut.sys_clk)
        cycle_count += 1
        
        # Always provide valid data based on current address
        addr_val = dut.core_addr.value
        if addr_val.is_resolvable:
            addr = addr_val.integer
            instr = prog.get(addr, 0x00000013)  # default NOP
            dut.core_data_in.value = instr
            
            if cycle_count <= 20:
                cyc_val = dut.core_cyc.value if hasattr(dut, 'core_cyc') else 'N/A'
                stb_val = dut.core_stb.value if hasattr(dut, 'core_stb') else 'N/A'
                dut._log.info(f"[mem_driver cycle {cycle_count}] cyc={cyc_val} stb={stb_val} addr={addr:#010x} data={instr:#010x}")
        else:
            dut.core_data_in.value = 0x00000013  # NOP if address not ready


async def data_mem_driver(dut):
    """
    Data memory driver for cores with separate instruction and data buses.
    Zero-wait-state: keeps ACK high and provides immediate responses.
    """
    # Check if core has separate data memory interface
    if not hasattr(dut, 'data_mem_ack'):
        return  # Core doesn't have separate data memory, exit
    
    dut.data_mem_data_in.value = 0
    dut.data_mem_ack.value = 1  # Keep ACK high - zero wait state
    
    while True:
        await RisingEdge(dut.sys_clk)
        # Always provide data (0 for all loads)
        dut.data_mem_data_in.value = 0


async def measure_with_interface_signals(dut, write_enable_sig, write_addr_sig, target_addr=1):
    """
    Measure pipeline depth using register file write interface signals.
    This is the most accurate method as it detects writeback at the exact cycle.
    
    Args:
        dut: Design under test
        write_enable_sig: Write enable signal handle
        write_addr_sig: Write address signal handle
        target_addr: Target register to watch (default: x1)
    
    Returns: (issue_cycle, write_cycle, write_edge) or (None, None, None) on failure
    """
    issue_cycle = None
    write_cycle = None
    write_edge = None
    max_cycles = 300  # Extended for cores with cache latency
    
    dut._log.info(f"[measure] Using register file INTERFACE signals for writeback detection")
    
    for cycle in range(max_cycles):
        # === CHECK RISING EDGE ===
        await RisingEdge(dut.sys_clk)
        
        # Detect fetch completion
        if dut.core_addr.value.is_resolvable:
            pc_val = dut.core_addr.value.integer
            
            if issue_cycle is None and pc_val == 0x000000a8 and dut.core_stb.value and dut.core_ack.value:
                issue_cycle = cycle
                dut._log.info(f"[measure] Fetch completes at cycle {cycle}.rising (PC=0x000000a8)")
        
        # After fetch, monitor write interface on rising edge
        if issue_cycle is not None and write_cycle is None:
            try:
                # Check if write is happening to our target register
                if write_enable_sig.value and write_addr_sig.value.is_resolvable:
                    addr = int(write_addr_sig.value)
                    if addr == target_addr:
                        write_cycle = cycle
                        write_edge = 'rising'
                        dut._log.info(f"[measure] WB detected at cycle {cycle}.rising via interface signals")
                        return (issue_cycle, write_cycle, write_edge)
            except Exception as e:
                pass
        
        # === CHECK FALLING EDGE ===
        if issue_cycle is not None and write_cycle is None:
            await FallingEdge(dut.sys_clk)
            
            try:
                if write_enable_sig.value and write_addr_sig.value.is_resolvable:
                    addr = int(write_addr_sig.value)
                    if addr == target_addr:
                        write_cycle = cycle
                        write_edge = 'falling'
                        dut._log.info(f"[measure] WB detected at cycle {cycle}.falling via interface signals")
                        return (issue_cycle, write_cycle, write_edge)
            except Exception as e:
                pass
    
    return (issue_cycle, write_cycle, write_edge)


async def measure_pipeline_depth(dut, regfile, core_name=None):
    """
    Measure pipeline depth by observing ADDI x1, x0, 5 at PC=0xa8.
    
    The cache is warmed up with 32 NOPs, then the pipeline is pre-filled with 
    independent ADDI instructions to different registers (x2-x11), ensuring no 
    hazards when our test instruction (writing to x1) enters the pipeline. 
    This gives us accurate timing of a pipeline running at steady state with 
    a warm cache.
    
    Strategy (two-tier approach):
    1. Try to use register file write interface signals (write_enable, write_addr)
       - Most accurate: detects exact writeback cycle
       - Eliminates 1-2 cycle observation delay
    2. Fallback to register file observation
       - Generic approach that works for any core
       - Has ~1 cycle delay from actual writeback
    
    Args:
        dut: Design under test
        regfile: Register file array handle
        core_name: Name of the core (for finding/caching interface signals)
    
    Returns measured pipeline stages (int) or None on failure.
    """
    x1_idx = 1
    expected_value = 5  # ADDI x1, x0, 5
    
    # Try to find/load register file interface signals for accurate measurement
    interface_signals = None
    if core_name:
        # Try to load previously found signals
        interface_signals = load_regfile_interface(core_name)
        
        if not interface_signals:
            # Try to find signals in the design
            dut._log.info(f"[measure] Searching for register file write interface signals...")
            interface_signals = find_regfile_write_signals(dut, core_name, regfile)
    
    # If we found interface signals, use them for accurate measurement
    if interface_signals and "write_enable" in interface_signals and "write_addr" in interface_signals:
        try:
            # Get signal handles
            we_path = interface_signals["write_enable"].replace("processorci_top.", "").split('.')
            wa_path = interface_signals["write_addr"].replace("processorci_top.", "").split('.')
            
            write_enable_sig = dut
            for part in we_path:
                write_enable_sig = getattr(write_enable_sig, part)
            
            write_addr_sig = dut
            for part in wa_path:
                write_addr_sig = getattr(write_addr_sig, part)
            
            # Use interface-based measurement
            issue_cycle, write_cycle, write_edge = await measure_with_interface_signals(
                dut, write_enable_sig, write_addr_sig, target_addr=x1_idx
            )
            
            if issue_cycle is not None and write_cycle is not None:
                cycles_through_pipeline = write_cycle - issue_cycle
                
                dut._log.info(f"[measure] === Timing Analysis (INTERFACE METHOD) ===")
                dut._log.info(f"[measure] Fetch: cycle {issue_cycle}.rising")
                dut._log.info(f"[measure] Writeback: cycle {write_cycle}.{write_edge}")
                dut._log.info(f"[measure] Cycles elapsed: {cycles_through_pipeline}")
                
                # With interface signals, stages = cycles + 1 (standard formula)
                stages = cycles_through_pipeline + 1
                dut._log.info(f"[measure] === Result: {stages}-stage pipeline (accurate) ===")
                return stages
        except Exception as e:
            dut._log.warning(f"[measure] Failed to use interface signals: {e}")
            dut._log.warning(f"[measure] Falling back to register file observation")
    
    # Fallback: Use register file observation (generic method)
    dut._log.info("[measure] Using register file observation for writeback detection")

    # Align to clock and sample a baseline for x1
    await RisingEdge(dut.sys_clk)
    try:
        baseline = int(regfile[x1_idx].value) if regfile[x1_idx].value.is_resolvable else 0
    except Exception:
        baseline = 0
    
    dut._log.info(f"[measure] Baseline value for x1: {baseline}")

    issue_cycle = None
    write_cycle = None
    write_edge = None

    # Maximum observation window (extended for cores with cache latency)
    max_cycles = 300

    for cycle in range(max_cycles):
        # === CHECK RISING EDGE ===
        await RisingEdge(dut.sys_clk)
        
        # Safe PC read
        if dut.core_addr.value.is_resolvable:
            pc_val = dut.core_addr.value.integer
        else:
            pc_val = None

        dut._log.debug(f"[measure] cycle={cycle}.rising pc={pc_val}")

        # Detect when fetch transaction COMPLETES (STB & ACK both high for target PC=0xa8)
        if issue_cycle is None and pc_val == 0x000000a8 and dut.core_stb.value and dut.core_ack.value:
            issue_cycle = cycle
            dut._log.info(f"[measure] Fetch completes at cycle {cycle}.rising (PC=0x000000a8)")
            
            # Check if writeback happens in the SAME cycle (single-cycle core)
            try:
                if regfile[x1_idx].value.is_resolvable:
                    new_val = int(regfile[x1_idx].value)
                    if new_val == expected_value:
                        write_cycle = cycle
                        write_edge = 'rising'
                        dut._log.info(f"[measure] WB at SAME cycle {cycle}.rising (single-cycle core)")
                        break
            except Exception:
                pass

        # After fetch detected, monitor for writeback on rising edge
        elif issue_cycle is not None and write_cycle is None:
            try:
                if regfile[x1_idx].value.is_resolvable:
                    new_val = int(regfile[x1_idx].value)
                    if new_val == expected_value:
                        write_cycle = cycle
                        write_edge = 'rising'
                        cycles_elapsed = cycle - issue_cycle
                        dut._log.info(f"[measure] WB at cycle {cycle}.rising ({cycles_elapsed} cycles after fetch)")
                        break
            except Exception:
                pass

        # === CHECK FALLING EDGE ===
        # Check falling edge if we haven't found the write yet and we've detected fetch
        if issue_cycle is not None and write_cycle is None:
            await FallingEdge(dut.sys_clk)
            
            dut._log.debug(f"[measure] cycle={cycle}.falling")
            
            # Check for writeback on falling edge
            try:
                if regfile[x1_idx].value.is_resolvable:
                    new_val = int(regfile[x1_idx].value)
                    if new_val == expected_value:
                        write_cycle = cycle
                        write_edge = 'falling'
                        cycles_elapsed = cycle - issue_cycle
                        dut._log.info(f"[measure] WB at cycle {cycle}.falling ({cycles_elapsed} cycles after fetch)")
                        break
            except Exception:
                pass

    if issue_cycle is None or write_cycle is None:
        dut._log.warning(f"[measure] failed to observe fetch/write (issue={issue_cycle}, write={write_cycle})")
        return None

    # Pipeline stages calculation
    cycles_through_pipeline = write_cycle - issue_cycle
    
    dut._log.info(f"[measure] === Timing Analysis (OBSERVATION METHOD) ===")
    dut._log.info(f"[measure] Fetch: cycle {issue_cycle}.rising")
    dut._log.info(f"[measure] Writeback observed: cycle {write_cycle}.{write_edge}")
    dut._log.info(f"[measure] Cycles elapsed: {cycles_through_pipeline}")
    
    # Pipeline stages = cycles elapsed + 1
    # When instruction enters at cycle N and completes at cycle N+K,
    # it goes through K+1 pipeline stages
    stages = cycles_through_pipeline + 1
    
    dut._log.info(f"[measure] === Result: {stages}-stage pipeline (observation-based) ===")
    return stages


async def test_pc_behavior(dut, regfile):
    # initialize driven signals
    dut.core_ack.value = 0
    dut.core_data_in.value = 0

    cocotb.start_soon(Clock(dut.sys_clk, 10, units="ns").start())
    cocotb.start_soon(instr_mem_driver(dut))
    cocotb.start_soon(data_mem_driver(dut))  # For cores with separate data memory

    # Reset
    dut.rst_n.value = 0
    dut.core_ack.value = 0
    await Timer(50, units="ns")
    dut.rst_n.value = 1

    # Measure pipeline depth - will catch test instruction whenever it appears
    dut._log.info("Phase 1: Measuring pipeline depth...")
    
    # Get core name from environment for interface signal lookup
    output_dir = os.environ.get('OUTPUT_DIR', "default")
    core_name = os.path.basename(output_dir)
    
    stages = await measure_pipeline_depth(dut, regfile, core_name=core_name)
    
    # Now analyze transaction intervals AFTER cache warmup to determine multicycle vs pipelined
    # We continue from where Phase 1 left off (no reset) to measure warm cache behavior
    dut._log.info("Phase 2: Analyzing transaction patterns for multicycle detection (warm cache)...")
    
    # NO RESET - continue measuring from warm cache state
    # The cache is already primed from Phase 1 execution
    
    transaction_intervals = []
    last_transaction_cycle = None
    first_pc_seen = None

    # Observe PC and bus transactions for 60 more cycles to catch the loop execution
    for cycle in range(60):
        await RisingEdge(dut.sys_clk)
        
        # Check for successful Wishbone transaction (stb & ack both high)
        transaction_occurred = (dut.core_cyc.value and 
                               dut.core_stb.value and 
                               dut.core_ack.value and 
                               not dut.core_we.value)
        
        if not dut.core_addr.value.is_resolvable:
            continue
            
        pc = dut.core_addr.value.integer
        
        if transaction_occurred:
            dut._log.info(f"Cycle {cycle}: PC = {pc:#010x} [TRANSACTION]")
        else:
            dut._log.info(f"Cycle {cycle}: PC = {pc:#010x}")

        # Track intervals between successful transactions (not just PC changes)
        if transaction_occurred:
            if first_pc_seen is None:
                first_pc_seen = pc
                last_transaction_cycle = cycle
            elif last_transaction_cycle is not None:
                interval = cycle - last_transaction_cycle
                transaction_intervals.append(interval)
                last_transaction_cycle = cycle

    output_dir = os.environ.get('OUTPUT_DIR', "default")
    processor_name = os.path.basename(output_dir)
    output_file = os.path.join(output_dir, f"{processor_name}_labels.json")
    if not os.path.exists(output_file):
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump({}, json_file, indent=4)
    try:
        with open(output_file, 'r', encoding='utf-8') as json_file:
            existing_data = json.load(json_file)
    except (json.JSONDecodeError, OSError) as e:
        logging.warning('Error reading existing JSON file: %s', e)
        existing_data = {}

    # Filter out zero-length intervals (shouldn't happen, but safe)
    filtered = [d for d in transaction_intervals if d > 0]

    dut._log.info(f"Transaction intervals: {filtered}")

    # Now classify based on both pipeline depth measurement and transaction patterns
    if not filtered:
        dut._log.warning("No transaction intervals detected. Core may not be functioning.")
        existing_data.setdefault(processor_name, {})
        existing_data[processor_name]["multicycle"] = None
        existing_data[processor_name]["pipeline"] = None
    elif all(delta == 1 for delta in filtered):
        dut._log.info("Detected consistent 1-cycle transaction intervals → likely pipelined or single-cycle core.")
        
        existing_data.setdefault(processor_name, {})
        if stages is None:
            dut._log.warning("Could not measure pipeline depth.")
            existing_data[processor_name]["multicycle"] = None
            existing_data[processor_name]["pipeline"] = None
        elif stages == 1:
            dut._log.info("Detected SINGLE-CYCLE core (1 stage).")
            existing_data[processor_name]["multicycle"] = False
            existing_data[processor_name]["pipeline"] = False
        elif stages > 1:
            dut._log.info(f"Detected PIPELINED core: {stages}-stage pipeline.")
            existing_data[processor_name]["multicycle"] = False
            existing_data[processor_name]["pipeline"] = {"depth": stages}
        else:
            dut._log.warning(f"Unexpected stages value: {stages}")
            existing_data[processor_name]["multicycle"] = None
            existing_data[processor_name]["pipeline"] = None
    else:
        # Multiple-cycle intervals between transactions → multicycle core
        avg_interval = sum(filtered) / len(filtered)
        dut._log.info(f"Detected variable/multi-cycle transaction intervals (avg: {avg_interval:.1f}) → likely multicycle core.")
        existing_data.setdefault(processor_name, {})
        existing_data[processor_name]["multicycle"] = True
        existing_data[processor_name]["pipeline"] = False

    try:
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(existing_data, json_file, indent=4)
        dut._log.info(f'Results saved to {output_file}')
    except OSError as e:
        logging.warning('Error writing to JSON file: %s', e)
