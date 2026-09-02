import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import main
from forwarding_proof import enforce_forwarding_positive
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_forwarding_results


def _hanging_core_worker(result_queue, *args):
    os.setsid()
    child = subprocess.Popen(["/bin/sleep", "30"])
    signal_pause = getattr(__import__("signal"), "pause")
    while True:
        _ = child.pid
        signal_pause()


def _aborting_core_worker(result_queue, *args):
    os.setsid()
    os._exit(7)


def _heartbeat_core_worker(result_queue, *args):
    os.setsid()
    directory, _, output_dir, *_ = args
    processor = Path(directory).name
    for index in range(3):
        main._write_core_progress(
            output_dir, processor, "test_heartbeat", index=index,
        )
        time.sleep(0.05)
    result_queue.put({"completed": True, "succeeded": True})


class ForwardingLifecycleTests(unittest.TestCase):
    def test_runtime_positive_gate_downgrades_missing_relocation(self):
        result = {
            "status": "detected",
            "present": True,
            "bypass_kind": "alu_to_ex",
            "forwarding_required": True,
            "zero_delay_behavior_observed": True,
            "zero_delay_classification": "confirmed_forwarding",
            "experiments": {
                "adjacent": {
                    "dependent": [{} for _ in range(3)],
                    "control": [{} for _ in range(3)],
                },
            },
            "independent_distance_sweep": {
                "tested_gaps": [1, 2],
                "per_gap": [],
                "corroboration": {"state": "validated"},
            },
        }
        interface = {
            "implementation_revision": 11,
            "stages": [{
                "normalized_role": "frontend",
                "pc_path": "dut.pc",
                "relocation_proven": False,
            }],
            "stage_graph": {
                "nodes": [{"path": "dut.pc"}],
                "accepted_edges": [],
                "canonical_path": ["dut.pc"],
            },
        }
        proof = enforce_forwarding_positive(
            result, interface, 10,
        )
        self.assertFalse(proof["valid"])
        self.assertEqual(result["status"], "inconclusive")
        self.assertIsNone(result["present"])
        self.assertEqual(
            result["zero_delay_classification"],
            "possible_forwarding",
        )
        self.assertIn(
            "pipeline_identity",
            result["requirement_missing_proofs"],
        )

    def test_failed_run_preserves_unrelated_labels_and_replaces_forwarding(self):
        previous = {
            "core": {
                "pipeline": {"depth_estimate": 5},
                "branch_prediction": {"status": "detected"},
                "forwarding": {"alu_to_alu": {"status": "detected", "present": True}},
                "hazard_handling": {"store_to_load": {"status": "handled"}},
            }
        }
        current = {
            "core": {
                "forwarding": {
                    "schema_version": 2,
                    "execution": {"state": "running", "run_id": "active-run"},
                    "applicable": True,
                }
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "core_labels.json"
            path.write_text(json.dumps(current), encoding="utf-8")
            main._mark_analysis_failed(
                path, json.dumps(previous).encode("utf-8"), "core",
                RuntimeError("simulator crashed"),
            )
            labels = json.loads(path.read_text(encoding="utf-8"))["core"]
            pipeline = json.loads(
                (Path(directory) / "core_pipeline_interface.json").read_text(encoding="utf-8")
            )

        self.assertEqual(labels["branch_prediction"]["status"], "detected")
        self.assertEqual(labels["forwarding"]["execution"]["state"], "failed")
        self.assertEqual(labels["forwarding"]["probe_suite_version"], "paired-forwarding-v8")
        self.assertEqual(labels["forwarding"]["implementation_revision"], 11)
        self.assertEqual(labels["forwarding"]["execution"]["run_id"], "active-run")
        self.assertNotIn("alu_to_alu", labels["forwarding"])
        self.assertNotIn("hazard_handling", labels)
        self.assertEqual(pipeline["state"], "failed")
        self.assertEqual(pipeline["schema_version"], 4)
        self.assertEqual(pipeline["discovery_version"], "dynamic-stage-signals-v4")
        self.assertEqual(pipeline["implementation_revision"], 11)

    def test_core_timeout_kills_worker_process_group_and_writes_fresh_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            core_dir = Path(directory) / "core"
            output_dir = Path(directory) / "labels"
            core_dir.mkdir()
            with mock.patch.object(main, "_core_worker", _hanging_core_worker):
                succeeded = main.core_labeler(
                    str(core_dir), str(Path(directory) / "config"),
                    str(output_dir), str(Path(directory) / "rtl"), False,
                    core_timeout=0.1,
                )
            labels = json.loads(
                (output_dir / "core" / "core_labels.json").read_text(
                    encoding="utf-8"
                )
            )["core"]["forwarding"]
            pipeline = json.loads(
                (output_dir / "core" / "core_pipeline_interface.json").read_text(
                    encoding="utf-8"
                )
            )
        self.assertFalse(succeeded)
        self.assertEqual(labels["execution"]["state"], "failed")
        self.assertEqual(labels["execution"]["error_type"], "TimeoutExpired")
        self.assertEqual(labels["execution"]["timeout_seconds"], 0.1)
        self.assertTrue(labels["execution"]["descendants_reaped"])
        self.assertIn(
            labels["execution"]["termination_signal"], {"SIGTERM", "SIGKILL"}
        )
        self.assertEqual(labels["implementation_revision"], 11)
        self.assertEqual(pipeline["implementation_revision"], 11)

    def test_abnormal_worker_exit_writes_fresh_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            core_dir = Path(directory) / "core"
            output_dir = Path(directory) / "labels"
            core_dir.mkdir()
            with mock.patch.object(main, "_core_worker", _aborting_core_worker):
                succeeded = main.core_labeler(
                    str(core_dir), str(Path(directory) / "config"),
                    str(output_dir), str(Path(directory) / "rtl"), False,
                    core_timeout=2,
                )
            labels = json.loads(
                (output_dir / "core" / "core_labels.json").read_text(
                    encoding="utf-8"
                )
            )["core"]["forwarding"]
        self.assertFalse(succeeded)
        self.assertEqual(labels["execution"]["state"], "failed")
        self.assertEqual(labels["execution"]["worker_exit_code"], 7)
        self.assertEqual(labels["implementation_revision"], 11)

    def test_idle_timeout_records_last_progress_and_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            core_dir = Path(directory) / "core"
            output_dir = Path(directory) / "labels"
            core_dir.mkdir()
            with mock.patch.object(
                main, "_core_worker", _hanging_core_worker,
            ):
                succeeded = main.core_labeler(
                    str(core_dir), str(Path(directory) / "config"),
                    str(output_dir), str(Path(directory) / "rtl"), False,
                    core_timeout=2, core_idle_timeout=0.1,
                )
            forwarding = json.loads(
                (
                    output_dir / "core" / "core_labels.json"
                ).read_text(encoding="utf-8")
            )["core"]["forwarding"]
        self.assertFalse(succeeded)
        execution = forwarding["execution"]
        self.assertEqual(execution["timeout_kind"], "idle")
        self.assertEqual(execution["hard_timeout_seconds"], 2)
        self.assertEqual(execution["idle_timeout_seconds"], 0.1)
        self.assertEqual(
            execution["last_progress_marker"]["phase"],
            "worker_start",
        )

    def test_heartbeat_refresh_prevents_idle_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            core_dir = Path(directory) / "core"
            output_dir = Path(directory) / "labels"
            core_dir.mkdir()
            with mock.patch.object(
                main, "_core_worker", _heartbeat_core_worker,
            ):
                succeeded = main.core_labeler(
                    str(core_dir), str(Path(directory) / "config"),
                    str(output_dir), str(Path(directory) / "rtl"), False,
                    core_timeout=2, core_idle_timeout=0.1,
                )
        self.assertTrue(succeeded)

    def test_compact_dropped_store_evidence_survives_debug_free_audit(self):
        dropped = [{
            "architectural_complete": True,
            "dependency_correct": None,
            "store_absence_architecturally_observable": True,
            "transaction_observable": False,
        } for _ in range(3)]
        control = [{
            "architectural_complete": True,
            "dependency_correct": True,
            "store_absence_architecturally_observable": False,
            "transaction_observable": True,
        } for _ in range(3)]
        labels = {
            "forwarding": {
                "load_to_store_data": {
                    "experiments": {"adjacent": {"dependent": dropped, "control": control}}
                }
            }
        }
        valid, reason = audit_forwarding_results.validated_store_failure(
            labels, "load_to_store_data"
        )
        self.assertTrue(valid)
        self.assertIn("stably absent", reason)

    def test_audit_downgrades_positive_without_revision7_proof(self):
        trial = {
            "architectural_complete": True,
            "dependency_correct": True,
            "latency": 5,
        }
        document = {
            "core": {
                "forwarding": {
                    "schema_version": 2,
                    "probe_suite_version": "paired-forwarding-v8",
                    "implementation_revision": 11,
                    "execution": {"state": "completed"},
                    "alu_to_alu": {
                        "status": "detected",
                        "present": True,
                        "bypass_kind": "alu_to_ex",
                        "forwarding_required": True,
                        "zero_delay_behavior_observed": True,
                        "zero_delay_classification": "confirmed_forwarding",
                        "experiments": {
                            "adjacent": {
                                "dependent": [dict(trial) for _ in range(3)],
                                "control": [dict(trial) for _ in range(3)],
                            },
                        },
                    },
                },
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "core_labels.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            (Path(directory) / "core_pipeline_interface.json").write_text(
                json.dumps({
                    "implementation_revision": 11,
                    "stages": [],
                    "stage_graph": {
                        "nodes": [], "accepted_edges": [],
                        "canonical_path": [],
                    },
                }),
                encoding="utf-8",
            )
            reports, changed = audit_forwarding_results.audit_file(
                path, apply=True,
            )
            saved = json.loads(path.read_text(encoding="utf-8"))
        result = saved["core"]["forwarding"]["alu_to_alu"]
        self.assertTrue(changed)
        self.assertFalse(reports[0][2])
        self.assertEqual(result["status"], "inconclusive")
        self.assertIsNone(result["present"])
        self.assertIsNone(result["bypass_kind"])
        self.assertEqual(
            result["zero_delay_classification"],
            "possible_forwarding",
        )

    def test_audit_keeps_revision11_fixed_chain_corroboration(self):
        trial = {
            "architectural_complete": True,
            "dependency_correct": True,
            "latency": 5,
            "consumer_token_proof": True,
            "source_selector_validation": True,
            "operand_differential_validation": True,
            "semantic_discriminators_passed": True,
            "stage_pc_path": "dut.ex_pc",
            "source_id_path": "dut.rs1",
            "operand_path": "dut.operand_a",
            "source_id_packed_slice": None,
            "operand_packed_slice": None,
            "consumer_requirement_event": {"phase": "post_edge"},
            "source_selector_lag": 0,
            "residence_relative_position": 0,
            "stage_token": {
                "path": "dut.ex_pc",
                "cycle": 4,
                "residence_entry_cycle": 4,
                "residence_exit_cycle": 4,
            },
            "lane_id": 0,
        }
        gaps = [{
            "gap": gap,
            "exact_proof_complete": True,
            "experiments": {
                "dependent": [
                    dict(trial, forwarding_gap=gap) for _ in range(3)
                ],
                "control": [
                    dict(trial, forwarding_gap=gap) for _ in range(3)
                ],
            },
        } for gap in (1, 2)]
        document = {
            "core": {
                "forwarding": {
                    "schema_version": 2,
                    "probe_suite_version": "paired-forwarding-v8",
                    "implementation_revision": 11,
                    "execution": {"state": "completed"},
                    "alu_to_alu": {
                        "status": "detected",
                        "present": True,
                        "forwarding_required": True,
                        "zero_delay_behavior_observed": True,
                        "experiments": {
                            "adjacent": {
                                "dependent": [
                                    dict(trial) for _ in range(3)
                                ],
                                "control": [
                                    dict(trial) for _ in range(3)
                                ],
                            },
                        },
                        "independent_distance_sweep": {
                            "tested_gaps": [1, 2],
                            "per_gap": gaps,
                            "corroboration": {"state": "validated"},
                        },
                    },
                },
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "core_labels.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            (Path(directory) / "core_pipeline_interface.json").write_text(
                json.dumps({
                    "implementation_revision": 11,
                    "calibration_base_selection": {
                        "state": "complete",
                        "selected_bases": [0x40, 0x98, 0x184],
                        "relocation_roles_permitted": True,
                    },
                    "stages": [{
                        "normalized_role": "execute",
                        "pc_path": "dut.ex_pc",
                        "relocation_proven": True,
                        "address_transform": {
                            "mode": "byte",
                            "bias": 0,
                            "width": 32,
                            "distinct_base_count": 3,
                            "delta_checks": 3,
                            "delta_matches": 3,
                            "rejection_reason": None,
                        },
                    }],
                    "stage_graph": {
                        "nodes": [{"path": "dut.ex_pc"}],
                        "accepted_edges": [],
                        "canonical_path": ["dut.ex_pc"],
                    },
                }),
                encoding="utf-8",
            )
            reports, changed = audit_forwarding_results.audit_file(
                path, apply=True,
            )
        self.assertFalse(changed)
        self.assertTrue(reports[0][2])


if __name__ == "__main__":
    unittest.main()
