import cocotb
import os
import json
import logging
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock


# Pipeline measurement program: ADDI x1, x0, 5 preceded by independent ADDIs
# We use different destination registers to avoid any hazards or dependencies
# This allows the pipeline to fill with independent instructions before our test instruction
prog = {
    0x00000000: 0x00000013,  # NOP (addi x0, x0, 0) - reset vector, let pipeline stabilize
    0x00000004: 0x00000013,  # NOP
    0x00000008: 0x00000013,  # NOP
    0x0000000c: 0x00000013,  # NOP
    0x00000010: 0x00000013,  # NOP
    0x00000014: 0x00000013,  # NOP
    0x00000018: 0x00000013,  # NOP
    0x0000001c: 0x00000013,  # NOP
    # Now pipeline is full of NOPs, insert our test instruction
    0x00000020: 0x00200113,  # addi x2, x0, 2  (fill pipe with independent instr)
    0x00000024: 0x00300193,  # addi x3, x0, 3
    0x00000028: 0x00400213,  # addi x4, x0, 4
    0x0000002c: 0x00500293,  # addi x5, x0, 5
    0x00000030: 0x00600313,  # addi x6, x0, 6
    0x00000034: 0x00700393,  # addi x7, x0, 7
    0x00000038: 0x00800413,  # addi x8, x0, 8
    0x0000003c: 0x00900493,  # addi x9, x0, 9
    0x00000040: 0x00a00513,  # addi x10, x0, 10
    0x00000044: 0x00b00593,  # addi x11, x0, 11
    # HERE is our test instruction - pipeline is now warmed up with independent instructions
    0x00000048: 0x00500093,  # addi x1, x0, 5 ← THE TEST INSTRUCTION
    0x0000004c: 0x00000013,  # NOP
    0x00000050: 0x00000013,  # NOP
}


async def instr_mem_driver(dut, prog):
    """
    Wishbone-compliant memory driver with proper handshaking.
    ACK stays high as long as STB is asserted to support both
    single-cycle and multi-cycle transactions.
    """
    dut.core_data_in.value = 0
    dut.core_ack.value = 0
    while True:
        await RisingEdge(dut.sys_clk)
        # Respond immediately when core requests (cyc & stb & read)
        if dut.core_cyc.value and dut.core_stb.value and not dut.core_we.value:
            addr_val = dut.core_addr.value
            if addr_val.is_resolvable:
                addr = addr_val.integer
                instr = prog.get(addr, 0x00000013)  # default NOP
                dut.core_data_in.value = instr
                dut.core_ack.value = 1
            else:
                # Address not resolvable yet; hold ack low
                dut.core_ack.value = 0
        else:
            # No valid request; deassert ack
            dut.core_ack.value = 0
            dut.core_data_in.value = 0


async def measure_pipeline_depth_with_interface(dut, regfile_interface):
    """
    Measure pipeline depth by observing ADDI x1, x0, 5 at PC=0x48.
    Uses the explicit register file interface signals to detect writeback.
    
    Args:
        dut: The design under test
        regfile_interface: Dict with keys:
            - "write_enable": path to write enable signal
            - "write_addr": path to write address signal
            - "write_data": path to write data signal (optional, for verification)
    
    The pipeline is pre-filled with independent ADDI instructions to different
    registers (x2-x11), ensuring no hazards when our test instruction (writing to x1)
    enters the pipeline.
    
    Strategy:
    1. Observe the register file write interface (write_enable + write_addr)
    2. Detect when write_enable is active AND write_addr == 1 (x1)
    3. This gives us the exact cycle when the writeback occurs
    
    Timing model:
    - issue_cycle: cycle where fetch transaction completes (STB & ACK high for PC=0x48)
    - write_cycle: cycle where writeback occurs (write_enable active + write_addr == 1)
    - Pipeline stages = write_cycle - issue_cycle + 1
    
    Returns measured pipeline stages (int) or None on failure.
    """
    x1_idx = 1
    
    # Get signal handles from the interface
    try:
        # Navigate to the signals using the paths provided
        write_enable_path = regfile_interface.get("write_enable")
        write_addr_path = regfile_interface.get("write_addr")
        write_data_path = regfile_interface.get("write_data")  # Optional
        
        if not write_enable_path or not write_addr_path:
            dut._log.error("[measure] Missing required register file interface signals")
            return None
        
        # Parse the signal paths (format: "module.submodule.signal")
        # Remove the "processorci_top." prefix if present
        write_enable_path = write_enable_path.replace("processorci_top.", "")
        write_addr_path = write_addr_path.replace("processorci_top.", "")
        
        # Navigate to the signals
        write_enable_signal = dut
        for part in write_enable_path.split('.'):
            write_enable_signal = getattr(write_enable_signal, part)
        
        write_addr_signal = dut
        for part in write_addr_path.split('.'):
            write_addr_signal = getattr(write_addr_signal, part)
        
        write_data_signal = None
        if write_data_path:
            write_data_path = write_data_path.replace("processorci_top.", "")
            write_data_signal = dut
            for part in write_data_path.split('.'):
                write_data_signal = getattr(write_data_signal, part)
        
        dut._log.info(f"[measure] Using register file interface:")
        dut._log.info(f"[measure]   write_enable: {write_enable_path}")
        dut._log.info(f"[measure]   write_addr: {write_addr_path}")
        if write_data_signal:
            dut._log.info(f"[measure]   write_data: {write_data_path}")
        
    except (AttributeError, KeyError) as e:
        dut._log.error(f"[measure] Failed to access register file interface signals: {e}")
        return None

    # Align to clock
    await RisingEdge(dut.sys_clk)

    issue_cycle = None
    write_cycle = None

    # Maximum observation window
    max_cycles = 200

    for cycle in range(max_cycles):
        await RisingEdge(dut.sys_clk)
        # After rising edge: we see values written ON this edge

        # Safe PC read
        if dut.core_addr.value.is_resolvable:
            pc_val = dut.core_addr.value.integer
        else:
            pc_val = None

        dut._log.debug(f"[measure] cycle={cycle} pc={pc_val}")

        # Detect when fetch transaction COMPLETES (STB & ACK both high for target PC=0x48)
        if issue_cycle is None and pc_val == 0x00000048 and dut.core_stb.value and dut.core_ack.value:
            issue_cycle = cycle
            dut._log.info(f"[measure] ADDI x1 fetch completes at cycle {cycle} (PC=0x00000048, transaction complete)")

        # Detect writeback using register file interface
        if issue_cycle is not None and write_cycle is None:
            try:
                # Check if write is happening to x1
                we_active = write_enable_signal.value.is_resolvable and int(write_enable_signal.value) == 1
                addr_is_x1 = write_addr_signal.value.is_resolvable and int(write_addr_signal.value) == x1_idx
                
                if we_active and addr_is_x1:
                    write_cycle = cycle
                    cycles_elapsed = cycle - issue_cycle
                    
                    if write_data_signal and write_data_signal.value.is_resolvable:
                        write_data_val = int(write_data_signal.value)
                        dut._log.info(f"[measure] x1 write detected at cycle {cycle} (write_data={write_data_val}, {cycles_elapsed} cycles after fetch)")
                    else:
                        dut._log.info(f"[measure] x1 write detected at cycle {cycle} ({cycles_elapsed} cycles after fetch)")
                    break
                    
            except Exception as e:
                dut._log.debug(f"[measure] Error reading register file interface at cycle {cycle}: {e}")

    if issue_cycle is None or write_cycle is None:
        dut._log.warning(f"[measure] failed to observe fetch/write (issue={issue_cycle}, write={write_cycle})")
        return None

    # Pipeline stages calculation
    cycles_through_pipeline = write_cycle - issue_cycle
    stages = cycles_through_pipeline + 1
    
    dut._log.info(f"[measure] detected {stages}-stage pipeline (fetch@cycle{issue_cycle} → WB@cycle{write_cycle}, diff={cycles_through_pipeline})")
    dut._log.info(f"[measure] analysis: instruction took {cycles_through_pipeline} cycles to traverse the pipeline")
    
    return stages


async def analyze_transaction_intervals(dut):
    """
    Analyze the intervals between instruction fetch transactions.
    For pipelined cores, we expect consistent 1-cycle intervals.
    For multicycle cores, we expect variable intervals (> 1 cycle per instruction).
    """
    dut._log.info("Phase 2: Analyzing transaction patterns for multicycle detection...")
    
    await RisingEdge(dut.sys_clk)
    
    # Track PC changes and transaction cycles
    transaction_cycles = []
    max_cycles = 30
    
    for cycle in range(max_cycles):
        await RisingEdge(dut.sys_clk)
        
        # Detect transaction completion: STB & ACK both high
        if dut.core_stb.value and dut.core_ack.value:
            if dut.core_addr.value.is_resolvable:
                pc = dut.core_addr.value.integer
                transaction_cycles.append(cycle)
                dut._log.info(f"Cycle {cycle}: PC = 0x{pc:08x} [TRANSACTION]")
    
    # Calculate intervals between transactions
    if len(transaction_cycles) < 2:
        dut._log.warning("Not enough transactions observed to determine pattern")
        return None
    
    intervals = [transaction_cycles[i+1] - transaction_cycles[i] 
                 for i in range(len(transaction_cycles) - 1)]
    
    dut._log.info(f"Transaction intervals: {intervals}")
    
    # Analyze intervals
    if all(interval == 1 for interval in intervals):
        dut._log.info("Detected consistent 1-cycle transaction intervals → likely pipelined or single-cycle core.")
        return "pipelined_or_single"
    elif any(interval > 1 for interval in intervals):
        avg_interval = sum(intervals) / len(intervals)
        dut._log.info(f"Detected variable/multi-cycle intervals (avg={avg_interval:.2f}) → likely multicycle core.")
        return "multicycle"
    else:
        return "unknown"


async def test_pc_behavior(dut):
    """Main test function"""
    # Get the output directory and processor name from environment
    output_dir = os.environ.get('OUTPUT_DIR', 'default')
    processor_name = os.path.basename(output_dir)
    
    dut._log.info(f"Processor name: {output_dir}")
    
    # Load register file interface if available
    regfile_interface_file = os.path.join(output_dir, f"{processor_name}_reg_file.json")
    regfile_interface = None
    
    if os.path.exists(regfile_interface_file):
        try:
            with open(regfile_interface_file, 'r') as f:
                data = json.load(f)
                regfile_interface = data.get("regfile_interface")
                if regfile_interface:
                    dut._log.info("Loaded register file interface from file")
                else:
                    dut._log.warning("Register file interface not found in file")
        except Exception as e:
            dut._log.error(f"Failed to load register file interface: {e}")
    
    # Start the clock
    clock = Clock(dut.sys_clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Start the instruction memory driver
    cocotb.start_soon(instr_mem_driver(dut, prog))
    
    # Reset the DUT
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    await Timer(30, units="ns")
    
    # Phase 1: Measure pipeline depth
    dut._log.info("Phase 1: Measuring pipeline depth...")
    
    if regfile_interface:
        # Use the interface-based measurement
        pipeline_stages = await measure_pipeline_depth_with_interface(dut, regfile_interface)
    else:
        dut._log.warning("No register file interface available, cannot measure pipeline depth accurately")
        pipeline_stages = None
    
    # Phase 2: Analyze transaction patterns
    transaction_pattern = await analyze_transaction_intervals(dut)
    
    # Determine core type
    if pipeline_stages is not None:
        if pipeline_stages == 1:
            core_type = "SINGLE-CYCLE"
            result = f"{core_type} core"
        elif transaction_pattern == "multicycle":
            core_type = "MULTICYCLE"
            result = f"{core_type} core"
        else:
            core_type = "PIPELINED"
            result = f"{core_type} core: {pipeline_stages}-stage pipeline"
    elif transaction_pattern == "multicycle":
        core_type = "MULTICYCLE"
        result = f"{core_type} core (pipeline depth unknown)"
    else:
        core_type = "UNKNOWN"
        result = "Unable to determine core type"
    
    dut._log.info(f"Detected {result}.")
    
    # Save results
    output_file = os.path.join(output_dir, f"{processor_name}_labels.json")
    output_data = {
        "core_type": core_type,
        "pipeline_stages": pipeline_stages,
        "transaction_pattern": transaction_pattern
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(output_data, json_file, indent=4)
        dut._log.info(f'Results saved to {output_file}')
    except OSError as e:
        dut._log.warning(f'Error writing to {output_file}: {e}')
