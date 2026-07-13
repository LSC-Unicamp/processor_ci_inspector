#!/usr/bin/env python3
"""Run and compare golden core label cases against the current analyzer.

The golden files are old public-label snapshots. This script treats them as a
behavioral contract and intentionally ignores newer debug-only JSON fields.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PUBLIC_FIELDS = (
    "license_types",
    "bits",
    "cache",
    "cache_dimensions",
    "language",
    "multicycle",
    "superscalar",
    "isa",
    "bus_type",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_root() -> Path:
    return repo_root().parent


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} does not contain a JSON object")
    return data


def load_core_labels(path: Path, core_name: str) -> dict[str, Any]:
    data = load_json(path)
    if core_name in data and isinstance(data[core_name], dict):
        return data[core_name]
    if len(data) == 1:
        only_value = next(iter(data.values()))
        if isinstance(only_value, dict):
            return only_value
    raise KeyError(f"{path} does not contain labels for {core_name!r}")


def discover_golden_files(golden_dir: Path) -> dict[str, Path]:
    golden_files: dict[str, Path] = {}
    for path in sorted(golden_dir.glob("*_labels.json")):
        core = path.name[: -len("_labels.json")]
        golden_files[core] = path
    return golden_files


def canonicalize_public_value(value: Any) -> Any:
    if isinstance(value, list):
        return sorted(str(item) for item in value)
    return value


def pipeline_depth_candidates(pipeline: Any) -> dict[str, Any]:
    if not isinstance(pipeline, dict):
        return {}
    candidates: dict[str, Any] = {}
    for key in ("depth", "depth_estimate", "raw_depth_estimate"):
        if key in pipeline:
            candidates[key] = pipeline[key]
    cycle_class = pipeline.get("classification")
    if isinstance(cycle_class, dict):
        nested_pipeline = cycle_class.get("pipeline")
        if isinstance(nested_pipeline, dict):
            for key in ("depth", "depth_estimate", "raw_depth_estimate"):
                if key in nested_pipeline:
                    candidates[f"classification.{key}"] = nested_pipeline[key]
    return candidates


def compare_pipeline(
    expected: Any,
    actual: Any,
    *,
    strict_depth: bool,
) -> tuple[list[str], list[str]]:
    mismatches: list[str] = []
    warnings: list[str] = []

    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            mismatches.append(f"pipeline expected {expected!r}, got {actual!r}")
            return mismatches, warnings

        expected_depth = expected.get("depth", expected.get("depth_estimate"))
        if expected_depth is None:
            return mismatches, warnings

        actual_depths = pipeline_depth_candidates(actual)
        primary_depth = actual.get("depth", actual.get("depth_estimate"))
        if strict_depth:
            if primary_depth != expected_depth:
                mismatches.append(
                    "pipeline primary depth expected "
                    f"{expected_depth!r}, got {primary_depth!r}; "
                    f"all candidates={actual_depths!r}"
                )
            return mismatches, warnings

        if expected_depth not in actual_depths.values():
            mismatches.append(
                "pipeline depth expected "
                f"{expected_depth!r}, got candidates {actual_depths!r}"
            )
        elif primary_depth != expected_depth:
            warnings.append(
                "pipeline expected depth matched a secondary estimate "
                f"({expected_depth!r}); primary depth is {primary_depth!r}"
            )
        return mismatches, warnings

    if expected != actual:
        mismatches.append(f"pipeline expected {expected!r}, got {actual!r}")
    return mismatches, warnings


def compare_labels(
    core_name: str,
    expected: dict[str, Any],
    actual: dict[str, Any],
    *,
    strict_depth: bool,
) -> tuple[list[str], list[str]]:
    del core_name
    mismatches: list[str] = []
    warnings: list[str] = []

    for field in PUBLIC_FIELDS:
        if field not in expected:
            continue
        if expected[field] is None:
            continue
        if field not in actual:
            mismatches.append(f"{field} missing from actual labels")
            continue
        exp_value = canonicalize_public_value(expected[field])
        act_value = canonicalize_public_value(actual[field])
        if exp_value != act_value:
            mismatches.append(f"{field} expected {exp_value!r}, got {act_value!r}")

    if "pipeline" in expected:
        pipe_mismatches, pipe_warnings = compare_pipeline(
            expected["pipeline"],
            actual.get("pipeline"),
            strict_depth=strict_depth,
        )
        mismatches.extend(pipe_mismatches)
        warnings.extend(pipe_warnings)

    return mismatches, warnings


def default_python() -> Path:
    env_python = repo_root() / "env" / "bin" / "python"
    if env_python.exists():
        return env_python
    return Path(sys.executable)


def run_core(args: argparse.Namespace, core_name: str) -> dict[str, Any]:
    command = [
        str(args.python),
        str(repo_root() / "src" / "main.py"),
        "-s",
        core_name,
        "-d",
        str(args.cores_dir),
        "-c",
        str(args.config_dir),
        "-t",
        str(args.wrappers_dir),
        "-o",
        str(args.output_dir),
    ]

    env = os.environ.copy()
    if args.cycle_debug:
        env["CYCLE_DEBUG"] = "1"
    if args.regfile_debug:
        env["REGFILE_FINDER_DEBUG"] = "1"

    log_path = None
    stdout_target = None
    stderr_target = None
    if args.log_dir:
        args.log_dir.mkdir(parents=True, exist_ok=True)
        log_path = args.log_dir / f"{core_name}.log"
        stdout_target = log_path.open("w", encoding="utf-8")
        stderr_target = subprocess.STDOUT

    try:
        completed = subprocess.run(
            command,
            cwd=args.project_root,
            env=env,
            stdout=stdout_target,
            stderr=stderr_target,
            text=True,
            timeout=args.run_timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "log": str(log_path) if log_path else None,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": None,
            "timeout": args.run_timeout,
            "error": str(exc),
            "log": str(log_path) if log_path else None,
        }
    finally:
        if stdout_target is not None:
            stdout_target.close()


def actual_label_path(output_dir: Path, core_name: str) -> Path:
    return output_dir / core_name / f"{core_name}_labels.json"


def validate_core(
    args: argparse.Namespace,
    core_name: str,
    golden_path: Path,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "core": core_name,
        "golden_path": str(golden_path),
        "actual_path": str(actual_label_path(args.output_dir, core_name)),
        "run": None,
        "status": "unknown",
        "mismatches": [],
        "warnings": [],
    }

    if args.run:
        run_result = run_core(args, core_name)
        result["run"] = run_result
        if run_result.get("returncode") != 0:
            result["status"] = "run_failed"
            result["mismatches"].append(
                f"analyzer run failed with return code {run_result.get('returncode')}"
            )
            if not args.compare_after_run_failure:
                return result

    actual_path = actual_label_path(args.output_dir, core_name)
    if not actual_path.exists():
        result["status"] = "missing_actual"
        result["mismatches"].append(f"missing actual labels at {actual_path}")
        return result

    try:
        expected = load_core_labels(golden_path, core_name)
        actual = load_core_labels(actual_path, core_name)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        result["status"] = "load_failed"
        result["mismatches"].append(str(exc))
        return result

    mismatches, warnings = compare_labels(
        core_name,
        expected,
        actual,
        strict_depth=args.strict_depth,
    )
    result["mismatches"] = mismatches
    result["warnings"] = warnings
    if mismatches:
        result["status"] = "failed"
    elif warnings and args.fail_on_warning:
        result["status"] = "failed"
        result["mismatches"] = warnings
    elif warnings:
        result["status"] = "passed_with_warnings"
    else:
        result["status"] = "passed"
    return result


def print_summary(results: list[dict[str, Any]]) -> None:
    print("\nGolden validation results")
    print("=========================")
    for result in results:
        core = result["core"]
        status = result["status"]
        marker = "PASS" if status in {"passed", "passed_with_warnings"} else "FAIL"
        if status == "passed_with_warnings":
            marker = "WARN"
        print(f"{marker:4} {core} ({status})")
        for message in result.get("mismatches", []):
            print(f"     - {message}")
        for message in result.get("warnings", []):
            print(f"     * {message}")
        run = result.get("run")
        if run and run.get("log"):
            print(f"       log: {run['log']}")

    total = len(results)
    failed = sum(1 for item in results if item["status"] not in {"passed", "passed_with_warnings"})
    warned = sum(1 for item in results if item["status"] == "passed_with_warnings")
    passed = total - failed
    print(f"\nSummary: {passed}/{total} passed, {failed} failed, {warned} warnings")


def write_report(path: Path, args: argparse.Namespace, results: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    failed = sum(1 for item in results if item["status"] not in {"passed", "passed_with_warnings"})
    warned = sum(1 for item in results if item["status"] == "passed_with_warnings")
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_enabled": args.run,
        "strict_depth": args.strict_depth,
        "summary": {
            "total": len(results),
            "passed": len(results) - failed,
            "failed": failed,
            "warnings": warned,
        },
        "results": results,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=4)


def parse_args(argv: list[str]) -> argparse.Namespace:
    root = repo_root()
    proj_root = project_root()
    parser = argparse.ArgumentParser(
        description=(
            "Validate current analyzer labels against golden public-label "
            "snapshots."
        )
    )
    parser.add_argument("--golden-dir", type=Path, default=root / "golden_cases")
    parser.add_argument("--project-root", type=Path, default=proj_root)
    parser.add_argument("--cores-dir", type=Path, default=proj_root / "cores")
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=proj_root / "RV-Bench" / "config" / "cores",
    )
    parser.add_argument(
        "--wrappers-dir",
        type=Path,
        default=proj_root / "processor_ci_lab" / "automated_wrappers_golden",
    )
    parser.add_argument("--output-dir", type=Path, default=proj_root / "cores_utils")
    parser.add_argument("--python", type=Path, default=default_python())
    parser.add_argument(
        "--cores",
        nargs="+",
        help="Only validate these core names. Defaults to all golden cases.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run src/main.py for each selected core before comparing labels.",
    )
    parser.add_argument(
        "--compare-after-run-failure",
        action="store_true",
        help="Still compare existing labels if a run fails.",
    )
    parser.add_argument(
        "--run-timeout",
        type=int,
        default=None,
        help="Optional per-core run timeout in seconds.",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        help="Capture per-core analyzer output here when --run is used.",
    )
    parser.add_argument(
        "--strict-depth",
        action="store_true",
        help="Require the current primary pipeline depth to match the golden depth.",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Treat schema-compatible depth warnings as failures.",
    )
    parser.add_argument(
        "--cycle-debug",
        action="store_true",
        help="Set CYCLE_DEBUG=1 during --run.",
    )
    parser.add_argument(
        "--regfile-debug",
        action="store_true",
        help="Set REGFILE_FINDER_DEBUG=1 during --run.",
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        help="Write a machine-readable validation report.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    golden_files = discover_golden_files(args.golden_dir)
    if not golden_files:
        print(f"No golden files found in {args.golden_dir}", file=sys.stderr)
        return 2

    selected_cores = args.cores or list(golden_files)
    missing_golden = [core for core in selected_cores if core not in golden_files]
    if missing_golden:
        print(
            "Missing golden files for: " + ", ".join(sorted(missing_golden)),
            file=sys.stderr,
        )
        return 2

    results = [
        validate_core(args, core, golden_files[core])
        for core in selected_cores
    ]
    print_summary(results)

    if args.json_report:
        write_report(args.json_report, args, results)
        print(f"\nWrote report: {args.json_report}")

    failed = any(result["status"] not in {"passed", "passed_with_warnings"} for result in results)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
