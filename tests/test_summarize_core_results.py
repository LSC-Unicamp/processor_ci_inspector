import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "summarize_core_results.py"
SPEC = importlib.util.spec_from_file_location("summarize_core_results", SCRIPT)
summary = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(summary)


class CoreSummaryTests(unittest.TestCase):
    def write_labels(self, root, core, labels):
        core_dir = root / core
        core_dir.mkdir()
        (core_dir / f"{core}_labels.json").write_text(
            json.dumps({core: labels}), encoding="utf-8"
        )

    def test_collects_requested_fields_from_pipeline_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_labels(root, "alpha", {
                "license_types": ["MIT"],
                "language": "SystemVerilog",
                "bits": 32,
                "cycle": {
                    "fetch_to_commit_latencies": [4, 4, 4],
                    "classification": {"pipeline": {"depth_estimate": 5}},
                },
            })
            rows, errors = summary.collect_rows(root)

        self.assertEqual(errors, [])
        self.assertEqual(rows, [[
            "alpha", "MIT", "SystemVerilog", "RV32", "Pipelined", "5",
            "4 cycles (3 samples)", "alpha/alpha_labels.json",
        ]])

    def test_distinguishes_non_pipeline_and_variable_latency(self):
        labels = {
            "license_types": ["Undetected"],
            "language": "Verilog",
            "bits": 64,
            "multicycle": True,
            "cycle": {"fetch_to_commit_latencies": [2, 3, 3, 4]},
        }
        row = summary.core_row("beta", labels, Path("/tmp/beta_labels.json"), Path("/tmp"))

        self.assertEqual(row[4], "Multi-cycle")
        self.assertEqual(row[5], "—")
        self.assertEqual(row[6], "3 cycles (mode; 2/4 samples; range 2–4)")

    def test_accepts_historical_single_key_core_name(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "renamed_labels.json"
            path.write_text(json.dumps({"actual-core": {"bits": 32}}), encoding="utf-8")
            core, labels = summary.load_labels(path)

        self.assertEqual(core, "actual-core")
        self.assertEqual(labels["bits"], 32)
