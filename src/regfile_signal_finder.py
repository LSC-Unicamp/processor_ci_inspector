"""
Register File Interface Signal Finder

This module searches for register file write interface signals in a RISC-V core.
These signals allow accurate pipeline depth measurement by detecting the exact
cycle when writeback occurs, eliminating the 1-2 cycle observation delay.

Signals to find:
- write_enable: Active when register write occurs (may be active-high or active-low)
- write_address: Destination register address (rd)
- write_data: Data being written (optional, for validation)
"""

import cocotb
import json
import os


def find_regfile_write_signals(dut, core_name, regfile=None):
    """
    Search for register file write interface signals.
    
    If regfile handle is provided, searches in the parent module of the register file.
    Otherwise searches from dut root.
    
    Common patterns:
    - write_enable: wen, we, write_en, reg_write, rf_wen, wren
    - write_address: waddr, rd, dest_reg, rd_addr, wa
    - write_data: wdata, rd_data, wd
    
    Args:
        dut: The design under test
        core_name: Name of the core being tested
        regfile: Optional handle to the register file array
    
    Returns:
        dict: {
            "write_enable": "path.to.signal",
            "write_addr": "path.to.signal", 
            "write_data": "path.to.signal"  # optional
        }
        or None if signals not found
    """
    
    # Patterns to search for (in priority order)
    # Exclude CSR-related signals
    write_enable_patterns = [
        "rf_wen", "regfile_wen", "gpr_wen", "reg_wen",
        "regwr_en",  # Kronos uses regwr_en
        "wr_en_i", "wr_en_o", "wr_en",  # Grande-Risco-5 uses wr_en_i
        "wen_wb", "wen_w", "wen",  # Common write enable names
        "we_i", "we_o", "we",  # Tinyriscv uses we_i
        "write_en", "write_enable", "reg_write", "wren"
    ]
    
    write_addr_patterns = [
        "instruction_rd_address",  # rvx uses instruction_rd_address - check first!
        "regwr_sel", "reg_wr_sel",  # Kronos uses regwr_sel
        "rd_address",  # Generic rd_address
        "rd_wb", "rd_w", "rd",  # Destination register
        "waddr_i", "waddr_o", "waddr",  # Tinyriscv uses waddr_i
        "wsel", "wrsel", "wr_sel",  # Write select variations
        "dest_reg", "rd_addr", "wa",
        "write_addr", "dest_addr", "regfile_waddr"
    ]
    
    write_data_patterns = [
        "regwr_data",  # Kronos uses regwr_data
        "writeback_multiplexer_output", "writeback_mux", "wb_data",  # rvx uses writeback_multiplexer_output
        "data_i",  # Grande-Risco-5 uses data_i (input only, not data_o which is output)
        "wdata_wb", "wdata_w", 
        "wdata_i", "wdata_o", "wdata",  # Tinyriscv uses wdata_i
        "rd_data", "wd", "write_data", "regfile_wdata"
    ]
    
    # Patterns to EXCLUDE (CSR, debug, JTAG, read signals, ready signals, load/store, instruction-specific, etc.)
    exclude_patterns = ["csr", "debug", "dbg", "trace", "jtag", "rdata", "raddr", "rdy", "ready", "fetch", "regrd", "read", "load", "store", "prev", "ebreak", "ecall", "mret", "_rs1", "_rs2", "size"]
    
    found_signals = {}
    
    def search_signals(module, path="", depth=0, max_depth=8):
        """Recursively search for signals in the design hierarchy."""
        if depth > max_depth:
            return
        
        # Get all signals/submodules in this module
        try:
            for name in dir(module):
                if name.startswith('_'):
                    continue
                
                try:
                    obj = getattr(module, name)
                    full_path = f"{path}.{name}" if path else name
                    
                    # Check if this signal matches any pattern
                    name_lower = name.lower()
                    
                    # Skip if matches exclude patterns
                    if any(excl in name_lower for excl in exclude_patterns):
                        continue
                    
                    # Check write enable patterns
                    if "write_enable" not in found_signals:
                        for pattern in write_enable_patterns:
                            if pattern in name_lower:
                                # Verify it's actually a signal (has value attribute)
                                if hasattr(obj, 'value'):
                                    found_signals["write_enable"] = full_path
                                    cocotb.log.info(f"Found write_enable: {full_path}")
                                    break
                    
                    # Check write address patterns
                    if "write_addr" not in found_signals:
                        for pattern in write_addr_patterns:
                            if pattern in name_lower:
                                if hasattr(obj, 'value'):
                                    found_signals["write_addr"] = full_path
                                    cocotb.log.info(f"Found write_addr: {full_path}")
                                    break
                    
                    # Check write data patterns
                    if "write_data" not in found_signals:
                        for pattern in write_data_patterns:
                            if pattern in name_lower:
                                if hasattr(obj, 'value'):
                                    found_signals["write_data"] = full_path
                                    cocotb.log.info(f"Found write_data: {full_path}")
                                    break
                    
                    # Recurse into submodules
                    if not hasattr(obj, 'value') and hasattr(obj, '__dict__'):
                        search_signals(obj, full_path, depth + 1, max_depth)
                    
                except (AttributeError, TypeError):
                    continue
                    
        except (AttributeError, TypeError):
            pass
    
    # Start search from the register file module if provided
    cocotb.log.info(f"Searching for register file write signals in {core_name}...")
    
    if regfile is not None:
        # Get the parent module of the register file (e.g., u_regs module)
        # The regfile is typically regfile_module.regs, so we search in regfile_module
        regfile_path = regfile._path
        cocotb.log.info(f"Register file path: {regfile_path}")
        
        # Extract parent path (remove last component which is the array name)
        parent_path_parts = regfile_path.split('.')
        if len(parent_path_parts) > 1:
            parent_path_parts = parent_path_parts[:-1]  # Remove array name (e.g., 'regs')
            parent_path = '.'.join(parent_path_parts)
            
            # Navigate to parent module
            try:
                parent_module = dut
                for part in parent_path_parts:
                    if part and hasattr(parent_module, part):
                        parent_module = getattr(parent_module, part)
                
                cocotb.log.info(f"Searching in register file parent module: {parent_path}")
                search_signals(parent_module, parent_path, depth=0, max_depth=3)
            except Exception as e:
                cocotb.log.warning(f"Failed to navigate to parent module: {e}")
                search_signals(dut, "", depth=0, max_depth=10)
        else:
            search_signals(dut, "", depth=0, max_depth=10)
    else:
        # No regfile provided, search from top
        search_signals(dut, "", depth=0, max_depth=10)
    
    # Validate we found the critical signals
    if "write_enable" in found_signals and "write_addr" in found_signals:
        cocotb.log.info(f"✓ Found register file write interface!")
        
        # Save to JSON for future use
        config_dir = os.path.join(os.getcwd(), "processor_ci", "config", "regfile_interfaces")
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, f"{core_name}_regfile.json")
        
        with open(config_file, 'w') as f:
            json.dump(found_signals, f, indent=2)
        
        cocotb.log.info(f"Saved configuration to {config_file}")
        return found_signals
    else:
        cocotb.log.warning(f"Could not find complete register file write interface")
        cocotb.log.warning(f"Found: {found_signals}")
        return None


def load_regfile_interface(core_name):
    """
    Load previously saved register file interface configuration.
    
    Returns dict with signal paths or None if not found.
    """
    config_file = os.path.join(
        os.getcwd(), 
        "processor_ci", 
        "config", 
        "regfile_interfaces",
        f"{core_name}_regfile.json"
    )
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return None
