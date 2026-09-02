"""Datapath execution-model discovery."""

try:
    from ._discovery_shared import (
        Counter,
        CYCLE_SIGNATURE,
        NOP,
        RisingEdge,
        Timer,
        _addi,
        _jal,
        _aligned_interface_values,
        _cycle_deltas,
        _env_flag,
        _fetch_transaction_ok,
        _get_regfile_reg_value,
        _is_high,
        _load_regfile_metadata,
        _measurement_cycle_budget,
        _program_address_aliases,
        _resolve_write_interface,
        _safe_signal_int,
        json,
        logging,
        os,
        program_memory,
    )
except ImportError:
    from _discovery_shared import (
        Counter,
        CYCLE_SIGNATURE,
        NOP,
        RisingEdge,
        Timer,
        _addi,
        _jal,
        _aligned_interface_values,
        _cycle_deltas,
        _env_flag,
        _fetch_transaction_ok,
        _get_regfile_reg_value,
        _is_high,
        _load_regfile_metadata,
        _measurement_cycle_budget,
        _program_address_aliases,
        _resolve_write_interface,
        _safe_signal_int,
        json,
        logging,
        os,
        program_memory,
    )

NOP_INSTRUCTION = NOP
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
    SIGNATURE_BY_REG_VALUE.setdefault(
        (entry["reg"], entry["value"] & 0xFFFFFFFF), []
    ).append(entry)
SIGNATURE_LOOP_PC = 0xB0
prog = program_memory.image


def _cycle_program_instruction(address):
    return program_memory.read(address)

def _canonical_signature_pc(address):
    """Map a relocated fetch PC back to the signature's programmed offset."""
    for candidate in _program_address_aliases(address):
        if candidate in SIGNATURE_BY_PC:
            return candidate
    return None

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

def _derive_compatibility_labels(cycle_result):
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

async def test_datapath_structure(dut, regfile, regfile_discovery=None):
    """Measure, persist, and return the processor execution model."""
    del regfile_discovery
    dut._log.info("Measuring execution model from architectural commit cadence...")
    output_dir = os.environ.get("OUTPUT_DIR", "default")
    processor_name = os.path.basename(output_dir)
    regfile_path = getattr(regfile, "_path", None)
    regfile_metadata = _load_regfile_metadata(
        output_dir, processor_name, regfile_path=regfile_path,
    )
    measurement = await measure_execution_model(
        dut, regfile, core_name=processor_name, regfile_metadata=regfile_metadata,
    )
    multicycle, pipeline = _derive_compatibility_labels(measurement["cycle"])
    result = {**measurement, "multicycle": multicycle, "pipeline": pipeline}
    output_file = os.path.join(output_dir, f"{processor_name}_labels.json")
    try:
        with open(output_file, "r", encoding="utf-8") as json_file:
            existing_data = json.load(json_file)
    except (json.JSONDecodeError, OSError):
        existing_data = {}
    labels = existing_data.setdefault(processor_name, {})
    labels.update({
        "cycle": measurement["cycle"],
        "multicycle": multicycle,
        "pipeline": pipeline,
    })
    labels.pop("cycle_evidence", None)
    if _env_flag("CYCLE_DEBUG") or _env_flag("DEBUG_CYCLE"):
        labels["cycle_debug"] = measurement["cycle_debug"]
    else:
        labels.pop("cycle_debug", None)
    try:
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(existing_data, json_file, indent=4)
        dut._log.info("Datapath results saved to %s", output_file)
    except OSError as exc:
        logging.warning("Error writing datapath results: %s", exc)
    return result
