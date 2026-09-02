#!/usr/bin/env python3
"""Validate source-grounded forwarding cases after focused or batch runs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.forwarding_proof import (  # noqa: E402
    validate_pipeline_identity,
    validate_forwarding_positive,
)


PROBE_SUITE_VERSION = "paired-forwarding-v8"
IMPLEMENTATION_REVISION = 11


def main():
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("labels_root", type=Path)
    parser.add_argument(
        "--expectations",
        type=Path,
        default=repo / "tests" / "forwarding_source_expectations.json",
    )
    parser.add_argument("--require-debug", action="store_true")
    parser.add_argument(
        "--core", action="append", default=[],
        help="validate only the named core (repeatable)",
    )
    args = parser.parse_args()
    expectations = json.loads(args.expectations.read_text(encoding="utf-8"))
    if args.core:
        expectations = {
            core: expectations[core] for core in args.core if core in expectations
        }
    failures = []
    for core, expected in expectations.items():
        path = args.labels_root / core / f"{core}_labels.json"
        if not path.exists():
            failures.append(f"{core}: labels are missing")
            continue
        labels = json.loads(path.read_text(encoding="utf-8"))[core]
        forwarding = labels.get("forwarding", {})
        execution = forwarding.get("execution", {})
        if (
            forwarding.get("schema_version") != 2
            or forwarding.get("probe_suite_version") != PROBE_SUITE_VERSION
            or forwarding.get("implementation_revision") != IMPLEMENTATION_REVISION
            or execution.get("state") != "completed"
        ):
            failures.append(f"{core}: forwarding result is stale or did not complete")
            continue
        if execution.get("full_pipeline_finalization_count", 99) > 2:
            failures.append(
                f"{core}: full pipeline classification ran more than twice"
            )
        if execution.get("topology_frozen") is not True:
            failures.append(f"{core}: final topology was not frozen")
        pipeline_path = args.labels_root / core / f"{core}_pipeline_interface.json"
        pipeline_interface = None
        if not pipeline_path.exists():
            failures.append(f"{core}: pipeline-interface discovery result is missing")
        else:
            pipeline_interface = json.loads(pipeline_path.read_text(encoding="utf-8"))
            if (
                pipeline_interface.get("schema_version") != 4
                or pipeline_interface.get("discovery_version") != "dynamic-stage-signals-v4"
                or pipeline_interface.get("implementation_revision")
                != IMPLEMENTATION_REVISION
            ):
                failures.append(f"{core}: pipeline-interface discovery result is stale")
            calibration = pipeline_interface.get("calibration", {})
            if calibration.get("execution_state") == "failed":
                failures.append(
                    f"{core}: pipeline calibration raised an execution error"
                )
            for key in ("architectural", "capability_coverage", "handshake"):
                if key not in calibration:
                    failures.append(f"{core}: pipeline calibration field {key} is missing")
            for key in (
                "behavioral_census", "stage_graph", "role_evidence",
                "topology_frozen", "full_pipeline_finalization_count",
                "stage_candidate_diagnostics",
                "source_id_linkage_diagnostics",
                "exact_capture_failures",
                "calibration_base_selection",
            ):
                if key not in pipeline_interface:
                    failures.append(
                        f"{core}: revision-11 pipeline field {key} is missing"
                    )
            pipeline_valid, pipeline_reason = validate_pipeline_identity(
                pipeline_interface, IMPLEMENTATION_REVISION,
            )
            if not pipeline_valid:
                failures.append(
                    f"{core}: shared pipeline proof failed: "
                    f"{pipeline_reason}"
                )
            census = pipeline_interface.get("behavioral_census", {})
            for key in (
                "discovered", "signature_evaluated", "promoted",
                "detailed_traced", "absolute_traversal_exclusion",
            ):
                if key not in census:
                    failures.append(
                        f"{core}: behavioral census field {key} is missing"
                    )
            graph = pipeline_interface.get("stage_graph", {})
            accepted_edges = {
                (edge.get("from"), edge.get("to"))
                for edge in graph.get("accepted_edges", ())
            }
            canonical_path = graph.get("canonical_path", ())
            if any(
                (left, right) not in accepted_edges
                for left, right in zip(
                    canonical_path, canonical_path[1:]
                )
            ):
                failures.append(
                    f"{core}: canonical stage path violates graph ordering"
                )
            for stage in pipeline_interface.get("stages", ()):
                if (
                    stage.get("pc_path") is not None
                    and stage.get("relocation_proven") is not True
                ):
                    failures.append(
                        f"{core}: {stage.get('normalized_role')} stage "
                        "lacks relocation proof"
                    )
                if stage.get("pc_path") is not None:
                    transform = stage.get("address_transform") or {}
                    if (
                        transform.get("mode") not in {"byte", "word"}
                        or not isinstance(transform.get("bias"), int)
                        or transform.get("delta_checks")
                        != transform.get("delta_matches")
                        or int(
                            transform.get("distinct_base_count") or 0
                        ) != 3
                    ):
                        failures.append(
                            f"{core}: {stage.get('normalized_role')} stage "
                            "lacks a validated affine transform"
                        )
                if (
                    stage.get("observation_kind")
                    == "transaction_aligned_operand_capture"
                ):
                    node = next((
                        item for item in graph.get("nodes", ())
                        if item.get("path")
                        == stage.get("graph_node_id")
                    ), None)
                    if (
                        node is None
                        or not node.get("exact_store_epochs")
                        or not node.get("exact_fetch_associations")
                    ):
                        failures.append(
                            f"{core}: transaction-local memory role "
                            "lacks exact store epochs"
                        )
        for probe_name, probe_expected in expected.get("behavioral_expectations", {}).items():
            result = forwarding.get(probe_name, {})
            for key in (
                "observation_source", "evidence_quality", "confidence_factors",
                "forwarding_required", "zero_delay_behavior_observed",
                "zero_delay_classification",
                "requirement_missing_proofs",
                "independent_distance_sweep",
            ):
                if key not in result:
                    failures.append(f"{core} {probe_name}: v8 field {key} is missing")
            comparison = result.get(
                "independent_distance_sweep", {}
            ).get("nop_comparison", {})
            timing_state = comparison.get("timing_comparison_state")
            if timing_state not in {
                "comparable", "gap_not_tested",
                "nop_timing_unavailable",
                "independent_timing_unavailable",
            }:
                failures.append(
                    f"{core} {probe_name}: invalid NOP timing comparison state"
                )
            if (
                timing_state != "comparable"
                and comparison.get("timing_divergence") is not None
            ):
                failures.append(
                    f"{core} {probe_name}: unavailable timing comparison "
                    "reported a divergence"
                )
            zero_delay_classification = result.get("zero_delay_classification")
            if (
                zero_delay_classification == "possible_forwarding"
                and not result.get("requirement_missing_proofs")
            ):
                failures.append(
                    f"{core} {probe_name}: possible forwarding lacks an "
                    "explicit missing-proof category"
                )
            if "zero_delay_classification" in result:
                expected_zero_delay = (
                    "confirmed_forwarding"
                    if result.get("present") is True
                    else "forwarding_not_required"
                    if result.get("forwarding_required") is False
                    and result.get("zero_delay_behavior_observed") is True
                    else "possible_forwarding"
                    if result.get("forwarding_required") is None
                    and result.get("zero_delay_behavior_observed") is True
                    else None
                )
                if zero_delay_classification != expected_zero_delay:
                    failures.append(
                        f"{core} {probe_name}: inconsistent zero-delay classification "
                        f"{zero_delay_classification}"
                    )
            if result.get("present") is True and result.get("forwarding_required") is not True:
                failures.append(
                    f"{core} {probe_name}: forwarding presence lacks required-stage proof"
                )
            if result.get("present") is True:
                sweep = result.get("independent_distance_sweep", {})
                if (
                    sweep.get("tested_gaps", [])[:2] != [1, 2]
                    or sweep.get("corroboration", {}).get("state")
                    != "validated"
                ):
                    failures.append(
                        f"{core} {probe_name}: confirmed forwarding lacks "
                        "independent-distance corroboration"
                    )
                for field in (
                    "consumer_token_proof",
                    "source_selector_validation",
                    "operand_differential_validation",
                    "semantic_discriminators_passed",
                ):
                    if result.get(field) is not True:
                        failures.append(
                            f"{core} {probe_name}: confirmed forwarding "
                            f"lacks {field}"
                        )
                for gap_record in sweep.get("per_gap", []):
                    experiments = gap_record.get("experiments", {})
                    for trial in (
                        experiments.get("dependent", [])
                        + experiments.get("control", [])
                    ):
                        for field in (
                            "operand_packed_slice",
                            "source_id_packed_slice",
                            "source_selector_lag", "forwarding_gap",
                            "spacer_kind", "filler_registers",
                            "filler_values",
                        ):
                            if field not in trial:
                                failures.append(
                                    f"{core} {probe_name}: independent "
                                    f"compact trial lacks {field}"
                                )
            if result.get("present") is not True and result.get("bypass_kind") is not None:
                failures.append(
                    f"{core} {probe_name}: bypass_kind is set without forwarding presence"
                )
            if result.get("status") not in probe_expected["allowed_statuses"]:
                failures.append(f"{core} {probe_name}: unexpected status {result.get('status')}")
            if result.get("present") not in probe_expected["allowed_present"]:
                failures.append(f"{core} {probe_name}: unexpected presence {result.get('present')}")
            if probe_expected.get("architectural_dependency_handled") is not None and result.get(
                "architectural_dependency_handled"
            ) is not probe_expected["architectural_dependency_handled"]:
                failures.append(f"{core} {probe_name}: unexpected architectural handling")
            if "expected_forwarding_required" in probe_expected and result.get(
                "forwarding_required"
            ) is not probe_expected["expected_forwarding_required"]:
                failures.append(f"{core} {probe_name}: unexpected forwarding requirement")
            penalty = result.get("raw_penalty_cycles")
            if "minimum_raw_penalty_cycles" in probe_expected and (
                penalty is None or penalty < probe_expected["minimum_raw_penalty_cycles"]
            ):
                failures.append(f"{core} {probe_name}: RAW penalty is too small")
            if "maximum_raw_penalty_cycles" in probe_expected and (
                penalty is None or penalty > probe_expected["maximum_raw_penalty_cycles"]
            ):
                failures.append(f"{core} {probe_name}: RAW penalty is too large")
            if "allowed_bypass_kinds" in probe_expected and result.get("bypass_kind") not in probe_expected["allowed_bypass_kinds"]:
                failures.append(f"{core} {probe_name}: unexpected bypass kind {result.get('bypass_kind')}")

            compact = result.get("experiments", {}).get("adjacent", {})
            compact_trials = compact.get("dependent", []) + compact.get("control", [])
            if not compact_trials:
                failures.append(f"{core} {probe_name}: compact trial evidence is missing")
            for trial in compact_trials:
                for key in (
                    "consumer_required_stage", "consumer_required_stage_cycle",
                    "forwarding_required", "requirement_observation",
                    "observation_source", "evidence_quality",
                    "producer_availability_event", "consumer_requirement_event",
                    "same_cycle_ordering", "operand_value_observed", "operand_path",
                    "source_id_path", "requirement_evidence_source",
                    "fetch_token", "memory_epoch_id", "memory_transaction_id",
                    "lane_id", "fetch_slot", "stage_token",
                    "consumer_request_event",
                    "path_role_evidence_state",
                    "aggregate_role_evidence_state",
                    "consumer_token_proof",
                    "source_selector_validation",
                    "operand_differential_validation",
                    "semantic_discriminators_passed",
                ):
                    if key not in trial:
                        failures.append(f"{core} {probe_name}: compact v8 field {key} is missing")
                for key in expected.get("required_compact_fields", []):
                    if trial.get(key) is None:
                        failures.append(f"{core} {probe_name}: compact field {key} is missing")
            if result.get("present") is True and not all(
                trial.get("path_role_evidence_state") == "confirmed"
                for trial in compact.get("dependent", [])
            ):
                failures.append(
                    f"{core} {probe_name}: forwarding presence uses an "
                    "unconfirmed path-local operand chain"
                )
            if result.get("present") is True and not all(
                all(
                    trial.get(field) is True
                    for field in (
                        "consumer_token_proof",
                        "source_selector_validation",
                        "operand_differential_validation",
                        "semantic_discriminators_passed",
                    )
                )
                for trial in compact.get("dependent", [])
            ):
                failures.append(
                    f"{core} {probe_name}: a qualifying dependent trial "
                    "lacks the complete revision-11 proof chain"
                )
            if result.get("present") is True:
                shared_proof = validate_forwarding_positive(
                    result, pipeline_interface,
                    IMPLEMENTATION_REVISION,
                )
                if not shared_proof["valid"]:
                    failures.append(
                        f"{core} {probe_name}: shared positive-proof "
                        f"gate failed: {shared_proof['reason']}"
                    )
            for kind, field in (
                ("source", "source_id_path"),
                ("operand", "operand_path"),
            ):
                accepted = probe_expected.get(
                    f"accepted_{kind}_path_patterns", []
                )
                forbidden = probe_expected.get(
                    f"forbidden_{kind}_path_patterns", []
                )
                paths = {
                    str(trial.get(field))
                    for trial in compact.get("dependent", [])
                    if trial.get(field)
                }
                if accepted and any(
                    not any(re.search(pattern, path) for pattern in accepted)
                    for path in paths
                ):
                    failures.append(
                        f"{core} {probe_name}: selected {kind} path is "
                        "outside documented accepted patterns"
                    )
                if forbidden and any(
                    any(re.search(pattern, path) for pattern in forbidden)
                    for path in paths
                ):
                    failures.append(
                        f"{core} {probe_name}: selected {kind} path matches "
                        "a documented forbidden pattern"
                    )

        probes = labels.get("forwarding_debug", {}).get("probes", {})
        if args.require_debug:
            for probe_name in expected.get("behavioral_expectations", {}):
                trials = probes.get(f"{probe_name}_paired_gap_0", [])
                if not trials:
                    failures.append(f"{core} {probe_name}: requested debug trials are missing")
                    continue
                for trial in trials:
                    events = {item.get("event") for item in trial.get("event_trace", [])}
                    missing = set(expected.get("required_debug_events", [])) - events
                    if missing:
                        failures.append(
                            f"{core} {probe_name} trial {trial.get('trial')} {trial.get('role')}: "
                            f"missing debug events {sorted(missing)}"
                        )
    if failures:
        print("Forwarding regression validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Forwarding regression validation passed for {len(expectations)} source-grounded core(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
