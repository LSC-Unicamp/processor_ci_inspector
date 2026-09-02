import cocotb

import os

import json

import logging

import re

import traceback

import uuid

from collections import Counter

from statistics import median

from cocotb.triggers import FallingEdge, RisingEdge, Timer

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
    from .probe_programs import (
        BRANCH_PREDICTION_PROBES,
        BRANCH_RESOLUTION_PROBES,
        CYCLE_SIGNATURE,
        FORWARDING_PROBES,
        direction_sequence_probe,
        forwarding_distance_variant,
        forwarding_probe_pair,
        long_history_probe,
        long_history_sweep,
        loop_predictor_probe,
        path_history_probe,
        path_history_sweep,
        paired_timing_probes,
        CALIBRATION_LANDING_BASES,
        pipeline_calibration_flow,
        pipeline_handshake_calibration,
        pipeline_relocation_landing,
        power_of_two_alias_sweep,
        ras_depth_sweep,
        store_to_load_hazard_probe,
    )
    from .riscv.encoding import ADD, ADDI, JAL, LW, NOP, SUB, SW
    from .simulation import DataMemory, ProgramMemory
    from .pipeline_interface_finder import (
        PIPELINE_INTERFACE_DISCOVERY_VERSION,
        PipelineSignalObserver,
        compact_pipeline_interface,
        consumer_stage_cycle,
        validate_frozen_forwarding_trials,
        write_pipeline_interface,
    )
except ImportError:
    from probe_programs import (
        BRANCH_PREDICTION_PROBES,
        BRANCH_RESOLUTION_PROBES,
        CYCLE_SIGNATURE,
        FORWARDING_PROBES,
        direction_sequence_probe,
        forwarding_distance_variant,
        forwarding_probe_pair,
        long_history_probe,
        long_history_sweep,
        loop_predictor_probe,
        path_history_probe,
        path_history_sweep,
        paired_timing_probes,
        CALIBRATION_LANDING_BASES,
        pipeline_calibration_flow,
        pipeline_handshake_calibration,
        pipeline_relocation_landing,
        power_of_two_alias_sweep,
        ras_depth_sweep,
        store_to_load_hazard_probe,
    )
    from riscv.encoding import ADD, ADDI, JAL, LW, NOP, SUB, SW
    from simulation import DataMemory, ProgramMemory
    from pipeline_interface_finder import (
        PIPELINE_INTERFACE_DISCOVERY_VERSION,
        PipelineSignalObserver,
        compact_pipeline_interface,
        consumer_stage_cycle,
        validate_frozen_forwarding_trials,
        write_pipeline_interface,
    )

NOP_INSTRUCTION = NOP

_addi, _add, _sub, _lw, _sw, _jal = ADDI, ADD, SUB, LW, SW, JAL

program_memory = ProgramMemory(CYCLE_SIGNATURE)

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

async def _load_optional_internal_data(dut, memory):
    """Initialize a wrapper-exposed internal data RAM while reset is asserted."""
    required = ("dmem_prog_we", "dmem_prog_addr", "dmem_prog_data")
    if not all(hasattr(dut, name) for name in required):
        return
    dut.dmem_prog_we.value = 0
    for address, value in sorted(memory.items()):
        dut.dmem_prog_addr.value = int(address)
        dut.dmem_prog_data.value = int(value) & 0xFFFFFFFF
        dut.dmem_prog_we.value = 1
        await RisingEdge(dut.sys_clk)
        await Timer(0.001, unit="ns")
    dut.dmem_prog_we.value = 0

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
        dut.core_ack.value = 1
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
    delayed_transaction = None
    delay_remaining = 0
    while True:
        await RisingEdge(dut.sys_clk)
        await Timer(0.001, unit="ns") # let signals settle
        # Delay ACK only while the configured qualifying load is active.  A
        # configured delay must not stall idle cycles, stores, or other loads.
        dut.data_mem_ack.value = 1
        cycle += 1
        memory.current_cycle = cycle
        if active_generation != memory.generation:
            active_transaction = None
            delayed_transaction = None
            delay_remaining = 0
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
            delayed_transaction = None
            delay_remaining = 0
            dut.data_mem_data_in.value = 0
            continue
        address = _safe_signal_int(dut.data_mem_addr)
        is_write = _is_high(dut.data_mem_we)
        value = _safe_signal_int(dut.data_mem_data_out)
        transaction = (address, is_write, value)
        if address is None:
            continue
        delay_applies = (
            memory.response_delay_cycles > 0
            and not is_write
            and (
                memory.response_delay_address is None
                or (int(address) & ~3) == memory.response_delay_address
            )
        )
        if delay_applies:
            if delayed_transaction != transaction:
                delayed_transaction = transaction
                delay_remaining = memory.response_delay_cycles
            if delay_remaining > 0:
                dut.data_mem_ack.value = 0
                delay_remaining -= 1
                dut.data_mem_data_in.value = memory.read_word(address)
                continue
            dut.data_mem_ack.value = 1
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
    if hasattr(dut, "probe_fetch_valid"):
        return _is_high(dut.probe_fetch_valid) or (
            hasattr(dut, "probe_fetch_valid_hi") and _is_high(dut.probe_fetch_valid_hi)
        )
    if hasattr(dut, "imem_fetch_addr"):
        return not hasattr(dut, "imem_fetch_valid") or _is_high(dut.imem_fetch_valid)
    required = ["core_stb", "core_ack"]
    optional = ["core_cyc"]
    if any(not hasattr(dut, name) or not _is_high(getattr(dut, name)) for name in required):
        return False
    if any(hasattr(dut, name) and not _is_high(getattr(dut, name)) for name in optional):
        return False
    if hasattr(dut, "core_we") and _is_high(dut.core_we):
        return False
    return True

def _probe_counter_snapshot(dut):
    """Read the optional, wrapper-standardized architectural BPU counters."""
    if not hasattr(dut, "probe_counter_valid") or not _is_high(dut.probe_counter_valid):
        return None
    branch_count = _safe_signal_int(getattr(dut, "probe_branch_count", None))
    mispredict_count = _safe_signal_int(getattr(dut, "probe_mispredict_count", None))
    if branch_count is None or mispredict_count is None:
        return None
    return {"branches": int(branch_count), "mispredicts": int(mispredict_count)}

def _probe_counter_delta(before, after):
    if before is None or after is None:
        return {"supported": False, "branch_delta": None, "mispredict_delta": None}
    branch_delta = after["branches"] - before["branches"]
    mispredict_delta = after["mispredicts"] - before["mispredicts"]
    if branch_delta < 0 or mispredict_delta < 0:
        return {
            "supported": True, "valid": False,
            "branch_delta": None, "mispredict_delta": None,
            "failure_reason": "counter_reset_or_wrap",
        }
    return {
        "supported": True, "valid": True,
        "branch_delta": branch_delta, "mispredict_delta": mispredict_delta,
        "failure_reason": None,
    }

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

def _record_probe_fetch(dut, cycle, spec, fetch_events, seen_transactions, redirect_events=None):
    """Record every accepted probe fetch, preserving repeated dynamic PCs."""
    if redirect_events is not None and hasattr(dut, "probe_redirect_valid") and _is_high(dut.probe_redirect_valid):
        redirect_pc = _safe_signal_int(getattr(dut, "probe_redirect_pc", None))
        source_pc = _safe_signal_int(getattr(dut, "probe_redirect_source_pc", None))
        redirect = {
            "cycle": int(cycle), "target_pc": redirect_pc, "source_pc": source_pc,
            "context_id": _safe_signal_int(getattr(dut, "probe_fetch_context", None)),
            "epoch_id": _safe_signal_int(getattr(dut, "probe_fetch_epoch", None)),
        }
        if not redirect_events or redirect_events[-1] != redirect:
            redirect_events.append(redirect)
    if not _fetch_transaction_ok(dut):
        return
    if hasattr(dut, "probe_fetch_pc"):
        pc_handle = dut.probe_fetch_pc
        accepted_by = "standardized_frontend"
    elif hasattr(dut, "imem_fetch_addr"):
        pc_handle = dut.imem_fetch_addr
        accepted_by = "direct_fetch"
    else:
        pc_handle = dut.core_addr
        accepted_by = "bus_handshake"
    raw_pc = _safe_signal_int(pc_handle)
    if raw_pc is None:
        return
    # A few wrappers (notably biriscv) expose a 64-bit instruction line while
    # the common bus address names only its low word.  Preserve both logical
    # instruction slots and tie them to one accepted transaction.  Consumers
    # can then see a control instruction in the high slot without mistaking
    # the low-slot fall-through from the same line for a prediction.
    if hasattr(dut, "probe_fetch_valid_hi") and _is_high(dut.probe_fetch_valid_hi):
        high_pc = _safe_signal_int(getattr(dut, "probe_fetch_pc_hi", None))
        low_addresses = (raw_pc,) if _is_high(dut.probe_fetch_valid) else ()
        slot_addresses = low_addresses + ((high_pc,) if high_pc is not None else ())
    else:
        wide_external_fetch = (
            hasattr(dut, "core_data_in_hi")
            and not hasattr(dut, "imem_fetch_addr")
            and not hasattr(dut, "probe_fetch_pc_hi")
        )
        slot_addresses = (raw_pc, raw_pc + 4) if wide_external_fetch else (raw_pc,)
    recorded = False
    explicit_transaction = _safe_signal_int(getattr(dut, "probe_fetch_transaction", None))
    transaction_id = str(explicit_transaction) if explicit_transaction is not None else f"{int(cycle)}:{int(raw_pc)}"
    squashed = _is_high(getattr(dut, "probe_fetch_squashed", 0))
    speculative = _is_high(getattr(dut, "probe_fetch_speculative", 0))
    context_id = _safe_signal_int(getattr(dut, "probe_fetch_context", None))
    epoch_id = _safe_signal_int(getattr(dut, "probe_fetch_epoch", None))
    for slot, slot_address in enumerate(slot_addresses):
        for candidate in _program_address_aliases(slot_address):
            for base in spec.base_addresses:
                offset = candidate - base
                is_loop = offset == spec.loop_offset
                if offset in spec.instructions or is_loop:
                    transaction = (int(cycle), int(raw_pc), int(offset))
                    if transaction in seen_transactions:
                        break
                    seen_transactions.add(transaction)
                    fetch_events.append({
                        "cycle": int(cycle),
                        "offset": int(offset),
                        "pc": int(slot_address),
                        "raw_pc": int(slot_address),
                        "canonical_pc": int(candidate),
                        "base_pc": int(base),
                        "accepted_by": accepted_by,
                        "transaction_id": transaction_id,
                        "transaction_slot": slot,
                        "squashed": squashed,
                        "speculative": speculative,
                        "context_id": context_id,
                        "epoch_id": epoch_id,
                        "terminal_loop": bool(is_loop),
                    })
                    recorded = True
                    break
            else:
                continue
            break
    if recorded:
        return
    if cycle < 25 and (_env_flag("CYCLE_DEBUG") or _env_flag("DEBUG_CYCLE")):
        dut._log.info("[forwarding] unmatched probe fetch cycle=%d raw_pc=%s probe=%s", cycle, raw_pc, spec.name)

def _record_probe_prediction(dut, cycle, spec, prediction_events):
    for suffix in ("", "_hi"):
        valid = getattr(dut, f"probe_prediction_valid{suffix}", None)
        if valid is None or not _is_high(valid):
            continue
        raw_pc = _safe_signal_int(getattr(dut, f"probe_prediction_pc{suffix}", None))
        taken = _safe_signal_int(getattr(dut, f"probe_prediction_taken{suffix}", None))
        raw_target = _safe_signal_int(getattr(dut, f"probe_prediction_target{suffix}", None))
        if raw_pc is None or (taken is None and raw_target is None):
            continue
        recorded = False
        for candidate in _program_address_aliases(raw_pc):
            for base in spec.base_addresses:
                offset = candidate - base
                if offset in spec.instructions:
                    target_offset = None
                    if raw_target is not None:
                        for target_candidate in _program_address_aliases(raw_target):
                            if target_candidate - base in spec.instructions or target_candidate - base == spec.loop_offset:
                                target_offset = int(target_candidate - base)
                                break
                    event = {
                        "cycle": int(cycle), "offset": int(offset),
                        "raw_pc": int(raw_pc),
                        "predicted_taken": bool(taken) if taken is not None else None,
                        "predicted_target": target_offset,
                        "source": "standardized_prediction" if not suffix else "standardized_prediction_hi",
                        "transaction_slot": 0 if not suffix else 1,
                        "context_id": _safe_signal_int(getattr(dut, f"probe_prediction_context{suffix}", None)),
                        "epoch_id": _safe_signal_int(getattr(dut, f"probe_prediction_epoch{suffix}", None)),
                    }
                    if event not in prediction_events[-2:]:
                        prediction_events.append(event)
                    recorded = True
                    break
            if recorded:
                break

def _record_probe_resolution(dut, cycle, spec, resolution_events):
    """Record an optional wrapper-standardized architectural branch decision."""
    if not hasattr(dut, "probe_resolution_valid") or not _is_high(dut.probe_resolution_valid):
        return
    raw_pc = _safe_signal_int(getattr(dut, "probe_resolution_pc", None))
    taken = _safe_signal_int(getattr(dut, "probe_resolution_taken", None))
    raw_target = _safe_signal_int(getattr(dut, "probe_resolution_target", None))
    if raw_pc is None or taken is None:
        return
    for candidate in _program_address_aliases(raw_pc):
        for base in spec.base_addresses:
            offset = candidate - base
            if offset not in spec.instructions:
                continue
            target_offset = None
            if raw_target is not None:
                for target_candidate in _program_address_aliases(raw_target):
                    candidate_offset = target_candidate - base
                    if candidate_offset in spec.instructions or candidate_offset == spec.loop_offset:
                        target_offset = int(candidate_offset)
                        break
            event = {
                "cycle": int(cycle), "offset": int(offset), "raw_pc": int(raw_pc),
                "actual_taken": bool(taken), "actual_target": target_offset,
                "context_id": _safe_signal_int(getattr(dut, "probe_resolution_context", None)),
                "epoch_id": _safe_signal_int(getattr(dut, "probe_resolution_epoch", None)),
                "source": "standardized_resolution",
            }
            if not resolution_events or resolution_events[-1] != event:
                resolution_events.append(event)
            return

def _aligned_interface_values(samples_by_cycle, reference_cycle, reference_offset, role_offsets):
    values = {}
    for role in ("write_enable", "write_addr", "write_data"):
        signal_cycle = reference_cycle + role_offsets.get(role, reference_offset) - reference_offset
        sample = samples_by_cycle.get(signal_cycle)
        if sample is None:
            return None
        values[role] = sample.get(role)
    return values

def _cycle_deltas(events):
    cycles = [event["cycle"] for event in sorted(events, key=lambda event: (event["cycle"], event.get("pc", 0)))]
    return [cycles[index] - cycles[index - 1] for index in range(1, len(cycles))]

def _is_pipeline_classification(pipeline):
    """Only a positive pipeline classification enables forwarding probing."""
    return isinstance(pipeline, dict)

async def _observe_probe_commits(
    dut, regfile, regfile_metadata, handles, spec, max_cycles=300,
    fetch_events=None, return_diagnostics=False, drain_cycles=8,
    require_fetched_completion=False, redirect_events=None, prediction_events=None,
    resolution_events=None, data_memory=None, memory_events=None,
    pipeline_observer=None,
):
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
    seen_fetch_transactions = set()
    loop_cycle = None
    cycles_used = 0
    memory_cursor = len(data_memory.transactions) if data_memory is not None else 0

    for cycle in range(max_cycles):
        cycles_used = cycle + 1
        if pipeline_observer is not None:
            await FallingEdge(dut.sys_clk)
            await Timer(0.001, unit="ns")
            pipeline_observer.sample(cycle, phase="pre_edge")
        await RisingEdge(dut.sys_clk)
        await Timer(0.001, unit="ns")
        if pipeline_observer is not None:
            pipeline_observer.sample(cycle, phase="post_edge")
        if data_memory is not None and memory_events is not None:
            new_transactions = data_memory.transactions[memory_cursor:]
            memory_events.extend({**item, "observed_cycle": cycle} for item in new_transactions)
            memory_cursor += len(new_transactions)
        _record_probe_fetch(
            dut, cycle, spec, fetch_events, seen_fetch_transactions,
            redirect_events=redirect_events,
        )
        if pipeline_observer is not None:
            pipeline_observer.note_fetch_events(fetch_events, cycle)
        if prediction_events is not None:
            _record_probe_prediction(dut, cycle, spec, prediction_events)
        if resolution_events is not None:
            _record_probe_resolution(dut, cycle, spec, resolution_events)
        if fetch_events and fetch_events[-1].get("cycle") == cycle:
            if fetch_events[-1].get("terminal_loop"):
                if loop_cycle is None:
                    loop_cycle = cycle
            else:
                # A terminal-loop fetch can be speculative wrong-path traffic.
                # Any later in-program fetch invalidates that candidate.
                loop_cycle = None

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
                fetched_offsets = {event.get("offset") for event in fetch_events}
                if (
                    entry is not None
                    and entry["offset"] not in seen_offsets
                    and (not require_fetched_completion or entry["offset"] in fetched_offsets)
                ):
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
                and (
                    not require_fetched_completion
                    or entry["offset"] in {event.get("offset") for event in fetch_events}
                )
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

        # Register-file observation cannot see a repeated write when reset does
        # not clear the destination. Once the terminal loop is reached and the
        # pipeline has drained, final architectural state is sufficient.
        if loop_cycle is not None and cycle - loop_cycle >= max(2, 2 * int(drain_cycles)):
            for entry in spec.entries():
                if entry["offset"] in seen_offsets:
                    continue
                value = _get_regfile_reg_value(regfile, entry["reg"], regfile_metadata)
                if value == (entry["value"] & 0xFFFFFFFF):
                    seen_offsets.add(entry["offset"])
                    commits.append({
                        "cycle": cycle,
                        "offset": entry["offset"],
                        "reg": entry["reg"],
                        "value": value,
                        "source": "terminal_state",
                    })
            break

    commits = sorted(commits, key=lambda event: event["offset"])
    complete = len(seen_offsets) == len(spec.expected_writes)
    diagnostics = {
        "complete": complete,
        "completion_method": (
            "write_observation" if complete and all(item["source"] != "terminal_state" for item in commits)
            else "terminal_loop_and_final_state" if complete
            else None
        ),
        "cycles_used": cycles_used,
        "cycle_budget": int(max_cycles),
        "timed_out": not complete and cycles_used >= int(max_cycles),
        "terminal_loop_observed": loop_cycle is not None,
        "terminal_loop_cycle": loop_cycle,
        "commits_observed": len(commits),
        "commits_expected": len(spec.expected_writes),
        "missing_offsets": sorted(
            entry["offset"] for entry in spec.entries() if entry["offset"] not in seen_offsets
        ),
    }
    return (commits, diagnostics) if return_diagnostics else commits

_STRONG_PREDICTION_EVIDENCE = {
    "explicit_prediction",
    "same_context_wrong_path_then_redirect",
    "pre_resolution_accepted_fetch",
}
