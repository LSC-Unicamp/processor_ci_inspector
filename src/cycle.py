import cocotb
import os
import json
import logging
import re
from collections import Counter
from statistics import median
from cocotb.triggers import RisingEdge, Timer
try:
    from .regfile_finder import (
        _start_clock_once,
        find_regfile_write_signals,
        load_regfile_interface,
    )
except ImportError:
    from regfile_finder import (
        _start_clock_once,
        find_regfile_write_signals,
        load_regfile_interface,
    )
try:
    from .probe_programs import CYCLE_SIGNATURE, FORWARDING_PROBES, forwarding_distance_variant, forwarding_probe_pair
    from .riscv.encoding import ADD, ADDI, JAL, LW, NOP, SUB, SW
    from .simulation import DataMemory, ProgramMemory
except ImportError:
    from probe_programs import CYCLE_SIGNATURE, FORWARDING_PROBES, forwarding_distance_variant, forwarding_probe_pair
    from riscv.encoding import ADD, ADDI, JAL, LW, NOP, SUB, SW
    from simulation import DataMemory, ProgramMemory


NOP_INSTRUCTION = NOP
_addi, _add, _sub, _lw, _sw, _jal = ADDI, ADD, SUB, LW, SW, JAL


# Straight-line execution signature. Each measured instruction writes a unique
# register/value pair exactly once, then the core parks in a self-loop after the
# measured window. Keep the signature away from regfile-finder loop addresses so
# cores without a real reset can still NOP-forward into this probe.
SIGNATURE_BASE_PC = CYCLE_SIGNATURE.base_addresses[0]
SIGNATURE_BASE_PCS = CYCLE_SIGNATURE.base_addresses
SIGNATURE_WRITE_TEMPLATES = [
    {**entry, "instruction": f"addi x{entry['reg']}, x0, {entry['value']:#x}"}
    for entry in CYCLE_SIGNATURE.entries()
]

def _signature_entries_for_base(base_pc):
    return [
        {**entry, "pc": base_pc + entry["offset"], "base_pc": base_pc}
        for entry in SIGNATURE_WRITE_TEMPLATES
    ]


SIGNATURE_WRITES = _signature_entries_for_base(SIGNATURE_BASE_PC)
SIGNATURE_ALIASED_WRITES = [
    entry
    for base_pc in SIGNATURE_BASE_PCS
    for entry in _signature_entries_for_base(base_pc)
]
SIGNATURE_BY_PC = {entry["pc"]: entry for entry in SIGNATURE_ALIASED_WRITES}
SIGNATURE_BY_REG_VALUE = {}
for entry in SIGNATURE_ALIASED_WRITES:
    SIGNATURE_BY_REG_VALUE.setdefault((entry["reg"], entry["value"] & 0xFFFFFFFF), []).append(entry)
SIGNATURE_LOOP_PC = 0xB0

# Regfile discovery runs before cycle analysis in the same simulation and may
# leave a self-loop below the signature (currently at 0x20 or 0x2c).  Explicitly
# overwrite the path from the reset vector to the primary signature with NOPs
# when a wrapper offers internal instruction-memory programming.
program_memory = ProgramMemory(CYCLE_SIGNATURE)
prog = program_memory.image  # Read-only compatibility view for existing tests.
HAZARD_BASE_PC = FORWARDING_PROBES["alu_to_alu"].base_addresses[0]
HAZARD_BASE_PCS = FORWARDING_PROBES["alu_to_alu"].base_addresses
HAZARD_WRITE_TEMPLATE = [
    {**entry, "instruction": FORWARDING_PROBES["alu_to_alu"].instructions[entry["offset"]]}
    for entry in FORWARDING_PROBES["alu_to_alu"].entries()
]
hazard_prog = FORWARDING_PROBES["alu_to_alu"].image()


async def _load_optional_internal_program(dut, program):
    required = ("imem_prog_we", "imem_prog_addr", "imem_prog_data")
    if not all(hasattr(dut, name) for name in required):
        return
    dut.imem_prog_we.value = 0
    # Program high aliases first. Some wrappers expose fewer address bits than
    # imem_prog_addr, so the 0x200 fallback image aliases onto low memory. In
    # that case the primary reset-vector image must be the final value written.
    for address, instruction in sorted(program.items(), reverse=True):
        dut.imem_prog_addr.value = int(address)
        dut.imem_prog_data.value = int(instruction)
        dut.imem_prog_we.value = 1
        await RisingEdge(dut.sys_clk)
        await Timer(0.001, unit="ns")
    dut.imem_prog_we.value = 0


async def instr_mem_driver(dut, memory=None):
    """
    Zero-wait-state memory driver that responds immediately.
    For cores that check valid/ack before asserting request (like AUK-V),
    we keep ACK high and data ready at all times.
    """
    memory = memory or program_memory
    dut.core_data_in.value = 0
    dut.core_ack.value = 1  # Keep ACK high - zero wait state memory
    cycle_count = 0
    while True:
        await RisingEdge(dut.sys_clk)
        await Timer(0.001, unit="ns") # let signals settle
        cycle_count += 1
        
        # Always provide valid data based on current address
        addr_signal = dut.imem_fetch_addr if hasattr(dut, "imem_fetch_addr") else dut.core_addr
        addr_val = addr_signal.value
        if addr_val.is_resolvable:
            addr = addr_val.to_unsigned()
            instr = memory.read(addr)
            dut.core_data_in.value = instr
            if hasattr(dut, "core_data_in_hi"):
                dut.core_data_in_hi.value = memory.read(addr + 4)
            
            if cycle_count <= 20:
                cyc_val = dut.core_cyc.value if hasattr(dut, 'core_cyc') else 'N/A'
                stb_val = dut.core_stb.value if hasattr(dut, 'core_stb') else 'N/A'
                dut._log.info(f"[mem_driver cycle {cycle_count}] cyc={cyc_val} stb={stb_val} addr={addr:#010x} data={instr:#010x}")
        else:
            dut.core_data_in.value = 0x00000013  # NOP if address not ready
            if hasattr(dut, "core_data_in_hi"):
                dut.core_data_in_hi.value = 0x00000013


async def data_mem_driver(dut, memory=None):
    """
    Data memory driver for cores with separate instruction and data buses.
    Zero-wait-state: keeps ACK high and provides immediate responses.
    """
    memory = memory or DataMemory()
    memory.reset()
    # Check if core has separate data memory interface
    if not hasattr(dut, 'data_mem_ack'):
        memory.supported = False
        return

    memory.supported = all(hasattr(dut, name) for name in (
        "data_mem_addr", "data_mem_we", "data_mem_data_out"
    ))
    dut.data_mem_data_in.value = 0
    dut.data_mem_ack.value = 1  # Keep ACK high - zero wait state
    cycle = 0
    active_transaction = None
    active_generation = memory.generation
    while True:
        await RisingEdge(dut.sys_clk)
        await Timer(0.001, unit="ns") # let signals settle
        cycle += 1
        memory.current_cycle = cycle
        if active_generation != memory.generation:
            active_transaction = None
            active_generation = memory.generation
        if not memory.supported:
            dut.data_mem_data_in.value = 0
            continue
        requested = (
            (not hasattr(dut, "data_mem_cyc") or _is_high(dut.data_mem_cyc))
            and (not hasattr(dut, "data_mem_stb") or _is_high(dut.data_mem_stb))
        )
        if not requested:
            active_transaction = None
            dut.data_mem_data_in.value = 0
            continue
        address = _safe_signal_int(dut.data_mem_addr)
        is_write = _is_high(dut.data_mem_we)
        value = _safe_signal_int(dut.data_mem_data_out)
        transaction = (address, is_write, value)
        if address is None:
            continue
        if transaction != active_transaction:
            if is_write:
                byte_enable = None
                for name in ("data_mem_wstrb", "data_mem_sel", "data_mem_be"):
                    if hasattr(dut, name):
                        byte_enable = _safe_signal_int(getattr(dut, name))
                        break
                memory.write_word(address, value or 0, byte_enable, cycle=cycle)
            else:
                memory.read_word(address, cycle=cycle)
            active_transaction = transaction
        dut.data_mem_data_in.value = memory.read_word(address)


def _get_handle_from_path(obj, path_str):
    """
    Resolve a dotted hierarchical path to a handle.
    E.g., "Processor.FE0.o_instr_valid" → handle to that signal
    Returns None if path cannot be resolved.
    """
    try:
        parts = path_str.split('.')
        current = obj
        for part in parts:
            current = getattr(current, part)
        return current
    except (AttributeError, TypeError):
        return None


def _find_core_instance(dut):
    """
    Find the core instance under processorci_top.
    Returns the instance name (string) or None if not found.
    Common names: Processor, aukv_inst, core_inst, etc.
    """
    try:
        # Try to list all scopes under dut to find core instances
        for name in dir(dut):
            if not name.startswith('_'):
                try:
                    obj = getattr(dut, name)
                    # Skip if it's a method, property, or other non-instance
                    if hasattr(obj, '_scope'):
                        return name
                except:
                    pass
    except:
        pass
    
    # Fallback: try common names
    for common_name in ['Processor', 'aukv_inst', 'core_inst', 'core', 'processor']:
        try:
            if hasattr(dut, common_name):
                return common_name
        except:
            pass
    
    return None


def _auto_find_fetch_signal(dut, core_instance_name):
    """
    Try to find fetch-valid signal under the core instance.
    Returns the signal handle or None if not found.
    
    Args:
        dut: Design under test (processorci_top)
        core_instance_name: Name of core instance (e.g., "Processor")
    """
    if not core_instance_name:
        return None
    
    fetch_candidates = [
        f"{core_instance_name}.FE0.o_instr_valid",
        f"{core_instance_name}.FE0.o_instr_addr_valid",
        f"{core_instance_name}.fetch.o_instr_valid",
        f"{core_instance_name}.fetch.o_valid",
        f"{core_instance_name}.FE.o_instr_valid",
        f"{core_instance_name}.if_stage.o_instr_valid",
    ]
    
    for candidate in fetch_candidates:
        sig = _get_handle_from_path(dut, candidate)
        if sig is not None:
            return sig
    
    return None


def _safe_signal_int(signal):
    try:
        value = signal.value if hasattr(signal, "value") else signal
        if hasattr(value, "is_resolvable") and not value.is_resolvable:
            return None
        if hasattr(value, "to_unsigned"):
            return value.to_unsigned()
        return int(value)
    except Exception:
        return None


def _env_flag(name):
    return str(os.environ.get(name, "")).strip().lower() in ("1", "true", "yes", "on", "debug")


def _is_high(signal):
    value = _safe_signal_int(signal)
    return value is not None and value != 0


def _fetch_transaction_ok(dut):
    if hasattr(dut, "imem_fetch_addr"):
        return True
    required = ["core_stb", "core_ack"]
    optional = ["core_cyc"]
    if any(not hasattr(dut, name) or not _is_high(getattr(dut, name)) for name in required):
        return False
    if any(hasattr(dut, name) and not _is_high(getattr(dut, name)) for name in optional):
        return False
    if hasattr(dut, "core_we") and _is_high(dut.core_we):
        return False
    return True


def _program_address_aliases(address):
    """Return common byte-address aliases used by wrapper-local memories."""
    if address is None:
        return ()
    address = int(address)
    aliases = []
    for candidate in (address, address & 0xFFF, address & 0x3FF, address & 0x7F):
        if candidate not in aliases:
            aliases.append(candidate)
    return tuple(aliases)


def _cycle_program_instruction(address):
    return program_memory.read(address)


def _canonical_signature_pc(address):
    """Map a relocated fetch PC back to the signature's programmed offset."""
    for candidate in _program_address_aliases(address):
        if candidate in SIGNATURE_BY_PC:
            return candidate
    return None


def _normalise_interface_path(path, actual_core_instance):
    normalised = path.replace("processorci_top.", "")
    if actual_core_instance:
        normalised = re.sub(r'^[^.]+\.', f'{actual_core_instance}.', normalised)
    return normalised


def _is_derived_interface_path(path):
    return isinstance(path, str) and path.startswith("__")


def _complete_real_interface(interface_signals):
    required = ("write_enable", "write_addr", "write_data")
    return (
        isinstance(interface_signals, dict)
        and all(interface_signals.get(role) for role in required)
        and not any(_is_derived_interface_path(interface_signals.get(role)) for role in required)
    )


def _current_regfile_interface_state(core_name):
    output_dir = os.environ.get("OUTPUT_DIR")
    if not output_dir or not core_name:
        return None, None

    metadata_file = os.path.join(output_dir, f"{core_name}_reg_file.json")
    try:
        with open(metadata_file, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except (json.JSONDecodeError, OSError):
        return None, None

    if "selected_regfile_interface" not in data and "regfile_interface" not in data:
        return None, None

    selected = data.get("selected_regfile_interface") or {}
    interface_signals = data.get("regfile_interface") or {
        "write_enable": selected.get("write_enable"),
        "write_addr": selected.get("write_addr"),
        "write_data": selected.get("write_data"),
    }
    if isinstance(interface_signals, dict) and selected.get("timing_offset") is not None:
        interface_signals = dict(interface_signals)
        interface_signals["timing_offset"] = selected.get("timing_offset")
        for role in ("write_enable", "write_addr", "write_data"):
            offset_key = f"{role}_timing_offset"
            if selected.get(offset_key) is not None:
                interface_signals[offset_key] = selected.get(offset_key)
    if isinstance(interface_signals, dict) and selected.get("write_addr_bit_offset") is not None:
        interface_signals = dict(interface_signals)
        interface_signals["write_addr_bit_offset"] = selected.get("write_addr_bit_offset")

    if selected.get("status") == "rejected_interface":
        return "rejected", interface_signals
    if _complete_real_interface(interface_signals):
        return "usable", interface_signals
    return "not_real_or_incomplete", interface_signals


def _resolve_write_interface(dut, core_name, regfile):
    current_state, current_interface = _current_regfile_interface_state(core_name)
    if current_state == "usable":
        interface_signals = current_interface
    elif current_state in ("rejected", "not_real_or_incomplete"):
        dut._log.info(
            "[measure] Current regfile finder did not provide a complete real write interface; "
            "using register-file observation instead of legacy cached interface"
        )
        return None
    else:
        interface_signals = load_regfile_interface(core_name) if core_name else None

    if core_name and not interface_signals:
        dut._log.info("[measure] Searching for register file write interface signals...")
        interface_signals = find_regfile_write_signals(dut, core_name, regfile)

    if not interface_signals:
        return None

    actual_core_instance = _find_core_instance(dut)
    handles = {}
    for role, key in (("write_enable", "write_enable"), ("write_addr", "write_addr"), ("write_data", "write_data")):
        if key not in interface_signals:
            continue
        path = _normalise_interface_path(interface_signals[key], actual_core_instance)
        handle = _get_handle_from_path(dut, path)
        if handle is not None:
            handles[role] = handle

    if "write_enable" in handles and "write_addr" in handles and "write_data" in handles:
        try:
            handles["_timing_offset"] = int(interface_signals.get("timing_offset", 0))
        except (TypeError, ValueError):
            handles["_timing_offset"] = 0
        handles["_role_timing_offsets"] = {}
        for role in ("write_enable", "write_addr", "write_data"):
            try:
                handles["_role_timing_offsets"][role] = int(
                    interface_signals.get(f"{role}_timing_offset", handles["_timing_offset"])
                )
            except (TypeError, ValueError):
                handles["_role_timing_offsets"][role] = handles["_timing_offset"]
        try:
            bit_offset = interface_signals.get("write_addr_bit_offset")
            handles["_write_addr_bit_offset"] = int(bit_offset) if bit_offset is not None else None
        except (TypeError, ValueError):
            handles["_write_addr_bit_offset"] = None
        return handles

    dut._log.warning(
        "[measure] Write interface is incomplete; need enable, address, and data. Found roles: %s",
        sorted(handles.keys()),
    )
    return None


def _infer_regfile_depth(regfile_metadata, regfile):
    if regfile_metadata and regfile_metadata.get("depth") is not None:
        return regfile_metadata.get("depth")
    try:
        return len(regfile)
    except Exception:
        return None


def _declared_regfile_indices(regfile):
    """Return HDL array indices when cocotb exposes the declared range."""
    declared_range = getattr(regfile, "range", None)
    if declared_range is None:
        return None
    try:
        return {int(index) for index in declared_range}
    except (TypeError, ValueError):
        return None


def _regfile_storage_index(arch_reg, regfile_metadata=None, regfile=None):
    if not 0 <= arch_reg <= 31:
        return None

    if getattr(regfile, "_architectural_indexed", False):
        return arch_reg

    mapping_order = (regfile_metadata or {}).get("mapping_order")
    mapping_delta = {
        "physical_index_plus_1": 1,
        "physical_index_minus_1": -1,
    }.get(mapping_order, 0)
    physical_index = arch_reg + mapping_delta

    declared_indices = _declared_regfile_indices(regfile)
    if declared_indices is not None:
        return physical_index if physical_index in declared_indices else None

    depth = _infer_regfile_depth(regfile_metadata, regfile)
    if depth == 31:
        return physical_index - 1 if 1 <= physical_index <= 31 else None
    return physical_index if 0 <= physical_index < (depth or 32) else None


def _get_regfile_reg_value(regfile, arch_reg, regfile_metadata=None):
    storage_index = _regfile_storage_index(arch_reg, regfile_metadata, regfile)
    if storage_index is None:
        return None
    try:
        return _safe_signal_int(regfile[storage_index])
    except Exception:
        return None


def _load_regfile_metadata(output_dir, processor_name, regfile_path=None):
    metadata_file = os.path.join(output_dir, f"{processor_name}_reg_file.json")
    try:
        with open(metadata_file, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except (json.JSONDecodeError, OSError):
        return None

    selected = data.get("selected_regfile")
    if selected:
        selected_path = selected.get("candidate_path") or selected.get("path")
        if regfile_path is None or selected_path == regfile_path:
            return selected

    for candidate in data.get("regfile_array_candidates", []):
        candidate_path = candidate.get("candidate_path") or candidate.get("path")
        if regfile_path is None or candidate_path == regfile_path:
            return candidate

    return None


def _measurement_cycle_budget(regfile_metadata):
    if isinstance(regfile_metadata, dict) and regfile_metadata.get("kind") == "bit_sliced_array":
        return 2000
    return 300


def _signature_entry_for(reg, value, fetched_pcs=None, seen_commit_pcs=None):
    fetched_pcs = fetched_pcs or set()
    seen_commit_pcs = seen_commit_pcs or set()
    candidates = SIGNATURE_BY_REG_VALUE.get((reg, value & 0xFFFFFFFF), [])
    # The same architectural signature is installed at multiple address
    # aliases. A level write-enable may remain asserted for more than one
    # sampled cycle; once any alias has committed, do not count another alias
    # as a second architectural instruction.
    if any(entry["pc"] in seen_commit_pcs for entry in candidates):
        return None
    for entry in candidates:
        if entry["pc"] in fetched_pcs and entry["pc"] not in seen_commit_pcs:
            return entry
    for entry in candidates:
        if entry["pc"] not in seen_commit_pcs:
            return entry
    return None


def _record_signature_fetch(dut, cycle, fetch_events, seen_fetch_pcs):
    pc_handle = dut.imem_fetch_addr if hasattr(dut, "imem_fetch_addr") else dut.core_addr
    raw_pc = _safe_signal_int(pc_handle)
    pc = _canonical_signature_pc(raw_pc)
    if pc is None and cycle < 40 and (_env_flag("CYCLE_DEBUG") or _env_flag("DEBUG_CYCLE")):
        dut._log.info("[measure] Unmatched raw fetch PC at cycle %d: %s", cycle, raw_pc)
    if pc is not None and _fetch_transaction_ok(dut) and pc not in seen_fetch_pcs:
        entry = SIGNATURE_BY_PC[pc]
        for prior_entry in SIGNATURE_ALIASED_WRITES:
            if prior_entry["base_pc"] != entry["base_pc"] or prior_entry["offset"] >= entry["offset"]:
                continue
            if prior_entry["pc"] in seen_fetch_pcs:
                continue
            cycle_delta = (entry["offset"] - prior_entry["offset"]) // 4
            seen_fetch_pcs.add(prior_entry["pc"])
            fetch_events.append({"cycle": cycle - cycle_delta, "pc": prior_entry["pc"]})
        seen_fetch_pcs.add(pc)
        fetch_events.append({"cycle": cycle, "pc": pc})


def _record_probe_fetch(dut, cycle, spec, fetch_events, seen_offsets):
    """Record the first accepted fetch of each instruction in a probe image."""
    pc_handle = dut.imem_fetch_addr if hasattr(dut, "imem_fetch_addr") else dut.core_addr
    raw_pc = _safe_signal_int(pc_handle)
    if raw_pc is None:
        return
    for candidate in _program_address_aliases(raw_pc):
        for base in spec.base_addresses:
            offset = candidate - base
            if offset in spec.instructions and offset not in seen_offsets:
                seen_offsets.add(offset)
                fetch_events.append({"cycle": cycle, "offset": offset, "pc": raw_pc})
                return
    if cycle < 25 and (_env_flag("CYCLE_DEBUG") or _env_flag("DEBUG_CYCLE")):
        dut._log.info("[forwarding] unmatched probe fetch cycle=%d raw_pc=%s probe=%s", cycle, raw_pc, spec.name)


def _aligned_interface_values(samples_by_cycle, reference_cycle, reference_offset, role_offsets):
    values = {}
    for role in ("write_enable", "write_addr", "write_data"):
        signal_cycle = reference_cycle + role_offsets.get(role, reference_offset) - reference_offset
        sample = samples_by_cycle.get(signal_cycle)
        if sample is None:
            return None
        values[role] = sample.get(role)
    return values


async def _observe_signature_commits_with_interface(
    dut,
    handles,
    regfile=None,
    regfile_metadata=None,
    max_cycles=300,
):
    dut._log.info("[measure] Observing signature commits through register-file interface")
    commit_events = []
    fetch_events = []
    seen_commit_pcs = set()
    seen_fetch_pcs = set()
    samples_by_cycle = {}
    previous_regfile_values = {}
    if regfile is not None:
        for entry in SIGNATURE_WRITES:
            previous_regfile_values[entry["reg"]] = _get_regfile_reg_value(
                regfile,
                entry["reg"],
                regfile_metadata,
            )
    reference_offset = handles.get("_timing_offset", 0)
    role_offsets = handles.get("_role_timing_offsets") or {
        role: reference_offset for role in ("write_enable", "write_addr", "write_data")
    }
    max_alignment_delta = max(
        role_offsets.get(role, reference_offset) - reference_offset
        for role in ("write_enable", "write_addr", "write_data")
    )

    for cycle in range(max_cycles):
        await RisingEdge(dut.sys_clk)
        await Timer(0.001, unit="ns")

        _record_signature_fetch(dut, cycle, fetch_events, seen_fetch_pcs)

        samples_by_cycle[cycle] = {
            role: _safe_signal_int(handles[role])
            for role in ("write_enable", "write_addr", "write_data")
        }
        reference_cycle = cycle - max(0, max_alignment_delta)
        aligned = _aligned_interface_values(
            samples_by_cycle,
            reference_cycle,
            reference_offset,
            role_offsets,
        )
        if aligned is not None and _is_high(aligned["write_enable"]):
            reg = aligned["write_addr"]
            value = aligned["write_data"]
            if reg is not None and value is not None:
                bit_offset = handles.get("_write_addr_bit_offset")
                if bit_offset is not None:
                    reg = (reg >> bit_offset) & 0x1F

                value &= 0xFFFFFFFF
                entry = _signature_entry_for(
                    reg,
                    value,
                    fetched_pcs=seen_fetch_pcs,
                    seen_commit_pcs=seen_commit_pcs,
                )
                if entry is not None and entry["pc"] not in seen_commit_pcs:
                    seen_commit_pcs.add(entry["pc"])
                    commit_events.append({
                        "cycle": reference_cycle,
                        "pc": entry["pc"],
                        "reg": reg,
                        "value": value,
                        "source": "interface",
                    })
                    dut._log.info(
                        "[measure] Commit %s at cycle %d: x%d = 0x%08x",
                        entry["instruction"],
                        reference_cycle,
                        reg,
                        value,
                    )

        # Keep architectural storage observation active alongside a real
        # interface. This recovers from an otherwise plausible interface whose
        # role timing is incomplete without discarding valid interface events.
        if regfile is not None:
            for signature_entry in SIGNATURE_WRITES:
                reg = signature_entry["reg"]
                value = _get_regfile_reg_value(regfile, reg, regfile_metadata)
                if value is None:
                    continue
                previous = previous_regfile_values.get(reg)
                previous_regfile_values[reg] = value
                expected = signature_entry["value"] & 0xFFFFFFFF
                if value != expected or previous == expected:
                    continue
                entry = _signature_entry_for(
                    reg,
                    expected,
                    fetched_pcs=seen_fetch_pcs,
                    seen_commit_pcs=seen_commit_pcs,
                ) or signature_entry
                if entry["pc"] in seen_commit_pcs:
                    continue
                seen_commit_pcs.add(entry["pc"])
                commit_events.append({
                    "cycle": cycle,
                    "pc": entry["pc"],
                    "reg": reg,
                    "value": value,
                    "source": "regfile_observation",
                })
                dut._log.info(
                    "[measure] Observed fallback commit %s at cycle %d: x%d = 0x%08x",
                    entry["instruction"],
                    cycle,
                    reg,
                    value,
                )

        if len(commit_events) == len(SIGNATURE_WRITES):
            break

    return fetch_events, commit_events


async def _observe_signature_commits_from_regfile(dut, regfile, regfile_metadata=None, max_cycles=300):
    dut._log.info("[measure] Observing signature commits through register-file value changes")
    commit_events = []
    fetch_events = []
    seen_commit_pcs = set()
    seen_fetch_pcs = set()
    previous_values = {}

    for entry in SIGNATURE_WRITES:
        previous_values[entry["reg"]] = _get_regfile_reg_value(regfile, entry["reg"], regfile_metadata)

    for cycle in range(max_cycles):
        await RisingEdge(dut.sys_clk)
        await Timer(0.001, unit="ns")

        _record_signature_fetch(dut, cycle, fetch_events, seen_fetch_pcs)

        for entry in SIGNATURE_WRITES:
            reg = entry["reg"]
            if entry["pc"] in seen_commit_pcs:
                continue

            value = _get_regfile_reg_value(regfile, reg, regfile_metadata)
            if value is None:
                continue

            expected = entry["value"] & 0xFFFFFFFF
            previous = previous_values.get(reg)
            previous_values[reg] = value

            if value == expected and previous != expected:
                matched_entry = _signature_entry_for(
                    reg,
                    expected,
                    fetched_pcs=seen_fetch_pcs,
                    seen_commit_pcs=seen_commit_pcs,
                ) or entry
                seen_commit_pcs.add(matched_entry["pc"])
                event = {
                    "cycle": cycle,
                    "pc": matched_entry["pc"],
                    "reg": reg,
                    "value": value,
                    "source": "regfile_observation",
                }
                commit_events.append(event)
                dut._log.info(
                    "[measure] Observed commit %s at cycle %d: x%d = 0x%08x",
                    matched_entry["instruction"],
                    cycle,
                    reg,
                    value,
                )

        if len(commit_events) == len(SIGNATURE_WRITES):
            break

    return fetch_events, commit_events


def _cycle_deltas(events):
    cycles = [event["cycle"] for event in sorted(events, key=lambda event: (event["cycle"], event.get("pc", 0)))]
    return [cycles[index] - cycles[index - 1] for index in range(1, len(cycles))]


def _modal_value(values):
    if not values:
        return None
    counts = Counter(values)
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _dominant_value(values, minimum_fraction=0.8):
    """Return the mode only when it represents a strong majority."""
    if not values:
        return None
    mode = _modal_value(values)
    return mode if values.count(mode) / len(values) >= minimum_fraction else None


def _pair_fetches_and_commits(fetch_events, commit_events):
    fetch_by_pc = {event["pc"]: event for event in sorted(fetch_events, key=lambda event: event["cycle"])}
    paired = []
    unmatched_commits = []

    for commit in sorted(commit_events, key=lambda event: (event["cycle"], event["pc"])):
        fetch = fetch_by_pc.get(commit["pc"])
        if fetch is None:
            unmatched_commits.append(commit)
            continue
        paired.append({
            "pc": commit["pc"],
            "reg": commit["reg"],
            "value": commit["value"],
            "fetch_cycle": fetch["cycle"],
            "commit_cycle": commit["cycle"],
            "latency": commit["cycle"] - fetch["cycle"],
        })

    paired_pcs = {event["pc"] for event in paired}
    unmatched_fetches = [event for event in fetch_events if event["pc"] not in paired_pcs]
    return paired, unmatched_fetches, unmatched_commits


def _commit_observation_offset(method):
    return 0


def _depth_estimate_source(method, commit_offset):
    if method == "interface":
        return "write_interface" if commit_offset == 0 else "write_interface_timing_corrected"
    return "regfile_observation_corrected" if commit_offset != 0 else method


def _confidence_score(evidence):
    expected = len(SIGNATURE_WRITES)
    penalties = [("measurement_uncertainty", 0.09)]
    missing_commits = max(0, expected - evidence["commits_observed"])
    missing_pairings = max(0, evidence["commits_observed"] - len(evidence["paired_events"]))

    if missing_commits:
        penalties.append(("missing_expected_commits", 0.08 * missing_commits))
    if missing_pairings:
        penalties.append(("missing_fetch_pairings", 0.06 * missing_pairings))
    if evidence["commits_observed"] < 3:
        penalties.append(("insufficient_commits", 0.25))
    if evidence["mixed_commit_intervals"]:
        penalties.append(("mixed_commit_intervals", 0.18))
    if evidence["unstable_latency"]:
        penalties.append(("unstable_latency_mode", 0.15))
    if evidence["method"] == "regfile_observation":
        penalties.append(("regfile_observation_fallback", 0.08))
    if evidence["interface_incomplete"]:
        penalties.append(("incomplete_write_interface", 0.05))
    if evidence["unmatched_fetches"]:
        penalties.append(("unmatched_fetches", 0.03 * len(evidence["unmatched_fetches"])))
    if evidence["unmatched_commits"]:
        penalties.append(("unmatched_commits", 0.03 * len(evidence["unmatched_commits"])))

    score = max(0.0, min(1.0, 1.0 - sum(penalty for _, penalty in penalties)))
    return round(score, 2), penalties


def _classify_cycle_behavior(evidence):
    commit_intervals = evidence["commit_intervals"]
    latencies = evidence["fetch_to_commit_latencies"]
    dominant_commit_interval = _dominant_value(commit_intervals)
    dominant_latency = _dominant_value(latencies)
    confidence, penalties = _confidence_score(evidence)
    reason = "ambiguous cycle behavior"

    classification = {
        "single_cycle": None,
        "multicycle": None,
        "pipeline": None,
        "confidence": confidence,
    }

    burst_pipeline = (
        evidence["commits_observed"] >= 3
        and any(interval == 0 for interval in commit_intervals)
        and all(interval >= 0 for interval in commit_intervals)
        and len(latencies) >= 3
        and all(latency > 0 for latency in latencies)
    )

    if evidence["commits_observed"] < 3 or not commit_intervals:
        reason = "insufficient signature commits observed"
    elif burst_pipeline:
        classification["single_cycle"] = False
        classification["multicycle"] = False
        classification["pipeline"] = {
            "depth_estimate": evidence["depth_estimate"],
            "depth_estimate_source": evidence["depth_estimate_source"],
            "superscalar_commit_evidence": True,
        }
        reason = "multiple architectural commits in sampled cycles with positive fetch-to-commit latency"
    elif all(interval > 1 for interval in commit_intervals):
        classification["single_cycle"] = False
        classification["multicycle"] = True
        classification["pipeline"] = False
        reason = (
            "architectural commits are consistently spaced by multiple cycles"
            if evidence["mixed_commit_intervals"]
            else "architectural commits are spaced by multiple cycles"
        )
    elif dominant_commit_interval is None:
        reason = "no dominant architectural commit interval observed"
    elif dominant_commit_interval == 1:
        if not latencies:
            reason = "one signature commit per cycle, but fetch-to-commit pairing is unavailable"
        elif dominant_latency == 0:
            classification["single_cycle"] = True
            classification["multicycle"] = False
            classification["pipeline"] = False
            reason = "dominant one-per-cycle commit cadence with zero modal fetch-to-commit latency"
        elif (
            evidence["method"] == "regfile_observation"
            and evidence["interface_incomplete"]
            and evidence["raw_modal_latency"] == 2
            and dominant_latency == 2
        ):
            classification["single_cycle"] = True
            classification["multicycle"] = False
            classification["pipeline"] = False
            reason = (
                "one architectural commit per cycle with two raw observation cycles; "
                "treated as single-cycle behind registered instruction delivery"
            )
        elif dominant_latency is not None and dominant_latency > 0:
            classification["single_cycle"] = False
            classification["multicycle"] = False
            pipeline = {
                "depth_estimate": evidence["depth_estimate"],
                "depth_estimate_source": evidence["depth_estimate_source"],
            }
            if evidence["raw_depth_estimate"] != evidence["depth_estimate"]:
                pipeline["raw_depth_estimate"] = evidence["raw_depth_estimate"]
            classification["pipeline"] = pipeline
            reason = "dominant one-per-cycle commit cadence with stable nonzero modal latency"
        else:
            reason = "one architectural commit per cycle without a dominant fetch-to-commit latency"
    elif dominant_commit_interval > 1:
        classification["single_cycle"] = False
        classification["multicycle"] = True
        classification["pipeline"] = False
        reason = (
            "dominant architectural commit interval is multiple cycles"
            if evidence["mixed_commit_intervals"]
            else "architectural commits are spaced by multiple cycles"
        )

    return classification, reason, penalties


def _build_cycle_measurement(
    fetch_events,
    commit_events,
    method="interface",
    interface_incomplete=False,
    commit_observation_offset=None,
):
    ordered_fetches = sorted(fetch_events, key=lambda event: (event["cycle"], event["pc"]))
    ordered_commits = sorted(commit_events, key=lambda event: (event["cycle"], event["pc"]))
    paired, unmatched_fetches, unmatched_commits = _pair_fetches_and_commits(ordered_fetches, ordered_commits)
    commit_offset = (
        _commit_observation_offset(method)
        if commit_observation_offset is None
        else commit_observation_offset
    )
    raw_latencies = [event["latency"] for event in paired]
    corrected_latencies = [max(0, latency + commit_offset) for latency in raw_latencies]
    modal_latency = _modal_value(corrected_latencies)
    raw_modal_latency = _modal_value(raw_latencies)
    commit_intervals = _cycle_deltas(ordered_commits)
    fetch_intervals = _cycle_deltas(ordered_fetches)
    mixed_commit_intervals = bool(commit_intervals) and len(set(commit_intervals)) > 1
    unstable_latency = bool(corrected_latencies) and len(set(corrected_latencies)) > 1
    depth_source = _depth_estimate_source(method, commit_offset)

    evidence = {
        "method": method,
        "interface_incomplete": interface_incomplete,
        "commit_observation_offset": commit_offset,
        "fetch_events": ordered_fetches,
        "commit_events": ordered_commits,
        "paired_events": paired,
        "unmatched_fetches": unmatched_fetches,
        "unmatched_commits": unmatched_commits,
        "commits_observed": len(ordered_commits),
        "raw_fetch_to_commit_latencies": raw_latencies,
        "corrected_fetch_to_commit_latencies": corrected_latencies,
        "fetch_to_commit_latencies": corrected_latencies,
        "commit_intervals": commit_intervals,
        "fetch_intervals": fetch_intervals,
        "modal_latency": modal_latency,
        "raw_modal_latency": raw_modal_latency,
        "depth_estimate": modal_latency + 1 if modal_latency is not None else None,
        "raw_depth_estimate": raw_modal_latency + 1 if raw_modal_latency is not None else None,
        "depth_estimate_source": depth_source,
        "mixed_commit_intervals": mixed_commit_intervals,
        "unstable_latency": unstable_latency,
        "cycle_convention": "rising-edge sampled after settle; raw_latency = observed_commit_cycle - fetch_cycle; corrected_latency = raw_latency + commit_observation_offset; depth_estimate = modal corrected latency + 1",
    }
    classification, reason, penalties = _classify_cycle_behavior(evidence)
    evidence["classification_reason"] = reason
    evidence["confidence_penalties"] = [{"name": name, "value": value} for name, value in penalties]

    compact = {
        "fetch_to_commit_latencies": corrected_latencies,
        "commit_intervals": commit_intervals,
        "fetch_intervals": fetch_intervals,
        "classification": classification,
    }

    debug = {
        **evidence,
        "program": [
            {
                "pc": entry["pc"],
                "reg": entry["reg"],
                "value": entry["value"],
                "instruction": entry["instruction"],
            }
            for entry in SIGNATURE_WRITES
        ],
    }
    return compact, debug


def _legacy_cycle_labels(cycle_result):
    classification = cycle_result["classification"]
    return classification.get("multicycle"), classification.get("pipeline")


async def measure_execution_model(dut, regfile, core_name=None, regfile_metadata=None):
    """
    Classify single-cycle, pipelined, or multicycle behavior from architectural
    register commits produced by a straight-line signature program.

    Depth estimates use the explicit convention documented in the compact
    result: latency = commit_cycle - fetch_cycle, depth = modal latency + 1.
    Fetch intervals are reported as frontend evidence, not as classification.
    """
    interface_handles = None
    interface_incomplete = False
    max_cycles = _measurement_cycle_budget(regfile_metadata)
    try:
        interface_handles = _resolve_write_interface(dut, core_name, regfile)
    except Exception as exc:
        dut._log.warning("[measure] Failed to resolve write interface: %s", exc)
        interface_incomplete = True

    if interface_handles:
        interface_timing_offset = interface_handles.get("_timing_offset", 0)
        fetch_events, commit_events = await _observe_signature_commits_with_interface(
            dut,
            interface_handles,
            regfile=regfile,
            regfile_metadata=regfile_metadata,
            max_cycles=max_cycles,
        )
        method = "interface"
    else:
        interface_timing_offset = None
        fetch_events, commit_events = await _observe_signature_commits_from_regfile(
            dut,
            regfile,
            regfile_metadata=regfile_metadata,
            max_cycles=max_cycles,
        )
        method = "regfile_observation"
        interface_incomplete = True

    compact, debug = _build_cycle_measurement(
        fetch_events,
        commit_events,
        method=method,
        interface_incomplete=interface_incomplete,
        commit_observation_offset=interface_timing_offset,
    )
    dut._log.info("[measure] Fetch intervals: %s", compact["fetch_intervals"])
    dut._log.info("[measure] Commit intervals: %s", compact["commit_intervals"])
    dut._log.info("[measure] Fetch-to-commit latencies: %s", compact["fetch_to_commit_latencies"])
    dut._log.info("[measure] Classification: %s", compact["classification"])
    return {
        "cycle": compact,
        "cycle_debug": debug,
    }

def _is_pipeline_classification(pipeline):
    """Only a positive pipeline classification enables forwarding probing."""
    return isinstance(pipeline, dict)


async def _observe_probe_commits(dut, regfile, regfile_metadata, handles, spec, max_cycles=300, fetch_events=None):
    """Return ordered architectural commits for a declarative probe."""
    commits = []
    expected_by_pair = {
        (entry["reg"], entry["value"] & 0xFFFFFFFF): entry
        for entry in spec.entries()
    }
    seen_offsets = set()
    previous_values = {
        entry["reg"]: _get_regfile_reg_value(regfile, entry["reg"], regfile_metadata)
        for entry in spec.entries()
    }
    samples_by_cycle = {}
    reference_offset = handles.get("_timing_offset", 0) if handles else 0
    role_offsets = (handles or {}).get("_role_timing_offsets") or {
        role: reference_offset for role in ("write_enable", "write_addr", "write_data")
    }
    max_alignment_delta = max(
        role_offsets.get(role, reference_offset) - reference_offset
        for role in ("write_enable", "write_addr", "write_data")
    )
    fetch_events = fetch_events if fetch_events is not None else []
    seen_fetch_offsets = set()

    for cycle in range(max_cycles):
        await RisingEdge(dut.sys_clk)
        await Timer(0.001, unit="ns")
        _record_probe_fetch(dut, cycle, spec, fetch_events, seen_fetch_offsets)

        if handles:
            samples_by_cycle[cycle] = {
                role: _safe_signal_int(handles[role])
                for role in ("write_enable", "write_addr", "write_data")
            }
            reference_cycle = cycle - max(0, max_alignment_delta)
            aligned = _aligned_interface_values(
                samples_by_cycle, reference_cycle, reference_offset, role_offsets
            )
            if aligned is not None and _is_high(aligned["write_enable"]):
                reg = aligned["write_addr"]
                value = aligned["write_data"]
                bit_offset = handles.get("_write_addr_bit_offset")
                if reg is not None and bit_offset is not None:
                    reg = (reg >> bit_offset) & 0x1F
                entry = expected_by_pair.get((reg, (value or 0) & 0xFFFFFFFF))
                if entry is not None and entry["offset"] not in seen_offsets:
                    seen_offsets.add(entry["offset"])
                    commits.append({
                        "cycle": reference_cycle,
                        "offset": entry["offset"],
                        "reg": reg,
                        "value": value & 0xFFFFFFFF,
                        "source": "interface",
                    })

        # Also watch architectural storage. This is the primary fallback when
        # no write interface exists and recovers from imperfect interface timing.
        for entry in spec.entries():
            reg = entry["reg"]
            value = _get_regfile_reg_value(regfile, reg, regfile_metadata)
            previous = previous_values.get(reg)
            previous_values[reg] = value
            if (
                entry["offset"] not in seen_offsets
                and value == (entry["value"] & 0xFFFFFFFF)
                and previous != value
            ):
                seen_offsets.add(entry["offset"])
                commits.append({
                    "cycle": cycle,
                    "offset": entry["offset"],
                    "reg": reg,
                    "value": value,
                    "source": "regfile_observation",
                })

        if len(seen_offsets) == len(spec.expected_writes):
            break

    return sorted(commits, key=lambda event: event["offset"])


def _classify_forwarding_probe(spec, commits, memory, memory_epoch, pipeline_depth):
    complete = len(commits) == len(spec.expected_writes)
    result = {
        "present": None,
        "status": "inconclusive",
        "commits_observed": len(commits),
        "commits_expected": len(spec.expected_writes),
    }
    if not complete:
        result["reason"] = "expected architectural results were not all observed"
        return result

    by_role = {event.get("role"): event for event in commits}
    if spec.name.startswith("alu_to_alu"):
        dependent = [event for event in commits if event.get("role") == "dependent"]
        if len(dependent) == 1:
            producer = next(event for event in commits if event.get("role") == "producer")
            interval = dependent[0]["cycle"] - producer["cycle"]
            instruction_distance = (dependent[0]["offset"] - producer["offset"]) // 4
            stalls = max(0, interval - instruction_distance)
            result.update({"present": stalls == 0, "dependent_commit_interval": interval, "stall_cycles": stalls})
        else:
            intervals = _cycle_deltas(dependent)
            result.update({
                "present": bool(intervals) and all(interval == 1 for interval in intervals),
                "dependent_commit_intervals": intervals,
                "stall_cycles": sum(max(0, interval - 1) for interval in intervals),
            })
    elif spec.name.startswith("load_to_alu"):
        interval = commits[-1]["cycle"] - commits[-2]["cycle"]
        instruction_distance = (commits[-1]["offset"] - commits[-2]["offset"]) // 4
        stalls = max(0, interval - instruction_distance)
        # Waiting for architectural writeback costs roughly the remaining
        # pipeline depth. A shorter separation is positive bypass evidence.
        no_bypass_distance = max(2, int(pipeline_depth or 2) - 1)
        result.update({
            "present": stalls <= 1,
            "dependent_commit_interval": interval,
            "stall_cycles": stalls,
            "no_bypass_distance_estimate": no_bypass_distance,
        })
    else:
        transactions = [
            {**item, "cycle": item["cycle"] - memory_epoch}
            for item in memory.transactions
        ] if memory and memory.supported else []
        stores = [item for item in transactions if item["kind"] == "store"]
        loads = [item for item in transactions if item["kind"] == "load"]
        result["memory_transactions"] = transactions
        if not memory or not memory.supported:
            result["reason"] = "separate data-memory transaction interface is unavailable"
            return result
        if spec.name.startswith("alu_to_store_data") or spec.name.startswith("alu_to_store_address"):
            producer_role = "producer" if spec.name.startswith("alu_to_store_data") else "address_producer"
            producer = by_role.get(producer_role)
            if not stores or producer is None:
                result["reason"] = "producer commit or store request was not observed"
                return result
            request_distance = stores[0]["cycle"] - producer["cycle"]
            result.update({
                # Correct store data/address proves that the RAW dependency was
                # handled, but external request timing cannot distinguish an
                # operand bypass from a stall until register-file writeback.
                # Leave capability undecided until the distance sweep can
                # compare this observation with a timing baseline.
                "present": None,
                "architectural_dependency_handled": True,
                "store_request_relative_to_producer_commit": request_distance,
                "reason": (
                    "architectural result is correct, but external store timing "
                    "cannot distinguish forwarding from a writeback stall"
                ),
            })
        elif spec.name.startswith("store_to_load"):
            if not stores or not loads:
                result["reason"] = "store/load transaction pair was not observed"
                return result
            distance = loads[-1]["cycle"] - stores[0]["cycle"]
            result.update({
                "present": loads[-1]["value"] == stores[0]["value"],
                "transaction_distance": distance,
            })

    if result["present"] is not None:
        result["status"] = "detected" if result["present"] else "not_detected"
    return result


def _summarize_forwarding_distance_sweep(name, classified_by_gap, pipeline_depth):
    """Combine focused probes without confusing fixed core latency with RAW stalls."""
    adjacent = dict(classified_by_gap[0])
    ordered = [(gap, classified_by_gap[gap]) for gap in sorted(classified_by_gap)]

    if name in ("alu_to_alu", "load_to_alu"):
        measured = [
            (gap, item.get("stall_cycles"))
            for gap, item in ordered
            if item.get("stall_cycles") is not None
        ]
        if not measured:
            return adjacent

        # Commit observation and some pipelines add a fixed cycle between all
        # instructions. Only delay above the best observed floor is evidence of
        # a dependency stall.
        structural_floor = min(stalls for _, stalls in measured)
        adjacent_stalls = measured[0][1]
        raw_penalty = max(0, adjacent_stalls - structural_floor)
        adjacent["structural_stall_floor"] = structural_floor
        adjacent["raw_dependency_penalty"] = raw_penalty

        allowed_penalty = 1 if name == "load_to_alu" else 0
        if raw_penalty <= allowed_penalty:
            adjacent["present"] = True
            adjacent["status"] = "detected"
            adjacent["evidence"] = "no dependency-specific delay above the measured structural floor"
        else:
            # A declining penalty across increasing gaps is consistent with a
            # consumer waiting for architectural availability. It is negative
            # behavioral evidence, not proof that the RTL lacks all bypasses.
            penalties = [max(0, stalls - structural_floor) for _, stalls in measured]
            adjacent["present"] = False
            adjacent["status"] = "not_detected"
            adjacent["evidence"] = "dependency-specific delay decreases as producer-consumer distance increases"
            adjacent["raw_dependency_penalty_sweep"] = penalties
        return adjacent

    if name in ("alu_to_store_data", "alu_to_store_address"):
        # There is no safe black-box absence inference here: both a forwarded
        # store and a correctly stalled store produce the same architectural
        # value at the memory interface.
        if adjacent.get("architectural_dependency_handled"):
            adjacent["present"] = None
            adjacent["status"] = "inconclusive"
        return adjacent

    return adjacent


def _trial_latency(name, spec, fetch_events, commits, transactions):
    fetch = next((item for item in fetch_events if item["offset"] == spec.consumer_offset), None)
    if fetch is None:
        return None
    if name in ("alu_to_store_data", "alu_to_store_address"):
        store = next((item for item in transactions if item.get("kind") == "store"), None)
        return None if store is None else store["cycle"] - fetch["cycle"]
    commit = next((item for item in commits if item.get("role") == "consumer"), None)
    return None if commit is None else commit["cycle"] - fetch["cycle"]


def _timing_series(trials):
    return [item["latency"] for item in trials if item.get("latency") is not None]


def _paired_trials_need_extension(dependent, control):
    """Use five trials when the initial three do not produce identical evidence."""
    for trials in (dependent, control):
        latencies = _timing_series(trials)
        completions = [item.get("complete", False) for item in trials]
        if len(latencies) != len(trials) or len(set(latencies)) > 1 or len(set(completions)) > 1:
            return True
    penalties = [d["latency"] - c["latency"] for d, c in zip(dependent, control)]
    return len(set(penalties)) > 1


def _classify_paired_forwarding(name, dependent, control, relaxed=None):
    """Classify effective bypass behavior from layout-matched trial timings."""
    category = "register_forwarding"
    result = {
        "status": "inconclusive",
        "present": None,
        "category": category,
        "register_forwarding_test": True,
        "architectural_dependency_handled": all(item.get("complete") for item in dependent),
        "dependent_trials": _timing_series(dependent),
        "control_trials": _timing_series(control),
        "timing_stable": False,
        "confidence": 0.35,
    }
    dep_complete = [item.get("complete", False) for item in dependent]
    ctl_complete = [item.get("complete", False) for item in control]
    dep = result["dependent_trials"]
    ctl = result["control_trials"]
    completion_stable = len(set(dep_complete)) == 1 and len(set(ctl_complete)) == 1

    if completion_stable and all(ctl_complete) and not any(dep_complete):
        result.update({
            "status": "not_detected", "present": False, "confidence": 0.6,
            "evidence": "control completed consistently but the dependent program did not",
        })
        return result
    if not completion_stable or not all(dep_complete) or not all(ctl_complete) or len(dep) != len(dependent) or len(ctl) != len(control):
        result["evidence"] = "paired programs did not complete consistently"
        return result

    stable = (max(dep) - min(dep) <= 1) and (max(ctl) - min(ctl) <= 1)
    result["timing_stable"] = stable
    result["dependent_median_latency"] = median(dep)
    result["control_median_latency"] = median(ctl)
    penalty = median(dep) - median(ctl)
    result["raw_penalty_cycles"] = penalty
    if not stable:
        result["evidence"] = "final paired timing range exceeds one cycle"
        return result

    relaxed_penalty = None
    if relaxed:
        rdep = _timing_series(relaxed[0])
        rctl = _timing_series(relaxed[1])
        if rdep and rctl:
            relaxed_penalty = median(rdep) - median(rctl)
            result["relaxed_raw_penalty_cycles"] = relaxed_penalty

    confidence = 0.92 if len(dependent) == 5 else 0.9
    if penalty <= 0:
        bypass = {
            "alu_to_alu": "alu_to_ex",
            "load_to_alu": "load_to_ex_zero_stall",
            "alu_to_store_data": "alu_to_store_data",
            "alu_to_store_address": "alu_to_store_address",
        }[name]
        result.update({
            "status": "detected", "present": True, "bypass_kind": bypass,
            "confidence": confidence,
            "evidence": "dependent and control median latencies are equal",
        })
    elif name == "load_to_alu" and penalty == 1 and relaxed_penalty is not None and relaxed_penalty <= 0:
        result.update({
            "status": "detected", "present": True,
            "bypass_kind": "load_to_ex_after_interlock", "confidence": confidence,
            "evidence": "one-cycle adjacent load-use interlock disappears at relaxed distance",
        })
    else:
        result.update({
            "status": "stall_handled", "present": False, "confidence": min(confidence, 0.88),
            "evidence": "dependency is architecturally correct but adds latency relative to control",
        })
    return result


async def forwarding_presence_test(dut, regfile, pipeline=None, data_memory=None):
    """
    Compare layout-matched dependent/control programs on pipelined cores.

    ``detected`` is behavioral evidence that the RAW dependency adds no latency
    relative to its control (or is a recognized one-cycle load interlock). It
    does not claim structural proof that a particular RTL bypass mux exists.
    """

    if not _is_pipeline_classification(pipeline):
        dut._log.info("[forwarding] Skipped: processor was not classified as pipelined")
        return None

    dut._log.info("[forwarding] Running isolated forwarding probes...")
    data_memory = data_memory or DataMemory()
    results = {"applicable": True}
    try:
        output_dir = os.environ.get("OUTPUT_DIR", "default")
        processor_name = os.path.basename(output_dir)

        regfile_path = getattr(regfile, "_path", None)
        regfile_metadata = _load_regfile_metadata(
            output_dir,
            processor_name,
            regfile_path=regfile_path,
        )

        interface_handles = _resolve_write_interface(
            dut,
            processor_name,
            regfile,
        )
        labels_file = os.path.join(
            output_dir,
            f"{processor_name}_labels.json",
        )

        debug_results = {}
        pipeline_depth = pipeline.get("depth_estimate")

        async def run_probe(spec):
            program_memory.select(spec)
            data_memory.reset(spec.initial_memory)
            dut.rst_n.value = 0
            dut.core_ack.value = 0
            await _load_optional_internal_program(dut, program_memory.image)
            await Timer(50, unit="ns")
            data_memory.reset(spec.initial_memory)
            dut.rst_n.value = 1
            memory_epoch = data_memory.current_cycle
            fetch_events = []
            commits = await _observe_probe_commits(
                dut, regfile, regfile_metadata, interface_handles, spec,
                max_cycles=_measurement_cycle_budget(regfile_metadata),
                fetch_events=fetch_events,
            )
            entries = {item["offset"]: item for item in spec.entries()}
            for event in commits:
                event["role"] = entries[event["offset"]]["role"]
            classified = _classify_forwarding_probe(
                spec, commits, data_memory, memory_epoch, pipeline_depth
            )
            transactions = [
                {**item, "cycle": item["cycle"] - memory_epoch}
                for item in data_memory.transactions
            ] if data_memory.supported else []
            trial = {
                "complete": len(commits) == len(spec.expected_writes),
                "latency": _trial_latency(spec.name.split("_dependent_")[0].split("_control_")[0], spec, fetch_events, commits, transactions),
            }
            details = {
                "program": spec.entries(), "instructions": spec.instructions,
                "fetch_events": fetch_events, "commit_events": commits,
                "memory_transactions": transactions, "classified": classified,
            }
            return trial, details

        async def run_pair_trials(name, gap):
            dependent_trials, control_trials, trial_debug = [], [], []
            for trial_index in range(3):
                dependent_spec, control_spec = forwarding_probe_pair(name, gap, trial_index)
                for role, spec, target in (
                    ("dependent", dependent_spec, dependent_trials),
                    ("control", control_spec, control_trials),
                ):
                    observation, details = await run_probe(spec)
                    target.append(observation)
                    trial_debug.append({"trial": trial_index, "role": role, **details, "observation": observation})
            if _paired_trials_need_extension(dependent_trials, control_trials):
                for trial_index in range(3, 5):
                    dependent_spec, control_spec = forwarding_probe_pair(name, gap, trial_index)
                    for role, spec, target in (
                        ("dependent", dependent_spec, dependent_trials),
                        ("control", control_spec, control_trials),
                    ):
                        observation, details = await run_probe(spec)
                        target.append(observation)
                        trial_debug.append({"trial": trial_index, "role": role, **details, "observation": observation})
            debug_results[f"{name}_paired_gap_{gap}"] = trial_debug
            return dependent_trials, control_trials

        for name in ("alu_to_alu", "alu_to_store_data", "alu_to_store_address", "load_to_alu"):
            adjacent = await run_pair_trials(name, 0)
            relaxed = None
            relaxed_gap = None
            if name in ("alu_to_alu", "load_to_alu"):
                relaxed_gap = max(1, int(pipeline_depth or 2) - 1)
                relaxed = await run_pair_trials(name, relaxed_gap)
            results[name] = _classify_paired_forwarding(name, *adjacent, relaxed=relaxed)
            results[name]["trial_count"] = len(adjacent[0])
            if relaxed_gap is not None:
                results[name]["relaxed_gap"] = relaxed_gap

        # Store-to-load is memory ordering, not register operand forwarding.
        memory_spec = forwarding_distance_variant("store_to_load", 0)
        memory_trial, memory_details = await run_probe(memory_spec)
        memory_classified = memory_details["classified"]
        results["store_to_load"] = {
            **memory_classified,
            "category": "memory_ordering",
            "register_forwarding_test": False,
            "architectural_dependency_handled": memory_trial["complete"],
            "confidence": 0.85 if memory_classified["status"] != "inconclusive" else 0.35,
            "evidence": "store/load ordering and returned memory value",
        }
        debug_results["store_to_load"] = [memory_details]

        #
        # Save result
        #
        try:
            with open(labels_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        data.setdefault(processor_name, {})
        data[processor_name]["forwarding"] = results

        if _env_flag("CYCLE_DEBUG") or _env_flag("DEBUG_CYCLE"):
            data[processor_name]["forwarding_debug"] = {
                "probes": debug_results,
            }
        else:
            data[processor_name].pop("forwarding_debug", None)

        with open(labels_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        dut._log.info(
            "[forwarding] probe results: %s",
            {name: value.get("status") for name, value in results.items() if isinstance(value, dict)},
        )

        return results

    finally:
        program_memory.select(CYCLE_SIGNATURE)


# Compatibility for callers which used the misspelled draft name.
fowarding_presence_test = forwarding_presence_test


async def test_pc_behavior(dut, regfile):
    # initialize driven signals
    dut.core_ack.value = 0
    dut.core_data_in.value = 0

    await _start_clock_once(dut)
    data_memory = DataMemory()
    program_memory.select(CYCLE_SIGNATURE)
    instruction_driver_task = cocotb.start_soon(instr_mem_driver(dut, program_memory))
    data_driver_task = cocotb.start_soon(data_mem_driver(dut, data_memory))

    # Reset
    dut.rst_n.value = 0
    dut.core_ack.value = 0
    await _load_optional_internal_program(dut, program_memory.image)
    await Timer(50, unit="ns")
    dut.rst_n.value = 1

    dut._log.info("Measuring execution model from architectural commit cadence...")
    
    # Get core name from environment for interface signal lookup
    output_dir = os.environ.get('OUTPUT_DIR', "default")
    core_name = os.path.basename(output_dir)
    regfile_path = getattr(regfile, "_path", None)
    regfile_metadata = _load_regfile_metadata(output_dir, core_name, regfile_path=regfile_path)
    
    measurement = await measure_execution_model(
        dut,
        regfile,
        core_name=core_name,
        regfile_metadata=regfile_metadata,
    )

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

    existing_data.setdefault(processor_name, {})
    multicycle, pipeline = _legacy_cycle_labels(measurement["cycle"])
    existing_data[processor_name]["cycle"] = measurement["cycle"]
    existing_data[processor_name]["multicycle"] = multicycle
    existing_data[processor_name]["pipeline"] = pipeline
    existing_data[processor_name].pop("cycle_evidence", None)
    if not _is_pipeline_classification(pipeline):
        existing_data[processor_name].pop("forwarding", None)
        existing_data[processor_name].pop("forwarding_debug", None)
    if _env_flag("CYCLE_DEBUG") or _env_flag("DEBUG_CYCLE"):
        existing_data[processor_name]["cycle_debug"] = measurement["cycle_debug"]
    else:
        existing_data[processor_name].pop("cycle_debug", None)

    try:
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(existing_data, json_file, indent=4)
        dut._log.info(f'Results saved to {output_file}')
    except OSError as e:
        logging.warning('Error writing to JSON file: %s', e)

    # Forwarding is a pipeline-specific property. Do not run a second program
    # (or emit a misleading false label) for single-cycle, multicycle, or
    # ambiguous classifications.
    if _is_pipeline_classification(pipeline):
        await forwarding_presence_test(
            dut, regfile, pipeline=pipeline, data_memory=data_memory
        )
    else:
        dut._log.info("[forwarding] Not applicable to this execution model")

    # Do not leave VPI-backed driver coroutines alive during simulator teardown.
    # Some Verilator designs otherwise abort in heap cleanup after a passing test.
    for task in (instruction_driver_task, data_driver_task):
        try:
            if hasattr(task, "cancel"):
                task.cancel()
            else:
                task.kill()
        except Exception:
            pass
