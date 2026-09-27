"""Atomic per-core progress markers consumed by the analysis watchdog."""

import json
import time
from pathlib import Path

ANALYSIS_IMPLEMENTATION_REVISION = 11


def write_analysis_progress(core_dir, processor_name, phase, revision, **details):
    path = Path(core_dir) / f"{processor_name}_analysis_progress.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        previous = {}
    record = {
        "implementation_revision": revision,
        "processor": processor_name,
        "phase": phase,
        "sequence": int(previous.get("sequence", 0)) + 1,
        "updated_at_unix": time.time(),
        **details,
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(record, indent=2), encoding="utf-8")
    temporary.replace(path)
    return record
