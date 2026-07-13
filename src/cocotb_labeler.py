import cocotb
import re
import os
import json
import logging
from regfile_finder import (
    run_register_file_finder,
    sample_candidate_value,
    selected_candidate_metadata,
    simulator_safe_hierarchy,
)
from cycle import instr_mem_driver, test_pc_behavior
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock

def resolve_path(dut, path: str):
    """Resolve a string path like 'processorci_top.u_core.regs[5]' into a cocotb handle."""
    parts = path.split('.')
    # Drop the first part if it matches top-level name
    if parts[0] == dut._name:
        parts = parts[1:]

    handle = dut
    for part in parts:
        if '[' in part and ']' in part:
            # Array element, e.g. regs[5]
            name, idx = part[:-1].split('[')
            handle = getattr(handle, name)[int(idx)]
        else:
            handle = getattr(handle, part)
    return handle


class _RegisterValue:
    def __init__(self, value, width):
        self.value = value
        self._width = width

    def __len__(self):
        return self._width


class _ArchitecturalRegfileView:
    """Present every discovered storage representation as x0..x31 words."""

    def __init__(self, dut, candidate):
        self._dut = dut
        self._candidate = candidate
        self._path = candidate.get("path")
        self._width = int(candidate.get("word_width") or 32)
        self._depth = int(candidate.get("depth") or 32)

    def __len__(self):
        return self._depth

    def __getitem__(self, index):
        sampled = sample_candidate_value(self._dut, self._candidate) or {}
        mapping = self._candidate.get("mapping_order")
        if self._candidate.get("kind") == "packed_flat_vector":
            mapping = mapping or "packed_lsb_reg0"
            sampled = sampled.get(mapping) or {}
        value = sampled.get(f"x{int(index)}")
        if value is None:
            raise IndexError(index)
        return _RegisterValue(value, self._width)


@cocotb.test()
async def processor_test(dut):
    """Test function for the processor.

    Args:
        dut: The design under test.
    """

    dut = simulator_safe_hierarchy(dut)
    bits = None

    discovery = await run_register_file_finder(dut)

    output_dir = os.environ.get('OUTPUT_DIR', "default")
    processor_name = os.path.basename(output_dir)
    dut._log.info(f"Processor name: {output_dir}")

    # Load register file candidates
    regfile_candidates = []
    try:
        with open(os.path.join(output_dir, f"{processor_name}_reg_file.json"), 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            regfile_candidates = data.get("regfile_candidates", [])
    except (json.JSONDecodeError, OSError) as e:
        logging.warning('Error reading register file candidates: %s', e)
    if not regfile_candidates:
        raise AssertionError(
            "No visible register file candidates were found; analysis is incomplete"
        )
    dut._log.info(f"Register file candidates: {regfile_candidates}")    

    regfile_path = regfile_candidates[0]
    dut._log.info(f"Using register file: {regfile_path}")

    candidate = selected_candidate_metadata(discovery)
    if candidate and candidate.get("kind") != "array_of_words":
        regfile = _ArchitecturalRegfileView(dut, candidate)
    else:
        regfile = resolve_path(dut, regfile_path)
    dut._log.info(f"Resolved register file: {regfile}")

    bits = len(regfile[7])

    await test_pc_behavior(dut, regfile)

    output_file = os.path.join(output_dir, f"{processor_name}_labels.json")

    if not os.path.exists(output_file):
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump({}, json_file, indent=4)

    # Load existing JSON data
    try:
        with open(output_file, 'r', encoding='utf-8') as json_file:
            existing_data = json.load(json_file)
    except (json.JSONDecodeError, OSError) as e:
        logging.warning('Error reading existing JSON file: %s', e)
        existing_data = {}

    existing_data.setdefault(processor_name, {})["bits"] = bits

    # Save the updated data back to the JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(existing_data, json_file, indent=4)
        dut._log.info(f'Results saved to {output_file}')
    except OSError as e:
        logging.warning('Error writing to JSON file: %s', e)
