#!/usr/bin/env python3
"""Render a compact, human-readable summary of ProcessorCI label artifacts.

The inspector writes one ``<core>_labels.json`` file per core.  This utility
collects those files from an output directory (``../cores_utils`` by default)
and produces a Markdown table intended for project documentation or review.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


UNKNOWN_VALUES = {"", "undetected", "unknown", "none", "n/a"}
LABEL_SUFFIX = "_labels.json"


def project_root() -> Path:
    """Return the directory that contains this inspector checkout."""
    return Path(__file__).resolve().parents[1]


def default_input_dir() -> Path:
    """Return the workspace-level results directory used by this project."""
    return project_root().parent / "cores_utils"


def display_value(value: Any, fallback: str = "Not measured") -> str:
    """Turn absent inspector values into a consistent table value."""
    if value is None:
        return fallback
    text = str(value).strip()
    return fallback if text.lower() in UNKNOWN_VALUES else text


def markdown_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def load_labels(path: Path) -> tuple[str, dict[str, Any]]:
    """Load one artifact, accepting the historical single-key JSON shape."""
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("top-level JSON value is not an object")

    expected_name = path.name[: -len(LABEL_SUFFIX)]
    labels = payload.get(expected_name)
    if isinstance(labels, dict):
        return expected_name, labels
    if len(payload) == 1:
        core_name, labels = next(iter(payload.items()))
        if isinstance(core_name, str) and isinstance(labels, dict):
            return core_name, labels
    raise ValueError(f"does not contain an object for {expected_name!r}")


def pipeline_value(labels: dict[str, Any]) -> Any:
    cycle = labels.get("cycle")
    classification = cycle.get("classification") if isinstance(cycle, dict) else None
    if isinstance(classification, dict) and "pipeline" in classification:
        return classification["pipeline"]
    return labels.get("pipeline")


def datapath_style(labels: dict[str, Any]) -> str:
    """Map current and older classifier schemas to a stable user-facing name."""
    pipeline = pipeline_value(labels)
    if isinstance(pipeline, dict) or pipeline is True:
        return "Pipelined"

    cycle = labels.get("cycle")
    classification = cycle.get("classification") if isinstance(cycle, dict) else None
    if isinstance(classification, dict):
        if classification.get("single_cycle") is True:
            return "Single-cycle"
        if classification.get("multicycle") is True:
            return "Multi-cycle"
    if labels.get("multicycle") is True:
        return "Multi-cycle"
    return "Not measured"


def pipeline_depth(labels: dict[str, Any], style: str) -> str:
    if style != "Pipelined":
        return "—"
    pipeline = pipeline_value(labels)
    if not isinstance(pipeline, dict):
        return "Not measured"
    depth = pipeline.get("depth_estimate", pipeline.get("depth"))
    return display_value(depth)


def instruction_latency(labels: dict[str, Any]) -> str:
    """Report modal fetch-to-commit latency, retaining variability when present."""
    cycle = labels.get("cycle")
    samples = cycle.get("fetch_to_commit_latencies") if isinstance(cycle, dict) else None
    if not isinstance(samples, list):
        return "Not measured"
    numeric_samples = [sample for sample in samples if isinstance(sample, (int, float))]
    if not numeric_samples:
        return "Not measured"

    counts = Counter(numeric_samples)
    mode, mode_count = max(counts.items(), key=lambda item: (item[1], -item[0]))
    unit = "cycle" if mode == 1 else "cycles"
    if len(counts) == 1:
        return f"{mode:g} {unit} ({len(numeric_samples)} samples)"
    minimum, maximum = min(numeric_samples), max(numeric_samples)
    return (
        f"{mode:g} {unit} (mode; {mode_count}/{len(numeric_samples)} samples; "
        f"range {minimum:g}–{maximum:g})"
    )


def license_type(labels: dict[str, Any]) -> str:
    values = labels.get("license_types")
    if not isinstance(values, list):
        return "Not measured"
    visible = sorted({display_value(value) for value in values})
    return ", ".join(visible) if visible else "Not measured"


def xlen(labels: dict[str, Any]) -> str:
    bits = display_value(labels.get("bits"))
    return f"RV{bits}" if bits != "Not measured" else bits


def core_row(core: str, labels: dict[str, Any], source: Path, input_dir: Path) -> list[str]:
    style = datapath_style(labels)
    try:
        source_text = str(source.relative_to(input_dir))
    except ValueError:
        source_text = str(source)
    return [
        core,
        license_type(labels),
        display_value(labels.get("language")),
        xlen(labels),
        style,
        pipeline_depth(labels, style),
        instruction_latency(labels),
        source_text,
    ]


def collect_rows(input_dir: Path) -> tuple[list[list[str]], list[str]]:
    """Collect usable label artifacts and non-fatal parse errors."""
    rows: list[list[str]] = []
    errors: list[str] = []
    for path in sorted(input_dir.rglob(f"*{LABEL_SUFFIX}")):
        try:
            core, labels = load_labels(path)
            rows.append(core_row(core, labels, path, input_dir))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
    return sorted(rows, key=lambda row: (row[0].casefold(), row[-1])), errors


def render_markdown(input_dir: Path, rows: Iterable[list[str]], errors: Iterable[str]) -> str:
    rows = list(rows)
    errors = list(errors)
    lines = [
        "# ProcessorCI core summary",
        "",
        f"Source: `{input_dir}`. Cores summarized: {len(rows)}.",
        "",
        "| Core | License | HDL | XLEN | Datapath | Pipeline depth estimate | Instruction latency | Artifact |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(markdown_escape(value) for value in row) + " |")

    lines.extend([
        "",
        "Instruction latency is the modal observed fetch-to-architectural-commit latency. "
        "A range is included when samples vary. Pipeline depth is shown only for cores classified as pipelined; it is an estimate, not a declared microarchitecture stage count.",
    ])
    if errors:
        lines.extend(["", "## Skipped artifacts", ""])
        lines.extend(f"- `{markdown_escape(error)}`" for error in errors)
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir", type=Path, default=default_input_dir(),
        help="Directory containing per-core *_labels.json artifacts (default: %(default)s).",
    )
    parser.add_argument(
        "--output", type=Path,
        help="Write the Markdown report to this path instead of standard output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    if not input_dir.is_dir():
        print(f"error: input directory does not exist: {input_dir}", file=sys.stderr)
        return 2

    rows, errors = collect_rows(input_dir)
    report = render_markdown(input_dir, rows, errors)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Wrote {len(rows)} core summaries to {args.output}")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
