"""An unobservable register file leaves independent Inspector findings intact."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cocotb_labeler import _mark_experimental_disabled, _record_unavailable_regfile
import main


def test_unavailable_regfile_keeps_existing_findings(tmp_path):
    output_dir = tmp_path / "sample"
    output_dir.mkdir()
    labels_path = output_dir / "sample_labels.json"
    labels_path.write_text(
        json.dumps({"sample": {"language": "Verilog", "license": "MIT"}}),
        encoding="utf-8",
    )

    dut = SimpleNamespace(_log=SimpleNamespace(warning=Mock()))
    with mock.patch.dict(
        "os.environ", {"RVB_INSPECTOR_SKIP_EXPERIMENTAL": "1"}
    ):
        _record_unavailable_regfile(
            dut, str(output_dir), "sample", "No visible register-file candidate was found"
        )

    labels = json.loads(labels_path.read_text(encoding="utf-8"))["sample"]
    assert labels["language"] == "Verilog"
    assert labels["license"] == "MIT"
    assert labels["analysis"]["state"] == "partial"
    assert labels["analysis"]["unavailable_probes"] == ["cycle"]
    assert set(labels["analysis"]["disabled_probes"]) == {
        "forwarding", "branch_prediction"
    }
    dut._log.warning.assert_called_once()


def test_disabled_probes_remove_prior_findings(monkeypatch):
    monkeypatch.setenv("RVB_INSPECTOR_SKIP_EXPERIMENTAL", "1")
    labels = {
        "language": "Verilog",
        "forwarding": {"present": True},
        "branch_prediction": {"present": True},
        "forwarding_debug": {},
        "hazard_handling": {},
    }
    _mark_experimental_disabled(labels)
    assert labels["language"] == "Verilog"
    assert not any(name in labels for name in (
        "forwarding", "branch_prediction", "forwarding_debug", "hazard_handling"
    ))
    assert labels["analysis"]["disabled_probes"]["forwarding"] == "not released"


def test_failed_rvbench_run_does_not_resurrect_experimental_results(tmp_path, monkeypatch):
    monkeypatch.setenv("RVB_INSPECTOR_SKIP_EXPERIMENTAL", "1")
    path = tmp_path / "sample_labels.json"
    previous = {"sample": {
        "branch_prediction": {"present": True},
        "forwarding": {"present": True},
    }}
    main._mark_analysis_failed(
        path, json.dumps(previous).encode(), "sample", RuntimeError("simulator failed")
    )
    labels = json.loads(path.read_text(encoding="utf-8"))["sample"]
    assert "branch_prediction" not in labels
    assert "forwarding" not in labels
    assert set(labels["analysis"]["disabled_probes"]) == {
        "forwarding", "branch_prediction"
    }
