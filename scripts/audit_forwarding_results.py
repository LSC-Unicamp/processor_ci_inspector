#!/usr/bin/env python3
"""Audit or downgrade unsupported forwarding positives and negatives."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.forwarding_proof import (  # noqa: E402
    enforce_forwarding_positive,
    validate_forwarding_positive,
    validate_independent_corroboration,
    validate_pipeline_identity,
)


STORE_PATHS = {
    "alu_to_store_data",
    "alu_to_store_address",
    "load_to_store_data",
    "load_to_store_address",
}
PROBE_SUITE_VERSION = "paired-forwarding-v8"
IMPLEMENTATION_REVISION = 11


def load_core(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    name, labels = next(iter(data.items()))
    return data, name, labels


def trial_groups(labels: dict, path_name: str):
    result = labels.get("forwarding", {}).get(path_name, {})
    adjacent = result.get("experiments", {}).get("adjacent", {})
    dependent = adjacent.get("dependent", [])
    control = adjacent.get("control", [])
    if dependent or control:
        return dependent, control
    # Legacy fallback for results generated before compact audit evidence.
    probes = labels.get("forwarding_debug", {}).get("probes", {})
    trials = probes.get(f"{path_name}_paired_gap_0", [])
    dependent = [item.get("observation", {}) for item in trials if item.get("role") == "dependent"]
    control = [item.get("observation", {}) for item in trials if item.get("role") == "control"]
    return dependent, control


def validated_store_failure(labels: dict, path_name: str):
    dependent, control = trial_groups(labels, path_name)
    if len(dependent) not in (3, 5) or len(control) != len(dependent):
        return False, "three or five paired compact/debug trials are not available"
    if not all(item.get("architectural_complete") is True for item in dependent + control):
        return False, "architectural program completion is not stable"
    if not all(item.get("dependency_correct") is True for item in control):
        return False, "the control store is not correct in every trial"
    stable_absence = all(
        item.get("store_absence_architecturally_observable") is True
        for item in dependent
    )
    if stable_absence:
        return True, "the fetched dependent store is stably absent through a working interface"
    if not all(item.get("dependency_correct") is False for item in dependent):
        return False, "the dependent failure is not stable"
    if not all(item.get("transaction_observable") is True for item in dependent):
        return False, "the dependent store transaction is not observable in every trial"
    signatures = {
        (
            (item.get("observed_store") or {}).get("address"),
            (item.get("observed_store") or {}).get("value"),
        )
        for item in dependent
    }
    if len(signatures) != 1 or signatures == {(None, None)}:
        return False, "the incorrect dependent store signature is not stable"
    return True, "stable observable architectural store failure"


def validated_independent_corroboration(result: dict, adjacent: list):
    return validate_independent_corroboration(result, adjacent)


def validated_pipeline_identity(labels_path: Path, core: str):
    path = labels_path.parent / f"{core}_pipeline_interface.json"
    if not path.exists():
        return False, "pipeline-interface artifact is missing"
    interface = json.loads(path.read_text(encoding="utf-8"))
    return validate_pipeline_identity(
        interface, IMPLEMENTATION_REVISION,
    )


def audit_file(path: Path, apply: bool):
    data, core, labels = load_core(path)
    forwarding = labels.get("forwarding")
    if not isinstance(forwarding, dict):
        return [], False
    if (
        forwarding.get("schema_version") != 2
        or forwarding.get("probe_suite_version") != PROBE_SUITE_VERSION
        or forwarding.get("implementation_revision") != IMPLEMENTATION_REVISION
    ):
        return [(
            core, "__run__", False,
            "forwarding result is stale or from an unsupported probe suite",
        )], False
    if forwarding.get("execution", {}).get("state") != "completed":
        return [], False
    reports = []
    changed = False
    interface_path = path.parent / f"{core}_pipeline_interface.json"
    interface = (
        json.loads(interface_path.read_text(encoding="utf-8"))
        if interface_path.exists() else None
    )
    for path_name, result in forwarding.items():
        if not isinstance(result, dict):
            continue
        if result.get("present") is True:
            proof = validate_forwarding_positive(
                result, interface, IMPLEMENTATION_REVISION,
            )
            valid = proof["valid"]
            reason = (
                "adjacent and independent trials carry the shared proof chain"
                if valid else
                "confirmed positive lacks revision-11 corroboration: "
                + proof["reason"]
            )
            reports.append((core, path_name, valid, reason))
            if not valid and apply:
                enforce_forwarding_positive(
                    result, interface, IMPLEMENTATION_REVISION,
                )
                changed = True
            continue
        if result.get("status") != "not_detected":
            continue
        if path_name in STORE_PATHS:
            valid, reason = validated_store_failure(labels, path_name)
        else:
            valid = result.get("absence_evidence_validated") is True
            reason = "classifier did not record validated architectural absence evidence"
        reports.append((core, path_name, valid, reason))
        if valid or not apply:
            continue
        result.update({
            "status": "inconclusive",
            "present": None,
            "confidence": 0.35,
            "absence_evidence_validated": False,
            "evidence": f"prior negative downgraded by forwarding audit: {reason}",
        })
        changed = True
    if changed:
        path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")
    return reports, changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("labels_root", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--core", action="append", default=[])
    args = parser.parse_args()
    reports = []
    changed_files = 0
    for path in sorted(args.labels_root.glob("*/*_labels.json")):
        if args.core and path.parent.name not in args.core:
            continue
        file_reports, changed = audit_file(path, args.apply)
        reports.extend(file_reports)
        changed_files += int(changed)
    for core, path_name, valid, reason in reports:
        print(f"{'KEEP' if valid else 'DOWNGRADE'} {core} {path_name}: {reason}")
    invalid = sum(not item[2] for item in reports)
    print(f"audited={len(reports)} unsupported={invalid} changed_files={changed_files}")
    return 1 if invalid and not args.apply else 0


if __name__ == "__main__":
    raise SystemExit(main())
