"""Forwarding and hazard-handling discovery."""

import time as _wall_time

try:
    from .forwarding_proof import enforce_forwarding_positive
    from ._discovery_shared import (
        CYCLE_SIGNATURE,
        DataMemory,
        FORWARDING_PROBES,
        PIPELINE_INTERFACE_DISCOVERY_VERSION,
        PipelineSignalObserver,
        CALIBRATION_LANDING_BASES,
        Timer,
        _cycle_deltas,
        _env_flag,
        _get_regfile_reg_value,
        _is_pipeline_classification,
        _load_optional_internal_data,
        _load_optional_internal_program,
        _load_regfile_metadata,
        _measurement_cycle_budget,
        _observe_probe_commits,
        _resolve_write_interface,
        consumer_stage_cycle,
        forwarding_probe_pair,
        json,
        median,
        os,
        pipeline_calibration_flow,
        pipeline_handshake_calibration,
        pipeline_relocation_landing,
        program_memory,
        store_to_load_hazard_probe,
        traceback,
        uuid,
        validate_frozen_forwarding_trials,
        write_pipeline_interface,
    )
except ImportError:
    from forwarding_proof import enforce_forwarding_positive
    from _discovery_shared import (
        CYCLE_SIGNATURE,
        DataMemory,
        FORWARDING_PROBES,
        PIPELINE_INTERFACE_DISCOVERY_VERSION,
        PipelineSignalObserver,
        CALIBRATION_LANDING_BASES,
        Timer,
        _cycle_deltas,
        _env_flag,
        _get_regfile_reg_value,
        _is_pipeline_classification,
        _load_optional_internal_data,
        _load_optional_internal_program,
        _load_regfile_metadata,
        _measurement_cycle_budget,
        _observe_probe_commits,
        _resolve_write_interface,
        consumer_stage_cycle,
        forwarding_probe_pair,
        json,
        median,
        os,
        pipeline_calibration_flow,
        pipeline_handshake_calibration,
        pipeline_relocation_landing,
        program_memory,
        store_to_load_hazard_probe,
        traceback,
        uuid,
        validate_frozen_forwarding_trials,
        write_pipeline_interface,
    )

FORWARDING_SCHEMA_VERSION = 2
FORWARDING_PROBE_SUITE_VERSION = "paired-forwarding-v8"
FORWARDING_IMPLEMENTATION_REVISION = 11
HAZARD_BASE_PC = FORWARDING_PROBES["alu_to_alu"].base_addresses[0]
HAZARD_BASE_PCS = FORWARDING_PROBES["alu_to_alu"].base_addresses
HAZARD_WRITE_TEMPLATE = [
    {
        **entry,
        "instruction": FORWARDING_PROBES["alu_to_alu"].instructions[entry["offset"]],
    }
    for entry in FORWARDING_PROBES["alu_to_alu"].entries()
]
hazard_prog = FORWARDING_PROBES["alu_to_alu"].image()


def _relocation_landing_record(spec, observation, details, accepted_raw_bases):
    """Summarize one relocation landing without trusting an assumed base."""
    requested_base = int(spec.calibration_requested_base)
    origin = int(spec.calibration_relocation_origin)
    control = spec.control_flow or {}
    fetches = [
        item for item in details.get("fetch_events", ())
        if not item.get("terminal_loop") and not item.get("squashed")
    ]
    entry = next((
        item for item in fetches if item.get("offset") == origin
    ), None)
    source_fetch = next((
        item for item in fetches
        if item.get("offset") == control.get("redirect_offset")
    ), None)
    target_fetch = next((
        item for item in fetches
        if item.get("offset") == control.get("target_offset")
    ), None)
    source_seen = source_fetch is not None
    target_seen = target_fetch is not None
    wrong_fetches = [
        item for item in fetches
        if item.get("offset") in set(
            control.get("wrong_path_offsets", ())
        )
    ]
    wrong_seen = bool(wrong_fetches)
    target_cycle = (
        None if target_fetch is None else target_fetch.get("cycle")
    )
    wrong_after_redirect_resolution = any(
        target_cycle is not None
        and item.get("cycle") is not None
        and int(item["cycle"]) >= int(target_cycle)
        for item in wrong_fetches
    )
    observed_raw_base = (
        None if entry is None else int(entry.get("raw_pc", entry.get("pc")))
    )
    alias_of = next((
        base for base in accepted_raw_bases
        if observed_raw_base is not None and int(base) == observed_raw_base
    ), None)
    accepted = bool(
        observation.get("architectural_complete") is True
        and entry is not None
        and source_seen and target_seen
        and not wrong_after_redirect_resolution
        and alias_of is None
    )
    if not observation.get("architectural_complete"):
        reason = "architectural_completion"
    elif entry is None:
        reason = "requested_base_not_fetched"
    elif (
        not source_seen or not target_seen
        or wrong_after_redirect_resolution
    ):
        reason = "redirect"
    elif alias_of is not None:
        reason = "instruction_address_alias"
    else:
        reason = None
    return {
        "landing_index": spec.calibration_landing_index,
        "requested_base": requested_base,
        "observed_raw_base": observed_raw_base,
        "redirect_source": {
            "expected_pc": requested_base
            + int(control.get("redirect_offset", origin)) - origin,
            "observed_pc": (
                None if source_fetch is None
                else source_fetch.get(
                    "raw_pc", source_fetch.get("pc")
                )
            ),
        },
        "redirect_target": {
            "expected_pc": requested_base
            + int(control.get("target_offset", origin)) - origin,
            "observed_pc": (
                None if target_fetch is None
                else target_fetch.get(
                    "raw_pc", target_fetch.get("pc")
                )
            ),
        },
        "entry_fetch_observed": entry is not None,
        "redirect_source_observed": source_seen,
        "redirect_target_observed": target_seen,
        "wrong_path_observed": wrong_seen,
        "wrong_path_after_redirect_resolution": (
            wrong_after_redirect_resolution
        ),
        "architectural_complete": bool(
            observation.get("architectural_complete")
        ),
        "alias_of_observed_raw_base": alias_of,
        "alias_outcome": (
            "unique" if alias_of is None and observed_raw_base is not None
            else "aliased" if alias_of is not None else "unobserved"
        ),
        "completion_marker": {
            "register": spec.expected_writes[-1].register,
            "value": spec.expected_writes[-1].value,
            "state": (
                observation.get("calibration_signature", {})
                .get("completion_marker", {})
                .get("state")
            ),
        },
        "accepted": accepted,
        "rejection_reason": reason,
    }


def _forwarding_execution_record(state, run_id=None, **details):
    record = {
        "state": state,
        "run_id": run_id or str(uuid.uuid4()),
        "debug_enabled": _env_flag("CYCLE_DEBUG") or _env_flag("DEBUG_CYCLE"),
    }
    record.update(details)
    return record

def _write_label_sections(labels_file, processor_name, sections, remove=()):
    """Atomically update selected label sections while preserving all others."""
    try:
        with open(labels_file, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        data = {}
    labels = data.setdefault(processor_name, {})
    labels.update(sections)
    for key in remove:
        labels.pop(key, None)
    temporary = f"{labels_file}.tmp"
    with open(temporary, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    os.replace(temporary, labels_file)


def _write_forwarding_progress(
    output_dir, processor_name, phase, **details,
):
    """Atomically refresh the per-core watchdog heartbeat."""
    path = os.path.join(
        output_dir, f"{processor_name}_analysis_progress.json",
    )
    previous = {}
    try:
        with open(path, "r", encoding="utf-8") as stream:
            previous = json.load(stream)
    except Exception:
        pass
    record = {
        "implementation_revision": FORWARDING_IMPLEMENTATION_REVISION,
        "processor": processor_name,
        "phase": phase,
        "sequence": int(previous.get("sequence", 0)) + 1,
        "updated_at_unix": _wall_time.time(),
        **details,
    }
    temporary = f"{path}.tmp"
    with open(temporary, "w", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2)
    os.replace(temporary, path)
    return record

def _evaluate_calibration_signature(spec, regfile, regfile_metadata, data_memory):
    """Evaluate calibration from final architectural state, not transient commits."""
    registers = []
    unavailable_registers = 0
    mismatch = False
    for entry in spec.entries():
        observed = _get_regfile_reg_value(regfile, entry["reg"], regfile_metadata)
        state = (
            "unobservable" if observed is None
            else "matched" if (int(observed) & 0xFFFFFFFF) == (int(entry["value"]) & 0xFFFFFFFF)
            else "mismatched"
        )
        unavailable_registers += state == "unobservable"
        mismatch |= state == "mismatched"
        registers.append({
            "offset": entry["offset"], "register": entry["reg"],
            "expected": int(entry["value"]) & 0xFFFFFFFF,
            "observed": None if observed is None else int(observed) & 0xFFFFFFFF,
            "role": entry["role"], "state": state,
        })

    completion = next((item for item in registers if item["role"] == "completion"), None)
    poison_checks = []
    for observation in getattr(spec, "operand_observations", ()):
        if observation.role != "wrong_path_poison" or observation.destination_register is None:
            continue
        observed = _get_regfile_reg_value(
            regfile, observation.destination_register, regfile_metadata,
        )
        poison = None if observation.result_value is None else int(observation.result_value) & 0xFFFFFFFF
        state = (
            "unobservable" if observed is None
            else "mismatched" if (int(observed) & 0xFFFFFFFF) == poison
            else "matched"
        )
        unavailable_registers += state == "unobservable"
        mismatch |= state == "mismatched"
        poison_checks.append({
            "register": observation.destination_register,
            "poison": poison,
            "observed": None if observed is None else int(observed) & 0xFFFFFFFF,
            "state": state,
        })

    memory = {"state": "not_required"}
    if getattr(spec, "expected_store_address", None) is not None:
        if data_memory.supported:
            address = int(spec.expected_store_address) & ~3
            observed = data_memory.words.get(address)
            expected = int(spec.expected_store_value) & 0xFFFFFFFF
            state = "matched" if observed == expected else "mismatched"
            mismatch |= state == "mismatched"
            memory = {
                "state": state, "address": address, "expected": expected,
                "observed": observed,
            }
        else:
            memory = {"state": "unobservable"}

    completion_observable = bool(
        completion is not None and completion.get("state") != "unobservable"
    )
    if mismatch:
        state = "failed"
    elif not completion_observable:
        state = "unavailable"
    else:
        # A readable completion marker plus no observable mismatch establishes
        # architectural completion.  Registers that the selected regfile view
        # cannot read, and an unavailable memory view, reduce capability
        # coverage rather than changing a correct signature into a partial run.
        state = "completed"
    sections = {}
    for section_name, definition in getattr(
        spec, "calibration_sections", {}
    ).items():
        offsets = set(definition.get("register_offsets", ()))
        section_registers = [
            item for item in registers if item.get("offset") in offsets
        ]
        section_poison = (
            poison_checks if definition.get("poison_required") else []
        )
        section_memory = (
            memory if definition.get("memory_required")
            else {"state": "not_required"}
        )
        states = [
            item.get("state") for item in (*section_registers, *section_poison)
        ]
        if section_memory.get("state") != "not_required":
            states.append(section_memory.get("state"))
        if any(item == "mismatched" for item in states):
            section_state = "failed"
        elif not states or all(item == "unobservable" for item in states):
            section_state = "unavailable"
        elif any(item == "unobservable" for item in states):
            section_state = "partial"
        else:
            section_state = "completed"
        sections[section_name] = {
            "state": section_state,
            "registers": section_registers,
            "memory": section_memory,
            "wrong_path_poison": section_poison,
            "failures": [
                {
                    "kind": "register", "register": item.get("register"),
                    "offset": item.get("offset"), "state": item.get("state"),
                }
                for item in section_registers
                if item.get("state") != "matched"
            ] + [
                {
                    "kind": "poison", "register": item.get("register"),
                    "state": item.get("state"),
                }
                for item in section_poison
                if item.get("state") != "matched"
            ] + (
                [{
                    "kind": "memory",
                    "state": section_memory.get("state"),
                    "address": section_memory.get("address"),
                }]
                if section_memory.get("state") not in {
                    "not_required", "matched",
                } else []
            ),
        }
    return {
        "state": state,
        "variant": getattr(spec, "calibration_variant", None),
        "kind": getattr(spec, "calibration_kind", None),
        "completion_marker": completion or {"state": "unobservable"},
        "registers": registers,
        "memory": memory,
        "wrong_path_poison": poison_checks,
        "sections": sections,
        "unobservable_register_count": int(unavailable_registers),
    }

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

    if name in (
        "alu_to_store_data", "alu_to_store_address",
        "load_to_store_data", "load_to_store_address",
    ):
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
    if name in (
        "alu_to_store_data", "alu_to_store_address",
        "load_to_store_data", "load_to_store_address",
    ):
        store = _matching_store_transaction(spec, transactions)
        return None if store is None else store["cycle"] - fetch["cycle"]
    commit = next((item for item in commits if item.get("role") == "consumer"), None)
    return None if commit is None else commit["cycle"] - fetch["cycle"]

def _matching_store_transaction(spec, transactions):
    expected_address = getattr(spec, "expected_store_address", None)
    expected_value = getattr(spec, "expected_store_value", None)
    return next((
        item for item in transactions
        if item.get("kind") == "store"
        and (expected_address is None or item.get("address") == expected_address)
        and (expected_value is None or item.get("value") == (expected_value & 0xFFFFFFFF))
    ), None)

def _store_transaction_observation(spec, transactions, interface_available):
    """Separate a program finishing from observing and validating its store."""
    expected_address = getattr(spec, "expected_store_address", None)
    expected_value = getattr(spec, "expected_store_value", None)
    stores = [item for item in transactions if item.get("kind") == "store"]
    matching = _matching_store_transaction(spec, transactions)
    observed = stores[0] if stores else None
    return {
        "transaction_interface_available": bool(interface_available),
        "transaction_observable": bool(interface_available and stores),
        "store_request_observed": bool(stores),
        "matching_store_observed": matching is not None,
        "store_correct": None if not stores else matching is not None,
        "store_address_correct": None if observed is None or expected_address is None else (
            observed.get("address") == expected_address
        ),
        "store_value_correct": None if observed is None or expected_value is None else (
            observed.get("value") == (expected_value & 0xFFFFFFFF)
        ),
        "observed_store": observed,
    }

def _forwarding_overlap_observation(name, spec, fetch_events, commits, transactions):
    """Identify whether the consumer entered the pipe before producer availability."""
    consumer_fetch = next((
        item.get("cycle") for item in fetch_events
        if item.get("offset") == spec.consumer_offset
    ), None)
    producer_commit = next((
        item.get("cycle") for item in commits
        if item.get("role") in ("producer", "address_producer")
    ), None)
    load_response = next((
        item.get("cycle") for item in transactions if item.get("kind") == "load"
    ), None)
    # A load response makes the value available inside the memory pipeline, but
    # it is not yet architecturally available through the register file. Stage-
    # aware forwarding requirements must therefore compare against writeback.
    producer_available = producer_commit
    availability_source = "producer_commit" if producer_commit is not None else None

    if name in (
        "alu_to_store_data", "alu_to_store_address",
        "load_to_store_data", "load_to_store_address",
    ):
        store = _matching_store_transaction(spec, transactions)
        if store is None:
            store = next((item for item in transactions if item.get("kind") == "store"), None)
        consumer_effect = None if store is None else store.get("cycle")
        store_request = consumer_effect
    else:
        consumer = next((item for item in commits if item.get("role") == "consumer"), None)
        consumer_effect = None if consumer is None else consumer.get("cycle")
        store_request = None
    completion = next((item for item in commits if item.get("role") == "completion"), None)

    if consumer_fetch is None or producer_available is None:
        overlap = "unobservable"
    elif consumer_fetch < producer_available:
        overlap = "overlapped"
    elif consumer_fetch > producer_available:
        overlap = "producer_available_before_consumer"
    else:
        overlap = "same_cycle"
    return {
        "producer_commit_cycle": producer_commit,
        "load_response_cycle": load_response,
        "producer_available_cycle": producer_available,
        "producer_architectural_availability_cycle": producer_commit,
        "producer_internal_result_cycle": load_response if name.startswith("load_to_") else producer_commit,
        "producer_availability_source": availability_source,
        "consumer_fetch_cycle": consumer_fetch,
        "consumer_effect_cycle": consumer_effect,
        "store_request_cycle": store_request,
        "completion_marker_cycle": None if completion is None else completion.get("cycle"),
        "producer_consumer_overlap": overlap,
    }

def _forwarding_required_stage(name):
    if name.endswith("store_data"):
        return "memory"
    return "execute"

def _forwarding_required_use(name):
    if name.endswith("store_data"):
        return "store_data"
    if name.endswith("store_address"):
        return "store_address"
    return "execute"

def _missing_forwarding_proof(reason):
    text = str(reason or "").lower()
    if "lane" in text or "slot" in text:
        return "lane_identity"
    if "availability" in text or "writeback" in text:
        return "producer_availability"
    if "source-id" in text or "source id" in text:
        return "source_id"
    if "transaction" in text or "store request" in text:
        return "transaction_association"
    if "phase" in text or "same cycle" in text or "ordering" in text:
        return "phase_ordering"
    if "operand" in text or "capture" in text:
        return "operand_capture"
    return "stage_token"

def _enrich_forwarding_requirement(name, trial, interface):
    """Attach stage-aware evidence that the RAW value was needed pre-writeback."""
    required_role = _forwarding_required_stage(name)
    required_use = _forwarding_required_use(name)
    consumer_cycle, stage = consumer_stage_cycle(
        interface,
        trial.get("pipeline_trial_id"),
        trial.get("consumer_offset"),
        required_role,
    )
    available_cycle = trial.get(
        "producer_architectural_availability_cycle",
        trial.get("producer_available_cycle"),
    )
    quality = (stage or {}).get("evidence_quality")
    trial_id = str(trial.get("pipeline_trial_id"))
    requirement_event = (
        interface.get("requirement_observations", {}).get(trial_id, {}).get(required_use)
    )
    role_evidence = interface.get("role_evidence", {}).get(
        required_use, {}
    )
    path_role_evidence_state = (
        (
            requirement_event.get("role_evidence_state", "confirmed")
            if requirement_event is not None else None
        )
    )
    availability_event = interface.get("producer_availability_observations", {}).get(trial_id)
    lane_unresolved = bool(
        interface.get("capabilities", {}).get("multi_lane")
        and not (requirement_event or {}).get("lane_identity_confirmed")
    )
    same_cycle_ordering = None
    if lane_unresolved:
        required = None
        observation = "consumer operand lane could not be bound to the fetched superscalar slot"
    elif (
        requirement_event is not None
        and availability_event is not None
        and path_role_evidence_state == "confirmed"
    ):
        requirement_order = (
            int(requirement_event["cycle"]), int(requirement_event.get("phase_order", 1))
        )
        availability_order = (
            int(availability_event["cycle"]), int(availability_event.get("phase_order", 1))
        )
        if requirement_order < availability_order:
            required = True
            same_cycle_ordering = (
                "consumer_before_writeback" if requirement_order[0] == availability_order[0]
                else "consumer_before_architectural_availability"
            )
            observation = "validated operand capture preceded producer architectural availability"
        elif requirement_order > availability_order:
            required = False
            same_cycle_ordering = (
                "writeback_before_consumer" if requirement_order[0] == availability_order[0]
                else "producer_available_before_consumer"
            )
            observation = "producer was architecturally available before validated operand capture"
        else:
            required = None
            same_cycle_ordering = "same_phase_ambiguous"
            observation = "operand capture and architectural availability share one sampling phase"
    elif consumer_cycle is None or available_cycle is None:
        required = None
        observation = (
            f"the {required_role} consumer stage or producer availability was not observable"
        )
        if role_evidence.get("rejection_reason"):
            observation += (
                "; role-local discovery: "
                + role_evidence["rejection_reason"]
            )
    elif consumer_cycle < available_cycle:
        required = None
        observation = (
            f"PC timing places the consumer in {required_role} at cycle {consumer_cycle} "
            f"before producer architectural availability at cycle {available_cycle}, but "
            "no validated operand capture establishes use ordering"
        )
    elif consumer_cycle > available_cycle:
        required = None
        observation = (
            f"PC timing places producer availability at cycle {available_cycle} before "
            f"consumer {required_role} entry at cycle {consumer_cycle}, but no validated "
            "operand capture establishes use ordering"
        )
    else:
        required = None
        observation = (
            f"producer availability and consumer {required_role} entry were both cycle "
            f"{consumer_cycle}; ordering is ambiguous"
        )
    trial.update({
        "consumer_required_stage": required_role,
        "consumer_required_stage_cycle": consumer_cycle,
        "forwarding_required": required,
        "requirement_observation": observation,
        "observation_source": (
            "lane_ambiguous" if lane_unresolved
            else "dynamic_operand_capture"
            if requirement_event is not None and availability_event is not None
            else "dynamic_pipeline_stage" if stage else "fetch_commit_fallback"
        ),
        "evidence_quality": (
            "ambiguous_lane" if lane_unresolved
            else "operand_phase_correlated"
            if requirement_event is not None and availability_event is not None
            else quality or "fetch_commit_only"
        ),
        "stage_pc_path": (stage or {}).get("pc_path"),
        "stage_valid_path": (stage or {}).get("valid_path"),
        "stage_instruction_path": (stage or {}).get("instruction_path"),
        "producer_availability_event": availability_event,
        "consumer_requirement_event": requirement_event,
        "same_cycle_ordering": same_cycle_ordering,
        "operand_value_observed": None if requirement_event is None else requirement_event.get("value"),
        "operand_path": None if requirement_event is None else requirement_event.get("path"),
        "source_id_path": None if requirement_event is None else requirement_event.get("source_id_path"),
        "operand_packed_slice": (
            None if requirement_event is None
            else requirement_event.get("packed_slice")
        ),
        "source_id_packed_slice": (
            None if requirement_event is None
            else requirement_event.get("source_id_packed_slice")
        ),
        "source_selector_lag": (
            None if requirement_event is None
            else requirement_event.get("source_selector_lag")
        ),
        "fetch_token": None if requirement_event is None else requirement_event.get("fetch_token"),
        "memory_epoch_id": None if requirement_event is None else requirement_event.get("memory_epoch_id"),
        "memory_transaction_id": None if requirement_event is None else requirement_event.get("memory_transaction_id"),
        "lane_id": None if requirement_event is None else requirement_event.get("lane_id"),
        "fetch_slot": None if requirement_event is None else requirement_event.get("fetch_slot"),
        "stage_token": None if requirement_event is None else requirement_event.get("stage_token"),
        "consumer_token_proof": (
            False if requirement_event is None
            else requirement_event.get("consumer_token_proof") is True
        ),
        "source_selector_validation": (
            False if requirement_event is None
            else requirement_event.get("source_selector_validation") is True
        ),
        "operand_differential_validation": (
            False if requirement_event is None
            else requirement_event.get(
                "operand_differential_validation"
            ) is True
        ),
        "semantic_discriminators_passed": (
            False if requirement_event is None
            else requirement_event.get(
                "semantic_discriminators_passed"
            ) is True
        ),
        "consumer_request_event": None if requirement_event is None else requirement_event.get("request_event"),
        "requirement_evidence_source": (
            "operand_capture_and_architectural_transition"
            if requirement_event is not None and availability_event is not None
            else "stage_and_commit_timing" if stage else "fetch_commit_fallback"
        ),
        "role_evidence_state": path_role_evidence_state,
        "path_role_evidence_state": path_role_evidence_state,
        "aggregate_role_evidence_state": role_evidence.get("state"),
        "requirement_rejection_reason": role_evidence.get(
            "rejection_reason"
        ) if requirement_event is None else (
            None if path_role_evidence_state == "confirmed"
            else "the selected per-trial operand chain was not confirmed"
        ),
    })
    return trial

def _forwarding_event_trace(fetch_events, commits, transactions):
    """Build a compact cycle-ordered trace for forwarding regression audits."""
    trace = []
    for item in fetch_events:
        trace.append({"event": "fetch", **item})
    for item in commits:
        trace.append({"event": "signature_commit", **item})
    for item in transactions:
        event = "store_request" if item.get("kind") == "store" else "load_response"
        trace.append({"event": event, **item})
    return sorted(trace, key=lambda item: (item.get("cycle", -1), item["event"]))

def _timing_series(trials):
    return [item["latency"] for item in trials if item.get("latency") is not None]

def _compact_forwarding_trial(item):
    """Keep audit-grade evidence without retaining a full simulator trace."""
    keys = (
        "latency", "architectural_complete", "dependency_correct",
        "transaction_interface_available", "transaction_observable",
        "store_request_observed", "matching_store_observed",
        "store_correct", "store_address_correct", "store_value_correct",
        "store_absence_architecturally_observable", "producer_available_cycle",
        "producer_architectural_availability_cycle", "producer_internal_result_cycle",
        "producer_availability_source", "producer_commit_cycle",
        "load_response_cycle", "consumer_fetch_cycle", "consumer_effect_cycle",
        "store_request_cycle", "completion_marker_cycle",
        "producer_consumer_overlap", "observed_store",
        "consumer_required_stage", "consumer_required_stage_cycle",
        "forwarding_required", "requirement_observation",
        "observation_source", "evidence_quality", "stage_pc_path",
        "stage_valid_path", "stage_instruction_path",
        "producer_availability_event", "consumer_requirement_event",
        "same_cycle_ordering", "operand_value_observed", "operand_path",
        "source_id_path", "requirement_evidence_source",
        "fetch_token", "memory_epoch_id", "memory_transaction_id",
        "lane_id", "fetch_slot", "stage_token", "consumer_request_event",
        "role_evidence_state", "requirement_rejection_reason",
        "path_role_evidence_state", "aggregate_role_evidence_state",
        "consumer_token_proof", "source_selector_validation",
        "operand_differential_validation",
        "semantic_discriminators_passed",
        "forwarding_gap", "spacer_kind", "filler_registers",
        "filler_values", "operand_packed_slice",
        "source_id_packed_slice", "source_selector_lag",
        "source_stage_path", "operand_stage_path", "joining_edge",
        "residence_relative_position",
    )
    return {key: item.get(key) for key in keys}

def _compact_forwarding_experiment(dependent, control):
    return {
        "dependent": [_compact_forwarding_trial(item) for item in dependent],
        "control": [_compact_forwarding_trial(item) for item in control],
    }

def _all_or_unknown(values):
    """Return a tri-state aggregate for architectural correctness evidence."""
    values = list(values)
    if values and all(value is True for value in values):
        return True
    if values and all(value is False for value in values):
        return False
    return None

def _paired_trials_need_extension(dependent, control):
    """Use five trials when the initial three do not produce identical evidence."""
    for trials in (dependent, control):
        latencies = _timing_series(trials)
        completions = [item.get("architectural_complete", item.get("complete", False)) for item in trials]
        correctness = [item.get("dependency_correct", item.get("complete", False)) for item in trials]
        observability = [item.get("transaction_observable") for item in trials]
        overlap = [item.get("producer_consumer_overlap") for item in trials]
        signatures = [
            (
                (item.get("observed_store") or {}).get("address"),
                (item.get("observed_store") or {}).get("value"),
                item.get("store_absence_architecturally_observable"),
            )
            for item in trials
        ]
        if (
            len(latencies) != len(trials)
            or len(set(latencies)) > 1
            or len(set(completions)) > 1
            or len(set(correctness)) > 1
            or len(set(observability)) > 1
            or len(set(overlap)) > 1
            or len(set(signatures)) > 1
        ):
            return True
    penalties = [d["latency"] - c["latency"] for d, c in zip(dependent, control)]
    return len(set(penalties)) > 1

def _paired_stage_evidence_needs_extension(dependent, control):
    """Escalate only when the frozen exact chain is internally unstable."""
    for trials in (dependent, control):
        exact = [_trial_exact_proof_complete(item) for item in trials]
        if any(exact) and not all(exact):
            return True
        signatures = {
            _chain_signature(item)
            for item, complete in zip(trials, exact) if complete
        }
        if len(signatures) > 1:
            return True
    return False

def _independent_sweep_limit(pipeline_depth):
    """Always cover gaps 1-2, then use the depth-derived bound up to gap 8."""
    try:
        depth = int(pipeline_depth)
    except (TypeError, ValueError):
        depth = 4
    return min(max(2, depth + 1), 8)


def _trial_exact_proof_complete(trial):
    return all(
        trial.get(field) is True
        for field in (
            "consumer_token_proof",
            "source_selector_validation",
            "operand_differential_validation",
            "semantic_discriminators_passed",
        )
    )


def _independent_gap_settled(dependent):
    """A stop-eligible gap proves writeback precedes exact operand capture."""
    return bool(
        len(dependent) >= 3
        and all(
            item.get("architectural_complete", item.get("complete", False))
            and item.get("dependency_correct", item.get("complete", False))
            and item.get("forwarding_required") is False
            and _trial_exact_proof_complete(item)
            for item in dependent
        )
    )


def _advance_independent_sweep(consecutive_available, gap, dependent):
    consecutive = (
        int(consecutive_available) + 1
        if _independent_gap_settled(dependent) else 0
    )
    return consecutive, bool(int(gap) >= 2 and consecutive >= 2)


def _architectural_failure_signature(trial):
    if trial.get(
        "architectural_complete", trial.get("complete", False)
    ):
        return None
    for key in (
        "architectural_failure_reason", "failure_reason",
        "termination_reason", "calibration_error_type",
    ):
        if trial.get(key):
            return f"{key}:{trial[key]}"
    if trial.get("dependency_correct") is False:
        return "dependency_correct:false"
    if trial.get("store_request_observed") is False:
        return "store_request_observed:false"
    return "architectural_completion:false"


def _architectural_gap_failure(dependent, control):
    """Describe a paired architectural failure that can gate later gaps."""
    trials = [*dependent, *control]
    if len(dependent) < 3 or len(control) < 3:
        return None
    signatures = [
        _architectural_failure_signature(item) for item in trials
    ]
    if any(signature is None for signature in signatures):
        return None
    categories = sorted(set(signatures))
    monotonic = bool(all(
        item.get("architectural_failure_monotonic") is True
        or item.get("program_construction_valid") is False
        for item in trials
    ))
    return {
        "category": (
            categories[0] if len(categories) == 1
            else "mixed_architectural_failure"
        ),
        "categories": categories,
        "affected_variants": sorted({
            item.get("variant") for item in trials
            if item.get("variant") is not None
        }),
        "monotonic": monotonic,
    }


def _chain_signature(trial):
    packed = trial.get("operand_packed_slice")
    source_packed = trial.get("source_id_packed_slice")
    requirement = trial.get("consumer_requirement_event") or {}
    exact_stage = (
        requirement.get("stage_token")
        or trial.get("stage_token")
        or {}
    )
    stage_identity = (
        exact_stage.get("path")
        or exact_stage.get("signal_kind")
        or exact_stage.get("source")
    )
    return (
        (
            f"@{stage_identity}" if stage_identity
            and not exact_stage.get("path") else stage_identity
        )
        or trial.get("stage_pc_path"),
        trial.get("source_id_path"),
        trial.get("operand_path"),
        trial.get("source_stage_path"),
        trial.get("operand_stage_path"),
        json.dumps(trial.get("joining_edge"), sort_keys=True),
        json.dumps(source_packed, sort_keys=True),
        json.dumps(packed, sort_keys=True),
        requirement.get(
            "phase", trial.get("same_cycle_ordering")
        ),
        trial.get("lane_id"),
    )


def _summarize_independent_distance_sweep(
    independent, adjacent, relaxed, pipeline_depth, policy=None,
):
    independent = independent or {}
    policy = dict(policy or {})
    gap_records = []
    all_signatures = {
        _chain_signature(item)
        for trials in adjacent for item in trials
        if _trial_exact_proof_complete(item)
    }
    complete_group_count = 0
    exact_group_count = 0
    for gap in sorted(independent):
        dependent, control = independent[gap]
        dep_timing = _timing_series(dependent)
        ctl_timing = _timing_series(control)
        complete = bool(
            len(dependent) >= 3 and len(control) >= 3
            and all(
                item.get(
                    "architectural_complete", item.get("complete", False)
                )
                and item.get(
                    "dependency_correct", item.get("complete", False)
                )
                for item in (*dependent, *control)
            )
        )
        exact = bool(
            complete
            and all(_trial_exact_proof_complete(item)
                    for item in (*dependent, *control))
        )
        requirements = [
            item.get("forwarding_required") for item in dependent
        ]
        requirement_state = (
            "required" if requirements and all(value is True for value in requirements)
            else "available_before_use"
            if requirements and all(value is False for value in requirements)
            else "unresolved"
        )
        signatures = {
            _chain_signature(item) for item in (*dependent, *control)
            if _trial_exact_proof_complete(item)
        }
        lags = [
            item.get("source_selector_lag")
            for item in (*dependent, *control)
            if item.get("source_selector_lag") is not None
        ]
        bounded_lag = bool(lags and all(abs(int(value)) <= 1 for value in lags))
        penalty = (
            median(dep_timing) - median(ctl_timing)
            if len(dep_timing) == len(dependent)
            and len(ctl_timing) == len(control)
            else None
        )
        complete_group_count += int(complete)
        exact_group_count += int(exact)
        all_signatures.update(signatures)
        gap_records.append({
            "gap": int(gap),
            "spacer_kind": "independent",
            "variant_count": min(len(dependent), len(control)),
            "architectural_dependency_handled": complete,
            "dependent_trials": dep_timing,
            "control_trials": ctl_timing,
            "raw_penalty_cycles": penalty,
            "requirement_state": requirement_state,
            "exact_proof_complete": exact,
            "exact_proof_coverage": {
                "matched": sum(
                    _trial_exact_proof_complete(item)
                    for item in (*dependent, *control)
                ),
                "eligible": len(dependent) + len(control),
            },
            "bounded_token_relative_lag": bounded_lag,
            "chain_signature_count": len(signatures),
            "architectural_gap_failure": (
                _architectural_gap_failure(dependent, control)
            ),
            "experiments": _compact_forwarding_experiment(
                dependent, control
            ),
        })
    tested_gaps = [item["gap"] for item in gap_records]
    fixed_chain = bool(len(all_signatures) == 1 and all_signatures)
    minimum_coverage = tested_gaps[:2] == [1, 2]
    all_groups_valid = bool(
        gap_records
        and complete_group_count == len(gap_records)
        and exact_group_count == len(gap_records)
        and all(item["bounded_token_relative_lag"] for item in gap_records)
        and fixed_chain
    )
    corroboration_state = (
        "validated" if minimum_coverage and all_groups_valid
        else "incomplete"
    )
    adjacent_dependent, adjacent_control = adjacent
    adjacent_requirements = [
        item.get("forwarding_required") for item in adjacent_dependent
    ]
    adjacent_exact = bool(
        adjacent_dependent
        and all(_trial_exact_proof_complete(item)
                for item in adjacent_dependent)
    )
    adjacent_requirement_state = (
        "required"
        if adjacent_requirements
        and all(value is True for value in adjacent_requirements)
        and adjacent_exact
        else "available_before_use"
        if adjacent_requirements
        and all(value is False for value in adjacent_requirements)
        and adjacent_exact
        else "unresolved"
    )
    adjacent_dep_timing = _timing_series(adjacent_dependent)
    adjacent_ctl_timing = _timing_series(adjacent_control)
    adjacent_penalty = (
        median(adjacent_dep_timing) - median(adjacent_ctl_timing)
        if len(adjacent_dep_timing) == len(adjacent_dependent)
        and len(adjacent_ctl_timing) == len(adjacent_control)
        else None
    )
    required_gaps = [
        item["gap"] for item in gap_records
        if item["requirement_state"] == "required"
        and item["exact_proof_complete"]
        and item["bounded_token_relative_lag"]
    ]
    if adjacent_requirement_state == "required":
        required_gaps.append(0)
    last_required = max(required_gaps, default=None)
    first_available = min((
        item["gap"] for item in gap_records
        if item["requirement_state"] == "available_before_use"
        and item["exact_proof_complete"]
        and item["bounded_token_relative_lag"]
    ), default=None)
    first_penalty_disappeared = min((
        item["gap"] for item in gap_records
        if adjacent_penalty is not None and adjacent_penalty > 0
        and item["raw_penalty_cycles"] == 0
    ), default=None)
    nop_comparison = {
        "available": False,
        "nop_gap": policy.get("nop_gap"),
        "independent_gap": None,
        "timing_divergence": None,
        "timing_comparison_state": "gap_not_tested",
        "requirement_divergence": None,
        "requirement_comparison_state": "gap_not_tested",
    }
    if relaxed:
        nop_gap = policy.get("nop_gap")
        match = next(
            (item for item in gap_records if item["gap"] == nop_gap), None
        )
        nop_dep = _timing_series(relaxed[0])
        nop_ctl = _timing_series(relaxed[1])
        nop_penalty = (
            median(nop_dep) - median(nop_ctl)
            if len(nop_dep) == len(relaxed[0])
            and len(nop_ctl) == len(relaxed[1])
            else None
        )
        nop_requirements = [
            item.get("forwarding_required") for item in relaxed[0]
        ]
        nop_state = (
            "required"
            if nop_requirements and all(value is True for value in nop_requirements)
            else "available_before_use"
            if nop_requirements and all(value is False for value in nop_requirements)
            else "unresolved"
        )
        nop_comparison.update({
            "nop_raw_penalty_cycles": nop_penalty,
            "nop_requirement_state": nop_state,
        })
        if match is not None:
            independent_penalty = match["raw_penalty_cycles"]
            if nop_penalty is None:
                timing_state = "nop_timing_unavailable"
            elif independent_penalty is None:
                timing_state = "independent_timing_unavailable"
            else:
                timing_state = "comparable"
            independent_requirement = match["requirement_state"]
            if nop_state == "unresolved":
                requirement_state = "nop_requirement_unresolved"
            elif independent_requirement == "unresolved":
                requirement_state = (
                    "independent_requirement_unresolved"
                )
            else:
                requirement_state = "comparable"
            nop_comparison.update({
                "available": True,
                "independent_gap": match["gap"],
                "independent_raw_penalty_cycles": independent_penalty,
                "independent_requirement_state": independent_requirement,
                "timing_comparison_state": timing_state,
                "timing_divergence": (
                    nop_penalty != independent_penalty
                    if timing_state == "comparable" else None
                ),
                "requirement_comparison_state": requirement_state,
                "requirement_divergence": (
                    nop_state != independent_requirement
                    if requirement_state == "comparable" else None
                ),
            })
    return {
        "policy": {
            "minimum_gaps": [1, 2],
            "stop_after_consecutive_available_gaps": 2,
            "maximum_gap": _independent_sweep_limit(pipeline_depth),
            "variants_per_gap": "3, extended to 5 on instability",
            "variant_extension_rule":
                "frozen_exact_chain_instability_only",
            "candidate_rescans": 0,
            **policy,
        },
        "tested_gaps": tested_gaps,
        "stop_reason": policy.get(
            "stop_reason",
            "depth_limit_reached" if tested_gaps else "not_run",
        ),
        "per_gap": gap_records,
        "adjacent_reference": {
            "gap": 0,
            "requirement_state": adjacent_requirement_state,
            "raw_penalty_cycles": adjacent_penalty,
            "exact_proof_complete": adjacent_exact,
        },
        "corroboration": {
            "state": corroboration_state,
            "minimum_coverage_complete": minimum_coverage,
            "completed_group_count": complete_group_count,
            "exact_group_count": exact_group_count,
            "fixed_chain": fixed_chain,
            "chain_signature_count": len(all_signatures),
        },
        "inferred_boundaries": {
            "last_gap_forwarding_required": last_required,
            "first_gap_architecturally_available_before_use": first_available,
            "first_gap_raw_penalty_disappeared": first_penalty_disappeared,
        },
        "nop_comparison": nop_comparison,
    }


def _classify_paired_forwarding(
    name, dependent, control, relaxed=None, independent=None,
    pipeline_depth=None, sweep_policy=None,
):
    """Classify behavioral forwarding from layout-matched trial timings.

    ``present`` is true only for stable zero-penalty execution where a
    dynamically confirmed consumer stage proves that the value was required
    before architectural availability.
    """
    category = "register_forwarding"
    result = {
        "status": "inconclusive",
        "present": None,
        "category": category,
        "register_forwarding_test": True,
        "bypass_kind": None,
        "architectural_dependency_handled": _all_or_unknown(
            item.get("dependency_correct", item.get("complete", False))
            for item in dependent
        ),
        "dependent_program_completion": [
            item.get("architectural_complete", item.get("complete", False))
            for item in dependent
        ],
        "control_program_completion": [
            item.get("architectural_complete", item.get("complete", False))
            for item in control
        ],
        "dependent_transaction_observable": [
            item.get("transaction_observable") for item in dependent
        ],
        "control_transaction_observable": [
            item.get("transaction_observable") for item in control
        ],
        "dependent_trials": _timing_series(dependent),
        "control_trials": _timing_series(control),
        "timing_stable": False,
        "zero_delay_behavior_observed": False,
        # This is deliberately independent from ``present``.  Matched external
        # timing can identify a possible forwarding path when internal operand
        # capture is unavailable, but it cannot prove that forwarding was
        # required (for example, a short pipeline may read after writeback).
        "zero_delay_classification": None,
        "absence_evidence_validated": False,
        "confidence": 0.4,
        "confidence_factors": [],
        "experiments": {
            "adjacent": _compact_forwarding_experiment(dependent, control),
        },
    }
    result["independent_distance_sweep"] = (
        _summarize_independent_distance_sweep(
            independent, (dependent, control), relaxed, pipeline_depth,
            sweep_policy,
        )
    )
    store_probe = name in (
        "alu_to_store_data", "alu_to_store_address",
        "load_to_store_data", "load_to_store_address",
    )
    dep_complete = result["dependent_program_completion"]
    ctl_complete = result["control_program_completion"]
    dep_correct = [item.get("dependency_correct", item.get("complete", False)) for item in dependent]
    ctl_correct = [item.get("dependency_correct", item.get("complete", False)) for item in control]
    dep = result["dependent_trials"]
    ctl = result["control_trials"]
    requirements = [item.get("forwarding_required") for item in dependent]
    proof_fields = (
        "consumer_token_proof",
        "source_selector_validation",
        "operand_differential_validation",
        "semantic_discriminators_passed",
    )
    for field in proof_fields:
        result[field] = bool(
            dependent and all(item.get(field) is True for item in dependent)
        )
    path_role_states = [
        item.get("path_role_evidence_state") for item in dependent
    ]
    path_role_contract_present = any(
        "path_role_evidence_state" in item for item in dependent
    )
    result["requirement_rejection_reasons"] = sorted({
        item.get("requirement_rejection_reason")
        or item.get("requirement_observation")
        for item in dependent
        if item.get("forwarding_required") is None
        and (
            item.get("requirement_rejection_reason")
            or item.get("requirement_observation")
        )
    })
    result["requirement_missing_proofs"] = sorted({
        _missing_forwarding_proof(reason)
        for reason in result["requirement_rejection_reasons"]
    })
    if (
        not result["requirement_missing_proofs"]
        and requirements
        and any(value is None for value in requirements)
    ):
        result["requirement_missing_proofs"] = ["operand_capture"]
    observation_sources = {item.get("observation_source") for item in dependent if item.get("observation_source")}
    evidence_qualities = {item.get("evidence_quality") for item in dependent if item.get("evidence_quality")}
    result["forwarding_required"] = (
        True if requirements and all(value is True for value in requirements)
        else False if requirements and all(value is False for value in requirements)
        else None
    )
    if (
        result["forwarding_required"] is True
        and path_role_contract_present
        and (
            not path_role_states
            or not all(state == "confirmed" for state in path_role_states)
        )
    ):
        result["forwarding_required"] = None
        result["requirement_rejection_reasons"].append(
            "the selected per-trial operand chain was not confirmed"
        )
        result["requirement_rejection_reasons"] = sorted(set(
            result["requirement_rejection_reasons"]
        ))
        result["requirement_missing_proofs"] = sorted(set(
            result["requirement_missing_proofs"] + ["operand_capture"]
        ))
    missing_exact_proofs = [
        field for field in proof_fields if result[field] is not True
    ]
    if result["forwarding_required"] is True and missing_exact_proofs:
        result["forwarding_required"] = None
        result["requirement_rejection_reasons"].append(
            "exact consumer-local proof was incomplete: "
            + ", ".join(missing_exact_proofs)
        )
        result["requirement_rejection_reasons"] = sorted(set(
            result["requirement_rejection_reasons"]
        ))
        category_by_field = {
            "consumer_token_proof": "consumer_token",
            "source_selector_validation": "source_id",
            "operand_differential_validation": "operand_capture",
            "semantic_discriminators_passed": "semantic_discriminator",
        }
        result["requirement_missing_proofs"] = sorted(set(
            result["requirement_missing_proofs"]
            + [category_by_field[field] for field in missing_exact_proofs]
        ))
    if (
        result["forwarding_required"] is True
        and independent is not None
        and result["independent_distance_sweep"].get(
            "corroboration", {}
        ).get("state") != "validated"
    ):
        result["forwarding_required"] = None
        result["requirement_rejection_reasons"] = sorted(set(
            result["requirement_rejection_reasons"] + [
                "independent-distance corroboration was incomplete"
            ]
        ))
        result["requirement_missing_proofs"] = sorted(set(
            result["requirement_missing_proofs"]
            + ["independent_distance_corroboration"]
        ))
    if (
        result["forwarding_required"] is None
        and not result["requirement_missing_proofs"]
    ):
        result["requirement_missing_proofs"] = (
            ["phase_ordering"] if requirements else ["operand_capture"]
        )
    result["observation_source"] = (
        next(iter(observation_sources)) if len(observation_sources) == 1 else "mixed_or_unavailable"
    )
    result["evidence_quality"] = (
        next(iter(evidence_qualities)) if len(evidence_qualities) == 1 else "mixed_or_incomplete"
    )
    completion_stable = (
        len(set(dep_complete)) == 1 and len(set(ctl_complete)) == 1
        and len(set(dep_correct)) == 1 and len(set(ctl_correct)) == 1
    )

    if relaxed:
        result["experiments"]["relaxed"] = _compact_forwarding_experiment(
            relaxed[0], relaxed[1]
        )
        relaxed_dep_complete = [
            item.get("architectural_complete", item.get("complete", False))
            for item in relaxed[0]
        ]
        relaxed_ctl_complete = [
            item.get("architectural_complete", item.get("complete", False))
            for item in relaxed[1]
        ]
        relaxed_dep_correct = [
            item.get("dependency_correct", item.get("complete", False))
            for item in relaxed[0]
        ]
        relaxed_ctl_correct = [
            item.get("dependency_correct", item.get("complete", False))
            for item in relaxed[1]
        ]
        result["relaxed_dependency_handled"] = bool(
            relaxed_dep_complete and relaxed_ctl_complete
            and all(relaxed_dep_complete) and all(relaxed_ctl_complete)
            and all(relaxed_dep_correct) and all(relaxed_ctl_correct)
        )
        result["relaxed_dependent_trials"] = _timing_series(relaxed[0])
        result["relaxed_control_trials"] = _timing_series(relaxed[1])
        if result["relaxed_dependent_trials"] and result["relaxed_control_trials"]:
            result["relaxed_raw_penalty_cycles"] = (
                median(result["relaxed_dependent_trials"])
                - median(result["relaxed_control_trials"])
            )

    stable_architectural_failure = (
        completion_stable
        and all(ctl_complete) and all(ctl_correct)
        and all(dep_complete) and not any(dep_correct)
    )
    if store_probe:
        dep_visible = [item.get("transaction_observable") is True for item in dependent]
        dep_store_absence_proven = [
            item.get("store_absence_architecturally_observable") is True
            for item in dependent
        ]
        failure_signatures = [
            (
                (item.get("observed_store") or {}).get("address"),
                (item.get("observed_store") or {}).get("value"),
            )
            for item in dependent
        ]
        stable_architectural_failure = (
            stable_architectural_failure
            and (
                (all(dep_visible) and len(set(failure_signatures)) == 1)
                or all(dep_store_absence_proven)
            )
        )

    if stable_architectural_failure:
        result.update({
            "status": "not_detected", "present": False, "confidence": 0.6,
            "confidence_factors": ["stable architectural failure", "matched control completed correctly"],
            "architectural_dependency_handled": False,
            "absence_evidence_validated": True,
            "evidence": (
                (
                    "the dependent store was fetched but stably dropped after a correct load; "
                    "the control store and later completion marker were observable"
                    if store_probe and all(
                        item.get("store_absence_architecturally_observable") is True
                        for item in dependent
                    ) else
                    "control stores were correct and the dependent program completed "
                    "with the same observable incorrect store in every trial"
                )
                if store_probe else
                "control completed correctly while the dependent architectural result failed consistently"
            ),
        })
        return result
    if not completion_stable or not all(dep_complete) or not all(ctl_complete):
        result["confidence"] = 0.25
        result["confidence_factors"] = ["architectural execution was incomplete or inconsistent"]
        result["evidence"] = "paired programs did not complete architecturally and consistently"
        return result
    if not all(dep_correct) or not all(ctl_correct):
        result["confidence_factors"] = ["architectural dependency correctness was not established"]
        result["evidence"] = (
            "store correctness was not observable in every trial"
            if store_probe else "paired architectural results were not correct in every trial"
        )
        return result
    if len(dep) != len(dependent) or len(ctl) != len(control):
        result["confidence_factors"] = ["consumer timing was not observable in every trial"]
        result["evidence"] = (
            "architectural execution completed, but consumer timing was not observable in every trial"
        )
        return result

    stable = (max(dep) - min(dep) <= 1) and (max(ctl) - min(ctl) <= 1)
    if relaxed:
        relaxed_dep = result.get("relaxed_dependent_trials", [])
        relaxed_ctl = result.get("relaxed_control_trials", [])
        result["relaxed_timing_stable"] = bool(
            relaxed_dep and relaxed_ctl
            and max(relaxed_dep) - min(relaxed_dep) <= 1
            and max(relaxed_ctl) - min(relaxed_ctl) <= 1
        )
    result["timing_stable"] = stable
    result["dependent_median_latency"] = median(dep)
    result["control_median_latency"] = median(ctl)
    penalty = median(dep) - median(ctl)
    result["raw_penalty_cycles"] = penalty
    if not stable:
        result["confidence_factors"] = ["paired timing range exceeded one cycle"]
        result["evidence"] = "final paired timing range exceeds one cycle"
        return result

    overlaps = [
        item.get("producer_consumer_overlap", "overlapped")
        for item in dependent
    ]
    result["producer_consumer_overlap"] = (
        overlaps[0] if overlaps and len(set(overlaps)) == 1 else "unobservable"
    )
    relaxed_penalty = result.get("relaxed_raw_penalty_cycles")
    if penalty < 0:
        result["confidence_factors"] = ["dependent latency was unexpectedly below its matched control"]
        result["evidence"] = "dependent latency was lower than its matched control"
        return result
    if penalty == 0:
        result["zero_delay_behavior_observed"] = True
        if result["forwarding_required"] is not True:
            if result["forwarding_required"] is False:
                result.update({
                    "zero_delay_classification": "forwarding_not_required",
                    "confidence": 0.75,
                    "confidence_factors": [
                        "confirmed consumer-stage timing",
                        "producer was available before consumer operand use",
                    ],
                    "evidence": (
                        "dependent and control median latencies are equal, but the producer "
                        "was already architecturally available before consumer operand use"
                    ),
                })
            else:
                fetch_only = result["evidence_quality"] == "fetch_commit_only"
                result.update({
                    "zero_delay_classification": "possible_forwarding",
                    "confidence": 0.55 if fetch_only else 0.4,
                    "confidence_factors": [
                        "zero-delay matched behavior",
                        "consumer operand-use timing was not established",
                    ],
                    "evidence": (
                        "dependent and control median latencies are equal, but dynamically "
                        "confirmed stage evidence did not establish that forwarding was required"
                    ),
                })
            return result
        bypass = {
            "alu_to_alu": "alu_to_ex",
            "load_to_alu": "load_to_ex_zero_stall",
            "alu_to_store_data": "alu_to_store_data",
            "alu_to_store_address": "alu_to_store_address",
            "load_to_store_data": "load_to_store_data",
            "load_to_store_address": "load_to_store_address_zero_stall",
        }[name]
        pc_only = result["evidence_quality"] == "pc_only"
        result.update({
            "status": "detected", "present": True, "bypass_kind": bypass,
            "zero_delay_classification": "confirmed_forwarding",
            "confidence": 0.9 if pc_only else 0.95,
            "confidence_factors": [
                "stable matched zero-delay behavior",
                "confirmed consumer stage preceded producer architectural availability",
                "stage PC correlation" if pc_only else "stage valid or instruction correlation",
            ],
            "evidence": (
                "dependent and control median latencies are equal and confirmed stage timing "
                "shows that the consumer required the producer value before writeback"
            ),
        })
    else:
        after_interlock = (
            result.get("relaxed_timing_stable") is True and relaxed_penalty == 0
        )
        persistent_stall = (
            result.get("relaxed_timing_stable") is True
            and relaxed_penalty is not None and relaxed_penalty > 0
        )
        result.update({
            "status": "stall_handled", "present": False, "confidence": 0.88,
            "confidence_factors": [
                "stable matched positive RAW penalty",
                "architectural dependency completed correctly",
            ],
            "handling_kind": (
                "after_interlock" if after_interlock
                else "stall_only" if persistent_stall
                else "interlock_or_stall"
            ),
            "evidence": (
                "adjacent dependency adds latency and the penalty disappears at relaxed distance"
                if after_interlock else
                "dependency is architecturally correct but adds latency relative to control"
            ),
        })
    return result

def _classify_store_to_load_hazard(trial, classified):
    """Report architectural ordering without claiming store-queue forwarding."""
    handled = bool(trial.get("complete"))
    externally_serialized = classified.get("present") is True
    return {
        "status": "handled" if handled else (
            "not_handled" if classified.get("present") is False else "inconclusive"
        ),
        "category": "memory_hazard_handling",
        "architectural_dependency_handled": handled,
        "mechanism": "stall_or_memory_serialization",
        "true_store_to_load_forwarding_observable": False,
        "external_transaction_order_observed": externally_serialized,
        "transaction_distance": classified.get("transaction_distance"),
        "memory_transactions": classified.get("memory_transactions", []),
        "evidence": (
            "the architectural load observed the older store; this proves hazard handling, not an internal store-queue bypass"
            if handled else classified.get("reason", "store/load ordering was not established")
        ),
    }

async def forwarding_presence_test(dut, regfile, pipeline=None, data_memory=None, regfile_discovery=None,):
    """
    Compare layout-matched dependent/control programs on pipelined cores.

    ``detected`` is behavioral evidence that an overlapped RAW dependency adds
    no latency relative to its control. Interlocked execution is correct hazard
    handling, not proof of forwarding or of a particular RTL bypass mux.
    """

    if not _is_pipeline_classification(pipeline):
        dut._log.info("[forwarding] Skipped: processor was not classified as pipelined")
        return None

    dut._log.info("[forwarding] Running isolated forwarding probes...")
    data_memory = data_memory or DataMemory()
    output_dir = os.environ.get("OUTPUT_DIR", "default")
    processor_name = os.path.basename(output_dir)
    labels_file = os.path.join(output_dir, f"{processor_name}_labels.json")
    run_id = str(uuid.uuid4())
    debug_enabled = _env_flag("CYCLE_DEBUG") or _env_flag("DEBUG_CYCLE")
    execution_started = _wall_time.monotonic()
    phase_timings = {}

    def record_phase_timing(name, started):
        phase_timings[name] = round(
            phase_timings.get(name, 0.0)
            + (_wall_time.monotonic() - started),
            6,
        )

    _write_forwarding_progress(
        output_dir, processor_name, "forwarding_start", run_id=run_id,
    )
    results = {
        "schema_version": FORWARDING_SCHEMA_VERSION,
        "probe_suite_version": FORWARDING_PROBE_SUITE_VERSION,
        "implementation_revision": FORWARDING_IMPLEMENTATION_REVISION,
        "execution": _forwarding_execution_record("running", run_id),
        "applicable": True,
    }
    _write_label_sections(
        labels_file, processor_name, {"forwarding": results},
        remove=("forwarding_debug",),
    )
    # Replace an older discovery artifact before entering the simulator-heavy
    # probe sequence.  If the simulator aborts the entire host process, this
    # fresh v4 lifecycle record remains instead of stale evidence.
    write_pipeline_interface(output_dir, processor_name, {
        "schema_version": 4,
        "discovery_version": PIPELINE_INTERFACE_DISCOVERY_VERSION,
        "implementation_revision": FORWARDING_IMPLEMENTATION_REVISION,
        "state": "running",
        "run_id": run_id,
        "stages": [],
        "calibration": {
            "state": "not_run", "execution_state": "not_run",
            "flow_trials": 0,
            "completed_flow_trials": 0, "forced_hold": "not_run",
            "sections": {
                name: {"state": "not_run", "variants": []}
                for name in ("straight_line", "memory", "redirect")
            },
        },
        "role_evidence": {
            use: {
                "state": "unavailable",
                "rejection_reason": "pipeline discovery has not run",
            }
            for use in ("execute", "store_address", "store_data")
        },
        "capabilities": {
            "consumer_stage_observable": False,
            "execute_stage_observable": False,
            "memory_stage_observable": False,
            "multi_lane": False,
            "lane_identity": False,
            "source_ids": False,
            "operand_values": False,
            "store_data_capture": False,
            "writeback_event": False,
            "phase_ordering": False,
            "sampling_phases": False,
        },
    })
    try:
        selected_regfile = (regfile_discovery or {}).get("selected_regfile") or {}
        regfile_path = (
            getattr(regfile, "_path", None)
            or selected_regfile.get("path")
            or selected_regfile.get("candidate_path")
        )
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
        debug_results = {}
        pipeline_depth = pipeline.get("depth_estimate")
        pipeline_observer = PipelineSignalObserver(
            dut,
            regfile_path=regfile_path,
            pipeline_depth=pipeline_depth,
            write_interface=interface_handles,
            register_reader=lambda register: _get_regfile_reg_value(
                regfile, register, regfile_metadata,
            ),
            architectural_xlen=regfile_metadata.get("word_width", 32),
        )

        async def run_probe(spec, calibration=False):
            pipeline_trial_id = pipeline_observer.start_trial(spec)
            program_memory.select(spec)
            data_memory.reset(spec.initial_memory)
            dut.rst_n.value = 0
            dut.core_ack.value = 0
            await _load_optional_internal_program(dut, program_memory.image)
            await _load_optional_internal_data(dut, spec.initial_memory)
            await Timer(50, unit="ns")
            data_memory.reset(spec.initial_memory)
            dut.rst_n.value = 1
            memory_epoch = data_memory.current_cycle
            fetch_events = []
            commits = await _observe_probe_commits(
                dut, regfile, regfile_metadata, interface_handles, spec,
                max_cycles=_measurement_cycle_budget(regfile_metadata),
                fetch_events=fetch_events,
                pipeline_observer=pipeline_observer,
            )
            entries = {item["offset"]: item for item in spec.entries()}
            for event in commits:
                event["role"] = entries[event["offset"]]["role"]
            classified = None if calibration else _classify_forwarding_probe(
                spec, commits, data_memory, memory_epoch, pipeline_depth
            )
            transactions = [
                {**item, "cycle": item["cycle"] - memory_epoch}
                for item in data_memory.transactions
            ] if data_memory.supported else []
            if calibration:
                signature = _evaluate_calibration_signature(
                    spec, regfile, regfile_metadata, data_memory,
                )
                complete = signature["state"] == "completed"
                pipeline_observer.finish_trial(
                    fetch_events, commits, transactions,
                    calibration_signature=signature,
                )
                return {
                    "complete": complete,
                    "architectural_complete": complete,
                    "pipeline_trial_id": pipeline_trial_id,
                    "calibration_signature": signature,
                    "load_transaction_observed": any(
                        item.get("kind") == "load"
                        and item.get("address") == getattr(spec, "calibration_load_address", None)
                        for item in transactions
                    ),
                }, {
                    "program": spec.entries(), "instructions": spec.instructions,
                    "fetch_events": fetch_events, "commit_events": commits,
                    "memory_transactions": transactions,
                    "event_trace": _forwarding_event_trace(fetch_events, commits, transactions),
                }
            pipeline_observer.finish_trial(fetch_events, commits, transactions)
            store_expected = getattr(spec, "expected_store_address", None) is not None
            architectural_complete = len(commits) == len(spec.expected_writes)
            store_observation = _store_transaction_observation(
                spec, transactions, data_memory.supported
            ) if store_expected else {
                "transaction_interface_available": bool(data_memory.supported),
                "transaction_observable": None,
                "store_request_observed": None,
                "matching_store_observed": None,
                "store_correct": None,
                "store_address_correct": None,
                "store_value_correct": None,
                "observed_store": None,
            }
            if not architectural_complete:
                dependency_correct = False
            elif not store_expected:
                dependency_correct = True
            else:
                # A completed marker proves execution reached beyond the store,
                # but an unavailable external request cannot prove the store's
                # architectural value or turn into a false failure.
                dependency_correct = store_observation["store_correct"]
            consumer_fetch_observed = any(
                item.get("offset") == spec.consumer_offset for item in fetch_events
            )
            completion_marker_observed = any(
                item.get("role") == "completion" for item in commits
            )
            producer_result_observed = any(
                item.get("role") in ("producer", "address_producer") for item in commits
            )
            load_response_observed = any(
                item.get("kind") == "load" for item in transactions
            )
            store_absence_architecturally_observable = bool(
                store_expected
                and data_memory.supported
                and consumer_fetch_observed
                and completion_marker_observed
                and producer_result_observed
                and load_response_observed
                and not store_observation["store_request_observed"]
            )
            overlap_observation = _forwarding_overlap_observation(
                spec.name.split("_dependent_")[0].split("_control_")[0],
                spec, fetch_events, commits, transactions,
            )
            trial = {
                # ``complete`` remains a compatibility alias for architectural
                # program completion. Store visibility/correctness is recorded
                # independently and never turns a missing request into failure.
                "complete": architectural_complete,
                "architectural_complete": architectural_complete,
                "dependency_correct": dependency_correct,
                "consumer_fetch_observed": consumer_fetch_observed,
                "completion_marker_observed": completion_marker_observed,
                "producer_result_observed": producer_result_observed,
                "load_response_observed": load_response_observed,
                "store_absence_architecturally_observable": store_absence_architecturally_observable,
                "pipeline_trial_id": pipeline_trial_id,
                "consumer_offset": spec.consumer_offset,
                "forwarding_gap": int(
                    getattr(spec, "forwarding_gap", 0)
                ),
                "spacer_kind": getattr(spec, "spacer_kind", "nop"),
                "filler_registers": list(
                    getattr(spec, "filler_registers", ())
                ),
                "filler_values": list(
                    getattr(spec, "filler_values", ())
                ),
                **store_observation,
                **overlap_observation,
                "latency": _trial_latency(
                    spec.name.split("_dependent_")[0].split("_control_")[0],
                    spec, fetch_events, commits, transactions,
                ),
            }
            details = {
                "program": spec.entries(), "instructions": spec.instructions,
                "fetch_events": fetch_events, "commit_events": commits,
                "memory_transactions": transactions, "classified": classified,
                "load_responses": [item for item in transactions if item.get("kind") == "load"],
                "store_requests": [item for item in transactions if item.get("kind") == "store"],
                "signature_trace": commits,
                "event_trace": _forwarding_event_trace(fetch_events, commits, transactions),
            }
            return trial, details

        def pair_debug_key(name, gap, spacer_kind):
            suffix = "" if spacer_kind == "nop" else f"_{spacer_kind}"
            return f"{name}_paired_gap_{gap}{suffix}"

        async def run_pair_trials(name, gap, spacer_kind="nop"):
            group_started = _wall_time.monotonic()
            dependent_trials, control_trials, trial_debug = [], [], []
            for trial_index in range(3):
                dependent_spec, control_spec = forwarding_probe_pair(
                    name, gap, trial_index, spacer_kind=spacer_kind,
                )
                for role, spec, target in (
                    ("dependent", dependent_spec, dependent_trials),
                    ("control", control_spec, control_trials),
                ):
                    observation, details = await run_probe(spec)
                    target.append(observation)
                    if debug_enabled:
                        trial_debug.append({
                            "trial": trial_index, "role": role,
                            **details, "observation": observation,
                        })
                _write_forwarding_progress(
                    output_dir, processor_name, "path_gap_variant",
                    path=name, gap=int(gap),
                    spacer_kind=spacer_kind, variant=trial_index,
                )
            debug_results[
                pair_debug_key(name, gap, spacer_kind)
            ] = trial_debug
            record_phase_timing(
                f"{spacer_kind}_gap_group", group_started,
            )
            _write_forwarding_progress(
                output_dir, processor_name, "path_gap_variant_group",
                path=name, gap=int(gap), spacer_kind=spacer_kind,
                variants=min(len(dependent_trials), len(control_trials)),
            )
            return dependent_trials, control_trials

        async def extend_pair_trials(
            name, gap, paired, spacer_kind="nop",
        ):
            extension_started = _wall_time.monotonic()
            dependent_trials, control_trials = paired
            trial_debug = debug_results[
                pair_debug_key(name, gap, spacer_kind)
            ]
            for trial_index in range(3, 5):
                dependent_spec, control_spec = forwarding_probe_pair(
                    name, gap, trial_index, spacer_kind=spacer_kind,
                )
                for role, spec, target in (
                    ("dependent", dependent_spec, dependent_trials),
                    ("control", control_spec, control_trials),
                ):
                    observation, details = await run_probe(spec)
                    target.append(observation)
                    if debug_enabled:
                        trial_debug.append({
                            "trial": trial_index, "role": role, **details,
                            "observation": observation,
                        })
                _write_forwarding_progress(
                    output_dir, processor_name, "path_gap_variant",
                    path=name, gap=int(gap),
                    spacer_kind=spacer_kind, variant=trial_index,
                    extension=True,
                )
            record_phase_timing(
                f"{spacer_kind}_gap_extension", extension_started,
            )
            _write_forwarding_progress(
                output_dir, processor_name, "path_gap_variant_group",
                path=name, gap=int(gap), spacer_kind=spacer_kind,
                variants=min(len(dependent_trials), len(control_trials)),
                extension=True,
            )

        async def run_calibration_spec(spec, variant):
            try:
                observation, details = await run_probe(spec, calibration=True)
                return {"variant": variant, "observation": observation, **details}
            except Exception as exc:
                traceback_text = traceback.format_exc()
                pipeline_observer.abort_trial(
                    exc, traceback_text=traceback_text,
                )
                dut._log.error(
                    "[forwarding] Calibration %s variant %s raised %s:\n%s",
                    spec.name, variant, type(exc).__name__, traceback_text,
                )
                return {
                    "variant": variant,
                    "observation": {
                        "complete": False,
                        "architectural_complete": False,
                        "calibration_error": str(exc),
                        "calibration_error_type": type(exc).__name__,
                        "calibration_traceback": traceback_text,
                    },
                }

        calibration_started = _wall_time.monotonic()
        handshake_debug = []
        baseline_spec = pipeline_handshake_calibration(0)
        baseline = await run_calibration_spec(baseline_spec, 0)
        baseline["handshake_role"] = "baseline"
        handshake_debug.append(baseline)
        handshake_prelim_supported = bool(
            data_memory.supported
            and baseline["observation"].get("architectural_complete")
            and baseline["observation"].get("load_transaction_observed")
        )
        if handshake_prelim_supported:
            for handshake_variant in (1, 2):
                delayed_spec = pipeline_handshake_calibration(handshake_variant)
                data_memory.configure_response_delay(
                    1, address=delayed_spec.calibration_load_address,
                )
                try:
                    delayed = await run_calibration_spec(delayed_spec, handshake_variant)
                    delayed["handshake_role"] = "delayed"
                    handshake_debug.append(delayed)
                    if not (
                        delayed["observation"].get("architectural_complete")
                        and delayed["observation"].get("load_transaction_observed")
                    ):
                        handshake_prelim_supported = False
                        break
                finally:
                    data_memory.configure_response_delay(0)

        landing_debug = []
        landing_records = []
        selected_bases = []
        selected_raw_bases = []
        for landing_index, requested_base in enumerate(
            CALIBRATION_LANDING_BASES
        ):
            landing_spec = pipeline_relocation_landing(
                requested_base, landing_index,
            )
            landing = await run_calibration_spec(
                landing_spec, landing_index,
            )
            record = _relocation_landing_record(
                landing_spec, landing["observation"], landing,
                selected_raw_bases,
            )
            landing["landing_record"] = record
            landing_debug.append(landing)
            landing_records.append(record)
            if record["accepted"]:
                selected_bases.append(int(requested_base))
                selected_raw_bases.append(record["observed_raw_base"])
            _write_forwarding_progress(
                output_dir, processor_name, "calibration_landing",
                requested_base=int(requested_base),
                accepted=record["accepted"],
                selected_count=len(selected_bases),
            )
            if len(selected_bases) == 3:
                break
        base_selection = {
            "state": (
                "complete" if len(selected_bases) == 3
                else "incomplete"
            ),
            "policy": {
                "candidate_bases": list(CALIBRATION_LANDING_BASES),
                "required_distinct_bases": 3,
                "stop_after_selected": 3,
                "single_body_with_entry_trampolines": True,
            },
            "attempted": landing_records,
            "selected_bases": selected_bases,
            "selected_observed_raw_bases": selected_raw_bases,
            "relocation_roles_permitted": len(selected_bases) == 3,
            "rejection_reason": (
                None if len(selected_bases) == 3
                else "fewer_than_three_distinct_reachable_bases"
            ),
        }
        pipeline_observer.set_calibration_base_selection(base_selection)
        debug_results["pipeline_calibration_landing"] = landing_debug

        calibration_debug = []
        flow_bases = (
            selected_bases
            if len(selected_bases) == 3
            else selected_bases[:1]
            or [CALIBRATION_LANDING_BASES[0]]
        )
        for calibration_variant, execution_base in enumerate(flow_bases):
            calibration_debug.append(await run_calibration_spec(
                pipeline_calibration_flow(
                    calibration_variant,
                    execution_base=execution_base,
                ),
                calibration_variant,
            ))
        debug_results["pipeline_calibration_flow"] = calibration_debug
        recovery_signature = (
            calibration_debug[0]["observation"].get(
                "calibration_signature", {}
            )
            if calibration_debug else {}
        )
        recovery_sections = recovery_signature.get("sections", {})
        recovery_state = (
            recovery_sections.get("memory", {}).get("state")
            if recovery_sections
            else recovery_signature.get("state")
        )
        recovery_complete = bool(
            calibration_debug
            and recovery_state == "completed"
            and calibration_debug[0]["observation"].get(
                "load_transaction_observed"
            )
        )
        handshake_supported = bool(
            handshake_prelim_supported
            and len(handshake_debug) == 3
            and recovery_complete
        )
        if not handshake_supported:
            pipeline_observer.set_stall_sampling_enabled(False)
        debug_results["pipeline_calibration_handshake"] = handshake_debug
        dut._log.info(
            "[forwarding] Handshake calibration complete: supported=%s "
            "recovery=%s trials=%d",
            handshake_supported, recovery_complete, len(handshake_debug),
        )
        dut._log.info("[forwarding] Architectural calibration variants complete")
        record_phase_timing("calibration", calibration_started)
        _write_forwarding_progress(
            output_dir, processor_name, "calibration_completion",
            handshake_supported=handshake_supported,
        )

        census_summary = pipeline_observer.finalize_census()
        debug_results["pipeline_behavioral_census"] = census_summary
        dut._log.info(
            "[forwarding] Behavioral signal census complete: before=%s after=%s",
            census_summary.get("candidate_counts_before"),
            census_summary.get("candidate_counts_after"),
        )

        paired_runs = {}
        for name in (
            "alu_to_alu", "alu_to_store_data", "alu_to_store_address",
            "load_to_alu", "load_to_store_data", "load_to_store_address",
        ):
            adjacent = await run_pair_trials(name, 0)
            paired_runs[name] = {"adjacent": adjacent}
            dut._log.info(
                "[forwarding] Initial adjacent discovery trials complete for %s",
                name,
            )

        provisional_started = _wall_time.monotonic()
        provisional_interface = pipeline_observer.finalize()
        record_phase_timing(
            "provisional_pipeline_classification", provisional_started,
        )
        missing_by_path = {}
        for name in paired_runs:
            use = _forwarding_required_use(name)
            evidence = provisional_interface.get(
                "role_evidence", {}
            ).get(use, {})
            if evidence.get("state") == "confirmed":
                continue
            reason = evidence.get("rejection_reason") or (
                f"{use} role-local proof is unavailable"
            )
            categories = {_missing_forwarding_proof(reason)}
            if evidence.get("stage_path") is None and use != "store_data":
                categories.add("stage_token")
            if evidence.get("source_id_path") is None:
                categories.add("source_id")
            if evidence.get("operand_path") is None:
                categories.add("operand_capture")
            if (
                evidence.get("captured_trials", 0)
                and evidence.get("availability_trials", 0)
                < evidence.get("captured_trials", 0)
            ):
                categories.add("producer_availability")
            if use == "store_data" and "transaction" in reason.lower():
                categories.add("transaction_association")
            missing_by_path[name] = categories
        focused_rescan = pipeline_observer.promote_focused_reserve(
            missing_by_path,
        )
        if (
            focused_rescan.get("affected_paths")
            and any(focused_rescan.get("promoted_counts", {}).values())
        ):
            affected = focused_rescan["affected_paths"]
            pipeline_observer.mark_adjacent_trials_discovery_only(
                affected,
            )
            for name in affected:
                debug_key = f"{name}_paired_gap_0"
                debug_results[f"{debug_key}_discovery_only"] = (
                    debug_results.get(debug_key, [])
                )
                paired_runs[name]["adjacent"] = await run_pair_trials(
                    name, 0,
                )
            dut._log.info(
                "[forwarding] Focused adjacent rescan complete for %s",
                affected,
            )
        _write_forwarding_progress(
            output_dir, processor_name, "focused_rescan",
            affected_paths=focused_rescan.get("affected_paths", []),
            ran=bool(focused_rescan.get("ran")),
        )

        # All roles see the same adjacent dependent/control evidence before
        # relaxed-distance trials begin. This prevents an early family from
        # monopolizing a candidate selected only because it ran first.
        for name, runs in paired_runs.items():
            relaxed_gap = max(1, int(pipeline_depth or 2) - 1)
            # Keep the consumer on the low word of an 8-byte fetch bundle for
            # wrappers that expose only one PC per line. Moving one instruction
            # farther remains safely beyond architectural availability.
            if relaxed_gap % 2:
                relaxed_gap += 1
            relaxed = await run_pair_trials(name, relaxed_gap)
            runs.update({"relaxed": relaxed, "relaxed_gap": relaxed_gap})
            dut._log.info("[forwarding] Paired trials complete for %s", name)
        _write_forwarding_progress(
            output_dir, processor_name, "nop_completion",
            completed_paths=sorted(paired_runs),
        )

        def enrich_all(interface):
            for path_name, path_runs in paired_runs.items():
                groups = [
                    path_runs["adjacent"], path_runs["relaxed"],
                    *path_runs.get("independent", {}).values(),
                ]
                for group in groups:
                    for trials in group:
                        for trial in trials:
                            _enrich_forwarding_requirement(
                                path_name, trial, interface,
                            )

        finalization_started = _wall_time.monotonic()
        pipeline_interface = pipeline_observer.finalize()
        record_phase_timing(
            "frozen_pipeline_classification", finalization_started,
        )
        for name in focused_rescan.get("affected_paths", []):
            use = _forwarding_required_use(name)
            focused_rescan["resolved"][name] = (
                pipeline_interface.get("role_evidence", {})
                .get(use, {}).get("state")
                == "confirmed"
            )
        pipeline_interface["focused_rescan"] = focused_rescan
        pipeline_interface["topology_frozen"] = True
        pipeline_interface["full_pipeline_finalization_count"] = (
            pipeline_observer.full_finalization_count
        )
        enrich_all(pipeline_interface)

        def enrich_trial_subset(path_name, paired, starts=(0, 0)):
            for role_index, trials in enumerate(paired):
                for trial in trials[int(starts[role_index]):]:
                    _enrich_forwarding_requirement(
                        path_name, trial, pipeline_interface,
                    )

        def validate_new_trials(cursor, path_name, paired, starts=(0, 0)):
            new_trials = pipeline_observer.trials_since(cursor)
            validate_frozen_forwarding_trials(
                pipeline_interface,
                new_trials,
                pipeline_depth=pipeline_depth,
            )
            enrich_trial_subset(path_name, paired, starts)
            # The full signal/event traces are no longer candidate inputs.
            # Compact requirement/availability ledgers and paired summaries
            # are sufficient for the final artifact and classifier.
            pipeline_observer.discard_trials_since(cursor)

        # If stage-linked instability appears only after the frozen selection,
        # add variants 4-5 and validate just those new traces.  No topology or
        # candidate ranking is repeated.
        for name, runs in paired_runs.items():
            for key, gap, spacer_kind in (
                ("adjacent", 0, "nop"),
                ("relaxed", runs["relaxed_gap"], "nop"),
            ):
                paired = runs[key]
                if (
                    len(paired[0]) == 3
                    and _paired_stage_evidence_needs_extension(*paired)
                ):
                    cursor = pipeline_observer.trial_cursor()
                    starts = (len(paired[0]), len(paired[1]))
                    await extend_pair_trials(
                        name, gap, paired, spacer_kind=spacer_kind,
                    )
                    validate_new_trials(cursor, name, paired, starts)

        if not debug_enabled:
            for internal_field in (
                "trial_signal_traces", "candidate_scores",
                "operand_candidate_scores", "control_candidate_scores",
                "writeback_candidate_scores", "stage_token_observations",
                "trial_observations",
            ):
                pipeline_interface.pop(internal_field, None)
            pipeline_observer.discard_trials_since(0)
            debug_results.clear()

        # Independent instructions exercise execute/writeback resources while
        # preserving a layout-matched control. Each path stops independently
        # only after two consecutive exact captures occur after architectural
        # producer availability.
        sweep_limit = _independent_sweep_limit(pipeline_depth)
        active_paths = set(paired_runs)
        consecutive_available = {name: 0 for name in paired_runs}
        consecutive_architectural_failure = {
            name: {"category": None, "count": 0}
            for name in paired_runs
        }
        sweep_policy = {
            name: {
                "nop_gap": runs["relaxed_gap"],
                "stop_reason": None,
                "terminal_gap": None,
                "architectural_gap_failure": None,
            }
            for name, runs in paired_runs.items()
        }
        for runs in paired_runs.values():
            runs["independent"] = {}
        for gap in range(1, sweep_limit + 1):
            scheduled = sorted(active_paths)
            if not scheduled:
                break
            for name in scheduled:
                cursor = pipeline_observer.trial_cursor()
                paired_runs[name]["independent"][gap] = (
                    await run_pair_trials(
                        name, gap, spacer_kind="independent",
                    )
                )
                paired = paired_runs[name]["independent"][gap]
                validate_new_trials(cursor, name, paired)
                if (
                    len(paired[0]) == 3
                    and _paired_stage_evidence_needs_extension(*paired)
                ):
                    cursor = pipeline_observer.trial_cursor()
                    starts = (len(paired[0]), len(paired[1]))
                    await extend_pair_trials(
                        name, gap, paired,
                        spacer_kind="independent",
                    )
                    validate_new_trials(cursor, name, paired, starts)
            for name in scheduled:
                dependent_gap, control_gap = paired_runs[name][
                    "independent"
                ][gap]
                architectural_failure = _architectural_gap_failure(
                    dependent_gap, control_gap,
                )
                if architectural_failure is not None:
                    prior = consecutive_architectural_failure[name]
                    if (
                        prior["category"]
                        == architectural_failure["category"]
                    ):
                        prior["count"] += 1
                    else:
                        prior.update({
                            "category": architectural_failure["category"],
                            "count": 1,
                        })
                    if (
                        architectural_failure["monotonic"]
                        or prior["count"] >= 2
                    ):
                        active_paths.remove(name)
                        sweep_policy[name].update({
                            "stop_reason": "architectural_gap_failure",
                            "terminal_gap": gap,
                            "architectural_gap_failure": {
                                **architectural_failure,
                                "confirmation": (
                                    "structurally_proven"
                                    if architectural_failure["monotonic"]
                                    else "two_consecutive_gaps"
                                ),
                                "consecutive_gaps": prior["count"],
                            },
                        })
                        continue
                else:
                    consecutive_architectural_failure[name].update({
                        "category": None, "count": 0,
                    })
                consecutive_available[name], should_stop = (
                    _advance_independent_sweep(
                        consecutive_available[name], gap, dependent_gap,
                    )
                )
                if should_stop:
                    active_paths.remove(name)
                    sweep_policy[name].update({
                        "stop_reason":
                            "two_consecutive_architecturally_available_gaps",
                        "terminal_gap": gap,
                    })
            dut._log.info(
                "[forwarding] Independent gap %s complete; active paths=%s",
                gap, sorted(active_paths),
            )
        for name in active_paths:
            sweep_policy[name].update({
                "stop_reason": "depth_limit_reached",
                "terminal_gap": sweep_limit,
            })

        final_artifact_started = _wall_time.monotonic()
        _write_forwarding_progress(
            output_dir, processor_name, "finalization",
            full_pipeline_finalization_count=(
                pipeline_observer.full_finalization_count
            ),
        )
        write_pipeline_interface(output_dir, processor_name, pipeline_interface)
        record_phase_timing("artifact_finalization", final_artifact_started)
        results["focused_rescan"] = focused_rescan
        for name, runs in paired_runs.items():
            results[name] = _classify_paired_forwarding(
                name, *runs["adjacent"], relaxed=runs["relaxed"],
                independent=runs["independent"],
                pipeline_depth=pipeline_depth,
                sweep_policy=sweep_policy[name],
            )
            if results[name].get("present") is True:
                enforce_forwarding_positive(
                    results[name], pipeline_interface,
                    FORWARDING_IMPLEMENTATION_REVISION,
                )
            results[name]["trial_count"] = len(runs["adjacent"][0])
            results[name]["relaxed_gap"] = runs["relaxed_gap"]
            results[name]["pipeline_interface_state"] = pipeline_interface.get("state")
            results[name]["pipeline_interface_discovery_version"] = PIPELINE_INTERFACE_DISCOVERY_VERSION

        # Store-to-load checks correct hazard handling/ordering. It cannot prove
        # an internal store-queue-to-load forwarding mechanism at this interface.
        memory_spec = store_to_load_hazard_probe(0)
        memory_trial, memory_details = await run_probe(memory_spec)
        memory_classified = memory_details["classified"]
        hazard_results = {
            "applicable": True,
            "store_to_load": _classify_store_to_load_hazard(memory_trial, memory_classified),
        }
        debug_results["store_to_load"] = [memory_details]

        results["execution"] = _forwarding_execution_record(
            "completed", run_id,
            elapsed_seconds=round(
                _wall_time.monotonic() - execution_started, 6,
            ),
            phase_timings_seconds=phase_timings,
            full_pipeline_finalization_count=(
                pipeline_observer.full_finalization_count
            ),
            topology_frozen=True,
            incremental_gap_validation=True,
            discarded_raw_trial_count=(
                pipeline_observer.discarded_raw_trial_count
            ),
        )
        sections = {
            "forwarding": results,
            "hazard_handling": hazard_results,
        }
        if _env_flag("CYCLE_DEBUG") or _env_flag("DEBUG_CYCLE"):
            sections["forwarding_debug"] = {
                "schema_version": FORWARDING_SCHEMA_VERSION,
                "probe_suite_version": FORWARDING_PROBE_SUITE_VERSION,
                "implementation_revision": FORWARDING_IMPLEMENTATION_REVISION,
                "run_id": run_id,
                "pipeline_interface": pipeline_interface,
                "probes": debug_results,
            }
        _write_label_sections(
            labels_file, processor_name, sections,
            remove=() if "forwarding_debug" in sections else ("forwarding_debug",),
        )
        _write_forwarding_progress(
            output_dir, processor_name, "artifact_write",
            terminal_state="completed",
            elapsed_seconds=results["execution"]["elapsed_seconds"],
            full_pipeline_finalization_count=(
                pipeline_observer.full_finalization_count
            ),
        )

        dut._log.info(
            "[forwarding] probe results: %s",
            {name: value.get("status") for name, value in results.items() if isinstance(value, dict)},
        )

        return results

    except Exception as exc:
        try:
            _write_forwarding_progress(
                output_dir, processor_name, "artifact_write",
                terminal_state="failed", error_type=type(exc).__name__,
                elapsed_seconds=round(
                    _wall_time.monotonic() - execution_started, 6,
                ),
            )
        except OSError:
            pass
        try:
            write_pipeline_interface(output_dir, processor_name, {
                "schema_version": 4,
                "discovery_version": PIPELINE_INTERFACE_DISCOVERY_VERSION,
                "implementation_revision": FORWARDING_IMPLEMENTATION_REVISION,
                "state": "failed",
                "error": str(exc),
                "stages": [],
                "capabilities": {
                    "consumer_stage_observable": False,
                    "execute_stage_observable": False,
                    "memory_stage_observable": False,
                    "multi_lane": False,
                    "lane_identity": False,
                    "source_ids": False,
                    "operand_values": False,
                    "store_data_capture": False,
                    "writeback_event": False,
                    "phase_ordering": False,
                    "sampling_phases": False,
                },
            })
        except OSError:
            pass
        results = {
            "schema_version": FORWARDING_SCHEMA_VERSION,
            "probe_suite_version": FORWARDING_PROBE_SUITE_VERSION,
            "implementation_revision": FORWARDING_IMPLEMENTATION_REVISION,
            "execution": _forwarding_execution_record(
                "failed", run_id, reason=str(exc),
                error_type=type(exc).__name__,
                elapsed_seconds=round(
                    _wall_time.monotonic() - execution_started, 6,
                ),
                phase_timings_seconds=phase_timings,
                full_pipeline_finalization_count=getattr(
                    locals().get("pipeline_observer"),
                    "full_finalization_count", 0,
                ),
            ),
            "applicable": True,
        }
        _write_label_sections(
            labels_file, processor_name, {"forwarding": results},
            remove=("forwarding_debug", "hazard_handling"),
        )
        raise

    finally:
        program_memory.select(CYCLE_SIGNATURE)

def record_not_applicable(dut):
    """Persist a fresh not-applicable forwarding result and interface artifact."""
    output_dir = os.environ.get("OUTPUT_DIR", "default")
    processor_name = os.path.basename(output_dir)
    labels_file = os.path.join(output_dir, f"{processor_name}_labels.json")
    result = {
        "schema_version": FORWARDING_SCHEMA_VERSION,
        "probe_suite_version": FORWARDING_PROBE_SUITE_VERSION,
        "implementation_revision": FORWARDING_IMPLEMENTATION_REVISION,
        "execution": _forwarding_execution_record("not_applicable"),
        "applicable": False,
    }
    _write_label_sections(
        labels_file, processor_name, {"forwarding": result},
        remove=("forwarding_debug", "hazard_handling"),
    )
    try:
        write_pipeline_interface(output_dir, processor_name, {
            "schema_version": 4,
            "discovery_version": PIPELINE_INTERFACE_DISCOVERY_VERSION,
            "implementation_revision": FORWARDING_IMPLEMENTATION_REVISION,
            "state": "unavailable",
            "reason": "forwarding is not applicable to the execution model",
            "stages": [],
            "capabilities": {
                name: False for name in (
                    "consumer_stage_observable", "execute_stage_observable",
                    "memory_stage_observable", "multi_lane", "lane_identity",
                    "source_ids", "operand_values", "store_data_capture",
                    "writeback_event", "phase_ordering", "sampling_phases",
                )
            },
        })
    except OSError as exc:
        dut._log.warning("Unable to write pipeline-interface result: %s", exc)
    return result
