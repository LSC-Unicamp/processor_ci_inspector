"""Branch-prediction discovery."""

try:
    from ._discovery_shared import (
        BRANCH_PREDICTION_PROBES,
        BRANCH_RESOLUTION_PROBES,
        CYCLE_SIGNATURE,
        Counter,
        DataMemory,
        Timer,
        _STRONG_PREDICTION_EVIDENCE,
        _env_flag,
        _is_pipeline_classification,
        _load_optional_internal_data,
        _load_optional_internal_program,
        _load_regfile_metadata,
        _measurement_cycle_budget,
        _observe_probe_commits,
        _probe_counter_delta,
        _probe_counter_snapshot,
        _resolve_write_interface,
        _safe_signal_int,
        direction_sequence_probe,
        json,
        long_history_probe,
        long_history_sweep,
        loop_predictor_probe,
        median,
        os,
        paired_timing_probes,
        path_history_probe,
        path_history_sweep,
        power_of_two_alias_sweep,
        program_memory,
        ras_depth_sweep,
    )
except ImportError:
    from _discovery_shared import (
        BRANCH_PREDICTION_PROBES,
        BRANCH_RESOLUTION_PROBES,
        CYCLE_SIGNATURE,
        Counter,
        DataMemory,
        Timer,
        _STRONG_PREDICTION_EVIDENCE,
        _env_flag,
        _is_pipeline_classification,
        _load_optional_internal_data,
        _load_optional_internal_program,
        _load_regfile_metadata,
        _measurement_cycle_budget,
        _observe_probe_commits,
        _probe_counter_delta,
        _probe_counter_snapshot,
        _resolve_write_interface,
        _safe_signal_int,
        direction_sequence_probe,
        json,
        long_history_probe,
        long_history_sweep,
        loop_predictor_probe,
        median,
        os,
        paired_timing_probes,
        path_history_probe,
        path_history_sweep,
        power_of_two_alias_sweep,
        program_memory,
        ras_depth_sweep,
    )

def _sign_extend(value, bits):
    sign = 1 << (bits - 1)
    return (value & (sign - 1)) - (value & sign)

def _opcode(instruction):
    return int(instruction) & 0x7F

def _rd(instruction):
    return (int(instruction) >> 7) & 0x1F

def _rs1(instruction):
    return (int(instruction) >> 15) & 0x1F

def _funct3(instruction):
    return (int(instruction) >> 12) & 0x7

def _decode_i_immediate(instruction):
    return _sign_extend((int(instruction) >> 20) & 0xFFF, 12)

def _decode_branch_target(instruction, pc):
    instruction = int(instruction)
    immediate = (
        (((instruction >> 31) & 0x1) << 12)
        | (((instruction >> 7) & 0x1) << 11)
        | (((instruction >> 25) & 0x3F) << 5)
        | (((instruction >> 8) & 0xF) << 1)
    )
    return int(pc) + _sign_extend(immediate, 13)

def _decode_jal_target(instruction, pc):
    instruction = int(instruction)
    immediate = (
        (((instruction >> 31) & 0x1) << 20)
        | (((instruction >> 12) & 0xFF) << 12)
        | (((instruction >> 20) & 0x1) << 11)
        | (((instruction >> 21) & 0x3FF) << 1)
    )
    return int(pc) + _sign_extend(immediate, 21)

def _contiguous_memory_outcomes(spec, base=0):
    """Read True=taken outcomes written by branch_prediction._outcome_memory."""
    outcomes = []
    address = int(base)
    while address in spec.initial_memory:
        outcomes.append(int(spec.initial_memory[address]) == 0)
        address += 4
    return tuple(outcomes)

def _conditional_site(spec, offset, outcomes, warmup=0):
    instruction = spec.instructions[offset]
    if _opcode(instruction) != 0x63:
        raise ValueError(f"probe {spec.name}: offset {offset:#x} is not a branch")
    target = _decode_branch_target(instruction, offset)
    return {
        "kind": "conditional",
        "offset": int(offset),
        "target": target,
        "fallthrough": int(offset) + 4,
        "actual_outcomes": tuple(bool(item) for item in outcomes),
        "actual_targets": tuple(target if item else int(offset) + 4 for item in outcomes),
        "warmup": max(0, int(warmup)),
    }

def _derive_probe_metadata(spec):
    """Recover the dynamic control-flow contract encoded by each probe.

    Keeping this outside ProgramSpec avoids changing the existing model class.
    The metadata is derived from the generated image and the deterministic
    memory patterns in branch_prediction.py.
    """
    if spec.control_flow:
        return spec.control_flow
    name = spec.name
    primary = spec.consumer_offset
    sites = {}
    metadata = {"family": spec.dependency_kind, "primary_site": "primary", "sites": sites}

    if name.startswith("static_"):
        actual_taken = str(spec.pair_role).endswith("_taken") and not str(spec.pair_role).endswith("not_taken")
        sites["primary"] = _conditional_site(spec, primary, (actual_taken,), warmup=0)
        metadata["static_direction"] = "backward" if "backward" in name else "forward"
        return metadata

    if name == "local_alternating":
        outcomes = _contiguous_memory_outcomes(spec)
        sites["primary"] = _conditional_site(spec, primary, outcomes, warmup=16)
        return metadata

    if name in ("dynamic_one_bit", "dynamic_two_bit") or name.startswith("counter_hysteresis_"):
        outcomes = _contiguous_memory_outcomes(spec)
        sites["primary"] = _conditional_site(spec, primary, outcomes, warmup=max(0, len(outcomes) - 4))
        metadata["train_length"] = next((index for index, value in enumerate(outcomes) if not value), len(outcomes))
        metadata["opposite_outcomes"] = max(0, len(outcomes) - metadata["train_length"] - 1)
        return metadata

    if name == "local_history":
        local = _contiguous_memory_outcomes(spec, 0)
        sites["primary"] = _conditional_site(spec, primary, local, warmup=min(16, len(local) // 4))
        return metadata

    if name == "global_history":
        outcomes = _contiguous_memory_outcomes(spec, 0)
        sites["primary"] = _conditional_site(spec, primary, outcomes, warmup=min(16, len(outcomes) // 4))
        return metadata

    if name == "path_history" or name.startswith("path_history_depth_"):
        outcomes = _contiguous_memory_outcomes(spec, 0)
        sites["primary"] = _conditional_site(spec, primary, outcomes, warmup=min(16, len(outcomes) // 4))
        if name.startswith("path_history_depth_"):
            metadata["path_depth"] = int(name.rsplit("_", 1)[1])
        return metadata

    if name == "combined_history":
        global_outcomes = _contiguous_memory_outcomes(spec, 0)
        local_outcomes = _contiguous_memory_outcomes(spec, 0x400)
        sites["global"] = _conditional_site(
            spec, primary, global_outcomes, warmup=min(16, len(global_outcomes) // 4)
        )
        # The generator emits the local consumer as the next BEQ after the
        # global consumer.  Ignore the loop-closing BNE.
        later_beqs = [
            offset
            for offset, instruction in sorted(spec.instructions.items())
            if offset > primary and _opcode(instruction) == 0x63 and _funct3(instruction) == 0
        ]
        if not later_beqs:
            raise ValueError("combined_history probe has no local consumer branch")
        sites["local"] = _conditional_site(
            spec, later_beqs[0], local_outcomes, warmup=min(16, len(local_outcomes) // 4)
        )
        metadata["primary_site"] = "global"
        return metadata

    if name == "long_history" or name.startswith("long_history_distance_"):
        outcomes = _contiguous_memory_outcomes(spec, 0)
        sites["primary"] = _conditional_site(spec, primary, outcomes, warmup=min(16, len(outcomes) // 4))
        if name.startswith("long_history_distance_"):
            metadata["history_distance"] = int(name.rsplit("_", 1)[1])
        elif name == "long_history":
            metadata["history_distance"] = 16
        return metadata

    if name == "loop_predictor" or name.startswith("loop_predictor_trip_"):
        repetitions = _decode_i_immediate(spec.instructions[0])
        trip_count = _decode_i_immediate(spec.instructions[4])
        one_loop = (True,) * max(0, trip_count - 1) + (False,)
        outcomes = one_loop * max(0, repetitions)
        sites["primary"] = _conditional_site(spec, primary, outcomes, warmup=trip_count * 2)
        metadata.update({"trip_count": trip_count, "repetitions": repetitions})
        return metadata

    if name == "direct_btb":
        instruction = spec.instructions[primary]
        iterations = max(1, _decode_i_immediate(spec.instructions[0]))
        target = _decode_jal_target(instruction, primary)
        sites["primary"] = {
            "kind": "direct_jump",
            "offset": primary,
            "fallthrough": primary + 4,
            "targets": (target,),
            "actual_targets": (target,) * iterations,
            "warmup": 2,
        }
        return metadata

    if name == "indirect_constant_target":
        iterations = max(1, _decode_i_immediate(spec.instructions[0]))
        target = primary + 12  # JALR, two wrong-path NOPs, then target.
        sites["primary"] = {
            "kind": "indirect_jump",
            "offset": primary,
            "fallthrough": primary + 4,
            "targets": (target,),
            "actual_targets": (target,) * iterations,
            "warmup": 2,
        }
        return metadata

    if name == "indirect_alternating_target":
        iterations = max(1, _decode_i_immediate(spec.instructions[0]))
        target_a = primary + 12
        target_b = target_a + 16
        actual = tuple(target_a if index % 2 == 0 else target_b for index in range(iterations))
        sites["primary"] = {
            "kind": "indirect_jump",
            "offset": primary,
            "fallthrough": primary + 4,
            "targets": (target_a, target_b),
            "actual_targets": actual,
            "warmup": 4,
        }
        return metadata

    if name in ("ras_standard_link", "ras_nonstandard_link_control") or name.startswith("ras_link_x"):
        instruction = spec.instructions[primary]
        link_register = _rs1(instruction)
        call_offsets = sorted(
            offset
            for offset, candidate in spec.instructions.items()
            if _opcode(candidate) == 0x6F and _rd(candidate) == link_register
        )
        if len(call_offsets) != 2:
            raise ValueError(f"{name}: expected two calls using x{link_register}, found {call_offsets}")
        return_b, return_a = call_offsets[0] + 4, call_offsets[1] + 4
        selectors = _contiguous_memory_outcomes(spec, 0)
        actual = tuple(return_a if selected_a else return_b for selected_a in selectors)
        sites["primary"] = {
            "kind": "return",
            "offset": primary,
            "fallthrough": primary + 4,
            "targets": (return_a, return_b),
            "actual_targets": actual,
            "warmup": min(8, len(actual) // 4),
        }
        metadata["link_register"] = link_register
        return metadata

    raise KeyError(f"no branch-prediction metadata rule for {name}")

def _probe_metadata(spec):
    """Return and cache the declarative control-flow contract on ProgramSpec."""
    if spec.control_flow:
        return spec.control_flow
    metadata = _derive_probe_metadata(spec)
    spec.control_flow.update(metadata)
    return spec.control_flow

def _normalized_fetch_events(fetch_events):
    result = []
    for sequence, item in enumerate(fetch_events):
        if item.get("offset") is None or item.get("cycle") is None:
            continue
        result.append({**item, "offset": int(item["offset"]), "cycle": int(item["cycle"]), "_sequence": sequence})
    result.sort(key=lambda item: (item["cycle"], item["_sequence"]))
    return result

def _fetch_baseline(events):
    """Median cycle spacing for ordinary sequential fetches in this run."""
    deltas = []
    for first, second in zip(events, events[1:]):
        if second["offset"] == first["offset"] + 4 and second["cycle"] >= first["cycle"]:
            deltas.append(second["cycle"] - first["cycle"])
    return median(deltas) if deltas else 1

def _analyze_control_site(
    fetch_events, site, prediction_events=None, redirect_events=None,
    resolution_events=None, dependency_barrier_cycle=None,
):
    events = _normalized_fetch_events(fetch_events)
    baseline = _fetch_baseline(events)
    branch_offset = int(site["offset"])
    fallthrough = int(site["fallthrough"])
    actual_targets = tuple(int(item) for item in site["actual_targets"])
    possible_targets = set(int(item) for item in site.get("targets", ()))
    if site.get("target") is not None:
        possible_targets.add(int(site["target"]))
    candidates = possible_targets | {fallthrough}
    explicit_predictions = [
        event for event in (prediction_events or [])
        if event.get("offset") == branch_offset
    ]
    explicit_resolutions = [
        event for event in (resolution_events or [])
        if event.get("offset") == branch_offset
    ]
    branch_events = [event for event in events if event.get("offset") == branch_offset]

    def same_context(first, second):
        for key in ("context_id", "epoch_id"):
            if first.get(key) is not None and second.get(key) != first.get(key):
                return False
        return True

    # Standardized wrapper events may be emitted at lookup, admission, or one
    # registered stage later. Calibrate that fixed phase offset from matching
    # PCs instead of assuming +/-1 cycle or pairing unrelated events by list
    # index. The latter incorrectly promoted sparse lookup samples on replaying
    # frontends into predictions for every dynamic occurrence.
    prediction_latency_samples = []
    for prediction in explicit_predictions:
        candidates_after = [
            event for event in branch_events
            if -4 <= int(event["cycle"]) - int(prediction["cycle"]) <= 32
            and same_context(event, prediction)
        ]
        if candidates_after:
            nearest = min(
                candidates_after,
                key=lambda event: abs(int(event["cycle"]) - int(prediction["cycle"])),
            )
            prediction_latency_samples.append(
                int(nearest["cycle"]) - int(prediction["cycle"])
            )
    prediction_latency = None
    if prediction_latency_samples:
        counts = Counter(prediction_latency_samples)
        prediction_latency = min(
            counts, key=lambda value: (-counts[value], abs(value), value)
        )

    def explicit_for(branch_event, occurrence_index):
        del occurrence_index
        if prediction_latency is None:
            return None
        calibrated = [
            event for event in explicit_predictions
            if abs(
                (int(branch_event["cycle"]) - int(event["cycle"]))
                - int(prediction_latency)
            ) <= 1
            and same_context(branch_event, event)
        ]
        if not calibrated:
            return None
        return min(
            calibrated,
            key=lambda event: abs(
                (int(branch_event["cycle"]) - int(event["cycle"]))
                - int(prediction_latency)
            ),
        )

    def matching_redirect(branch_event, first_path_event, actual_cycle):
        if actual_cycle is None:
            return None
        return next((
            event for event in (redirect_events or [])
            if int(first_path_event["cycle"]) <= int(event["cycle"]) <= int(actual_cycle)
            and same_context(branch_event, event)
        ), None)

    def resolution_for(branch_event, next_branch_cycle):
        return next((
            event for event in explicit_resolutions
            if int(event["cycle"]) >= int(branch_event["cycle"])
            and (next_branch_cycle is None or int(event["cycle"]) < int(next_branch_cycle))
            and same_context(branch_event, event)
        ), None)

    occurrences = []
    cursor = 0
    for occurrence_index, actual_target in enumerate(actual_targets):
        branch_index = next(
            (index for index in range(cursor, len(events)) if events[index]["offset"] == branch_offset),
            None,
        )
        if branch_index is None:
            break
        branch_event = events[branch_index]

        next_branch_index = next(
            (
                index for index in range(branch_index + 1, len(events))
                if events[index]["offset"] == branch_offset
                and same_context(branch_event, events[index])
            ),
            len(events),
        )
        next_branch_cycle = (
            events[next_branch_index]["cycle"] if next_branch_index < len(events) else None
        )
        resolution = resolution_for(branch_event, next_branch_cycle)

        path_events = [
            (index, event)
            for index, event in enumerate(
                events[branch_index + 1 : next_branch_index], start=branch_index + 1
            )
            if event["offset"] in candidates
            and same_context(branch_event, event)
            and (
                events[branch_index].get("transaction_id") is None
                or event.get("transaction_id") != events[branch_index].get("transaction_id")
            )
        ]
        if not path_events:
            explicit = explicit_for(branch_event, occurrence_index)
            predicted_taken = explicit.get("predicted_taken") if explicit is not None else None
            predicted_target = explicit.get("predicted_target") if explicit is not None else None
            if predicted_target is None and predicted_taken is not None and site["kind"] == "conditional":
                predicted_target = int(site["target"]) if predicted_taken else fallthrough
            occurrence = {
                "index": occurrence_index,
                "branch_cycle": events[branch_index]["cycle"],
                "actual_target": actual_target,
                "predicted_target": predicted_target,
                "observable_prediction": explicit is not None,
                "correct": predicted_target == actual_target if predicted_target is not None else None,
                "reason": "explicit prediction decision" if explicit is not None else "no target or fall-through fetch was observed",
                "evidence_grade": "explicit_prediction" if explicit is not None else "ambiguous",
                "prediction_source": "standardized_prediction" if explicit is not None else None,
                "context_id": branch_event.get("context_id"),
                "epoch_id": branch_event.get("epoch_id"),
                "resolution_cycle": resolution.get("cycle") if resolution else None,
                "branch_to_resolution_latency": (
                    int(resolution["cycle"]) - int(branch_event["cycle"])
                    if resolution else None
                ),
                "dependency_barrier_cycle": dependency_barrier_cycle,
            }
            if site["kind"] == "conditional":
                expected_taken = bool(site["actual_outcomes"][occurrence_index])
                occurrence["actual_taken"] = expected_taken
                occurrence["predicted_taken"] = predicted_taken
                occurrence["resolution_mismatch"] = bool(
                    resolution is not None and (
                        resolution.get("actual_taken") != expected_taken
                        or (
                            resolution.get("actual_target") is not None
                            and int(resolution["actual_target"]) != int(actual_target)
                        )
                    )
                )
            occurrences.append(occurrence)
            cursor = branch_index + 1
            continue

        earliest_cycle = min(event["cycle"] for _, event in path_events)
        earliest = [(index, event) for index, event in path_events if event["cycle"] == earliest_cycle]
        earliest_offsets = sorted({event["offset"] for _, event in earliest})
        predicted_target = earliest_offsets[0] if len(earliest_offsets) == 1 else None
        first_path_index = min(index for index, _ in earliest)

        actual_index = next(
            (
                index
                for index in range(branch_index + 1, next_branch_index)
                if events[index]["offset"] == actual_target
                and same_context(branch_event, events[index])
            ),
            None,
        )
        branch_cycle = events[branch_index]["cycle"]
        path_latency = earliest_cycle - branch_cycle
        # A wrong first path is necessarily speculative.  A correct first path
        # is called speculative only when it arrives at approximately the
        # ordinary fetch cadence; a delayed correct path may simply reflect
        # waiting for branch resolution.
        observable_prediction = predicted_target is not None and (
            predicted_target != actual_target or path_latency <= baseline + 1
        )
        correct = (
            predicted_target == actual_target
            if predicted_target is not None and observable_prediction
            else None
        )

        actual_cycle = events[actual_index]["cycle"] if actual_index is not None else None
        redirect = matching_redirect(branch_event, earliest[0][1], actual_cycle)
        redirect_latency = None
        if predicted_target is not None and predicted_target != actual_target and actual_cycle is not None:
            redirect_latency = actual_cycle - earliest_cycle

        wrong_path_fetches = 0
        if actual_index is not None:
            wrong_path_fetches = sum(
                1
                for event in events[branch_index + 1 : actual_index]
                if event["offset"] != actual_target
            )

        occurrence = {
            "index": occurrence_index,
            "branch_cycle": branch_cycle,
            "actual_target": actual_target,
            "predicted_target": predicted_target,
            "observable_prediction": observable_prediction,
            "correct": correct,
            "path_latency": path_latency,
            "redirect_latency": redirect_latency,
            "wrong_path_fetches": wrong_path_fetches,
            "ambiguous_same_cycle_paths": len(earliest_offsets) > 1,
            "context_id": branch_event.get("context_id"),
            "epoch_id": branch_event.get("epoch_id"),
            "resolution_cycle": resolution.get("cycle") if resolution else None,
            "branch_to_resolution_latency": (
                int(resolution["cycle"]) - int(branch_cycle) if resolution else None
            ),
            "dependency_barrier_cycle": dependency_barrier_cycle,
        }
        expected_taken = (
            bool(site["actual_outcomes"][occurrence_index])
            if site["kind"] == "conditional" else None
        )
        resolution_mismatch = bool(
            resolution is not None and (
                (expected_taken is not None and resolution.get("actual_taken") != expected_taken)
                or (
                    resolution.get("actual_target") is not None
                    and int(resolution["actual_target"]) != int(actual_target)
                )
            )
        )
        occurrence["resolution_mismatch"] = resolution_mismatch
        explicit = explicit_for(branch_event, occurrence_index)
        if explicit is not None and explicit.get("predicted_target") is not None:
            occurrence["predicted_target"] = explicit["predicted_target"]
            occurrence["observable_prediction"] = True
            occurrence["correct"] = explicit["predicted_target"] == actual_target
            occurrence["prediction_source"] = "standardized_prediction"
            occurrence["evidence_grade"] = "explicit_prediction"
        elif predicted_target is not None and predicted_target != actual_target and (
            redirect is not None or earliest[0][1].get("squashed")
        ):
            occurrence["evidence_grade"] = "same_context_wrong_path_then_redirect"
            occurrence["prediction_source"] = "accepted_wrong_path"
        elif predicted_target is not None and resolution is not None and earliest_cycle < int(resolution["cycle"]):
            occurrence["evidence_grade"] = "pre_resolution_accepted_fetch"
            occurrence["prediction_source"] = "explicit_resolution_boundary"
        elif (
            predicted_target is not None and dependency_barrier_cycle is not None
            and earliest_cycle < int(dependency_barrier_cycle)
        ):
            occurrence["evidence_grade"] = "pre_resolution_accepted_fetch"
            occurrence["prediction_source"] = "dependency_load_response_barrier"
        elif predicted_target is not None and earliest[0][1].get("speculative"):
            occurrence["evidence_grade"] = "pre_resolution_accepted_fetch"
            occurrence["prediction_source"] = "standardized_speculative_fetch"
        elif predicted_target is not None and observable_prediction:
            occurrence["evidence_grade"] = "timing_only"
            occurrence["prediction_source"] = "fetch_cadence_inference"
        else:
            occurrence["evidence_grade"] = "resolved_path" if predicted_target == actual_target else "ambiguous"
        if site["kind"] == "conditional":
            actual_taken = bool(site["actual_outcomes"][occurrence_index])
            occurrence["actual_taken"] = actual_taken
            occurrence["predicted_taken"] = (
                predicted_target == int(site["target"])
                if predicted_target is not None and observable_prediction
                else None
            )
            explicit = explicit_for(branch_event, occurrence_index)
            if explicit is not None and explicit.get("predicted_taken") is not None:
                explicit_taken = explicit["predicted_taken"]
                occurrence["predicted_taken"] = explicit_taken
                occurrence["predicted_target"] = int(site["target"]) if explicit_taken else fallthrough
                occurrence["observable_prediction"] = True
                occurrence["correct"] = explicit_taken == actual_taken
                occurrence["prediction_source"] = "standardized_prediction"
                occurrence["evidence_grade"] = "explicit_prediction"
        occurrences.append(occurrence)
        cursor = next_branch_index if next_branch_index < len(events) else (
            max(first_path_index, actual_index if actual_index is not None else first_path_index) + 1
        )

    expected_count = len(actual_targets)
    observed_count = len(occurrences)
    return {
        "expected_occurrences": expected_count,
        "observed_occurrences": observed_count,
        "occurrence_coverage": observed_count / expected_count if expected_count else 0.0,
        "fetch_baseline_cycles": baseline,
        "prediction_latency_cycles": prediction_latency,
        "prediction_latency_samples": prediction_latency_samples,
        "warmup": int(site.get("warmup", 0)),
        "occurrences": occurrences,
    }

def _summarize_site_analysis(analysis):
    occurrences = analysis["occurrences"]
    raw_predictions = [item for item in occurrences if item.get("correct") is not None]
    predictions = [item for item in raw_predictions if _strong_prediction_occurrence(item)]
    warmup = min(analysis.get("warmup", 0), len(occurrences))
    warm = [
        item for item in occurrences[warmup:]
        if item.get("correct") is not None and _strong_prediction_occurrence(item)
    ]
    latencies = [item["path_latency"] for item in predictions if item.get("path_latency") is not None]
    warm_latencies = [item["path_latency"] for item in warm if item.get("path_latency") is not None]

    result = {
        "expected_occurrences": analysis["expected_occurrences"],
        "observed_occurrences": analysis["observed_occurrences"],
        "predictions_observed": len(predictions),
        "raw_path_inferences": len(raw_predictions),
        "evidence_grades": dict(Counter(
            item.get("evidence_grade", "ungraded") for item in occurrences
        )),
        "prediction_coverage": (
            len(predictions) / analysis["expected_occurrences"]
            if analysis["expected_occurrences"]
            else 0.0
        ),
        "accuracy": sum(bool(item["correct"]) for item in predictions) / len(predictions) if predictions else None,
        "warm_accuracy": sum(bool(item["correct"]) for item in warm) / len(warm) if warm else None,
        "mispredictions": sum(item.get("correct") is False for item in predictions),
        "fetch_baseline_cycles": analysis["fetch_baseline_cycles"],
        "prediction_latency_cycles": analysis.get("prediction_latency_cycles"),
        "prediction_latency_sample_count": len(analysis.get("prediction_latency_samples", ())),
        "median_path_latency": median(latencies) if latencies else None,
        "warm_median_path_latency": median(warm_latencies) if warm_latencies else None,
    }
    if occurrences and occurrences[0].get("predicted_taken") is not None:
        result["first_prediction_taken"] = occurrences[0]["predicted_taken"]
    conditional_predictions = [item for item in predictions if "actual_taken" in item]
    for outcome, label in ((True, "taken_accuracy"), (False, "not_taken_accuracy")):
        matching = [item for item in conditional_predictions if item["actual_taken"] is outcome]
        result[label] = (
            sum(bool(item["correct"]) for item in matching) / len(matching)
            if matching
            else None
        )
    return result

def _branch_probe_cycle_budget(spec, metadata, regfile_metadata, pipeline_depth):
    base_budget = int(_measurement_cycle_budget(regfile_metadata))
    longest_site = max(
        (len(site.get("actual_targets", ())) for site in metadata["sites"].values()),
        default=1,
    )
    static_size = max(1, len(spec.instructions))
    depth = max(1, int(pipeline_depth or 1))
    estimate = 256 + longest_site * (2 * static_size + depth + 16)
    return min(250_000, max(base_budget, estimate))

def _trial_site_occurrences(trial, site_name=None):
    site_name = site_name or trial["metadata"]["primary_site"]
    return trial["site_analysis"][site_name]["occurrences"]

def _strong_prediction_occurrence(occurrence):
    """Return true only for a decision proven to precede branch resolution."""
    grade = occurrence.get("evidence_grade")
    # Unit fixtures and callers predating evidence grades represent explicit
    # synthetic decisions. Reconstructed occurrences always carry a grade.
    return grade is None or grade in _STRONG_PREDICTION_EVIDENCE

def _all_site_occurrences(trials, site_name=None, warm=True, strong_only=False):
    combined = []
    for trial in trials:
        chosen = site_name or trial["metadata"]["primary_site"]
        analysis = trial["site_analysis"][chosen]
        occurrences = analysis["occurrences"]
        if warm:
            occurrences = occurrences[min(analysis.get("warmup", 0), len(occurrences)) :]
        if strong_only:
            occurrences = [item for item in occurrences if _strong_prediction_occurrence(item)]
        combined.extend(occurrences)
    return combined

def _trials_valid(*trial_groups):
    trials = []
    for group in trial_groups:
        trials.extend(group)
    return bool(trials) and all(trial.get("valid", trial.get("complete", False)) for trial in trials)

def _accuracy_capability(trials, site_name=None, threshold=0.75, label="predictor"):
    complete = [trial["complete"] for trial in trials]
    occurrences = _all_site_occurrences(trials, site_name=site_name, warm=True)
    predicted = [
        item for item in occurrences
        if item.get("correct") is not None and _strong_prediction_occurrence(item)
    ]
    accuracy = sum(bool(item["correct"]) for item in predicted) / len(predicted) if predicted else None
    coverage = len(predicted) / len(occurrences) if occurrences else 0.0
    outcomes = [item.get("actual_taken") for item in occurrences if item.get("actual_taken") is not None]
    taken_fraction = sum(bool(item) for item in outcomes) / len(outcomes) if outcomes else None
    bias_baseline = max(taken_fraction, 1.0 - taken_fraction) if taken_fraction is not None else 0.5
    required_accuracy = max(float(threshold), min(0.95, bias_baseline + 0.10))
    result = {
        "status": "inconclusive",
        "present": None,
        "capability": label,
        "architecturally_complete": all(complete),
        "warm_predictions": len(predicted),
        "warm_prediction_coverage": coverage,
        "warm_accuracy": accuracy,
        "outcome_bias_baseline": bias_baseline,
        "required_accuracy": required_accuracy,
        "confidence": 0.35,
    }
    if not _trials_valid(trials):
        result["evidence"] = "one or more probe runs failed completion, fetch visibility, or occurrence coverage validation"
    elif not predicted or coverage < 0.75:
        result.update({
            "status": "not_observable",
            "present": None,
            "confidence": 0.35,
            "evidence": (
                "speculative next-path prediction coverage is below 75%; "
                "partial fetch visibility or resolved redirects can mimic learned behavior"
            ),
        })
    elif accuracy >= required_accuracy:
        result.update({
            "status": "detected",
            "present": True,
            "confidence": min(0.95, 0.7 + 0.25 * coverage),
            "evidence": f"warm accuracy {accuracy:.3f} exceeds bias-aware threshold {required_accuracy:.2f}",
        })
    elif accuracy <= 0.60:
        result.update({
            "status": "not_detected",
            "present": False,
            "confidence": 0.75,
            "evidence": f"warm accuracy {accuracy:.3f} is close to or below a simple chance/bias baseline",
        })
    else:
        result["evidence"] = f"warm accuracy {accuracy:.3f} lies in the inconclusive range"
    return result

def _majority(values):
    values = [value for value in values if value is not None]
    if not values:
        return None
    true_count = sum(bool(value) for value in values)
    if true_count * 2 == len(values):
        return None
    return true_count * 2 > len(values)

def _classify_static_policy(trials_by_name):
    predictions = {}
    speculative_cases = 0
    for name, trials in trials_by_name.items():
        first_predictions = []
        for trial in trials:
            occurrences = _trial_site_occurrences(trial)
            first_predictions.append(occurrences[0].get("predicted_taken") if occurrences else None)
        predictions[name] = _majority(first_predictions)
        speculative_cases += predictions[name] is not None

    f_t = predictions.get("static_forward_taken")
    f_n = predictions.get("static_forward_not_taken")
    b_t = predictions.get("static_backward_taken")
    b_n = predictions.get("static_backward_not_taken")
    result = {
        "status": "inconclusive",
        "present": None,
        "policy": "unknown",
        "cold_predictions": predictions,
        "confidence": 0.35,
    }
    if not all(_trials_valid(trials) for trials in trials_by_name.values()):
        result["evidence"] = "one or more cold-policy trials failed validity checks"
        return result
    if speculative_cases == 0:
        result.update({
            "status": "not_observable",
            "present": None,
            "policy": "no_observable_cold_speculation",
            "confidence": 0.7,
            "evidence": "all cold branches waited for a resolved path or produced ambiguous fetches",
        })
    elif all(value is False for value in (f_t, f_n, b_t, b_n)):
        result.update({
            "status": "detected", "present": True, "policy": "static_sequential",
            "confidence": 0.9, "evidence": "all cold conditional branches first fetched fall-through",
        })
    elif all(value is True for value in (f_t, f_n, b_t, b_n)):
        result.update({
            "status": "detected", "present": True, "policy": "static_taken",
            "confidence": 0.9, "evidence": "all cold conditional branches first fetched the branch target",
        })
    elif f_t is False and f_n is False and b_t is True and b_n is True:
        result.update({
            "status": "detected", "present": True, "policy": "static_btfnt",
            "confidence": 0.92, "evidence": "cold forward branches predicted not taken and backward branches predicted taken",
        })
    else:
        result.update({
            "status": "detected", "present": True, "policy": "dynamic_or_other_cold_policy",
            "confidence": 0.55,
            "evidence": "cold predictions do not match always-taken, sequential, or BTFNT",
        })
    return result

def _outcome_correctness(trials, index):
    values = []
    for trial in trials:
        occurrences = _trial_site_occurrences(trial)
        values.append(
            occurrences[index].get("correct")
            if len(occurrences) > index and _strong_prediction_occurrence(occurrences[index])
            else None
        )
    return _majority(values)

def _classify_counter_hysteresis(one_bit_trials, two_bit_trials):
    one_meta = one_bit_trials[0]["metadata"]
    two_meta = two_bit_trials[0]["metadata"]
    one_train = int(one_meta["train_length"])
    two_train = int(two_meta["train_length"])

    one_exception = _outcome_correctness(one_bit_trials, one_train)
    one_final_taken = _outcome_correctness(one_bit_trials, one_train + 1)
    two_first_exception = _outcome_correctness(two_bit_trials, two_train)
    two_second_exception = _outcome_correctness(two_bit_trials, two_train + 1)
    two_final_taken = _outcome_correctness(two_bit_trials, two_train + 2)

    result = {
        "status": "inconclusive",
        "present": None,
        "classification": "unknown",
        "confidence": 0.35,
        "one_exception_probe": {
            "exception_correct": one_exception,
            "final_taken_correct": one_final_taken,
        },
        "two_exception_probe": {
            "first_exception_correct": two_first_exception,
            "second_exception_correct": two_second_exception,
            "final_taken_correct": two_final_taken,
        },
    }
    observed = [one_exception, one_final_taken, two_first_exception, two_second_exception, two_final_taken]
    if not _trials_valid(one_bit_trials, two_bit_trials):
        result["evidence"] = "one or more hysteresis trials failed validity checks"
    elif all(item is None for item in observed):
        result.update({
            "status": "not_observable", "present": None, "classification": "no_observable_dynamic_prediction",
            "confidence": 0.35, "evidence": "the counter probes exposed no unambiguous speculative predictions",
        })
    # Both probes are trained taken.  A stateful predictor must therefore
    # initially predict taken for the first not-taken exception (and be
    # wrong).  Without this gate an always-not-taken/static-sequential core
    # produces the same final-T misses as a one-bit predictor and was
    # previously mislabeled as rapid adaptation.
    elif (
        one_exception is False
        and two_first_exception is False
        and one_final_taken is False
        and two_second_exception is True
    ):
        result.update({
            "status": "detected", "present": True, "classification": "one_bit_last_outcome_equivalent",
            "confidence": 0.9,
            "evidence": "the same branch PC adapts after one opposite outcome; this proves stateful direction prediction but not a specific counter structure",
        })
    elif (
        one_exception is False
        and two_first_exception is False
        and one_final_taken is True
        and two_second_exception is False
        and two_final_taken is False
    ):
        result.update({
            "status": "detected", "present": True, "classification": "two_bit_hysteresis",
            "confidence": 0.92,
            "evidence": "one exception preserves the trained direction; two consecutive exceptions cross the prediction threshold",
        })
    elif (
        one_exception is False
        and two_first_exception is False
        and one_final_taken is True
        and two_final_taken is True
    ):
        result.update({
            "status": "detected", "present": True, "classification": "stronger_than_two_bit_or_overridden",
            "confidence": 0.65,
            "evidence": "the trained prediction survives two opposite outcomes",
        })
    elif one_exception is True and two_first_exception is True:
        result.update({
            "status": "not_detected", "present": False,
            "classification": "no_trained_direction_state",
            "confidence": 0.88,
            "evidence": "after taken training, both probes still predicted the first not-taken exception correctly; the observations match a static/sequential baseline",
        })
    else:
        result["evidence"] = "observed transition pattern does not uniquely match one- or two-bit hysteresis"
    return result

def _classify_loop_predictor(trials):
    exits = []
    continuations = []
    for trial in trials:
        for item in _trial_site_occurrences(trial):
            if not _strong_prediction_occurrence(item):
                continue
            if item.get("actual_taken") is False:
                exits.append(item)
            elif item.get("actual_taken") is True:
                continuations.append(item)
    predicted_exits = [item for item in exits if item.get("correct") is not None]
    split = max(1, len(predicted_exits) // 3)
    early = predicted_exits[:split]
    late = predicted_exits[-split:]
    early_accuracy = sum(bool(item["correct"]) for item in early) / len(early) if early else None
    late_accuracy = sum(bool(item["correct"]) for item in late) / len(late) if late else None
    continuation_predictions = [item for item in continuations if item.get("correct") is not None]
    continuation_accuracy = (
        sum(bool(item["correct"]) for item in continuation_predictions) / len(continuation_predictions)
        if continuation_predictions
        else None
    )
    result = {
        "status": "inconclusive",
        "present": None,
        "classification": "fixed_trip_loop_learning",
        "exit_predictions": len(predicted_exits),
        "early_exit_accuracy": early_accuracy,
        "late_exit_accuracy": late_accuracy,
        "continuation_accuracy": continuation_accuracy,
        "confidence": 0.35,
    }
    if not predicted_exits:
        result.update({
            "status": "not_observable", "present": None, "confidence": 0.35,
            "evidence": "loop-exit predictions were not visible on the fetch interface",
        })
    elif late_accuracy is not None and late_accuracy >= 0.75 and (
        early_accuracy is None or late_accuracy - early_accuracy >= 0.25
    ):
        result.update({
            "status": "detected", "present": True, "confidence": 0.78,
            "evidence": "fixed-trip loop exits become predictable after repeated executions",
        })
    elif late_accuracy is not None and late_accuracy <= 0.25:
        result.update({
            "status": "not_detected", "present": False, "confidence": 0.75,
            "evidence": "late loop exits remain consistently mispredicted",
        })
    else:
        result["evidence"] = "fixed-trip exit behavior is not strong enough to identify a dedicated loop component"
    return result

def _warm_accuracy(trials, site_name=None):
    all_occurrences = _all_site_occurrences(trials, site_name=site_name, warm=True)
    occurrences = [item for item in all_occurrences if _strong_prediction_occurrence(item)]
    predicted = [item for item in occurrences if item.get("correct") is not None]
    return (
        sum(bool(item["correct"]) for item in predicted) / len(predicted) if predicted else None,
        len(predicted),
        len(all_occurrences),
    )

def _classify_direct_target(trials):
    accuracy, predicted_count, total = _warm_accuracy(trials)
    first_latencies = []
    warm_latencies = []
    first_correct = []
    for trial in trials:
        analysis = trial["site_analysis"][trial["metadata"]["primary_site"]]
        occurrences = analysis["occurrences"]
        if occurrences:
            first_latencies.append(occurrences[0].get("path_latency"))
            first_correct.append(occurrences[0].get("correct"))
        warm_latencies.extend(
            item.get("path_latency")
            for item in occurrences[max(2, analysis.get("warmup", 0)) :]
            if item.get("path_latency") is not None and item.get("correct") is not None
        )
    cold_latency = median([item for item in first_latencies if item is not None]) if any(item is not None for item in first_latencies) else None
    warm_latency = median(warm_latencies) if warm_latencies else None
    result = {
        "status": "inconclusive", "present": None, "classification": "direct_target_prediction",
        "warm_accuracy": accuracy, "warm_predictions": predicted_count,
        "cold_path_latency": cold_latency, "warm_path_latency": warm_latency,
        "confidence": 0.35,
    }
    if accuracy is None:
        result.update({
            "status": "not_observable", "present": None, "confidence": 0.35,
            "evidence": "no speculative direct-jump target fetch was visible",
        })
    elif accuracy >= 0.9:
        trained_improvement = (
            cold_latency is not None and warm_latency is not None and warm_latency < cold_latency
        ) or any(value is False for value in first_correct if value is not None)
        result.update({
            "status": "detected", "present": True,
            "classification": "trainable_direct_btb" if trained_improvement else "direct_target_prediction",
            "confidence": 0.9 if trained_improvement else 0.75,
            "evidence": (
                "warm direct jumps fetch the target accurately and improve relative to the cold occurrence"
                if trained_improvement
                else "direct jumps fetch their targets accurately; timing does not prove a trainable BTB"
            ),
        })
    elif accuracy <= 0.6:
        result.update({
            "status": "not_detected", "present": False, "confidence": 0.75,
            "evidence": "repeated direct jumps do not produce reliable early target fetches",
        })
    else:
        result["evidence"] = "direct target behavior is partially predictive but unstable"
    return result

def _classify_indirect_targets(constant_trials, alternating_trials):
    constant_accuracy, constant_predictions, _ = _warm_accuracy(constant_trials)
    alternating_accuracy, alternating_predictions, _ = _warm_accuracy(alternating_trials)
    result = {
        "status": "inconclusive", "present": None, "classification": "unknown",
        "constant_target_accuracy": constant_accuracy,
        "alternating_target_accuracy": alternating_accuracy,
        "constant_target_predictions": constant_predictions,
        "alternating_target_predictions": alternating_predictions,
        "confidence": 0.35,
    }
    speculative_misses = sum(
        occurrence.get("correct") is False and _strong_prediction_occurrence(occurrence)
        for trials in (constant_trials, alternating_trials)
        for trial in trials
        for occurrence in _trial_site_occurrences(trial)
    )
    result["speculative_misses"] = speculative_misses
    if not _trials_valid(constant_trials, alternating_trials):
        result["evidence"] = "one or more indirect-target trials failed validity checks"
    elif constant_accuracy is None and alternating_accuracy is None:
        result.update({
            "status": "not_observable", "present": None, "classification": "none_observed",
            "confidence": 0.35, "evidence": "no speculative JALR target prediction was visible",
        })
    elif constant_accuracy is not None and constant_accuracy >= 0.8 and speculative_misses:
        if alternating_accuracy is not None and alternating_accuracy >= 0.75:
            result.update({
                "status": "detected", "present": True,
                "classification": "multi_target_or_history_based",
                "confidence": 0.88,
                "evidence": "one JALR PC predicts an alternating two-target sequence after warm-up",
            })
        elif alternating_accuracy is None or alternating_accuracy <= 0.6:
            result.update({
                "status": "detected", "present": True, "classification": "last_target",
                "confidence": 0.82,
                "evidence": "constant targets are learned but alternating targets are not",
            })
        else:
            result.update({
                "status": "detected", "present": True, "classification": "indirect_target_basic",
                "confidence": 0.65,
                "evidence": "constant JALR targets are predictable, while multi-target behavior is ambiguous",
            })
    elif constant_accuracy is not None and constant_accuracy >= 0.8:
        result.update({
            "status": "inconclusive", "present": None,
            "classification": "resolved_target_not_distinguished",
            "confidence": 0.4,
            "evidence": "JALR targets were always the resolved target; without a visible cold miss or wrong-path target, early execution cannot be distinguished from prediction",
        })
    elif constant_accuracy is not None and constant_accuracy <= 0.6:
        result.update({
            "status": "not_detected", "present": False, "classification": "none_observed",
            "confidence": 0.75, "evidence": "even a repeated constant JALR target is not predicted reliably",
        })
    else:
        result["evidence"] = "indirect-target prediction accuracy lies in the inconclusive range"
    return result

def _classify_ras(standard_trials, control_trials):
    standard_accuracy, standard_predictions, _ = _warm_accuracy(standard_trials)
    control_accuracy, control_predictions, _ = _warm_accuracy(control_trials)
    advantage = (
        standard_accuracy - control_accuracy
        if standard_accuracy is not None and control_accuracy is not None
        else None
    )
    result = {
        "status": "inconclusive", "present": None,
        "standard_link_accuracy": standard_accuracy,
        "nonstandard_link_accuracy": control_accuracy,
        "standard_predictions": standard_predictions,
        "control_predictions": control_predictions,
        "accuracy_advantage": advantage,
        "confidence": 0.35,
    }
    if standard_accuracy is None:
        result.update({
            "status": "not_observable", "present": None, "confidence": 0.35,
            "evidence": "return-target prediction was not visible for the standard x1 link register",
        })
    elif standard_accuracy >= 0.8 and advantage is not None and advantage >= 0.20:
        result.update({
            "status": "detected", "present": True, "confidence": 0.9,
            "evidence": "returns through x1 are substantially more predictable than layout-matched returns through x10",
        })
    elif standard_accuracy >= 0.8 and control_accuracy is not None and control_accuracy >= 0.75:
        result.update({
            "status": "inconclusive", "present": None, "confidence": 0.5,
            "evidence": "both standard and nonstandard links are predicted; a generic indirect predictor can explain the result",
        })
    elif standard_accuracy <= 0.6:
        result.update({
            "status": "inconclusive", "present": None, "confidence": 0.4,
            "evidence": (
                "standard-link returns remain poorly predicted, but an ordinary return "
                "probe cannot distinguish RAS absence from unavailable speculative fetch "
                "visibility or target reconstruction"
            ),
        })
    else:
        result["evidence"] = "standard-link return prediction is not sufficiently distinct from the control"
    return result

def _classify_reset_retention(baseline_trials, training_trials, post_reset_trials):
    """Detect direction state that survives the wrapper's normal reset pulse."""
    all_trials = baseline_trials + training_trials + post_reset_trials
    if not all_trials or not _trials_valid(all_trials):
        return {
            "status": "inconclusive", "present": None, "confidence": 0.35,
            "classification": "not_measured",
            "evidence": "one or more reset-retention trials failed validity checks",
        }

    def first_prediction(trials):
        values = []
        for trial in trials:
            sites = list(trial.get("site_analysis", {}).values())
            occurrences = sites[0].get("occurrences", []) if sites else []
            values.append(occurrences[0].get("predicted_taken") if occurrences else None)
        return values

    baseline = first_prediction(baseline_trials)
    post_reset = first_prediction(post_reset_trials)
    observable = all(value is not None for value in baseline + post_reset)
    result = {
        "status": "inconclusive", "present": None, "confidence": 0.4,
        "classification": "predictor_reset_behavior_unobservable",
        "baseline_first_predictions_taken": baseline,
        "post_training_reset_first_predictions_taken": post_reset,
    }
    if not observable:
        result["evidence"] = "the first post-reset branch path was not observable"
    elif any(after and not before for before, after in zip(baseline, post_reset)):
        result.update({
            "status": "detected", "present": True, "confidence": 0.9,
            "classification": "predictor_state_retained_across_reset",
            "evidence": "taken training changed the first prediction after a subsequent processor reset",
        })
    else:
        result.update({
            "status": "not_detected", "present": False, "confidence": 0.7,
            "classification": "no_reset_retention_observed",
            "evidence": "the observable first prediction did not move toward the trained direction across reset",
        })
    return result

def _classify_alias_sweep(trials_by_spacing, timing_evidence=None):
    """Classify stateful per-PC prediction and destructive PC aliasing."""
    spacings = {}
    for spacing, trials in sorted(trials_by_spacing.items()):
        site_results = {}
        for site_name in ("site_a", "site_b"):
            accuracy, predictions, total = _warm_accuracy(trials, site_name=site_name)
            analysis = trials[0]["site_analysis"][site_name] if trials else {"occurrences": [], "warmup": 0}
            occurrences = analysis.get("occurrences", [])
            warmup = min(analysis.get("warmup", 0), len(occurrences))
            cold = [item.get("correct") for item in occurrences[:warmup] if item.get("correct") is not None]
            cold_latencies = [item.get("path_latency") for item in occurrences[:warmup] if item.get("path_latency") is not None]
            warm_latencies = [item.get("path_latency") for item in occurrences[warmup:] if item.get("path_latency") is not None]
            site_results[site_name] = {
                "warm_accuracy": accuracy,
                "warm_predictions": predictions,
                "occurrences": total,
                "cold_accuracy": sum(bool(item) for item in cold) / len(cold) if cold else None,
                "cold_path_latency": median(cold_latencies) if cold_latencies else None,
                "warm_path_latency": median(warm_latencies) if warm_latencies else None,
            }
        accuracies = [item["warm_accuracy"] for item in site_results.values() if item["warm_accuracy"] is not None]
        balanced_accuracy = sum(accuracies) / len(accuracies) if len(accuracies) == 2 else None
        cold_values = [item["cold_accuracy"] for item in site_results.values() if item["cold_accuracy"] is not None]
        cold_accuracy = sum(cold_values) / len(cold_values) if len(cold_values) == 2 else None
        spacings[str(spacing)] = {
            "sites": site_results,
            "balanced_warm_accuracy": balanced_accuracy,
            "balanced_cold_accuracy": cold_accuracy,
            "warm_improvement": (
                balanced_accuracy - cold_accuracy
                if balanced_accuracy is not None and cold_accuracy is not None else None
            ),
            "cycles_per_control_occurrence": (
                median([trial["diagnostic"]["cycles_used"] for trial in trials])
                / max(1, sum(len(trial["site_analysis"][name]["occurrences"]) for trial in trials for name in ("site_a", "site_b")))
            ),
            "valid": _trials_valid(trials),
        }

    valid_scores = {
        int(spacing): item["balanced_warm_accuracy"]
        for spacing, item in spacings.items()
        if item["valid"] and item["balanced_warm_accuracy"] is not None
    }
    passing = sorted(spacing for spacing, score in valid_scores.items() if score >= 0.75)
    score_spread = max(valid_scores.values()) - min(valid_scores.values()) if len(valid_scores) >= 2 else None
    stateful = bool(passing)
    aliasing = stateful and score_spread is not None and score_spread >= 0.20
    redirect_observed = any(
        trial.get("diagnostic", {}).get("redirect_events", 0) > 0
        for trials in trials_by_spacing.values() for trial in trials
    )
    timing_confirmed = bool((timing_evidence or {}).get("present") is True)
    independently_confirmed = redirect_observed or timing_confirmed
    if not valid_scores:
        status, present, evidence = "inconclusive", None, "no valid two-PC alias trials"
    elif stateful and independently_confirmed:
        status, present = "detected", True
        evidence = (
            "oppositely trained branch PCs both exceed static-policy accuracy"
            + (" and accuracy changes across power-of-two spacing" if aliasing else "")
        )
    elif stateful:
        status, present = "inconclusive", None
        evidence = (
            "PC-interference behavior was observed, but neither an independent timing advantage "
            "nor an explicit speculative redirect confirmed predictor state"
        )
    else:
        status, present = "not_detected", False
        evidence = "oppositely biased branch PCs did not both learn beyond the 50% static-policy baseline"
    return {
        "status": status, "present": present,
        "classification": "stateful_control_prediction_aliased" if aliasing else (
            "stateful_per_pc_direction_prediction" if stateful else "not_established"
        ),
        "aliasing_observed": aliasing,
        "raw_stateful_interference": stateful,
        "independent_evidence": {
            "paired_timing": timing_confirmed,
            "explicit_redirect": redirect_observed,
        },
        "effective_non_aliasing_spacing": passing[0] if passing else None,
        "accuracy_spread": score_spread, "spacings": spacings,
        "confidence": 0.86 if present is True else 0.72 if present is False else 0.35,
        "evidence": evidence,
    }

def _classify_paired_branch_timing(learnable_trials, control_trials):
    learnable = [trial["diagnostic"]["cycles_used"] for trial in learnable_trials if trial.get("valid")]
    control = [trial["diagnostic"]["cycles_used"] for trial in control_trials if trial.get("valid")]
    result = {
        "status": "inconclusive", "present": None,
        "classification": "stateful_direction_prediction_aliased_or_opaque",
        "learnable_cycles": learnable, "shuffled_control_cycles": control,
        "confidence": 0.35,
    }
    learnable_mispredicts = [
        trial["diagnostic"].get("architectural_counters", {}).get("mispredict_delta")
        for trial in learnable_trials
        if trial.get("valid") and trial["diagnostic"].get("architectural_counters", {}).get("valid")
    ]
    control_mispredicts = [
        trial["diagnostic"].get("architectural_counters", {}).get("mispredict_delta")
        for trial in control_trials
        if trial.get("valid") and trial["diagnostic"].get("architectural_counters", {}).get("valid")
    ]
    counters_comparable = (
        len(learnable_mispredicts) == len(learnable_trials)
        and len(control_mispredicts) == len(control_trials)
        and bool(learnable_mispredicts) and bool(control_mispredicts)
    )
    result["counter_evidence"] = {
        "available": counters_comparable,
        "learnable_mispredicts": learnable_mispredicts,
        "shuffled_control_mispredicts": control_mispredicts,
    }
    if len(learnable) != len(learnable_trials) or len(control) != len(control_trials) or not learnable or not control:
        result["evidence"] = "one or more paired timing trials failed validity checks"
        return result
    learnable_median = median(learnable)
    control_median = median(control)
    advantage = control_median - learnable_median
    required = max(2, int(round(control_median * 0.03)))
    result.update({
        "learnable_median_cycles": learnable_median,
        "control_median_cycles": control_median,
        "cycle_advantage": advantage,
        "required_cycle_advantage": required,
    })
    if counters_comparable:
        counter_advantage = median(control_mispredicts) - median(learnable_mispredicts)
        result["counter_evidence"]["mispredict_advantage"] = counter_advantage
        if counter_advantage >= max(2, int(round(median(control_mispredicts) * 0.10))):
            result.update({
                "status": "detected", "present": True, "confidence": 0.94,
                "evidence": "the learnable sequence produces fewer architectural misprediction events than its equal-layout shuffled control",
            })
            return result
    if advantage >= required:
        result.update({
            "status": "detected", "present": True, "confidence": 0.84,
            "evidence": "an equal-layout, equal-bias learnable sequence completes faster than its shuffled control",
        })
    elif abs(advantage) < required:
        result.update({
            "status": "not_detected", "present": False, "confidence": 0.72,
            "evidence": "learnable and shuffled equal-bias sequences have equivalent completion cost",
        })
    else:
        result["evidence"] = "the shuffled control was unexpectedly faster; timing evidence is unstable"
    return result

def _classify_speculation_visibility(trials):
    occurrences = [
        item for trial in trials
        for analysis in trial.get("site_analysis", {}).values()
        for item in analysis.get("occurrences", [])
    ]
    diagnostics = [trial.get("diagnostic", {}) for trial in trials]
    explicit = any(item.get("resolution_events", 0) > 0 for item in diagnostics)
    dependency = any(item.get("dependency_barrier_cycle") is not None for item in diagnostics)
    redirected = any(
        item.get("evidence_grade") == "same_context_wrong_path_then_redirect"
        for item in occurrences
    )
    if explicit:
        method = "explicit_resolution"
    elif dependency:
        method = "dependency_barrier"
    elif redirected:
        method = "wrong_path_redirect"
    else:
        method = "unavailable"
    valid_trials = [trial for trial in trials if trial.get("valid")]
    latencies = [
        item["branch_to_resolution_latency"] for item in occurrences
        if item.get("branch_to_resolution_latency") is not None
    ]
    calibrated = sum(
        item.get("resolution_cycle") is not None
        or item.get("dependency_barrier_cycle") is not None
        or item.get("evidence_grade") in {
            "explicit_prediction", "same_context_wrong_path_then_redirect",
        }
        for item in occurrences
    )
    available = bool(trials) and len(valid_trials) == len(trials) and method != "unavailable"
    if not valid_trials:
        failure_reason = next(
            (item.get("failure_reason") for item in diagnostics if item.get("failure_reason")),
            "calibration_probe_invalid",
        )
    elif len(valid_trials) != len(trials):
        failure_reason = "calibration_pair_incomplete"
    elif method == "unavailable":
        failure_reason = "resolution_and_dependency_barriers_unavailable"
    else:
        failure_reason = None
    return {
        "available": available,
        "method": method,
        "calibrated_occurrences": calibrated,
        "observed_occurrences": len(occurrences),
        "resolution_latencies": latencies,
        "context_supported": all(
            item.get("fetch_context_count") in (None, 0, 1)
            or item.get("fetch_context_tagged") is True
            for item in diagnostics
        ),
        "failure_reason": failure_reason,
        "evidence": (
            f"branch-path ordering calibrated with {method}"
            if available else "no trustworthy pre-resolution boundary was observable"
        ),
    }

def _hierarchical_branch_classification(results):
    """Preserve specific labels and select the least-general proven class."""
    specific = []
    for key in (
        "direction_hysteresis", "local_history", "global_history", "path_history",
        "combined_history", "long_history", "loop_predictor", "direct_target_predictor",
        "indirect_target_predictor", "return_address_stack", "reset_retention",
    ):
        if results.get(key, {}).get("present") is True:
            specific.append(key)
    alias = results.get("pc_aliasing", {})
    timing = results.get("paired_timing", {})
    cold = results.get("cold_direction_policy", {})
    hysteresis = results.get("direction_hysteresis", {})
    history = [key for key in ("local_history", "global_history", "path_history", "combined_history", "long_history") if results.get(key, {}).get("present") is True]

    if history:
        primary = "history_based_dynamic_prediction"
    elif hysteresis.get("present") is True:
        primary = hysteresis.get("classification") or "stateful_direction_prediction"
    elif alias.get("present") is True:
        primary = alias.get("classification") or "stateful_control_prediction_aliased"
    elif timing.get("present") is True:
        primary = timing.get("classification") or "stateful_direction_prediction_aliased_or_opaque"
    elif results.get("reset_retention", {}).get("present") is True:
        primary = "stateful_direction_prediction_reset_retained"
    elif cold.get("present") is True and cold.get("policy") not in (None, "static_sequential", "no_observable_cold_speculation"):
        primary = "static_prediction_only"
    elif specific:
        primary = "control_target_prediction"
    else:
        primary = "inconclusive_unobservable_frontend"
    return {
        "primary": primary,
        "specific_labels": specific,
        "static_policy": cold.get("policy") if primary == "static_prediction_only" else None,
        "observed_cold_policy": cold.get("policy"),
        "direction_subtype": hysteresis.get("classification") if hysteresis.get("present") is True else None,
        "history_subtypes": history,
        "aliasing_observed": alias.get("aliasing_observed") if alias.get("present") is True else None,
    }

def _sanitize_trial_for_debug(trial):
    return {
        "complete": trial["complete"],
        "valid": trial.get("valid"),
        "diagnostic": trial.get("diagnostic"),
        "metadata": trial["metadata"],
        "site_summaries": trial["site_summaries"],
        "site_analysis": trial["site_analysis"],
        "fetch_events": trial["fetch_events"],
        "redirect_events": trial.get("redirect_events", []),
        "prediction_events": trial.get("prediction_events", []),
        "resolution_events": trial.get("resolution_events", []),
        "memory_events": trial.get("memory_events", []),
        "commit_events": trial["commit_events"],
        "program": trial["program"],
        "instructions": trial["instructions"],
    }

async def branch_prediction_presence_test(dut, regfile, pipeline=None, data_memory=None):
    """Detect and behaviorally classify branch-prediction capabilities.

    Architectural writes are completion checks.  Direction/target prediction,
    wrong-path fetches, and warm-up are inferred from the instruction-fetch
    trace.  Exact RTL structures such as GShare versus TAGE remain hypotheses
    unless confirmed by static analysis.
    """
    dut._log.info("[branch_prediction] Running branch-prediction probes...")
    data_memory = data_memory or DataMemory()
    results = {
        "applicable": True,
        "execution_model_gate": (
            "pipeline_confirmed" if _is_pipeline_classification(pipeline)
            else "run_without_pipeline_classification"
        ),
    }

    try:
        output_dir = os.environ.get("OUTPUT_DIR", "default")
        processor_name = os.path.basename(output_dir)
        regfile_path = getattr(regfile, "_path", None)
        regfile_metadata = _load_regfile_metadata(
            output_dir,
            processor_name,
            regfile_path=regfile_path,
        )
        interface_handles = _resolve_write_interface(dut, processor_name, regfile)
        labels_file = os.path.join(output_dir, f"{processor_name}_labels.json")
        pipeline_depth = pipeline.get("depth_estimate") if isinstance(pipeline, dict) else None
        debug_results = {}
        diagnostics = {}

        async def run_probe(spec):
            metadata = _probe_metadata(spec)
            program_memory.select(spec)
            data_memory.reset(spec.initial_memory)
            dut.rst_n.value = 0
            dut.core_ack.value = 0
            await _load_optional_internal_program(dut, program_memory.image)
            await _load_optional_internal_data(dut, spec.initial_memory)
            await Timer(50, unit="ns")
            data_memory.reset(spec.initial_memory)
            dut.rst_n.value = 1

            fetch_events = []
            redirect_events = []
            prediction_events = []
            resolution_events = []
            memory_events = []
            counter_before = _probe_counter_snapshot(dut)
            commits, termination = await _observe_probe_commits(
                dut,
                regfile,
                regfile_metadata,
                interface_handles,
                spec,
                max_cycles=_branch_probe_cycle_budget(
                    spec, metadata, regfile_metadata, pipeline_depth
                ),
                fetch_events=fetch_events,
                return_diagnostics=True,
                drain_cycles=max(4, int(pipeline_depth or 1)),
                require_fetched_completion=True,
                redirect_events=redirect_events,
                prediction_events=prediction_events,
                resolution_events=resolution_events,
                data_memory=data_memory,
                memory_events=memory_events,
            )
            counter_evidence = _probe_counter_delta(counter_before, _probe_counter_snapshot(dut))
            entries = {item["offset"]: item for item in spec.entries()}
            for event in commits:
                entry = entries.get(event.get("offset"))
                if entry is not None:
                    event["role"] = entry["role"]

            context_count = _safe_signal_int(getattr(dut, "probe_context_count", None))
            barrier = metadata.get("resolution_barrier") or {}
            dependency_barrier_cycle = None
            if barrier.get("kind") == "dependency_load_response" and (
                context_count is None or context_count <= 1
            ):
                matching_loads = [
                    item for item in memory_events
                    if item.get("kind") == "load"
                    and int(item.get("address", -1)) == int(barrier.get("address", -2))
                ]
                if matching_loads:
                    dependency_barrier_cycle = int(matching_loads[0]["observed_cycle"])

            site_analysis = {
                site_name: _analyze_control_site(
                    fetch_events, site, prediction_events, redirect_events,
                    resolution_events, dependency_barrier_cycle,
                )
                for site_name, site in metadata["sites"].items()
            }
            site_summaries = {
                site_name: _summarize_site_analysis(analysis)
                for site_name, analysis in site_analysis.items()
            }
            fetch_available = bool(fetch_events)
            minimum_coverage = float(metadata.get("minimum_occurrence_coverage", (
                1.0 if all(
                    len(site.get("actual_targets", ())) <= 1 for site in metadata["sites"].values()
                ) else 0.5
            )))
            coverage = min(
                (analysis.get("occurrence_coverage", 0.0) for analysis in site_analysis.values()),
                default=0.0,
            )
            context_tagged = bool(fetch_events) and all(
                event.get("context_id") is not None for event in fetch_events
            )
            context_available = context_count is None or context_count <= 1 or context_tagged
            memory_required = barrier.get("kind") == "dependency_load_response"
            memory_available = not memory_required or bool(data_memory.supported)
            resolution_mismatch = any(
                item.get("resolution_mismatch")
                for analysis in site_analysis.values() for item in analysis["occurrences"]
            )
            valid = bool(
                termination["complete"] and fetch_available
                and coverage >= minimum_coverage and context_available and memory_available
                and not resolution_mismatch
            )
            if not termination["complete"]:
                failure_reason = "probe_timeout" if termination["timed_out"] else "architectural_completion_failed"
            elif not fetch_available:
                failure_reason = "fetch_interface_unavailable"
            elif coverage < minimum_coverage:
                failure_reason = "insufficient_occurrence_coverage"
            elif not context_available:
                failure_reason = "fetch_context_unavailable"
            elif not memory_available:
                failure_reason = "dependency_memory_interface_unavailable"
            elif resolution_mismatch:
                failure_reason = "resolution_interface_mismatch"
            else:
                failure_reason = None
            diagnostic = {
                **termination,
                "valid": valid,
                "failure_reason": failure_reason,
                "fetch_events": len(fetch_events),
                "occurrence_coverage": coverage,
                "minimum_occurrence_coverage": minimum_coverage,
                "data_memory_supported": data_memory.supported,
                "fetch_observation_source": (
                    "standardized_frontend"
                    if any(event.get("accepted_by") == "standardized_frontend" for event in fetch_events)
                    else "legacy_fetch_interface" if fetch_events else None
                ),
                "redirect_events": len(redirect_events),
                "prediction_events": len(prediction_events),
                "resolution_events": len(resolution_events),
                "dependency_barrier_cycle": dependency_barrier_cycle,
                "resolution_interface_mismatch": resolution_mismatch,
                "fetch_context_count": context_count,
                "fetch_context_tagged": context_tagged,
                "strong_prediction_events": sum(
                    _strong_prediction_occurrence(item)
                    for analysis in site_analysis.values()
                    for item in analysis["occurrences"]
                    if item.get("correct") is not None
                ),
                "architectural_counters": counter_evidence,
            }
            if not valid:
                dut._log.warning(
                    "[branch_prediction] probe=%s invalid reason=%s complete=%s fetches=%d coverage=%.3f",
                    spec.name, failure_reason, termination["complete"], len(fetch_events), coverage,
                )
            return {
                "complete": termination["complete"],
                "valid": valid,
                "diagnostic": diagnostic,
                "metadata": metadata,
                "site_analysis": site_analysis,
                "site_summaries": site_summaries,
                "fetch_events": fetch_events,
                "redirect_events": redirect_events,
                "prediction_events": prediction_events,
                "resolution_events": resolution_events,
                "memory_events": memory_events,
                "commit_events": commits,
                "program": spec.entries(),
                "instructions": spec.instructions,
            }

        def branch_prediction_probe_spec(name, pattern=None, trial_index=0):
            if pattern is None:
                try:
                    return BRANCH_PREDICTION_PROBES[name]
                except KeyError as error:
                    raise KeyError(f"unknown branch-prediction probe: {name}") from error
            if name == "direction_sequence":
                return direction_sequence_probe(
                    f"direction_sequence_trial_{trial_index}", pattern
                )
            if name == "long_history":
                return long_history_probe(
                    distance=int(pattern),
                    name=f"long_history_distance_{int(pattern)}",
                )
            if name == "path_history":
                return path_history_probe(
                    flush_depth=int(pattern),
                    name=f"path_history_depth_{int(pattern)}",
                )
            if name == "loop_predictor":
                return loop_predictor_probe(
                    trip_count=int(pattern),
                    name=f"loop_predictor_trip_{int(pattern)}",
                )
            raise ValueError(f"probe {name} does not accept a pattern argument")

        async def branch_prediction_probe(name, pattern=None, trial_index=0):
            """Run one named probe; unlike the draft, this must be async."""
            spec = branch_prediction_probe_spec(name, pattern, trial_index)
            return await run_probe(spec)

        async def run_trials(name, count=1, pattern=None):
            trials = []
            for trial_index in range(max(1, int(count))):
                trial = await branch_prediction_probe(name, pattern, trial_index)
                trials.append(trial)
            debug_results[name if pattern is None else f"{name}_{pattern}"] = [
                _sanitize_trial_for_debug(item) for item in trials
            ]
            diagnostics[name if pattern is None else f"{name}_{pattern}"] = [
                item["diagnostic"] for item in trials
            ]
            return trials

        resolution_trials = []
        for spec in BRANCH_RESOLUTION_PROBES:
            trial = await run_probe(spec)
            resolution_trials.append(trial)
            debug_results[spec.name] = [_sanitize_trial_for_debug(trial)]
            diagnostics[spec.name] = [trial["diagnostic"]]
        results["speculation_visibility"] = _classify_speculation_visibility(
            resolution_trials
        )

        # Cold-policy probes get repeated resets so their first prediction can
        # be checked for deterministic initialization.
        static_names = (
            "static_forward_taken",
            "static_forward_not_taken",
            "static_backward_taken",
            "static_backward_not_taken",
        )
        static_trials = {
            name: await run_trials(name, count=3)
            for name in static_names
        }
        results["cold_direction_policy"] = _classify_static_policy(static_trials)

        one_bit_trials = await run_trials("dynamic_one_bit")
        two_bit_trials = await run_trials("dynamic_two_bit")
        results["direction_hysteresis"] = _classify_counter_hysteresis(
            one_bit_trials, two_bit_trials
        )
        if results["direction_hysteresis"].get("present") is True:
            results["direction_predictor"] = {
                "status": "detected",
                "present": True,
                "classification": "stateful_per_pc_outcome_history",
                "confidence": results["direction_hysteresis"]["confidence"],
                "evidence": (
                    "predictions at one conditional-branch PC changed after its prior outcomes; "
                    "the exact history or counter structure is not uniquely identifiable"
                ),
            }
        else:
            results["direction_predictor"] = {
                "status": results["direction_hysteresis"].get("status", "inconclusive"),
                "present": results["direction_hysteresis"].get("present"),
                "classification": "not_established",
                "confidence": results["direction_hysteresis"].get("confidence", 0.35),
                "evidence": results["direction_hysteresis"].get("evidence"),
            }

        local_trials = await run_trials("local_history")
        alternating_local_trials = await run_trials("local_alternating")
        global_trials = await run_trials("global_history")
        path_trials = await run_trials("path_history")
        combined_trials = await run_trials("combined_history")
        long_trials = await run_trials("long_history")

        local_pattern = _accuracy_capability(
            local_trials, label="ttnn_local_pattern_learning"
        )
        alternating_pattern = _accuracy_capability(
            alternating_local_trials, label="alternating_local_pattern_learning"
        )
        detected_local = any(
            item.get("present") is True for item in (local_pattern, alternating_pattern)
        )
        valid_local = all(
            item.get("present") is not None for item in (local_pattern, alternating_pattern)
        )
        results["local_history"] = {
            "status": "detected" if detected_local else ("not_detected" if valid_local else "inconclusive"),
            "present": True if detected_local else (False if valid_local else None),
            "classification": "per_pc_outcome_history_pattern" if detected_local else "not_established",
            "patterns": {"ttnn": local_pattern, "alternating": alternating_pattern},
            "confidence": 0.88 if detected_local else 0.35,
            "evidence": (
                "a repeating outcome pattern at one branch PC is learned beyond its direction-bias baseline"
                if detected_local else "tested local patterns were not learned beyond their bias baselines"
            ),
        }
        results["global_history"] = _accuracy_capability(
            global_trials, label="cross_branch_global_correlation"
        )
        results["path_history"] = _accuracy_capability(
            path_trials, label="path_sensitive_correlation"
        )
        results["combined_history"] = {
            "global_component": _accuracy_capability(
                combined_trials, site_name="global", label="interleaved_global_correlation"
            ),
            "local_component": _accuracy_capability(
                combined_trials, site_name="local", label="interleaved_local_pattern"
            ),
        }
        both_combined = (
            results["combined_history"]["global_component"].get("present") is True
            and results["combined_history"]["local_component"].get("present") is True
        )
        results["combined_history"].update({
            "status": "detected" if both_combined else "inconclusive",
            "present": True if both_combined else None,
            "confidence": 0.8 if both_combined else 0.4,
            "evidence": (
                "local and global correlations remain predictable while interleaved"
                if both_combined
                else "the interleaved probe did not establish both capabilities"
            ),
        })
        results["long_history"] = _accuracy_capability(
            long_trials, label="history_correlation_at_distance_16"
        )

        loop_trials = await run_trials("loop_predictor")
        results["loop_predictor"] = _classify_loop_predictor(loop_trials)

        direct_trials = await run_trials("direct_btb")
        constant_indirect_trials = await run_trials("indirect_constant_target")
        alternating_indirect_trials = await run_trials("indirect_alternating_target")
        standard_ras_trials = await run_trials("ras_standard_link")
        control_ras_trials = await run_trials("ras_nonstandard_link_control")

        results["direct_target_predictor"] = _classify_direct_target(direct_trials)
        results["indirect_target_predictor"] = _classify_indirect_targets(
            constant_indirect_trials, alternating_indirect_trials
        )
        results["return_address_stack"] = _classify_ras(
            standard_ras_trials, control_ras_trials
        )

        learnable_spec, shuffled_spec = paired_timing_probes()
        learnable_timing_trials = [await run_probe(learnable_spec) for _ in range(3)]
        shuffled_timing_trials = [await run_probe(shuffled_spec) for _ in range(3)]
        for spec, trials in ((learnable_spec, learnable_timing_trials), (shuffled_spec, shuffled_timing_trials)):
            debug_results[spec.name] = [_sanitize_trial_for_debug(trial) for trial in trials]
            diagnostics[spec.name] = [trial["diagnostic"] for trial in trials]
        results["paired_timing"] = _classify_paired_branch_timing(
            learnable_timing_trials, shuffled_timing_trials
        )

        # Run the same not-taken layout before and after taken training. Every
        # trial uses the ordinary processor reset; a changed first prediction
        # therefore measures predictor state specifically retained by reset.
        reset_observe = direction_sequence_probe(
            "reset_retention_observe", (False,) * 16, marker=0x16A, warmup=0
        )
        reset_train = direction_sequence_probe(
            "reset_retention_train", (True,) * 16, marker=0x16B, warmup=0
        )
        baseline_reset_trials = [await run_probe(reset_observe)]
        training_reset_trials = [await run_probe(reset_train)]
        post_reset_trials = [await run_probe(reset_observe)]
        for name, trials in (
            ("reset_retention_baseline", baseline_reset_trials),
            ("reset_retention_training", training_reset_trials),
            ("reset_retention_post", post_reset_trials),
        ):
            debug_results[name] = [_sanitize_trial_for_debug(trial) for trial in trials]
            diagnostics[name] = [trial["diagnostic"] for trial in trials]
        results["reset_retention"] = _classify_reset_retention(
            baseline_reset_trials, training_reset_trials, post_reset_trials
        )

        alias_trials = {}
        for alias_spec in power_of_two_alias_sweep():
            trials = [await run_probe(alias_spec)]
            spacing = int(trials[0]["metadata"]["spacing"])
            alias_trials[spacing] = trials
            debug_results[alias_spec.name] = [_sanitize_trial_for_debug(trials[0])]
            diagnostics[alias_spec.name] = [trials[0]["diagnostic"]]
        results["pc_aliasing"] = _classify_alias_sweep(
            alias_trials, timing_evidence=results["paired_timing"]
        )

        # Optional expensive sweeps estimate effective history/path reach.
        if _env_flag("BRANCH_PREDICTION_DEEP"):
            ras_depth_results = {}
            for standard_spec, control_spec in ras_depth_sweep():
                standard = [await run_probe(standard_spec)]
                control = [await run_probe(control_spec)]
                depth = int(standard[0]["metadata"]["depth"])
                for spec, trials in ((standard_spec, standard), (control_spec, control)):
                    debug_results[spec.name] = [_sanitize_trial_for_debug(trials[0])]
                    diagnostics[spec.name] = [trials[0]["diagnostic"]]
                ras_depth_results[str(depth)] = _classify_ras(standard, control)
            detected_ras_depths = [
                int(depth) for depth, item in ras_depth_results.items()
                if item.get("present") is True
            ]
            results["return_address_stack_depth"] = {
                "depths": ras_depth_results,
                "max_detected_depth": max(detected_ras_depths) if detected_ras_depths else None,
                "status": "detected" if detected_ras_depths else "inconclusive",
                "present": True if detected_ras_depths else None,
            }

            long_sweep_results = {}
            for spec in long_history_sweep():
                trials = [await run_probe(spec)]
                debug_results[spec.name] = [_sanitize_trial_for_debug(trials[0])]
                long_sweep_results[str(trials[0]["metadata"].get("history_distance"))] = _accuracy_capability(
                    trials,
                    label=f"history_distance_{trials[0]['metadata'].get('history_distance')}",
                )
            detected_distances = [
                int(distance)
                for distance, item in long_sweep_results.items()
                if item.get("present") is True
            ]
            results["long_history_sweep"] = {
                "distances": long_sweep_results,
                "max_detected_distance": max(detected_distances) if detected_distances else None,
            }

            path_sweep_results = {}
            for spec in path_history_sweep():
                trials = [await run_probe(spec)]
                debug_results[spec.name] = [_sanitize_trial_for_debug(trials[0])]
                depth = trials[0]["metadata"].get("path_depth")
                path_sweep_results[str(depth)] = _accuracy_capability(
                    trials, label=f"path_depth_{depth}"
                )
            detected_depths = [
                int(depth)
                for depth, item in path_sweep_results.items()
                if item.get("present") is True
            ]
            results["path_history_sweep"] = {
                "depths": path_sweep_results,
                "max_detected_depth": max(detected_depths) if detected_depths else None,
            }

        behavioral_components = []
        for key in (
            "cold_direction_policy",
            "direction_hysteresis",
            "local_history",
            "global_history",
            "path_history",
            "combined_history",
            "long_history",
            "loop_predictor",
            "direct_target_predictor",
            "indirect_target_predictor",
            "return_address_stack",
            "pc_aliasing",
            "paired_timing",
            "reset_retention",
        ):
            if results[key].get("present") is True:
                behavioral_components.append(key)

        # Sequential fall-through on a cold branch is observable behavior, but
        # by itself it is not proof of predictor hardware: an ordinary frontend
        # naturally continues at PC+4.  Likewise, a direct JAL target available
        # immediately on every occurrence may come from early decode rather
        # than a trainable BTB.  Keep those cases separate from stronger stateful
        # evidence.
        hardware_components = [
            key
            for key in behavioral_components
            if key not in ("cold_direction_policy", "direct_target_predictor")
        ]
        results["classification"] = _hierarchical_branch_classification(results)
        cold_policy = results["cold_direction_policy"].get("policy")
        if cold_policy in ("static_taken", "static_btfnt"):
            hardware_components.append("cold_direction_policy")
        if results["direct_target_predictor"].get("classification") == "trainable_direct_btb":
            hardware_components.append("direct_target_predictor")

        hardware_components = list(dict.fromkeys(hardware_components))
        results["diagnostics"] = diagnostics
        invalid_probes = sorted(
            name
            for name, trial_diagnostics in diagnostics.items()
            if any(not item.get("valid", False) for item in trial_diagnostics)
        )
        results["invalid_probes"] = invalid_probes
        results["behavioral_prediction_observed"] = bool(behavioral_components)
        results["behavioral_components"] = behavioral_components
        results["detected_components"] = hardware_components
        if hardware_components:
            results["present"] = True
            results["status"] = "detected"
        elif behavioral_components:
            results["present"] = None
            results["status"] = "inconclusive"
            results["evidence"] = (
                "only static sequential or non-trainable early-target behavior was observed; "
                "this does not prove predictor state exists"
            )
        elif invalid_probes:
            results["present"] = None
            results["status"] = "inconclusive"
            results["evidence"] = (
                "no predictor component was established and one or more probes failed validity checks"
            )
        else:
            results["present"] = False
            results["status"] = "not_detected"
            results["evidence"] = "no observable speculative or trained next-path behavior"
        results["classification_scope"] = (
            "behavioral fetch-trace evidence; exact RTL predictor names require static confirmation"
        )

        try:
            with open(labels_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        except Exception:
            data = {}

        data.setdefault(processor_name, {})
        data[processor_name]["branch_prediction"] = results
        if _env_flag("CYCLE_DEBUG") or _env_flag("DEBUG_CYCLE"):
            data[processor_name]["branch_prediction_debug"] = {
                "probes": debug_results,
            }
        else:
            data[processor_name].pop("branch_prediction_debug", None)

        with open(labels_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        dut._log.info(
            "[branch_prediction] status=%s components=%s",
            results["status"],
            hardware_components,
        )
        return results

    finally:
        program_memory.select(CYCLE_SIGNATURE)


