#!/usr/bin/env python3
"""Run the inspector sequentially for every core named in a text file.

The runner is restart-safe: by default, cores that already have a terminal
artifact for the requested implementation revision are skipped.  Failed
invocations do not prevent later cores from running.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


TERMINAL_STATES = {"completed", "failed", "not_applicable"}


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_core_file(path: Path) -> list[str]:
    cores: list[str] = []
    seen: set[str] = set()
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        core = raw_line.split("#", 1)[0].strip()
        if not core:
            continue
        if any(character.isspace() for character in core):
            raise ValueError(
                f"{path}:{line_number}: core names cannot contain whitespace"
            )
        if core in seen:
            raise ValueError(
                f"{path}:{line_number}: duplicate core name {core!r}"
            )
        seen.add(core)
        cores.append(core)
    if not cores:
        raise ValueError(f"{path}: no core names found")
    return cores


def artifact_state(
    output_root: Path, core: str, expected_revision: int
) -> tuple[str, int | None, dict[str, Any]]:
    label_path = output_root / core / f"{core}_labels.json"
    if not label_path.exists():
        return "missing", None, {}
    try:
        labels = json.loads(label_path.read_text(encoding="utf-8"))[core]
        forwarding = labels.get("forwarding", {})
        execution = forwarding.get("execution", {})
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return "invalid", None, {}
    revision = forwarding.get("implementation_revision")
    state = str(execution.get("state") or "unknown")
    if revision != expected_revision:
        return "stale", revision, execution
    return state, revision, execution


def inspector_command(args: argparse.Namespace, core: str) -> list[str]:
    return [
        sys.executable,
        str(args.repo / "src" / "main.py"),
        "-d",
        str(args.cores),
        "-c",
        str(args.config),
        "-o",
        str(args.output),
        "-t",
        str(args.top),
        "-s",
        core,
        "--core-timeout",
        str(args.hard_timeout),
        "--core-idle-timeout",
        str(args.idle_timeout),
    ]


def load_manifest(path: Path, expected_revision: int) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "implementation_revision": expected_revision,
        "runs": {},
    }
    if not path.exists():
        return manifest
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return manifest
    if previous.get("implementation_revision") == expected_revision:
        manifest["runs"].update(previous.get("runs", {}))
    return manifest


def validate_inputs(args: argparse.Namespace, cores: list[str]) -> None:
    missing_configs = [
        core for core in cores if not (args.config / f"{core}.json").is_file()
    ]
    missing_repositories = [
        core for core in cores if not (args.cores / core).is_dir()
    ]
    if missing_configs:
        print(
            "warning: missing configs (the inspector will record terminal "
            "failures): " + ", ".join(missing_configs),
            file=sys.stderr,
        )
    if missing_repositories:
        raise ValueError(
            "missing core repositories: " + ", ".join(missing_repositories)
        )


def parse_args() -> argparse.Namespace:
    repo = Path(__file__).resolve().parents[1]
    project = repo.parent
    parser = argparse.ArgumentParser(
        description=(
            "Run the processor inspector individually for cores in a text file."
        )
    )
    parser.add_argument(
        "core_file",
        nargs="?",
        type=Path,
        default=repo / "revision10_missing_cores.txt",
    )
    parser.add_argument("--revision", type=int, default=10)
    parser.add_argument("--repo", type=Path, default=repo)
    parser.add_argument("--cores", type=Path, default=project / "cores")
    parser.add_argument(
        "--config",
        type=Path,
        default=project / "RV-Bench" / "config" / "cores",
    )
    parser.add_argument(
        "--top",
        type=Path,
        default=project / "RV-Bench" / "wrappers_golden",
    )
    parser.add_argument("--output", type=Path, default=project / "cores_utils")
    parser.add_argument("--hard-timeout", type=int, default=900)
    parser.add_argument("--idle-timeout", type=int, default=180)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--rerun-terminal",
        action="store_true",
        help="run even when a terminal artifact already exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate inputs and print commands without starting simulations",
    )
    args = parser.parse_args()
    for attribute in ("core_file", "repo", "cores", "config", "top", "output"):
        setattr(args, attribute, getattr(args, attribute).resolve())
    args.manifest = (
        args.manifest.resolve()
        if args.manifest
        else args.output / (
            f"revision{args.revision}_completion_manifest.json"
        )
    )
    return args


def main() -> int:
    args = parse_args()
    try:
        cores = read_core_file(args.core_file)
        validate_inputs(args, cores)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    manifest = load_manifest(args.manifest, args.revision)
    manifest.update(
        {
            "implementation_revision": args.revision,
            "core_file": str(args.core_file),
            "hard_timeout_seconds": args.hard_timeout,
            "idle_timeout_seconds": args.idle_timeout,
            "requested_cores": cores,
        }
    )
    environment = os.environ.copy()
    environment.pop("CYCLE_DEBUG", None)
    environment.pop("DEBUG_CYCLE", None)
    failures: list[str] = []

    for index, core in enumerate(cores, start=1):
        prior_state, prior_revision, _ = artifact_state(
            args.output, core, args.revision
        )
        command = inspector_command(args, core)
        if prior_state in TERMINAL_STATES and not args.rerun_terminal:
            print(
                f"[{index}/{len(cores)}] {core}: skip "
                f"revision-{prior_revision} {prior_state}"
            )
            continue
        print(f"[{index}/{len(cores)}] {core}: {shlex.join(command)}")
        if args.dry_run:
            continue

        log_path = args.output / "logs" / f"{core}.completion.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        started_monotonic = time.monotonic()
        started_unix = time.time()
        with log_path.open("w", encoding="utf-8") as log:
            result = subprocess.run(
                command,
                cwd=args.repo,
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        duration = round(time.monotonic() - started_monotonic, 3)
        state, revision, execution = artifact_state(
            args.output, core, args.revision
        )
        successful = (
            result.returncode == 0
            and revision == args.revision
            and state in {"completed", "not_applicable"}
        )
        if not successful:
            failures.append(core)
        manifest["runs"][core] = {
            "core": core,
            "command": command,
            "started_at_unix": started_unix,
            "duration_seconds": duration,
            "return_code": result.returncode,
            "terminal_state": state,
            "artifact_revision": revision,
            "timeout_kind": execution.get("timeout_kind"),
            "last_progress_marker": execution.get("last_progress_marker"),
            "log": str(log_path),
        }
        manifest["failed_cores"] = failures
        atomic_json(args.manifest, manifest)
        print(
            f"[{index}/{len(cores)}] {core}: {state} "
            f"revision={revision} rc={result.returncode} duration={duration}s"
        )

    if args.dry_run:
        print(f"Dry run complete: {len(cores)} core(s) validated.")
        return 0
    manifest["failed_cores"] = failures
    manifest["complete"] = not failures
    atomic_json(args.manifest, manifest)
    print(
        f"Completion run finished: {len(cores) - len(failures)} succeeded, "
        f"{len(failures)} failed."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
