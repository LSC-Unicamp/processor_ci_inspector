"""Shared forwarding-positive proof validation.

Keep this module free of simulator dependencies so result classification,
offline validation, and auditing cannot drift onto different proof gates.
"""

from __future__ import annotations

import json


PROOF_FIELDS = (
    "consumer_token_proof",
    "source_selector_validation",
    "operand_differential_validation",
    "semantic_discriminators_passed",
)

PROOF_CATEGORIES = {
    "consumer_token_proof": "consumer_token",
    "source_selector_validation": "source_id",
    "operand_differential_validation": "operand_capture",
    "semantic_discriminators_passed": "semantic_discriminator",
}


def validate_pipeline_identity(interface, implementation_revision):
    if not isinstance(interface, dict):
        return False, "pipeline-interface artifact is missing"
    if interface.get("implementation_revision") != implementation_revision:
        return False, "pipeline-interface artifact is stale"
    pc_stages = [
        stage for stage in interface.get("stages", ())
        if stage.get("pc_path") is not None
    ]
    if implementation_revision >= 11 and pc_stages:
        selection = interface.get("calibration_base_selection") or {}
        if (
            selection.get("state") != "complete"
            or selection.get("relocation_roles_permitted") is not True
            or len(selection.get("selected_bases", ())) != 3
        ):
            return False, (
                "PC-backed roles lack three completed non-aliasing "
                "relocation landings"
            )
    for stage in interface.get("stages", ()):
        if (
            stage.get("pc_path") is not None
            and stage.get("relocation_proven") is not True
        ):
            return False, (
                f"{stage.get('normalized_role')} stage lacks "
                "relocation-backed PC identity"
            )
        if implementation_revision >= 11 and stage.get(
            "pc_path"
        ) is not None:
            transform = stage.get("address_transform") or {}
            if (
                transform.get("mode") not in {"byte", "word"}
                or not isinstance(transform.get("bias"), int)
                or int(transform.get("width") or 0) <= 0
                or int(transform.get("distinct_base_count") or 0) != 3
                or int(transform.get("delta_checks") or 0) <= 0
                or transform.get("delta_checks")
                != transform.get("delta_matches")
                or transform.get("rejection_reason") is not None
            ):
                return False, (
                    f"{stage.get('normalized_role')} stage lacks one "
                    "validated affine PC transform"
                )
        if (
            stage.get("observation_kind")
            == "transaction_aligned_operand_capture"
        ):
            node_id = stage.get("graph_node_id")
            node = next((
                item for item in interface.get(
                    "stage_graph", {}
                ).get("nodes", ())
                if item.get("path") == node_id
            ), None)
            if (
                node is None
                or node.get("kind") != "transaction_local_store"
                or not node.get("exact_store_epochs")
                or (
                    implementation_revision >= 11
                    and not node.get("exact_fetch_associations")
                )
            ):
                return False, (
                    "transaction-local memory stage lacks exact store epochs"
                )
    graph = interface.get("stage_graph", {})
    path_nodes = graph.get("canonical_path", ())
    accepted = {
        (edge.get("from"), edge.get("to"))
        for edge in graph.get("accepted_edges", ())
    }
    if any(
        (left, right) not in accepted
        for left, right in zip(path_nodes, path_nodes[1:])
    ):
        return False, "canonical stage roles violate accepted graph edges"
    return True, "pipeline stage identity and graph ordering are valid"


def validate_independent_corroboration(result, adjacent):
    sweep = result.get("independent_distance_sweep", {})
    gap_records = sweep.get("per_gap", [])
    if sweep.get("tested_gaps", [])[:2] != [1, 2]:
        return False, [], "independent gaps 1 and 2 are not both present"
    if sweep.get("corroboration", {}).get("state") != "validated":
        return False, [], "the sweep corroboration state is not validated"
    trials = []
    for record in gap_records:
        experiment = record.get("experiments", {})
        dependent = experiment.get("dependent", [])
        control = experiment.get("control", [])
        if (
            len(dependent) not in (3, 5)
            or len(control) != len(dependent)
            or record.get("exact_proof_complete") is not True
        ):
            return (
                False, trials,
                "an independent gap lacks 3/5 exact paired trials",
            )
        trials.extend(dependent + control)
    signatures = set()
    residence_positions = []
    for trial in adjacent + trials:
        phase = (trial.get("consumer_requirement_event") or {}).get(
            "phase"
        )
        signatures.add((
            trial.get("stage_pc_path")
            or (trial.get("stage_token") or {}).get("path"),
            trial.get("source_id_path"),
            trial.get("operand_path"),
            trial.get("source_stage_path"),
            trial.get("operand_stage_path"),
            json.dumps(trial.get("joining_edge"), sort_keys=True),
            json.dumps(
                trial.get("source_id_packed_slice"), sort_keys=True,
            ),
            json.dumps(
                trial.get("operand_packed_slice"), sort_keys=True,
            ),
            phase,
            trial.get("lane_id"),
        ))
        lag = trial.get("source_selector_lag")
        if lag is None or abs(int(lag)) > 1:
            return (
                False, trials,
                "source-selector lag is missing or unbounded",
            )
        position = trial.get("residence_relative_position")
        if position is not None:
            residence_positions.append(int(position))
        stage_token = trial.get("stage_token") or {}
        residence_span = (
            int(stage_token.get(
                "residence_exit_cycle", stage_token.get("cycle", 0)
            ))
            - int(stage_token.get(
                "residence_entry_cycle", stage_token.get("cycle", 0)
            ))
        )
        if (
            position is not None
            and not 0 <= int(position) <= residence_span + 1
        ):
            return (
                False, trials,
                "operand capture lies outside the token residence",
            )
    if (
        not residence_positions
        or max(residence_positions) - min(residence_positions) > 1
    ):
        return (
            False, trials,
            "operand capture lacks one bounded residence-relative position",
        )
    if len(signatures) != 1:
        return (
            False, trials,
            "the selected consumer-local chain changed across gaps",
        )
    return (
        True, trials,
        "independent gaps validate one fixed consumer-local chain",
    )


def validate_forwarding_positive(
    result, interface, implementation_revision,
):
    adjacent = result.get("experiments", {}).get("adjacent", {})
    dependent = adjacent.get("dependent", [])
    control = adjacent.get("control", [])
    pipeline_valid, pipeline_reason = validate_pipeline_identity(
        interface, implementation_revision,
    )
    sweep_valid, independent_trials, sweep_reason = (
        validate_independent_corroboration(
            result, dependent + control,
        )
    )
    missing_fields = sorted({
        field
        for trial in dependent + independent_trials
        for field in PROOF_FIELDS
        if trial.get(field) is not True
    })
    reasons = []
    if len(dependent) not in (3, 5) or len(control) != len(dependent):
        reasons.append("adjacent 3/5 matched trials are incomplete")
    if missing_fields:
        reasons.append(
            "missing exact proof: " + ", ".join(missing_fields)
        )
    if not sweep_valid:
        reasons.append(sweep_reason)
    if not pipeline_valid:
        reasons.append(pipeline_reason)
    if result.get("zero_delay_behavior_observed") is not True:
        reasons.append("stable zero-delay behavior is absent")
    if result.get("forwarding_required") is not True:
        reasons.append("pre-availability operand use is unresolved")
    return {
        "valid": not reasons,
        "reason": (
            "adjacent and independent trials carry the shared proof chain"
            if not reasons else "; ".join(reasons)
        ),
        "missing_fields": missing_fields,
        "missing_categories": sorted({
            PROOF_CATEGORIES[field] for field in missing_fields
        } | (
            set() if sweep_valid
            else {"independent_distance_corroboration"}
        ) | (
            set() if pipeline_valid else {"pipeline_identity"}
        )),
        "pipeline_valid": pipeline_valid,
        "pipeline_reason": pipeline_reason,
        "sweep_valid": sweep_valid,
        "sweep_reason": sweep_reason,
    }


def enforce_forwarding_positive(
    result, interface, implementation_revision,
):
    """Downgrade an unsupported raw positive while preserving zero delay."""
    proof = validate_forwarding_positive(
        result, interface, implementation_revision,
    )
    result["positive_proof_validation"] = proof
    if result.get("present") is not True or proof["valid"]:
        return proof
    result.update({
        "status": "inconclusive",
        "present": None,
        "bypass_kind": None,
        "confidence": 0.4,
        "forwarding_required": None,
        "zero_delay_classification": (
            "possible_forwarding"
            if result.get("zero_delay_behavior_observed") is True
            else None
        ),
        "requirement_missing_proofs": sorted(set(
            result.get("requirement_missing_proofs", ())
        ) | set(proof["missing_categories"])),
        "evidence": (
            "zero-delay behavior retained without a confirmed positive: "
            + proof["reason"]
        ),
    })
    return proof
