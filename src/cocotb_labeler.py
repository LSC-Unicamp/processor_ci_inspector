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
try:
    from . import Branch, Datapath, Forwarding
    from . import _discovery_shared as _discovery
    from .simulation import DataMemory
except ImportError:
    import Branch
    import Datapath
    import Forwarding
    import _discovery_shared as _discovery
    from simulation import DataMemory


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
        self._architectural_indexed = True

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


def _record_unavailable_regfile(dut, output_dir, processor_name, reason):
    """Keep independent findings when storage-dependent probes cannot run."""
    dut._log.warning("Register-file-dependent probes unavailable: %s", reason)
    output_file = os.path.join(output_dir, f"{processor_name}_labels.json")
    try:
        with open(output_file, 'r', encoding='utf-8') as json_file:
            labels = json.load(json_file)
    except (json.JSONDecodeError, OSError):
        labels = {}
    core_labels = labels.setdefault(processor_name, {})
    core_labels["analysis"] = {
        "state": "partial",
        "reason": reason,
        "unavailable_probes": (
            ["cycle"] if _discovery._env_flag("RVB_INSPECTOR_SKIP_EXPERIMENTAL")
            else ["cycle", "forwarding", "branch_prediction"]
        ),
    }
    _mark_experimental_disabled(core_labels)
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(labels, json_file, indent=4)


def _mark_experimental_disabled(core_labels):
    """Discard prior experimental findings from RV-Bench result reuse."""
    if not _discovery._env_flag("RVB_INSPECTOR_SKIP_EXPERIMENTAL"):
        return
    for name in ("forwarding", "forwarding_debug", "branch_prediction", "hazard_handling"):
        core_labels.pop(name, None)
    core_labels.setdefault("analysis", {})["disabled_probes"] = {
        "forwarding": "not released",
        "branch_prediction": "not released",
    }


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
        _record_unavailable_regfile(
            dut, output_dir, processor_name,
            "No visible register-file candidate was found",
        )
        return
    dut._log.info(f"Register file candidates: {regfile_candidates}")    

    candidate = selected_candidate_metadata(discovery)
    regfile_path = (
        candidate.get("path") or candidate.get("candidate_path")
        if candidate
        else regfile_candidates[0]
    )
    dut._log.info(f"Using register file: {regfile_path}")

    try:
        if candidate and candidate.get("kind") != "array_of_words":
            regfile = _ArchitecturalRegfileView(dut, candidate)
        else:
            regfile = resolve_path(dut, regfile_path)
        bits = len(regfile[7])
    except (AttributeError, IndexError, KeyError, TypeError) as error:
        _record_unavailable_regfile(
            dut, output_dir, processor_name,
            f"Candidate {regfile_path!r} is not observable: {error}",
        )
        return
    dut._log.info(f"Resolved register file: {regfile}")

    # All discovery phases share one pair of memory drivers. Individual probes
    # select/reset their program and data images without spawning competing
    # coroutines.
    dut.core_ack.value = 0
    dut.core_data_in.value = 0
    if hasattr(dut, "dmem_prog_we"):
        dut.dmem_prog_we.value = 0
        dut.dmem_prog_addr.value = 0
        dut.dmem_prog_data.value = 0

    await _discovery._start_clock_once(dut)
    data_memory = DataMemory()
    _discovery.program_memory.select(_discovery.CYCLE_SIGNATURE)
    instruction_driver_task = cocotb.start_soon(
        _discovery.instr_mem_driver(dut, _discovery.program_memory)
    )
    data_driver_task = cocotb.start_soon(
        _discovery.data_mem_driver(dut, data_memory)
    )

    try:
        dut.rst_n.value = 0
        dut.core_ack.value = 0
        await _discovery._load_optional_internal_program(
            dut, _discovery.program_memory.image,
        )
        await _discovery.Timer(50, units="ns")
        dut.rst_n.value = 1

        datapath = await Datapath.test_datapath_structure(
            dut, regfile, regfile_discovery=discovery,
        )
        if _discovery._env_flag("RVB_INSPECTOR_SKIP_EXPERIMENTAL"):
            dut._log.info("Skipping forwarding and branch prediction probes for RV-Bench")
        else:
            pipeline = datapath["pipeline"]
            if Forwarding._is_pipeline_classification(pipeline):
                await Forwarding.forwarding_presence_test(
                    dut,
                    regfile,
                    pipeline=pipeline,
                    data_memory=data_memory,
                    regfile_discovery=discovery,
                )
            else:
                dut._log.info("[forwarding] Not applicable to this execution model")
                Forwarding.record_not_applicable(dut)

            await Branch.branch_prediction_presence_test(
                dut, regfile, pipeline=pipeline, data_memory=data_memory,
            )
    finally:
        # Do not leave VPI-backed coroutines alive during simulator teardown.
        for task in (instruction_driver_task, data_driver_task):
            try:
                if hasattr(task, "cancel"):
                    task.cancel()
                else:
                    task.kill()
            except Exception:
                pass

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

    core_labels = existing_data.setdefault(processor_name, {})
    core_labels["bits"] = bits
    _mark_experimental_disabled(core_labels)

    # Save the updated data back to the JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(existing_data, json_file, indent=4)
        dut._log.info(f'Results saved to {output_file}')
    except OSError as e:
        logging.warning('Error writing to JSON file: %s', e)
