import cocotb
import argparse
import json
import os
import subprocess
import logging
import re

def get_arrays_current_module(module):
    submodules = []
    arrays = []

    for name in dir(module):
        if name.startswith('_'):
            continue  # Skip Python/Cocotb internals
        if callable(getattr(module, name)):
            continue  # Skip methods like get_definition_name()

        obj_handle = getattr(module, name)
        try:
            obj_type = obj_handle._type # This is the cocotb type (wire, reg, array, etc)

            obj_path = obj_handle._path # cocotb path including the instantiated modules

        except AttributeError:
            continue  # Not a SimHandle

        if obj_type == 'GPI_MODULE':
            submodules.append(name)
        elif obj_type == 'GPI_ARRAY':
            arrays.append([obj_handle, obj_path])
        elif obj_type == 'GPI_REGISTER' and len(obj_handle) >= 992: # 31*32 registers = 992 bits
            arrays.append([obj_handle, obj_path])

    return arrays, submodules


def get_arrays_hierarchy(module, regfile_candidates=[]):
    arrays, submodules = get_arrays_current_module(module)

    if arrays:
        for a in arrays:
            # https://github.com/rafaelcalcada/rvx does not have registers[0]. Read directly from 1
            if ((len(a[0]) == 31 or len(a[0]) == 32 or len(a[0]) == 16) and
               (len(a[0][1]) == 32 or len(a[0][1]) == 64)
               ): # 16, 31 or 32 registers, 32/64-bit width registers
                regfile_candidates.append(a[1])

    for m in submodules:
        submodule_instance = getattr(module, m)
        regfile_candidates = get_arrays_hierarchy(submodule_instance, regfile_candidates)

    return regfile_candidates

def get_all_leaf_handles(module, leaves=[]):
    new_leaves, submodules = get_current_module_leaf_handles(module)

    leaves.extend(new_leaves)

    for m in submodules:
        submodule_instance = getattr(module, m)
        leaves = get_all_leaf_handles(submodule_instance, leaves)

    return leaves

def get_current_module_leaf_handles(module):
    """
    Get all leaf signal handles in the current module.
    Check its type to differentiate between submodules and leaf signals.
    """
    submodules = []
    leaves = []
    # separate handles
    for name in dir(module):
            if name.startswith('_'):
                continue  # Skip Python/Cocotb internals
            if callable(getattr(module, name)):
                continue  # Skip methods like get_definition_name()

            obj_handle = getattr(module, name)
            try:
                obj_type = obj_handle._type # This is the cocotb type (wire, reg, array, etc)
                obj_path = obj_handle._path # cocotb path including the instantiated modules

            except AttributeError:
                continue  # Not a SimHandle

            if obj_type == 'GPI_MODULE':
                submodules.append(name)
            else:
                leaves.append(obj_path)

    return leaves, submodules

def guess_register_file_location(module):
    """
    Get all leaf signal handles and filter them by name.
    The selected leaves may be part of the register file
    """
    regfile_guesses = []
    common_names = [
        "reg", # includes register, regfile, reg_file, etc.
        "file",
        "bank", # includes regbank, etc.
        "rf",
        "gpr"
    ]

    all_leaf_handles = get_all_leaf_handles(module)

    # Rank by how early the common name appears
    ranked_entries = []  # (match_idx, leaf)
    for leaf in all_leaf_handles:
        parts = leaf.split('.')
        # Find index of first component containing any common name (case-insensitive)
        match_idx = None
        for idx, comp in enumerate(parts):
            comp_l = comp.lower()
            if any(name in comp_l for name in common_names):
                match_idx = idx
                break
        if match_idx is None:
            # No component contains a common name; skip this leaf
            continue
        ranking_idx = len(parts) - match_idx # How far from the leaf the match is
        ranked_entries.append((ranking_idx, leaf))

    # Sort so higher-level matches (smaller match_idx) come first
    ranked_entries.sort(key=lambda e: e[0], reverse=True)
    regfile_guesses = [leaf for _, leaf in ranked_entries]

    # Filter processor_ci_top.Processor from guesses
    filtered_regfile_guesses = []
    for guess in regfile_guesses:
        split_guess = guess.split(".")
        joined_guess = ".".join(split_guess[2:])
        filtered_regfile_guesses.append(joined_guess)

    return filtered_regfile_guesses


def filter_processor_interface_from_response(response):
    """
    It is expected a response with the following json format:
    {
        "read_addr_1": "signal_path",
        "read_addr_2": "signal_path",
        "read_data_1": "signal_path",
        "read_data_2": "signal_path",
        "write_enable": "signal_path",
        "write_addr": "signal_path",
        "write_data": "signal_path"
    }
    This function extracts and returns only the JSON part of the response.
    """

    # Scan for the last balanced JSON object in the text
    in_string = False
    string_char = ""
    escape = False
    depth = 0
    start_idx = None
    last_obj = None

    for i, ch in enumerate(response):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == string_char:
                in_string = False
        else:
            if ch in ("'", '"'):
                in_string = True
                string_char = ch
            elif ch == "{":
                if depth == 0:
                    start_idx = i
                depth += 1
            elif ch == "}":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start_idx is not None:
                        last_obj = response[start_idx:i+1]

    if not last_obj:
        raise ValueError("No JSON object found in the response")

    try:
        return json.loads(last_obj)
    except json.JSONDecodeError as e:
        raise ValueError(f"Found a JSON-like object but failed to parse: {e}") from e


def find_register_file_interface(dut, regfile_guesses):
    """
    Identify the register file interface signals from the guessed leaves.
    Uses Ollama.
    Put imports and defines here because this function may be moved to another file
    """
    from ollama import Client
    SERVER_URL = 'http://enqii.lsc.ic.unicamp.br:11434'
    client = Client(host=SERVER_URL)

    def send_prompt(prompt: str, model: str = 'qwen2.5:14b') -> tuple[bool, str]:
        """
        Sends a prompt to the specified server and receives the model's response.
        Args:
            prompt (str): The prompt to be sent to the model.
            model (str, optional): The model to use. Default is 'qwen2.5:32b'.
        Returns:
            tuple: A tuple containing a boolean value (indicating success)
                and the model's response as a string.
        """
        response = client.generate(prompt=prompt, model=model)

        if not response or 'response' not in response:
            return 0, ''

        return 1, response['response']

    find_regfile_prompt = """
        You're a Hardware Engineer. You must analyze signals from an RTL simulation and decide which signals are part of the register file interface of a RISC-V processor. Then you must map these signals to a standard interface.
        **Part 1 Filtering signals**
            1. Analyze the given signal paths in the format "module.module.signal".
            2. First look for a module that is most probably the register file. These are common names found in register file modules: ["reg","bank","rf","gpr","integer_file"]
            3. Check if the module's signals correspond to the standard regfile interface signals: [read_addr_1, read_addr_2, read_data_1, read_data_2, write_enable, write_addr, write_data]
            4. List the chosen signals **Part 2 Mapping signals** Map the signal chosen from part 1 to the standard interface signals.
            Provide your reasoning first and then use extactly the following json format, it is crucial for the system.
            {{
            "read_addr_1": "signal_path",
            "read_addr_2": "signal_path",
            "read_data_1": "signal_path",
            "read_data_2": "signal_path",
            "write_enable": "signal_path",
            "write_addr": "signal_path",
            "write_data": "signal_path"
            }}
        - Register File Guessed signals:
        {regfile_guesses}
    """
    find_regfile_prompt = find_regfile_prompt.format(regfile_guesses="\n".join(regfile_guesses))

    success, response = send_prompt(find_regfile_prompt, model='gpt-oss:20b')

    if not success:
        dut._log.error('Error communicating with the server.')
        return None
    
    dut._log.info(f"Ollama response for register file interface extraction: \n{response}\n\n")
    
    regfile_interface = filter_processor_interface_from_response(response)

    return regfile_interface

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

@cocotb.test()
async def find_register_file(dut):
    output_dir = os.environ.get('OUTPUT_DIR', "default")
    processor_name = os.path.basename(output_dir)
    output_data = {}

    print("""
            ####################################################
            #Looking for the register file - regfile_finder.py #
            ####################################################
          """)
    
    regfile_candidates = get_arrays_hierarchy(dut)

    if regfile_candidates:
        dut._log.info("- Register File Candidates Found:")
        for i, candidate in enumerate(regfile_candidates):
            dut._log.info(f"  {i + 1}: {candidate}")
        dut._log.info("\n")

        output_data = {
            "regfile_candidates": regfile_candidates
        }
    
    ollama_flag = os.environ.get('OLLAMA', False)
    ollama_flag = True if str(ollama_flag).lower() == 'true' else False
    if not ollama_flag:
        dut._log.info("Skipping register file interface detection via Ollama.")
        # Save the current data back to the JSON file
        output_file = os.path.join(output_dir, f"{processor_name}_reg_file.json")

        try:
            with open(output_file, 'w', encoding='utf-8') as json_file:
                json.dump(output_data, json_file, indent=4)
            logging.info(f'Results saved to {output_file}')
        except OSError as e:
            logging.warning(f'Error writing to {output_file}: %s', e)
        return
    else:
        dut._log.info("Register file interface detection via Ollama enabled.")
        # In case no candidates were found, look for the interface
        regfile_guesses = guess_register_file_location(dut)

        if regfile_guesses:
            dut._log.info("- Register File Guessed Signals:")
            for i, guess in enumerate(regfile_guesses):
                dut._log.info(f"  {i + 1}: {guess}")
            dut._log.info("\n")

            regfile_interface = find_register_file_interface(dut, regfile_guesses)

            if isinstance(regfile_interface, dict):
                dut._log.info("- Register File Interface:")
                for signal, path in regfile_interface.items():
                    dut._log.info(f"  {signal}: {path}")

                output_data["regfile_interface"] = regfile_interface

        # Save the updated data back to the JSON file
        output_file = os.path.join(output_dir, f"{processor_name}_reg_file.json")

        try:
            with open(output_file, 'w', encoding='utf-8') as json_file:
                json.dump(output_data, json_file, indent=4)
            logging.info(f'Results saved to {output_file}')
        except OSError as e:
            logging.warning(f'Error writing to {output_file}: %s', e)

        # Consider the interface invalid if at least one required entry is null or missing
        # Other error condition are harder to detect
        required_keys = {
            "read_addr_1",
            "read_addr_2",
            "read_data_1",
            "read_data_2",
            "write_enable",
            "write_addr",
            "write_data",
        }

        if isinstance(regfile_interface, dict) and required_keys.issubset(regfile_interface.keys()):
            # invalid if any required entry is None
            any_nulls = any(regfile_interface[k] is None for k in required_keys)
            valid_regfile_interface = not any_nulls
        else:
            valid_regfile_interface = False

        if not regfile_candidates and not valid_regfile_interface:
            assert False, f"No register file found for the {processor_name} processor"


# This script is intended to be run as a cocotb testbench.
# If called directly, it will open a subprocess and run the cocotb simulation
# The simulation will run only the 'async def find_register_file(dut)' function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This regfile_finder testbench runs a cocotb simulation and parses the design hierarchy to find the register file.")
    parser.add_argument("--makefile", required=True, help="Specify the cocotb makefile path")
    parser.add_argument("--output", required=True, default="detected_reg_file.json", help="Specify the output file path. Must be an absolute path.")
    args = parser.parse_args()

    if not os.path.isabs(args.output):
        raise ValueError("The --output argument must be an absolute path.")

    
    # These commands:
    # copy this file to the makefile directory
    # run the simulation to find the register file
    # remove the copy
    # TODO: change this to use "PYTHONPATH" and "make -f"

    makefile_dir = os.path.dirname(os.path.abspath(args.makefile))
    subprocess.run(["cp", __file__, makefile_dir])

    module_name = os.path.splitext(os.path.basename(__file__))[0]
    subprocess.run(["make", f"MODULE={module_name}", f"OUTPUT_FILE={args.output}"], cwd=makefile_dir)

    file_copy_path = os.path.join(makefile_dir, os.path.basename(__file__))
    subprocess.run(["rm", "-f", file_copy_path], cwd=makefile_dir)


    
