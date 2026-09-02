#!/usr/bin/env python3
"""Run revision-8 forwarding retries individually and retain a manifest."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


PRIORITY_CORES = [
    "AdamRiscv",
    "RISCVPipelinedProcessor",
    "Grande-Risco-5",
    "RISC-V",
    "RV12",
]
REMAINING_TIMEOUT_CORES = [
    "Pequeno-Risco-5",
    "RISC-V_Angelo",
    "RISCV_Pipeline_Core",
    "VexRiscv",
    "VexiiRiscv",
    "clarvi",
    "cv32e40s",
    "cv32e40x",
    "cv32e41p",
    "kronos",
    "mr1",
    "riscv",
    "rv3n",
    "scr1",
    "yarvi",
]
TIMEOUT_CORES = PRIORITY_CORES + REMAINING_TIMEOUT_CORES
REVISION11_CANARY_CORES = [
    "AdamRiscv", "arRISCado", "dv-cpu-rv", "starsea_riscv",
    "VexRiscv", "Pequeno-Risco-5", "RISCV_Verilog",
    "RV32i-Verilog", "clarvi", "scr1", "yarvi", "mr1", "RS5",
    "cv32e41p", "RISCVPipelinedProcessor", "cve2", "super-riscv",
]
IMPLEMENTATION_REVISION = 8


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def artifact_state(output_root: Path, core: str) -> tuple[str, dict]:
    label_path = output_root / core / f"{core}_labels.json"
    if not label_path.exists():
        return "missing", {}
    try:
        labels = json.loads(label_path.read_text(encoding="utf-8"))[core]
    except (OSError, KeyError, json.JSONDecodeError):
        return "invalid", {}
    forwarding = labels.get("forwarding", {})
    execution = forwarding.get("execution", {})
    if forwarding.get("implementation_revision") != IMPLEMENTATION_REVISION:
        return "stale", execution
    return str(execution.get("state") or "unknown"), execution


def run_individual(
    args: argparse.Namespace, core: str, manifest: dict,
) -> bool:
    command = [
        sys.executable, str(args.repo / "src" / "main.py"),
        "-d", str(args.cores),
        "-c", str(args.config),
        "-o", str(args.output),
        "-t", str(args.top),
        "-s", core,
        "--core-timeout", str(args.hard_timeout),
        "--core-idle-timeout", str(args.idle_timeout),
    ]
    log_path = args.output / "logs" / f"{core}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.pop("CYCLE_DEBUG", None)
    environment.pop("DEBUG_CYCLE", None)
    started = time.monotonic()
    started_unix = time.time()
    with log_path.open("w", encoding="utf-8") as log:
        completed = subprocess.run(
            command, cwd=args.repo, env=environment,
            stdout=log, stderr=subprocess.STDOUT, check=False,
        )
    duration = round(time.monotonic() - started, 3)
    terminal_state, execution = artifact_state(args.output, core)
    progress_path = (
        args.output / core / f"{core}_analysis_progress.json"
    )
    try:
        last_progress = json.loads(
            progress_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        last_progress = execution.get("last_progress_marker")
    record = {
        "core": core,
        "command": command,
        "hard_timeout_seconds": args.hard_timeout,
        "idle_timeout_seconds": args.idle_timeout,
        "started_at_unix": started_unix,
        "duration_seconds": duration,
        "return_code": completed.returncode,
        "terminal_state": terminal_state,
        "last_progress_marker": last_progress,
        "timeout_kind": execution.get("timeout_kind"),
        "log": str(log_path),
    }
    manifest.setdefault("runs", {})[core] = record
    atomic_json(args.manifest, manifest)
    print(
        f"{core}: {terminal_state} rc={completed.returncode} "
        f"duration={duration}s"
    )
    return completed.returncode == 0 and terminal_state == "completed"


def main(implementation_revision: int = 8) -> int:
    global IMPLEMENTATION_REVISION
    IMPLEMENTATION_REVISION = int(implementation_revision)
    repo = Path(__file__).resolve().parents[1]
    project = repo.parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scope", choices=("priority", "timeouts", "canaries", "broad"),
        default="priority",
    )
    parser.add_argument(
        "--core", action="append", default=[],
        help="run only this named timeout core (repeatable)",
    )
    parser.add_argument("--repo", type=Path, default=repo)
    parser.add_argument("--cores", type=Path, default=project / "cores")
    parser.add_argument(
        "--config", type=Path,
        default=project / "RV-Bench" / "config" / "cores",
    )
    parser.add_argument(
        "--top", type=Path,
        default=project / "RV-Bench" / "wrappers_golden",
    )
    parser.add_argument(
        "--output", type=Path,
        default=project / f"cores_utils_revision{IMPLEMENTATION_REVISION}",
    )
    parser.add_argument("--hard-timeout", type=int, default=900)
    parser.add_argument("--idle-timeout", type=int, default=180)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    args.cores = args.cores.resolve()
    args.config = args.config.resolve()
    args.top = args.top.resolve()
    args.output = args.output.resolve()
    args.manifest = (
        args.manifest.resolve()
        if args.manifest else args.output / "run_manifest.json"
    )
    manifest = {
        "implementation_revision": IMPLEMENTATION_REVISION,
        "scope": args.scope,
        "hard_timeout_seconds": args.hard_timeout,
        "idle_timeout_seconds": args.idle_timeout,
        "excluded_non_timeout_failures": ["biriscv", "serv"],
        "runs": {},
    }
    if args.manifest.exists():
        try:
            previous = json.loads(
                args.manifest.read_text(encoding="utf-8")
            )
            if (
                previous.get("implementation_revision")
                == IMPLEMENTATION_REVISION
            ):
                manifest["runs"].update(previous.get("runs", {}))
        except (OSError, json.JSONDecodeError):
            pass

    if args.scope == "broad":
        priority_ready = all(
            artifact_state(args.output, core)[0] == "completed"
            for core in PRIORITY_CORES
        )
        if not priority_ready:
            print(
                "Broad rollout blocked: all five priority cores must have "
                f"completed revision-{IMPLEMENTATION_REVISION} artifacts.",
                file=sys.stderr,
            )
            return 2
        command = [
            sys.executable, str(args.repo / "src" / "main.py"),
            "-d", str(args.cores), "-c", str(args.config),
            "-o", str(args.output), "-t", str(args.top), "-b",
            "--core-timeout", str(args.hard_timeout),
            "--core-idle-timeout", str(args.idle_timeout),
        ]
        manifest["broad_command"] = command
        atomic_json(args.manifest, manifest)
        return subprocess.run(command, cwd=args.repo, check=False).returncode

    selected = args.core or (
        PRIORITY_CORES
        if args.scope == "priority"
        else REVISION11_CANARY_CORES
        if args.scope == "canaries"
        else TIMEOUT_CORES
    )
    supported_individual = (
        set(TIMEOUT_CORES)
        if IMPLEMENTATION_REVISION < 11
        else set(TIMEOUT_CORES) | set(REVISION11_CANARY_CORES)
    )
    unsupported = sorted(set(selected) - supported_individual)
    if unsupported:
        parser.error(
            f"individual revision-{IMPLEMENTATION_REVISION} retries are "
            "limited to the revision-specific timeout/canary "
            f"cores; unsupported: {', '.join(unsupported)}"
        )
    all_completed = True
    for core in selected:
        completed = run_individual(args, core, manifest)
        all_completed &= completed
    manifest["priority_gate_passed"] = all(
        artifact_state(args.output, core)[0] == "completed"
        for core in PRIORITY_CORES
    )
    manifest["all_selected_completed"] = all_completed
    atomic_json(args.manifest, manifest)
    return 0 if all_completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
