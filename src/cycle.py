import cocotb
import os
import json
import logging
import re
from collections import Counter
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
from regfile_finder import find_regfile_write_signals, load_regfile_interface


NOP_INSTRUCTION = 0x00000013


def _addi(rd, rs1, imm):
    return ((imm & 0xFFF) << 20) | ((rs1 & 0x1F) << 15) | (0 << 12) | ((rd & 0x1F) << 7) | 0x13


def _jal(rd, offset):
    bit20 = (offset >> 20) & 0x1
    bits10_1 = (offset >> 1) & 0x3FF
    bit11 = (offset >> 11) & 0x1
    bits19_12 = (offset >> 12) & 0xFF
    return (bit20 << 31) | (bits10_1 << 21) | (bit11 << 20) | (bits19_12 << 12) | ((rd & 0x1F) << 7) | 0x6F


# Straight-line execution signature. Each measured instruction writes a unique
# register/value pair exactly once, then the core parks in a self-loop after the
# measured window. Keep the signature away from regfile-finder loop addresses so
# cores without a real reset can still NOP-forward into this probe.
SIGNATURE_BASE_PC = 0x40
SIGNATURE_BASE_PCS = (SIGNATURE_BASE_PC, 0x200)
SIGNATURE_WRITE_TEMPLATES = [
    {"offset": 0x00, "reg": 5, "value": 0x135, "instruction": "addi x5, x0, 0x135"},
    {"offset": 0x04, "reg": 6, "value": 0x246, "instruction": "addi x6, x0, 0x246"},
    {"offset": 0x08, "reg": 7, "value": 0x357, "instruction": "addi x7, x0, 0x357"},
    {"offset": 0x0C, "reg": 8, "value": 0x468, "instruction": "addi x8, x0, 0x468"},
    {"offset": 0x10, "reg": 9, "value": 0x579, "instruction": "addi x9, x0, 0x579"},
    {"offset": 0x14, "reg": 10, "value": 0x68A, "instruction": "addi x10, x0, 0x68a"},
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
SIGNATURE_LOOP_PC = SIGNATURE_BASE_PC + 0x30

prog = {entry["pc"]: _addi(entry["reg"], 0, entry["value"]) for entry in SIGNATURE_ALIASED_WRITES}
for base_pc in SIGNATURE_BASE_PCS:
    prog[base_pc + 0x30] = _jal(0, 0)


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
        await Timer(0.001, unit="ns") # let signals settle
        cycle_count += 1
        
        # Always provide valid data based on current address
        addr_val = dut.core_addr.value
        if addr_val.is_resolvable:
            addr = addr_val.to_unsigned()
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
        await Timer(0.001, unit="ns") # let signals settle

        # Always provide data (0 for all loads)
        dut.data_mem_data_in.value = 0


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
    required = ["core_stb", "core_ack"]
    optional = ["core_cyc"]
    if any(not hasattr(dut, name) or not _is_high(getattr(dut, name)) for name in required):
        return False
    if any(hasattr(dut, name) and not _is_high(getattr(dut, name)) for name in optional):
        return False
    if hasattr(dut, "core_we") and _is_high(dut.core_we):
        return False
    return True


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


def _regfile_storage_index(arch_reg, regfile_metadata=None, regfile=None):
    depth = _infer_regfile_depth(regfile_metadata, regfile)
    if depth == 31:
        return arch_reg - 1 if 1 <= arch_reg <= 31 else None
    return arch_reg


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


def _signature_entry_for(reg, value, fetched_pcs=None, seen_commit_pcs=None):
    fetched_pcs = fetched_pcs or set()
    seen_commit_pcs = seen_commit_pcs or set()
    candidates = SIGNATURE_BY_REG_VALUE.get((reg, value & 0xFFFFFFFF), [])
    for entry in candidates:
        if entry["pc"] in fetched_pcs and entry["pc"] not in seen_commit_pcs:
            return entry
    for entry in candidates:
        if entry["pc"] not in seen_commit_pcs:
            return entry
    return None


def _record_signature_fetch(dut, cycle, fetch_events, seen_fetch_pcs):
    pc = _safe_signal_int(dut.core_addr)
    if pc in SIGNATURE_BY_PC and _fetch_transaction_ok(dut) and pc not in seen_fetch_pcs:
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


async def _observe_signature_commits_with_interface(dut, handles, max_cycles=300):
    dut._log.info("[measure] Observing signature commits through register-file interface")
    commit_events = []
    fetch_events = []
    seen_commit_pcs = set()
    seen_fetch_pcs = set()

    for cycle in range(max_cycles):
        await RisingEdge(dut.sys_clk)
        await Timer(0.001, unit="ns")

        _record_signature_fetch(dut, cycle, fetch_events, seen_fetch_pcs)

        if not _is_high(handles["write_enable"]):
            continue

        reg = _safe_signal_int(handles["write_addr"])
        value = _safe_signal_int(handles["write_data"])
        if reg is None or value is None:
            continue

        value &= 0xFFFFFFFF
        entry = _signature_entry_for(
            reg,
            value,
            fetched_pcs=seen_fetch_pcs,
            seen_commit_pcs=seen_commit_pcs,
        )
        if entry is None or entry["pc"] in seen_commit_pcs:
            continue

        seen_commit_pcs.add(entry["pc"])
        event = {
            "cycle": cycle,
            "pc": entry["pc"],
            "reg": reg,
            "value": value,
            "source": "interface",
        }
        commit_events.append(event)
        dut._log.info(
            "[measure] Commit %s at cycle %d: x%d = 0x%08x",
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
    confidence, penalties = _confidence_score(evidence)
    reason = "ambiguous cycle behavior"

    classification = {
        "single_cycle": None,
        "multicycle": None,
        "pipeline": None,
        "confidence": confidence,
    }

    if evidence["commits_observed"] < 3 or not commit_intervals:
        reason = "insufficient signature commits observed"
    elif evidence["mixed_commit_intervals"]:
        reason = "mixed architectural commit intervals observed"
    elif all(interval == 1 for interval in commit_intervals):
        if not latencies:
            reason = "one signature commit per cycle, but fetch-to-commit pairing is unavailable"
        elif all(latency == 0 for latency in latencies):
            classification["single_cycle"] = True
            classification["multicycle"] = False
            classification["pipeline"] = False
            reason = "one architectural commit per cycle with zero fetch-to-commit latency"
        elif (
            evidence["method"] == "regfile_observation"
            and evidence["interface_incomplete"]
            and evidence["raw_modal_latency"] == 2
            and not evidence["unstable_latency"]
        ):
            classification["single_cycle"] = True
            classification["multicycle"] = False
            classification["pipeline"] = False
            reason = (
                "one architectural commit per cycle with two raw observation cycles; "
                "treated as single-cycle behind registered instruction delivery"
            )
        elif all(latency > 0 for latency in latencies) and not evidence["unstable_latency"]:
            classification["single_cycle"] = False
            classification["multicycle"] = False
            pipeline = {
                "depth_estimate": evidence["depth_estimate"],
                "depth_estimate_source": evidence["depth_estimate_source"],
            }
            if evidence["raw_depth_estimate"] != evidence["depth_estimate"]:
                pipeline["raw_depth_estimate"] = evidence["raw_depth_estimate"]
            classification["pipeline"] = pipeline
            reason = "one architectural commit per cycle with stable nonzero fetch-to-commit latency"
        else:
            reason = "one architectural commit per cycle with unstable or mixed fetch-to-commit latencies"
    elif all(interval > 1 for interval in commit_intervals):
        classification["single_cycle"] = False
        classification["multicycle"] = True
        classification["pipeline"] = False
        reason = "architectural commits are spaced by multiple cycles"

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
    try:
        interface_handles = _resolve_write_interface(dut, core_name, regfile)
    except Exception as exc:
        dut._log.warning("[measure] Failed to resolve write interface: %s", exc)
        interface_incomplete = True

    if interface_handles:
        interface_timing_offset = interface_handles.get("_timing_offset", 0)
        fetch_events, commit_events = await _observe_signature_commits_with_interface(dut, interface_handles)
        method = "interface"
    else:
        interface_timing_offset = None
        fetch_events, commit_events = await _observe_signature_commits_from_regfile(
            dut,
            regfile,
            regfile_metadata=regfile_metadata,
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


async def test_pc_behavior(dut, regfile):
    # initialize driven signals
    dut.core_ack.value = 0
    dut.core_data_in.value = 0

    cocotb.start_soon(Clock(dut.sys_clk, 10, unit="ns").start())
    cocotb.start_soon(instr_mem_driver(dut))
    cocotb.start_soon(data_mem_driver(dut))  # For cores with separate data memory

    # Reset
    dut.rst_n.value = 0
    dut.core_ack.value = 0
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
