import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from src.pipeline_interface_finder import (
    PIPELINE_INTERFACE_DISCOVERY_VERSION,
    PipelineSignalObserver,
    _behavioral_candidate_roles,
    _behaviorally_equivalent_stage_stream,
    _build_stage_graph,
    _candidate_pool,
    _candidate_role,
    _candidate_side,
    _compose_stage_candidates,
    _fit_affine_stage_events,
    _limit_packed_parent_candidates,
    _limit_virtual_candidates_for_use,
    _program_offset,
    _source_id_candidate_incompatible,
    _stage_candidate_identity,
    _validate_source_selector_candidate,
    _validate_data_candidate,
    _validate_controls,
    classify_pipeline_interface,
    compact_pipeline_interface,
    consumer_stage_cycle,
    validate_frozen_forwarding_trials,
    write_pipeline_interface,
)
from src.forwarding_proof import validate_pipeline_identity


def synthetic_trials(stage_count=5, trial_count=4, enhanced=True):
    if stage_count == 2:
        paths = ["dut.pipe.if_pc", "dut.pipe.ex_mem_pc"]
    else:
        names = ["if_pc", "id_pc", "ex_pc", "mem_pc", "wb_pc"]
        paths = [f"dut.pipe.{name}" for name in names[:stage_count]]
    trials = []
    for trial_index in range(trial_count):
        fetch = [
            {"cycle": 1, "offset": 12, "transaction_id": f"{trial_index}:p", "epoch_id": 0},
            {"cycle": 2, "offset": 16, "transaction_id": f"{trial_index}:c", "epoch_id": 0},
        ]
        events = []
        for stage in range(stage_count):
            for offset, fetch_cycle in ((12, 1), (16, 2)):
                event = {
                    "cycle": fetch_cycle + stage,
                    "path": paths[stage],
                    "offset": offset,
                    "value": offset,
                }
                if enhanced:
                    event.update({
                        "instruction_path": f"dut.pipe.insn_{stage}",
                        "instruction_matches": True,
                        "valid_path": f"dut.pipe.valid_{stage}",
                        "valid_value": 1,
                    })
                events.append(event)
        trials.append({
            "trial_id": str(trial_index),
            "program": f"alu_to_store_data_dependent_{trial_index}",
            "producer_offset": 12,
            "consumer_offset": 16,
            "events": events,
            "fetch_events": fetch,
            "commits": [
                {"cycle": 1 + stage_count, "offset": 12},
                {"cycle": 2 + stage_count, "offset": 16},
            ],
            "transactions": [{
                "cycle": 2 + (stage_count - 1 if stage_count == 2 else stage_count - 2),
                "offset": 16,
                "kind": "store",
                "epoch_id": trial_index + 1,
                "transaction_id": f"data:{trial_index + 1}:0",
            }],
        })
    return trials


class PipelineInterfaceFinderTests(unittest.TestCase):
    @staticmethod
    def _affine_trials(bases, bias, width=16, word=False):
        modulus = 1 << width
        trials = []
        for index, base in enumerate(bases):
            fetches = []
            samples = []
            for fetch_index, offset in enumerate((0, 4, 12)):
                canonical = base + offset
                cycle = 2 + fetch_index
                fetches.append({
                    "cycle": cycle,
                    "offset": offset,
                    "canonical_pc": canonical,
                    "base_pc": base,
                    "transaction_id": f"{index}:{fetch_index}",
                    "epoch_id": index,
                    "transaction_slot": 0,
                })
                scaled = canonical >> 2 if word else canonical
                samples.append({
                    "cycle": cycle + 1,
                    "path": "dut.pipe.pc",
                    "value": (scaled + bias) % modulus,
                    "width": width,
                })
            trials.append({
                "trial_id": str(index),
                "program": f"pipeline_calibration_flow_{index}",
                "calibration_relocation_base": base,
                "calibration_relocation_origin": 0,
                "relocation_roles_permitted": True,
                "fetch_events": fetches,
                "raw_stage_samples": samples,
                "instruction_by_offset": {},
                "commits": [],
                "transactions": [],
            })
        return trials

    def test_affine_pc_fit_uses_one_bias_across_noncongruent_bases(self):
        trials = self._affine_trials(
            (0x40, 0x98, 0x184), 0x31,
        )
        transform, events = _fit_affine_stage_events(
            "dut.pipe.pc", trials, "byte", width=16,
        )
        self.assertEqual(transform["mode"], "byte")
        self.assertEqual(transform["bias"], 0x31)
        self.assertEqual(len(events), 3)
        self.assertTrue(all(len(items) == 3 for items in events.values()))

    def test_word_affine_fit_supports_negative_modular_bias(self):
        trials = self._affine_trials(
            (0x40, 0x98, 0x184), -7, width=12, word=True,
        )
        transform, _ = _fit_affine_stage_events(
            "dut.pipe.pc", trials, "word", width=12,
        )
        self.assertEqual(transform["bias"], (1 << 12) - 7)

    def test_affine_residence_rejects_ambiguous_replayed_pc(self):
        trial = self._affine_trials((0x40,), 0)[0]
        for sample in trial["raw_stage_samples"]:
            sample["cycle"] += 1
        replay = dict(trial["fetch_events"][0])
        replay.update({
            "cycle": replay["cycle"] + 2,
            "transaction_id": "replay",
        })
        trial["fetch_events"].insert(1, replay)
        trial["raw_stage_samples"].append({
            "cycle": replay["cycle"] + 1,
            "path": "dut.pipe.pc",
            "value": replay["canonical_pc"],
            "width": 16,
        })
        transform, events = _fit_affine_stage_events(
            "dut.pipe.pc", [trial], "byte", width=16,
        )
        self.assertGreater(transform["residence_ambiguity_count"], 0)
        self.assertEqual(sum(
            item["offset"] == replay["offset"]
            for item in events[trial["trial_id"]]
        ), 1)

    def test_bad_instruction_companion_does_not_reject_affine_pc(self):
        bases = (0x40, 0x98, 0x184)
        trials = self._affine_trials(bases, 9)
        paired = {}
        for trial in trials:
            trial["control_flow"] = {
                "redirect_offset": 0,
                "wrong_path_offsets": (4,),
                "target_offset": 12,
            }
            paired[trial["trial_id"]] = [{
                "cycle": fetch["cycle"] + 1,
                "offset": fetch["offset"],
                "value": fetch["canonical_pc"] + 9,
                "fetch_canonical_pc": fetch["canonical_pc"],
                "fetch_base_pc": fetch["base_pc"],
                "fetch_cycle": fetch["cycle"],
                "transaction_id": fetch["transaction_id"],
                "epoch_id": fetch["epoch_id"],
                "transaction_slot": 0,
                "lag": 1,
                "instruction_path": "dut.pipe.bad_instruction",
                "instruction_matches": False,
            } for fetch in (
                trial["fetch_events"][0], trial["fetch_events"][2],
            )]
        identity = _stage_candidate_identity({
            "path": "dut.pipe.pc",
            "signal_kind": "pc",
            "address_mode": "byte",
            "address_transform": {
                "mode": "byte", "scale": "1",
                "bias": 9, "width": 16,
            },
            "median_fetch_offset_cycles": 1,
            "paired_by_trial": paired,
            "lane_id": None,
        }, {trial["trial_id"]: trial for trial in trials})
        self.assertTrue(identity["relocation_proven"])
        self.assertIsNone(identity["primary_rejection_reason"])
        self.assertGreater(
            identity["rejection_counts"]["instruction_companion"], 0,
        )

    def test_incomplete_landing_selection_blocks_pc_proof_gate(self):
        interface = {
            "implementation_revision": 11,
            "calibration_base_selection": {
                "state": "incomplete",
                "selected_bases": [0x40, 0x98],
                "relocation_roles_permitted": False,
            },
            "stages": [{
                "normalized_role": "frontend",
                "pc_path": "dut.pipe.pc",
                "relocation_proven": True,
                "address_transform": {
                    "mode": "byte", "bias": 0, "width": 32,
                    "distinct_base_count": 3,
                    "delta_checks": 3, "delta_matches": 3,
                    "rejection_reason": None,
                },
            }],
            "stage_graph": {
                "canonical_path": [], "accepted_edges": [],
            },
        }
        valid, reason = validate_pipeline_identity(interface, 11)
        self.assertFalse(valid)
        self.assertIn("three completed", reason)

    def test_observer_limits_full_classification_and_slices_new_trials(self):
        observer = PipelineSignalObserver.__new__(PipelineSignalObserver)
        observer._trials = [
            {"trial_id": "old"},
            {"trial_id": "new"},
        ]
        observer.discovery = {"candidates": {}}
        observer.discovery_error = None
        observer.pipeline_depth = 4
        observer.full_finalization_count = 0
        observer.discarded_raw_trial_count = 0
        cursor = 1
        with mock.patch(
            "src.pipeline_interface_finder.classify_pipeline_interface",
            return_value={"state": "partial"},
        ) as classify:
            observer.finalize()
            observer.finalize()
            with self.assertRaisesRegex(RuntimeError, "at most two"):
                observer.finalize()
        self.assertEqual(classify.call_count, 2)
        self.assertEqual(
            [item["trial_id"] for item in observer.trials_since(cursor)],
            ["new"],
        )
        self.assertEqual(observer.discard_trials_since(cursor), 1)
        self.assertEqual(observer.discarded_raw_trial_count, 1)
        self.assertEqual(
            [item["trial_id"] for item in observer._trials], ["old"],
        )

    def test_incremental_group_validates_only_the_frozen_chain(self):
        interface = {
            "role_evidence": {
                "execute": {
                    "state": "confirmed",
                    "side": "rs1",
                    "independent_corroboration": {
                        "fixed_stage_path": "dut.ex_pc",
                        "fixed_source_id_path": "dut.rs1",
                        "fixed_operand_path": "dut.operand_a",
                        "fixed_packed_slice": None,
                        "fixed_source_id_packed_slice": None,
                        "fixed_phase": "pre_edge",
                        "fixed_source_id_phase": "pre_edge",
                        "fixed_source_selector_lag": 0,
                        "fixed_lane_id": None,
                        "tested_gaps": [],
                        "trial_groups": [],
                    },
                }
            },
            "requirement_observations": {},
            "producer_availability_observations": {},
            "selected_writeback_paths": None,
        }
        producer = {
            "offset": 0, "role": "producer",
            "destination_register": 5, "result_value": 0x12345678,
        }
        consumer = {
            "offset": 2, "role": "consumer",
            "rs1_register": 5, "rs1_value": 0x12345678,
            "rs1_use": "execute", "rs2_register": 7,
            "rs2_value": 0x22222222, "rs2_use": "execute",
            "result_value": 0x3456789A,
            "immediate_value": 0x77,
            "forbidden_operand_values": [0x22222222, 0x77],
        }
        trial = {
            "trial_id": "gap1-dependent-0",
            "program": "alu_to_alu_dependent_gap_1_variant_0",
            "pair_role": "dependent", "variant": 0,
            "spacer_kind": "independent", "forwarding_gap": 1,
            "operand_expectations": [producer, consumer],
            "fetch_events": [{
                "cycle": 2, "offset": 2, "epoch_id": 4,
                "transaction_id": "fetch-2", "transaction_slot": 0,
            }],
            "events": [{
                "cycle": 3, "offset": 2, "path": "dut.ex_pc",
                "instruction_matches": True,
            }],
            "signal_samples": [
                {
                    "cycle": 3, "phase": "pre_edge",
                    "path": "dut.rs1", "value": 5,
                },
                {
                    "cycle": 3, "phase": "pre_edge",
                    "path": "dut.operand_a", "value": 0x12345678,
                },
            ],
            "architectural_samples": [
                {
                    "cycle": 2, "phase": "pre_edge",
                    "register": 5, "value": 0,
                },
                {
                    "cycle": 5, "phase": "post_edge",
                    "register": 5, "value": 0x12345678,
                },
            ],
            "writeback_samples": [],
            "commits": [{"cycle": 5, "offset": 0}],
            "transactions": [],
            "instruction_by_offset": {2: 0x00B50533},
        }
        diagnostics = validate_frozen_forwarding_trials(
            interface, [trial], pipeline_depth=4,
        )
        event = interface["requirement_observations"][
            trial["trial_id"]
        ]["execute"]
        self.assertEqual(event["path"], "dut.operand_a")
        self.assertTrue(event["consumer_token_proof"])
        self.assertEqual(event["source_selector_lag"], 0)
        self.assertEqual(diagnostics[0]["matched_trials"], 1)
        self.assertEqual(
            interface["producer_availability_observations"][
                trial["trial_id"]
            ]["cycle"],
            5,
        )

        rejected = dict(trial)
        rejected["trial_id"] = "gap1-dependent-1"
        rejected["variant"] = 1
        rejected["signal_samples"] = [
            sample for sample in trial["signal_samples"]
            if sample["path"] != "dut.operand_a"
        ]
        validate_frozen_forwarding_trials(
            interface, [rejected], pipeline_depth=4,
        )
        self.assertNotIn(
            rejected["trial_id"], interface["requirement_observations"],
        )
        self.assertEqual(
            interface["role_evidence"]["execute"]["state"], "confirmed",
        )
        self.assertIn(
            "operand_capture",
            {
                mismatch
                for item in interface["near_miss_diagnostics"]
                for mismatch in item["mismatches"]
            },
        )

    def test_frozen_chain_failure_preserves_upstream_stage_rejection(self):
        interface = {
            "role_evidence": {
                "execute": {
                    "state": "unavailable",
                    "side": "rs1",
                    "rejection_reason": (
                        "no dynamically validated execute token stream"
                    ),
                    "independent_corroboration": {},
                },
            },
            "stage_candidate_diagnostics": [{
                "path": "dut.debug_EX_PC",
                "state": "rejected",
                "primary_rejection_reason": "redirect",
                "eligible_epoch_count": 42,
                "exact_matched_epoch_count": 30,
                "rejection_counts": {
                    "redirect": 3, "relocation": 0,
                },
            }],
            "source_id_linkage_diagnostics": [],
            "requirement_observations": {},
            "producer_availability_observations": {},
            "selected_writeback_paths": None,
        }
        trial = {
            "trial_id": "gap1-dependent-0",
            "program": "alu_to_alu_dependent_gap_1_variant_0",
            "pair_role": "dependent",
            "variant": 0,
            "spacer_kind": "independent",
            "forwarding_gap": 1,
            "operand_expectations": [{
                "offset": 0, "role": "producer",
                "destination_register": 5, "result_value": 0x123,
            }, {
                "offset": 8, "role": "consumer",
                "rs1_register": 5, "rs1_value": 0x123,
                "rs1_use": "execute",
            }],
            "fetch_events": [],
            "events": [],
            "signal_samples": [],
            "architectural_samples": [],
            "writeback_samples": [],
            "commits": [],
            "transactions": [],
        }
        validate_frozen_forwarding_trials(
            interface, [trial], pipeline_depth=4,
        )
        failure = interface["exact_capture_failures"][0]
        self.assertEqual(
            failure["mismatch"], "frozen_chain_unavailable",
        )
        self.assertIn(
            "stage_redirect", failure["failure_categories"],
        )
        self.assertEqual(
            failure["root_cause"]["stage_candidate"]["path"],
            "dut.debug_EX_PC",
        )

    def test_independent_filler_writeback_is_forbidden_operand_evidence(self):
        trials = []
        observations = {}
        for variant in range(3):
            trial_id = str(variant)
            expected = 0x220 + variant
            filler = 0x520 + variant
            observation = {
                "offset": 20,
                "role": "consumer",
                "rs1_register": 1 + variant,
                "rs1_value": expected,
                "rs1_use": "execute",
                "forbidden_operand_values": (filler,),
            }
            observations[trial_id] = [(observation, 5)]
            trials.append({
                "trial_id": trial_id,
                "program": (
                    f"alu_to_alu_dependent_gap_1_independent_{variant}"
                ),
                "pair_role": "dependent",
                "variant": variant,
                "forwarding_gap": 1,
                "spacer_kind": "independent",
                "instructions": {"16": 0x50000013 + variant},
                "signal_samples": [{
                    "cycle": 5,
                    "phase": "pre_edge",
                    "phase_order": 0,
                    "path": "dut.operand_candidate",
                    "value": filler,
                }],
            })
        score = _validate_data_candidate(
            "dut.operand_candidate", trials, observations,
            "rs1_value",
        )
        self.assertFalse(score["confirmed"])
        self.assertEqual(score["semantic_collision_captures"], 3)
        self.assertIn(
            "forbidden semantic discriminator",
            score["rejection_reason"],
        )

    def test_revision6_source_selector_requires_paired_control_change(self):
        trials = []
        observations = {}
        for variant, (dependent_id, control_id) in enumerate(
            ((1, 2), (4, 5), (7, 8))
        ):
            for role, expected in (
                ("dependent", dependent_id),
                ("control", control_id),
            ):
                trial_id = f"{variant}:{role}"
                observation = {
                    "offset": 16, "role": "consumer",
                    "rs1_register": expected, "rs1_use": "execute",
                    "destination_register": dependent_id + 2,
                    "non_source_registers": (
                        control_id if role == "dependent"
                        else dependent_id,
                        dependent_id + 2,
                    ),
                    "immediate_value": 32 + variant,
                    "result_value": 0x300 + variant,
                    "poison_value": 0x500 + variant,
                }
                observations[trial_id] = [(observation, 5)]
                trials.append({
                    "trial_id": trial_id,
                    "program": f"alu_to_alu_{role}_gap_0",
                    "pair_role": role,
                    "variant": variant,
                    "signal_samples": [{
                        "cycle": 5, "phase": "post_edge",
                        "phase_order": 1, "path": "dut.ex_rs1",
                        "value": expected,
                    }],
                })
        score = _validate_source_selector_candidate(
            {"path": "dut.ex_rs1"}, trials, observations,
            "rs1", "execute",
        )
        self.assertTrue(score["confirmed"])
        self.assertEqual(score["paired_variants"], 3)
        self.assertEqual(score["distinct_dependent_source_ids"], 3)
        self.assertEqual(score["distinct_control_source_ids"], 3)

        for trial in trials:
            trial["signal_samples"][0]["value"] = (
                1 if trial["variant"] == 0
                else 4 if trial["variant"] == 1 else 7
            )
        destination = _validate_source_selector_candidate(
            {"path": "dut.wb_rd"}, trials, observations,
            "rs1", "execute",
        )
        self.assertFalse(destination["confirmed"])
        self.assertEqual(
            destination["rejection_category"],
            "dependent_control_selector_mismatch",
        )

    def test_source_selector_ignores_unrelated_dependency_families(self):
        trials = []
        observations = {}
        for variant in range(3):
            for family, use, dependent_id, control_id in (
                ("alu_to_store_data", "store_data",
                 3 + variant, 9 + variant),
                # Store-address probes keep rs2 identical by design and must
                # not dilute store-data selector validation.
                ("alu_to_store_address", "store_address",
                 12 + variant, 12 + variant),
            ):
                for role, expected in (
                    ("dependent", dependent_id),
                    ("control", control_id),
                ):
                    trial_id = f"{family}:{variant}:{role}"
                    observations[trial_id] = [({
                        "offset": 16, "role": "consumer",
                        "rs2_register": expected,
                        "rs2_use": "store_data",
                    }, 5)]
                    trials.append({
                        "trial_id": trial_id,
                        "program": f"{family}_{role}_gap_0",
                        "pair_role": role,
                        "variant": variant,
                        "signal_samples": [{
                            "cycle": 5, "phase": "pre_edge",
                            "phase_order": 0, "path": "dut.mem_rs2",
                            "value": expected,
                        }],
                    })
        score = _validate_source_selector_candidate(
            {"path": "dut.mem_rs2"}, trials, observations,
            "rs2", "store_data",
        )
        self.assertTrue(score["confirmed"])
        self.assertEqual(score["matching_trial_count"], 6)
        self.assertEqual(
            {item["probe"] for item in score["required_trial_groups"]},
            {"alu_to_store_data"},
        )

    def test_focused_reserve_is_single_pass_and_twice_budget_bounded(self):
        observer = PipelineSignalObserver.__new__(PipelineSignalObserver)
        observer._focused_rescan_ran = False
        observer.discovery = {
            "candidates": {
                "source_id": [
                    {"path": f"dut.selected_{index}"}
                    for index in range(48)
                ],
                "packed_parent": [],
            },
        }
        observer._census_reserve = {
            "source_id": [
                {"path": f"dut.reserve_{index}"}
                for index in range(80)
            ],
            "packed_parent": [],
        }
        report = observer.promote_focused_reserve({
            "alu_to_alu": {"source_id"},
        })
        self.assertTrue(report["ran"])
        self.assertEqual(report["promoted_counts"]["source_id"], 48)
        self.assertEqual(
            len(observer.discovery["candidates"]["source_id"]), 96,
        )
        self.assertTrue(report["truncated"])
        second = observer.promote_focused_reserve({
            "load_to_alu": {"operand_capture"},
        })
        self.assertFalse(second["ran"])

    def test_stage_stream_alias_allows_only_irrelevant_extra_token(self):
        common = [{
            "fetch_token": f"0:{index}:0:0",
            "offset": 4 * index,
            "cycle": 10 + index,
        } for index in range(4)]
        left = {
            "lane_id": None,
            "signal_kind": "pc",
            "median_fetch_offset_cycles": 2,
            "paired_by_trial": {"0": common},
        }
        right = {
            **left,
            "paired_by_trial": {
                "0": [
                    *common,
                    {
                        "fetch_token": "0:terminal:0:0",
                        "offset": 20,
                        "cycle": 15,
                    },
                ],
            },
        }
        self.assertFalse(
            _behaviorally_equivalent_stage_stream(left, right),
        )
        right["paired_by_trial"]["0"] = [
            *common,
            # With hundreds of real tokens, one reset/loop artifact is below
            # the 2% tolerance. A compact fixture uses exact equivalence.
        ]
        self.assertTrue(
            _behaviorally_equivalent_stage_stream(left, right),
        )

    def test_stage_alias_tolerates_rare_one_cycle_boundary_difference(self):
        common = [{
            "fetch_token": f"0:{index}:0:0",
            "offset": 4 * index,
            "cycle": 10 + index,
        } for index in range(100)]
        shifted = [dict(item) for item in common]
        shifted[17]["cycle"] += 1
        left = {
            "lane_id": None,
            "signal_kind": "pc",
            "median_fetch_offset_cycles": 2,
            "paired_by_trial": {"0": common},
        }
        right = {
            **left,
            "paired_by_trial": {"0": shifted},
        }
        self.assertTrue(
            _behaviorally_equivalent_stage_stream(left, right),
        )
        shifted[18]["cycle"] += 2
        self.assertFalse(
            _behaviorally_equivalent_stage_stream(left, right),
        )

    def test_operand_a_b_names_preserve_source_side(self):
        self.assertEqual(_candidate_side("dut.alu_operand_a_ex"), "rs1")
        self.assertEqual(_candidate_side("dut.alu_operand_b_ex"), "rs2")

    def test_destination_id_cannot_be_selected_as_source_id(self):
        reason = _source_id_candidate_incompatible(
            {"path": "dut.regfile_alu_waddr_id_i"},
            "store_data",
        )
        self.assertIn("destination", reason)

    def test_abbreviated_immediate_cannot_be_selected_as_source_id(self):
        reason = _source_id_candidate_incompatible(
            {"path": "dut.csr.csr_imm_i"},
            "execute",
        )
        self.assertIn("instruction field", reason)

    def test_program_offset_miss_always_returns_a_pair(self):
        spec = type(
            "Spec", (), {
                "instructions": {0: 0x13, 4: 0x93},
                "base_addresses": (0x40,),
            },
        )()
        self.assertEqual(_program_offset(None, spec), (None, None))
        self.assertEqual(_program_offset(0xDEADBEEF, spec), (None, None))

    def test_anonymous_widths_enter_behavioral_census(self):
        self.assertIn(
            "instruction", _behavioral_candidate_roles("dut.q17", 32)
        )
        self.assertIn("operand", _behavioral_candidate_roles("dut.q17", 32))
        self.assertIn("source_id", _behavioral_candidate_roles("dut.z9", 5))
        self.assertEqual(
            _behavioral_candidate_roles("dut.probe_fetch_pc", 32), ()
        )

    def test_census_promotes_anonymous_behavior_and_bounds_name_fallback(self):
        observer = PipelineSignalObserver.__new__(PipelineSignalObserver)
        observer._trials = []
        observer.discovery_phase = "census"
        observer.discovery = {
            "search_truncated": False,
            "truncation_reasons": [],
            "candidates": {
                "operand": [
                    {
                        "path": "dut.q17", "static_rank": 1,
                        "name_seed": False,
                    },
                    {
                        "path": "dut.named_operand", "static_rank": 100,
                        "name_seed": True,
                    },
                ],
            },
        }
        for index, value in enumerate((0x111, 0x222, 0x333)):
            observer._trials.append({
                "trial_id": str(index),
                "program": f"pipeline_calibration_flow_{index}",
                "events": [],
                "signal_samples": [{
                    "path": "dut.q17", "value": value,
                    "candidate_role": "operand",
                }],
            })
        summary = observer.finalize_census()
        retained = observer.discovery["candidates"]["operand"]
        self.assertEqual(retained[0]["path"], "dut.q17")
        self.assertTrue(retained[0]["census_behavioral_match"])
        self.assertEqual(summary["candidate_counts_before"]["operand"], 2)

    def test_stage_graph_uses_shared_dynamic_tokens_not_names(self):
        fingerprint = tuple(
            (str(trial), f"token-{offset}", trial + offset)
            for trial in range(3) for offset in (1, 2)
        )
        later = tuple(
            (trial, token, cycle + 2)
            for trial, token, cycle in fingerprint
        )
        graph = _build_stage_graph([
            {
                "path": "dut.q1", "signal_kind": "instruction",
                "lane_id": None, "median_fetch_offset_cycles": 1,
                "coverage": 1.0, "event_fingerprint": fingerprint,
                "memory_alignment_error": None,
                "commit_alignment_error": None,
            },
            {
                "path": "dut.q2", "signal_kind": "instruction",
                "lane_id": None, "median_fetch_offset_cycles": 3,
                "coverage": 1.0, "event_fingerprint": later,
                "memory_alignment_error": 1,
                "commit_alignment_error": 2,
            },
        ])
        self.assertEqual(len(graph["accepted_edges"]), 1)
        self.assertEqual(graph["accepted_edges"][0]["from"], "dut.q1")

    def test_stage_graph_keeps_ordered_edge_with_variable_backpressure(self):
        earlier = (
            ("a", "token-1", 4),
            ("a", "token-2", 5),
            ("b", "token-1", 8),
        )
        later = (
            ("a", "token-1", 5),
            ("a", "token-2", 9),
            ("b", "token-1", 10),
        )
        graph = _build_stage_graph([
            {
                "path": "dut.fetch_pc", "signal_kind": "pc",
                "lane_id": None, "median_fetch_offset_cycles": 1,
                "coverage": 1.0, "event_fingerprint": earlier,
                "memory_alignment_error": None,
                "commit_alignment_error": None,
            },
            {
                "path": "dut.execute_pc", "signal_kind": "pc",
                "lane_id": None, "median_fetch_offset_cycles": 2,
                "coverage": 1.0, "event_fingerprint": later,
                "memory_alignment_error": 1,
                "commit_alignment_error": 1,
            },
        ])
        self.assertEqual(len(graph["accepted_edges"]), 1)
        self.assertEqual(graph["accepted_edges"][0]["cycle_delta_span"], 3)

    def test_unavailable_stage_emits_role_local_rejection_detail(self):
        result = classify_pipeline_interface([{
            "trial_id": "0", "program": "alu_to_alu_dependent_gap_0",
            "events": [], "signal_samples": [], "fetch_events": [],
            "commits": [], "transactions": [],
        }], discovery={
            "candidates": {"pc": [{"path": "dut.hidden_pc"}]},
            "search_truncated": False, "visited_scopes": 1,
        })
        reason = result["role_evidence"]["execute"]["rejection_reason"]
        self.assertIn("role-local execute proof unavailable", reason)
        self.assertIn("transaction-scoped token matches", reason)

    def test_sectioned_calibration_without_relocation_stays_diagnostic(self):
        trials = synthetic_trials(trial_count=3)
        for index, trial in enumerate(trials):
            trial["program"] = f"pipeline_calibration_flow_{index}"
            memory_state = "failed" if index == 2 else "completed"
            trial["calibration_signature"] = {
                "state": "failed" if index == 2 else "completed",
                "variant": index,
                "sections": {
                    "straight_line": {
                        "state": "completed",
                        "registers": [
                            {"offset": 12, "state": "matched"},
                            {"offset": 16, "state": "matched"},
                        ],
                    },
                    "memory": {
                        "state": memory_state,
                        "registers": [],
                        "failures": (
                            [{"kind": "memory", "state": "mismatched"}]
                            if memory_state == "failed" else []
                        ),
                    },
                    "redirect": {
                        "state": "completed", "registers": [],
                    },
                },
            }
        result = classify_pipeline_interface(trials)
        self.assertEqual(result["calibration"]["state"], "partial")
        self.assertEqual(
            result["calibration"]["sections"]["straight_line"]["state"],
            "completed",
        )
        self.assertEqual(
            result["calibration"]["sections"]["memory"]["state"], "partial",
        )
        self.assertFalse(result["stages"])
        self.assertTrue(result["stage_candidate_diagnostics"])
        self.assertTrue(all(
            item["state"] == "rejected"
            for item in result["stage_candidate_diagnostics"]
        ))

    def test_stage_pc_requires_exact_relocation_and_redirect_identity(self):
        trials = synthetic_trials(stage_count=2, trial_count=3)
        bases = (0x40, 0x44, 0x78)
        for index, (trial, base_pc) in enumerate(
            zip(trials, bases)
        ):
            trial["program"] = f"pipeline_calibration_flow_{index}"
            trial["base_addresses"] = [base_pc]
            trial["calibration_variant"] = index
            trial["control_flow"] = {
                "redirect_offset": 12,
                "target_offset": 16,
                "wrong_path_offsets": (20,),
            }
            trial["calibration_signature"] = {
                "state": "completed",
                "variant": index,
                "sections": {
                    "straight_line": {
                        "state": "completed",
                        "registers": [{"offset": 12}],
                    },
                    "memory": {
                        "state": "completed", "registers": [],
                    },
                    "redirect": {
                        "state": "completed",
                        "registers": [{"offset": 16}],
                    },
                },
            }
            for fetch in trial["fetch_events"]:
                fetch.update({
                    "pc": base_pc + fetch["offset"],
                    "raw_pc": base_pc + fetch["offset"],
                    "canonical_pc": base_pc + fetch["offset"],
                    "base_pc": base_pc,
                    "transaction_slot": 0,
                })
            genuine = []
            counters = []
            for event in trial["events"]:
                event["value"] = base_pc + event["offset"]
                genuine.append(event)
                counters.append({
                    **event,
                    "path": "dut.pipe.order_index",
                    "value": 0x100 + event["offset"],
                    "instruction_path": None,
                })
            trial["events"] = [*genuine, *counters]
        result = classify_pipeline_interface(trials)
        self.assertTrue(result["stages"])
        self.assertTrue(all(
            stage.get("relocation_proven") is True
            for stage in result["stages"]
        ))
        self.assertFalse(any(
            stage.get("pc_path") == "dut.pipe.order_index"
            for stage in result["stages"]
        ))
        rejected = next(
            item for item in result["stage_candidate_diagnostics"]
            if item["path"] == "dut.pipe.order_index"
        )
        self.assertEqual(rejected["state"], "rejected")
        self.assertGreater(
            rejected["rejection_counts"]["relocation"], 0,
        )
        accepted = next(
            item for item in result["stage_candidate_diagnostics"]
            if item["state"] == "accepted"
        )
        self.assertEqual(accepted["executed_bases"], list(bases))
        self.assertEqual(accepted["redirect_matches"], 3)

    def test_downstream_stage_redirect_is_relative_to_fetch_progression(self):
        trials = synthetic_trials(stage_count=2, trial_count=3)
        bases = (0x80, 0xC0, 0x100)
        paired = {}
        for index, (trial, base) in enumerate(zip(trials, bases)):
            trial_id = trial["trial_id"]
            trial["program"] = f"pipeline_calibration_flow_{index}"
            trial["calibration_relocation_base"] = base
            trial["calibration_relocation_origin"] = 0
            trial["control_flow"] = {
                "redirect_offset": 12,
                "target_offset": 16,
                "wrong_path_offsets": (20,),
            }
            for fetch in trial["fetch_events"]:
                fetch.update({
                    "pc": base + fetch["offset"],
                    "raw_pc": base + fetch["offset"],
                    "canonical_pc": base + fetch["offset"],
                    "base_pc": base,
                })
            # The downstream stage observes the taken target, but the
            # redirecting instruction itself is flushed before reaching it.
            paired[trial_id] = [{
                "cycle": 4,
                "offset": 16,
                "value": base + 16,
                "fetch_canonical_pc": base + 16,
                "fetch_base_pc": base,
                "fetch_cycle": 2,
                "transaction_id": f"{index}:c",
                "epoch_id": 0,
                "transaction_slot": 0,
                "lag": 2,
            }, {
                "cycle": 5,
                "offset": 24,
                "value": base + 24,
                "fetch_canonical_pc": base + 24,
                "fetch_base_pc": base,
                "fetch_cycle": 3,
                "transaction_id": f"{index}:n",
                "epoch_id": 0,
                "transaction_slot": 0,
                "lag": 2,
            }]
            trial["fetch_events"].append({
                "cycle": 3, "offset": 24,
                "pc": base + 24, "raw_pc": base + 24,
                "canonical_pc": base + 24, "base_pc": base,
                "transaction_id": f"{index}:n", "epoch_id": 0,
            })
        identity = _stage_candidate_identity({
            "path": "dut.debug_MEM_PC",
            "signal_kind": "pc",
            "address_mode": "byte",
            "median_fetch_offset_cycles": 2,
            "paired_by_trial": paired,
            "lane_id": None,
        }, {trial["trial_id"]: trial for trial in trials})
        self.assertTrue(identity["relocation_proven"])
        self.assertEqual(identity["redirect_source_matches"], 3)
        self.assertEqual(identity["redirect_matches"], 3)

    def test_failed_redirect_signature_does_not_hide_pc_target_events(self):
        trials = synthetic_trials(stage_count=2, trial_count=3)
        for index, (trial, base) in enumerate(
            zip(trials, (0x80, 0xC0, 0x100))
        ):
            trial["program"] = f"pipeline_calibration_flow_{index}"
            trial["calibration_relocation_base"] = base
            trial["calibration_relocation_origin"] = 0
            trial["control_flow"] = {
                "redirect_offset": 12,
                "target_offset": 16,
                "wrong_path_offsets": (20,),
            }
            trial["calibration_signature"] = {
                "state": "failed",
                "variant": index,
                "sections": {
                    "straight_line": {
                        "state": "completed",
                        "registers": [{"offset": 12}],
                    },
                    "memory": {"state": "failed", "registers": []},
                    "redirect": {"state": "failed", "registers": []},
                },
            }
            for fetch in trial["fetch_events"]:
                fetch.update({
                    "pc": base + fetch["offset"],
                    "raw_pc": base + fetch["offset"],
                    "canonical_pc": base + fetch["offset"],
                    "base_pc": base,
                    "transaction_slot": 0,
                })
            for event in trial["events"]:
                event["value"] = base + event["offset"]
        result = classify_pipeline_interface(trials)
        self.assertTrue(result["stages"])
        self.assertTrue(all(
            stage.get("relocation_proven") is True
            for stage in result["stages"]
        ))

    def test_explicit_straight_line_failure_fails_calibration(self):
        trials = synthetic_trials(trial_count=3)
        for index, trial in enumerate(trials):
            trial["program"] = f"pipeline_calibration_flow_{index}"
            straight_state = "failed" if index == 2 else "completed"
            trial["calibration_signature"] = {
                "state": straight_state,
                "variant": index,
                "sections": {
                    "straight_line": {
                        "state": straight_state,
                        "registers": [],
                    },
                    "memory": {"state": "completed", "registers": []},
                    "redirect": {"state": "completed", "registers": []},
                },
            }
        result = classify_pipeline_interface(trials)
        self.assertEqual(result["calibration"]["state"], "failed")

    def test_calibration_architecture_uses_final_signature_not_commit_count(self):
        trials = synthetic_trials(trial_count=3)
        for index, trial in enumerate(trials):
            trial["program"] = f"pipeline_calibration_flow_{index}"
            trial["expected_write_count"] = 10
            trial["commits"] = trial["commits"][-1:]
            trial["calibration_signature"] = {
                "state": "completed", "variant": index,
                "completion_marker": {"state": "matched"},
                "registers": [], "memory": {"state": "matched"},
                "wrong_path_poison": [],
            }
        result = classify_pipeline_interface(trials)
        self.assertEqual(result["calibration"]["state"], "completed")
        self.assertEqual(result["calibration"]["completed_flow_trials"], 3)

    def test_calibration_mixed_signatures_are_partial(self):
        trials = synthetic_trials(trial_count=3)
        for index, trial in enumerate(trials):
            trial["program"] = f"pipeline_calibration_flow_{index}"
            trial["calibration_signature"] = {
                "state": "completed" if index < 2 else "failed", "variant": index,
            }
        result = classify_pipeline_interface(trials)
        self.assertEqual(result["calibration"]["state"], "partial")

    def test_calibration_execution_error_is_not_architectural_failure(self):
        trials = synthetic_trials(trial_count=3)
        for index, trial in enumerate(trials):
            trial["program"] = f"pipeline_calibration_flow_{index}"
            trial["calibration_variant"] = index
            trial["calibration_error"] = "observer return contract failed"
            trial["calibration_error_type"] = "TypeError"
            trial["calibration_traceback"] = "traceback text"
        result = classify_pipeline_interface(trials)
        self.assertEqual(result["calibration"]["state"], "unavailable")
        self.assertEqual(
            result["calibration"]["execution_state"], "failed",
        )
        self.assertEqual(
            len(result["calibration"]["execution_errors"]), 3,
        )
        self.assertTrue(all(
            item["state"] == "execution_error"
            for item in result["calibration"]["architectural"]["variants"]
        ))

    def test_packed_virtual_slice_is_validated_at_one_stable_offset(self):
        trials = []
        observations = {}
        for index in range(4):
            value = 0x510 + index
            path = "dut.pipe.payload[37+:32]"
            trial_id = str(index)
            observations[trial_id] = [({"rs1_value": value}, 5)]
            trials.append({
                "trial_id": trial_id,
                "signal_samples": [{
                    "cycle": 5, "phase": "pre_edge", "phase_order": 0,
                    "path": path, "parent_path": "dut.pipe.payload",
                    "bit_offset": 37, "slice_width": 32,
                    "candidate_role": "operand", "value": value,
                    "packed": True, "lane_id": None,
                }],
            })
        candidates = _candidate_pool(
            {"candidates": {"operand": []}}, trials, "operand"
        )
        self.assertEqual(candidates[0]["bit_offset"], 37)
        score = _validate_data_candidate(
            candidates[0]["path"], trials, observations, "rs1_value",
        )
        self.assertTrue(score["confirmed"])
        self.assertEqual(score["phase"], "pre_edge")

    def test_packed_limits_apply_per_semantic_scope_and_per_use(self):
        parents = [
            {
                "path": f"dut.{role}.payload_{index}",
                "static_rank": 100 - index,
                "name_role_hint": role,
                "lane_id": lane,
            }
            for role in ("execute", "memory")
            for lane in (0, 1)
            for index in range(20)
        ]
        selected, truncated, total_truncated = _limit_packed_parent_candidates(
            parents, per_scope=16, total=128,
        )
        self.assertEqual(len(selected), 64)
        self.assertEqual(len(truncated), 4)
        self.assertFalse(total_truncated)

        scored = [
            {
                "path": f"dut.mem.payload[{index}+:32]",
                "coverage": index / 10,
                "phase_consistency": 1.0,
                "packed_slice": {"parent_path": "dut.mem.payload"},
            }
            for index in range(12)
        ]
        self.assertEqual(len(_limit_virtual_candidates_for_use(scored)), 8)

    def test_correct_capture_is_rejected_when_poison_also_appears(self):
        trials = []
        observations = {}
        for index in range(3):
            trial_id = str(index)
            expected = 0x710 + index
            observation = {
                "offset": 16, "rs1_value": expected,
                "poison_value": 0x155,
            }
            observations[trial_id] = [(observation, 5)]
            trials.append({
                "trial_id": trial_id,
                "instruction_by_offset": {},
                "fetch_events": [],
                "signal_samples": [
                    {"cycle": 5, "phase": "pre_edge", "path": "dut.ex.op",
                     "value": expected},
                    {"cycle": 5, "phase": "pre_edge", "path": "dut.ex.op",
                     "value": 0x155},
                ],
            })
        score = _validate_data_candidate(
            "dut.ex.op", trials, observations, "rs1_value",
        )
        self.assertFalse(score["confirmed"])
        self.assertEqual(score["poison_captures"], 3)
        self.assertIn("poison", score["rejection_reason"])

    def test_destination_poison_does_not_reject_producer_source_operand(self):
        trials = []
        observations = {}
        for index in range(3):
            trial_id = str(index)
            observation = {
                "offset": 12, "role": "producer",
                "rs1_value": 0, "poison_value": 0x155 + index,
            }
            observations[trial_id] = [(observation, 5)]
            trials.append({
                "trial_id": trial_id,
                "instruction_by_offset": {},
                "fetch_events": [],
                "signal_samples": [
                    {
                        "cycle": 5, "phase": "pre_edge",
                        "path": "dut.ex.op", "value": 0,
                    },
                    {
                        "cycle": 5, "phase": "pre_edge",
                        "path": "dut.ex.op", "value": 0x155 + index,
                    },
                ],
            })
        score = _validate_data_candidate(
            "dut.ex.op", trials, observations, "rs1_value",
            minimum_distinct=1,
        )
        self.assertTrue(score["confirmed"])
        self.assertEqual(score["poison_captures"], 0)

    def test_value_stable_across_both_phases_selects_one_global_phase(self):
        trials = []
        observations = {}
        for index in range(3):
            trial_id = str(index)
            value = 0x610 + index
            observations[trial_id] = [({"rs1_value": value}, 5)]
            trials.append({
                "trial_id": trial_id,
                "signal_samples": [
                    {"cycle": 5, "phase": "pre_edge", "path": "dut.pipe.operand", "value": value},
                    {"cycle": 5, "phase": "post_edge", "path": "dut.pipe.operand", "value": value},
                ],
            })
        score = _validate_data_candidate(
            "dut.pipe.operand", trials, observations, "rs1_value",
        )
        self.assertTrue(score["confirmed"])
        self.assertEqual(score["phase"], "pre_edge")
        self.assertEqual(score["phase_consistency"], 1.0)
        self.assertEqual(score["trial_coverage"], 1.0)

    def test_differential_candidate_must_follow_control_consumer_too(self):
        trials = []
        observations = {}
        for role in ("dependent", "control"):
            for index in range(3):
                trial_id = f"{role}-{index}"
                expected = (
                    0x700 + index if role == "dependent"
                    else 0x900 + index
                )
                observations[trial_id] = [({
                    "offset": 16, "role": "consumer",
                    "rs1_value": expected,
                }, 5)]
                samples = []
                if role == "dependent":
                    samples.append({
                        "cycle": 5, "phase": "pre_edge",
                        "path": "dut.q_result", "value": expected,
                    })
                trials.append({
                    "trial_id": trial_id,
                    "program": (
                        f"alu_to_alu_{role}_gap_0_variant_{index}"
                    ),
                    "pair_role": role,
                    "signal_samples": samples,
                })
        score = _validate_data_candidate(
            "dut.q_result", trials, observations, "rs1_value",
        )
        self.assertFalse(score["confirmed"])
        self.assertTrue(score["differential_required"])
        self.assertFalse(score["differential_validated"])
        self.assertIn("matched dependent and control", score["rejection_reason"])

    def test_candidate_must_follow_consumer_across_relaxed_distance(self):
        trials = []
        observations = {}
        for gap in (0, 4):
            for role in ("dependent", "control"):
                for index in range(3):
                    trial_id = f"{gap}-{role}-{index}"
                    expected = 0x700 + index
                    observations[trial_id] = [({
                        "offset": 16 + gap * 4,
                        "role": "consumer",
                        "rs1_value": expected,
                    }, 5 + gap)]
                    samples = []
                    # This models a producer/immediate bus that aliases the
                    # adjacent consumer value but does not travel with the
                    # actual consumer when the dependency is separated.
                    if gap == 0:
                        samples.append({
                            "cycle": 5, "phase": "pre_edge",
                            "path": "dut.previous_instruction_value",
                            "value": expected,
                        })
                    trials.append({
                        "trial_id": trial_id,
                        "program": (
                            f"alu_to_alu_{role}_gap_{gap}_variant_{index}"
                        ),
                        "pair_role": role,
                        "signal_samples": samples,
                    })
        score = _validate_data_candidate(
            "dut.previous_instruction_value",
            trials,
            observations,
            "rs1_value",
        )
        self.assertFalse(score["confirmed"])
        self.assertTrue(score["relaxed_validation_required"])
        self.assertFalse(score["relaxed_validated"])
        self.assertIn("relaxed-distance", score["rejection_reason"])

    def test_five_distinct_stages_are_normalized(self):
        result = classify_pipeline_interface(synthetic_trials())
        self.assertEqual(result["state"], "confirmed")
        self.assertEqual(
            [stage["normalized_role"] for stage in result["stages"]],
            ["frontend", "operand_read", "execute", "memory", "writeback"],
        )
        self.assertTrue(result["capabilities"]["execute_stage_observable"])
        self.assertTrue(result["capabilities"]["memory_stage_observable"])

    def test_two_stage_pipeline_uses_combined_execute_memory_role(self):
        result = classify_pipeline_interface(synthetic_trials(stage_count=2))
        self.assertEqual(
            [stage["normalized_role"] for stage in result["stages"]],
            ["frontend", "execute_memory"],
        )
        cycle, stage = consumer_stage_cycle(result, "0", 16, "memory")
        self.assertEqual(cycle, 3)
        self.assertEqual(stage["normalized_role"], "execute_memory")

    def test_pc_only_stage_is_confirmed_at_lower_quality(self):
        result = classify_pipeline_interface(synthetic_trials(enhanced=False))
        execute = next(stage for stage in result["stages"] if stage["normalized_role"] == "execute")
        self.assertEqual(execute["evidence_quality"], "pc_only")
        self.assertEqual(execute["confidence"], 0.9)

    def test_missing_matching_stage_signals_is_unavailable(self):
        result = classify_pipeline_interface([{
            "trial_id": "0", "producer_offset": 12, "consumer_offset": 16,
            "events": [], "fetch_events": [], "commits": [], "transactions": [],
        }])
        self.assertEqual(result["state"], "unavailable")
        self.assertFalse(result["capabilities"]["consumer_stage_observable"])

    def test_unstable_candidate_is_rejected_as_ambiguous(self):
        trials = synthetic_trials(stage_count=2, enhanced=False)
        for index, trial in enumerate(trials):
            for event in trial["events"]:
                if event["path"].endswith("ex_mem_pc"):
                    event["cycle"] += index * 2
        result = classify_pipeline_interface(trials)
        self.assertIn(result["state"], {"partial", "ambiguous"})
        self.assertFalse(result["capabilities"]["consumer_stage_observable"])

    def test_compact_artifact_excludes_trial_and_candidate_traces(self):
        result = classify_pipeline_interface(synthetic_trials())
        compact = compact_pipeline_interface(result)
        self.assertNotIn("trial_observations", compact)
        self.assertNotIn("candidate_scores", compact)
        with tempfile.TemporaryDirectory() as directory:
            path = write_pipeline_interface(directory, "core", result)
            saved = json.loads(Path(path).read_text(encoding="utf-8"))
        self.assertEqual(saved["discovery_version"], PIPELINE_INTERFACE_DISCOVERY_VERSION)
        self.assertEqual(saved["schema_version"], 4)
        self.assertEqual(saved["implementation_revision"], 11)
        self.assertEqual(saved["state"], "confirmed")

    def test_late_repeated_pc_is_rejected_by_fetch_commit_window(self):
        trials = synthetic_trials(stage_count=2)
        for trial in trials:
            for event in trial["events"]:
                event["cycle"] += 64
        result = classify_pipeline_interface(trials, pipeline_depth=5)
        self.assertEqual(result["state"], "ambiguous")
        self.assertLessEqual(result["stage_window_cycles"]["maximum"], 16)
        self.assertEqual(result["candidate_scores"][0]["coverage"], 0.0)

    def test_exact_trace_aliases_do_not_create_a_competing_stage(self):
        trials = synthetic_trials()
        for trial in trials:
            aliases = []
            for event in trial["events"]:
                if event["path"].endswith("ex_pc"):
                    aliases.append({**event, "path": "dut.alias.execute_pc"})
            trial["events"].extend(aliases)
        result = classify_pipeline_interface(trials)
        execute = next(stage for stage in result["stages"] if stage["normalized_role"] == "execute")
        self.assertIn("dut.alias.execute_pc", [execute["pc_path"], *execute["alias_paths"]])
        self.assertFalse(result["candidate_summary"]["unresolved_stage_ties"])

    def test_same_lag_non_alias_traces_are_ambiguous(self):
        trials = synthetic_trials()
        for index, trial in enumerate(trials):
            copies = []
            for event in trial["events"]:
                if event["path"].endswith("ex_pc"):
                    copies.append({
                        **event,
                        "path": "dut.other.execute_pc",
                        "cycle": event["cycle"] + (-1 if index % 2 == 0 else 1),
                    })
            trial["events"].extend(copies)
        result = classify_pipeline_interface(trials)
        self.assertEqual(result["state"], "ambiguous")
        self.assertTrue(result["candidate_summary"]["unresolved_stage_ties"])
        self.assertFalse(result["capabilities"]["consumer_stage_observable"])

    def test_pc_and_instruction_views_of_same_stage_are_companions(self):
        trials = synthetic_trials()
        for trial in trials:
            companions = []
            for event in trial["events"]:
                if (
                    event["path"].endswith("mem_pc")
                    and not (trial["trial_id"] == "0" and event["offset"] == 12)
                ):
                    companions.append({
                        **event,
                        "path": "dut.pipe.mem_instruction",
                        "address_mode": "instruction",
                        "signal_kind": "instruction",
                        "instruction_matches": True,
                    })
            trial["events"].extend(companions)
        result = classify_pipeline_interface(trials)
        self.assertEqual(result["state"], "confirmed")
        memory = next(stage for stage in result["stages"] if stage["normalized_role"] == "memory")
        self.assertIn("dut.pipe.mem_instruction", memory["companion_paths"])

    def test_companion_pairing_is_one_to_one_and_records_alternative(self):
        fingerprint = tuple(
            (str(index), str(token), index + token)
            for index in range(3) for token in (12, 16)
        )
        candidates = [
            {
                "path": "dut.pipe.ex_pc_a", "signal_kind": "pc",
                "lane_id": None, "name_role_hint": "execute",
                "event_fingerprint": fingerprint, "score": 90,
                "coverage": 1.0,
            },
            {
                "path": "dut.pipe.ex_pc_b", "signal_kind": "pc",
                "lane_id": None, "name_role_hint": "execute",
                "event_fingerprint": tuple(
                    (trial, token, cycle + (1 if trial == "2" else 0))
                    for trial, token, cycle in fingerprint
                ),
                "score": 80, "coverage": 1.0,
            },
            {
                "path": "dut.pipe.ex_instruction",
                "signal_kind": "instruction", "lane_id": None,
                "name_role_hint": "execute",
                "event_fingerprint": fingerprint, "score": 85,
                "coverage": 1.0,
            },
        ]
        composites, accepted, rejected = _compose_stage_candidates(candidates)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(
            accepted[0]["canonical"], "dut.pipe.ex_pc_a",
        )
        self.assertTrue(any(
            item["reason"] == "one-to-one companion was already assigned"
            for item in rejected
        ))
        self.assertEqual(
            next(
                item for item in composites
                if item["path"] == "dut.pipe.ex_pc_a"
            )["instruction_path"],
            "dut.pipe.ex_instruction",
        )

    def test_frontend_conflict_does_not_clear_execute_capability(self):
        trials = synthetic_trials()
        for index, trial in enumerate(trials):
            copies = []
            for event in trial["events"]:
                if event["path"].endswith("if_pc"):
                    copies.append({
                        **event,
                        "path": "dut.other.fetch_pc",
                        "cycle": event["cycle"] + (
                            1 if index == 0 else 0
                        ),
                    })
            trial["events"].extend(copies)
        result = classify_pipeline_interface(trials)
        conflicts = result["candidate_summary"]["unresolved_stage_ties"]
        self.assertTrue(any(
            conflict["roles"] == ["frontend"]
            for conflict in conflicts.values()
        ))
        self.assertTrue(
            result["capabilities"]["execute_stage_observable"],
        )
        first = result["stage_graph"]["canonical_path"][0]
        self.assertIn(first, {
            "dut.pipe.if_pc", "dut.other.fetch_pc",
        })
        self.assertNotEqual(first, "dut.pipe.ex_pc")
        frontend_conflict = next(
            conflict for conflict in conflicts.values()
            if conflict["roles"] == ["frontend"]
        )
        self.assertEqual(
            frontend_conflict["selected_representative"], first,
        )
        self.assertIn(
            next(iter(frontend_conflict["retained_as_ambiguous"])),
            result["stage_graph"]["unassigned_nodes"],
        )

    def test_wrapper_fetch_pc_is_not_an_internal_candidate(self):
        self.assertIsNone(_candidate_role("dut.probe_fetch_pc", 32))

    def test_broadened_stage_names_are_shortlisted(self):
        for path in ("dut.pc", "dut.r_pc", "dut.r_pc_val", "dut.debug_EX_PC"):
            self.assertEqual(_candidate_role(path, 32), "pc")

    def test_short_alu_inputs_are_scoped_operand_candidates(self):
        self.assertEqual(_candidate_role("dut.core.u_alu.a", 32), "operand")
        self.assertEqual(_candidate_role("dut.core.execute.b", 32), "operand")
        self.assertIsNone(_candidate_role("dut.wrapper.a", 32))

    def test_instruction_stream_without_relocated_pc_is_not_a_stage(self):
        trials = synthetic_trials()
        for trial in trials:
            for event in trial["events"]:
                if event["path"].endswith("ex_pc"):
                    event["path"] = "dut.pipe.ex_instruction"
                    event["address_mode"] = "instruction"
                    event["signal_kind"] = "instruction"
                    event["instruction_matches"] = True
        result = classify_pipeline_interface(trials)
        self.assertFalse(any(
            stage.get("observation_kind") == "instruction"
            for stage in result["stages"]
        ))
        diagnostic = next(
            item for item in result["stage_candidate_diagnostics"]
            if item["path"] == "dut.pipe.ex_instruction"
        )
        self.assertEqual(diagnostic["state"], "rejected")

    def test_operand_and_source_id_candidates_are_dynamically_confirmed(self):
        trials = synthetic_trials()
        for index, trial in enumerate(trials):
            register = 1 + index
            value = 0x210 + index
            trial["operand_expectations"] = [
                {
                    "offset": 12, "role": "producer", "destination_register": register,
                    "result_value": value, "poison_value": 0x155,
                },
                {
                    "offset": 16, "role": "consumer", "rs1_register": register,
                    "rs1_value": value, "rs1_use": "execute",
                },
            ]
            trial["signal_samples"] = [
                {"cycle": 4, "phase": "post_edge", "phase_order": 1,
                 "path": "dut.pipe.ex_rs1", "candidate_role": "source_id", "value": register},
                {"cycle": 5, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.ex_operand", "candidate_role": "operand", "value": value},
            ]
            trial["architectural_samples"] = [
                {"cycle": 5, "phase": "pre_edge", "phase_order": 0,
                 "register": register, "value": 0x155},
                {"cycle": 5, "phase": "post_edge", "phase_order": 1,
                 "register": register, "value": value},
            ]
            trial["writeback_samples"] = []
        discovery = {
            "candidates": {
                "source_id": [{"path": "dut.pipe.ex_rs1"}],
                "operand": [{"path": "dut.pipe.ex_operand"}],
                "store_data": [], "valid": [], "stall": [], "flush": [],
            },
            "search_truncated": False,
            "visited_scopes": 1,
        }
        result = classify_pipeline_interface(trials, discovery=discovery)
        execute = next(stage for stage in result["stages"] if stage["normalized_role"] == "execute")
        self.assertEqual(execute["source_id_paths"]["rs1"], "dut.pipe.ex_rs1")
        self.assertEqual(execute["operand_paths"]["execute"], "dut.pipe.ex_operand")
        self.assertTrue(result["capabilities"]["source_ids"])
        self.assertTrue(result["capabilities"]["operand_values"])
        self.assertEqual(
            execute["operand_uses"]["execute"]["distinct_source_ids"], 4,
        )
        self.assertGreaterEqual(
            result["calibration"]["capability_coverage"]["source_ids"][
                "distinct_source_ids"
            ],
            4,
        )
        self.assertEqual(
            result["requirement_observations"]["0"]["execute"]["phase"],
            "pre_edge",
        )
        self.assertEqual(
            result["requirement_observations"]["0"]["execute"][
                "capture_source"
            ],
            "validated_candidate_ledger",
        )
        self.assertEqual(
            result["role_evidence"]["execute"]["state"], "confirmed",
        )

    def test_missing_dependent_capture_rejects_role_local_operand_use(self):
        trials = synthetic_trials()
        for index, trial in enumerate(trials):
            register = 1 + index
            value = 0x2A0 + index
            trial["operand_expectations"] = [{
                "offset": 12, "role": "producer",
                "destination_register": register,
                "result_value": value,
            }, {
                "offset": 16, "role": "consumer",
                "rs1_register": register, "rs1_value": value,
                "rs1_use": "execute",
            }]
            trial["signal_samples"] = [{
                "cycle": 4, "phase": "post_edge", "phase_order": 1,
                "path": "dut.pipe.ex_rs1", "candidate_role": "source_id",
                "value": register,
            }]
            if index != 3:
                trial["signal_samples"].append({
                    "cycle": 5, "phase": "pre_edge", "phase_order": 0,
                    "path": "dut.pipe.ex_operand",
                    "candidate_role": "operand", "value": value,
                })
            trial["architectural_samples"] = []
            trial["writeback_samples"] = []
        discovery = {
            "candidates": {
                "source_id": [{"path": "dut.pipe.ex_rs1"}],
                "operand": [{"path": "dut.pipe.ex_operand"}],
                "store_data": [], "valid": [], "stall": [], "flush": [],
                "destination_id": [], "wb_data": [], "wb_enable": [],
            },
            "search_truncated": False, "visited_scopes": 1,
        }
        result = classify_pipeline_interface(trials, discovery=discovery)
        execute = next(
            stage for stage in result["stages"]
            if stage["normalized_role"] == "execute"
        )
        use = execute["operand_uses"]["execute"]
        self.assertEqual(use["state"], "rejected")
        self.assertIn("3", use["rejection_reason"])
        self.assertNotEqual(
            result["role_evidence"]["execute"]["state"], "confirmed",
        )

    def test_dependency_side_ledger_rejects_result_and_independent_side(self):
        trials = synthetic_trials()
        for index, trial in enumerate(trials):
            producer_register = 1 + index
            independent_register = 12 + index
            value = 0x320 + index
            independent_value = 0x440 + index
            trial["program"] = f"alu_to_alu_dependent_gap_0_variant_{index}"
            trial["operand_expectations"] = [{
                "offset": 12, "role": "producer",
                "destination_register": producer_register,
                "result_value": value,
            }, {
                "offset": 16, "role": "consumer",
                "rs1_register": producer_register, "rs1_value": value,
                "rs1_use": "execute",
                "rs2_register": independent_register,
                "rs2_value": independent_value, "rs2_use": "execute",
            }]
            trial["signal_samples"] = [
                {"cycle": 4, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.rs1_ex", "candidate_role": "source_id",
                 "value": producer_register},
                {"cycle": 4, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.rs2_ex", "candidate_role": "source_id",
                 "value": independent_register},
                {"cycle": 4, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.u_alu.a", "candidate_role": "operand",
                 "value": value},
                {"cycle": 4, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.u_alu.b", "candidate_role": "operand",
                 "value": independent_value},
                # Producer result collision: it must never become a consumer
                # operand merely because the values happen to match.
                {"cycle": 4, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.alu_rd_dat", "candidate_role": "operand",
                 "value": value},
            ]
            trial["architectural_samples"] = [{
                "cycle": 5, "phase": "post_edge", "phase_order": 1,
                "register": producer_register, "value": value,
            }]
            trial["writeback_samples"] = []
        discovery = {
            "candidates": {
                "source_id": [
                    {"path": "dut.pipe.rs1_ex"},
                    {"path": "dut.pipe.rs2_ex"},
                ],
                "operand": [
                    {"path": "dut.pipe.u_alu.a"},
                    {"path": "dut.pipe.u_alu.b"},
                    {"path": "dut.pipe.alu_rd_dat"},
                ],
                "store_data": [], "valid": [], "stall": [], "flush": [],
                "destination_id": [], "wb_data": [], "wb_enable": [],
            },
            "search_truncated": False, "visited_scopes": 1,
        }
        result = classify_pipeline_interface(trials, discovery=discovery)
        requirement = result["requirement_observations"]["0"]["execute"]
        self.assertEqual(requirement["side"], "rs1")
        self.assertEqual(requirement["path"], "dut.pipe.u_alu.a")
        self.assertEqual(
            result["role_evidence"]["execute"]["operand_path"],
            "dut.pipe.u_alu.a",
        )
        rejected = [
            item for item in result["operand_candidate_scores"]
            if item.get("path") == "dut.pipe.alu_rd_dat"
        ]
        self.assertTrue(rejected)
        self.assertTrue(all(not item.get("confirmed") for item in rejected))

    def test_relaxed_only_capture_gap_does_not_reject_adjacent_role(self):
        trials = synthetic_trials(trial_count=6)
        for index, trial in enumerate(trials):
            adjacent = index < 3
            trial["program"] = (
                f"alu_to_alu_dependent_gap_"
                f"{0 if adjacent else 4}"
            )
            register = 1 + (index % 3)
            value = 0x2E0 + index
            trial["operand_expectations"] = [{
                "offset": 12, "role": "producer",
                "destination_register": register,
                "result_value": value,
            }, {
                "offset": 16, "role": "consumer",
                "rs1_register": register, "rs1_value": value,
                "rs1_use": "execute",
            }]
            trial["signal_samples"] = [{
                "cycle": 4, "phase": "post_edge", "phase_order": 1,
                "path": "dut.pipe.ex_rs1", "candidate_role": "source_id",
                "value": register,
            }]
            if adjacent:
                trial["signal_samples"].append({
                    "cycle": 5, "phase": "pre_edge", "phase_order": 0,
                    "path": "dut.pipe.forward_operand",
                    "candidate_role": "operand", "value": value,
                })
            trial["architectural_samples"] = [{
                "cycle": 6, "phase": "post_edge", "phase_order": 1,
                "register": register, "value": value,
            }]
            trial["writeback_samples"] = []
        discovery = {
            "candidates": {
                "source_id": [{"path": "dut.pipe.ex_rs1"}],
                "operand": [{"path": "dut.pipe.forward_operand"}],
                "store_data": [], "valid": [], "stall": [], "flush": [],
                "destination_id": [], "wb_data": [], "wb_enable": [],
            },
            "search_truncated": False, "visited_scopes": 1,
        }
        result = classify_pipeline_interface(trials, discovery=discovery)
        execute = next(
            stage for stage in result["stages"]
            if stage["normalized_role"] == "execute"
        )
        self.assertEqual(
            execute["operand_uses"]["execute"]["state"], "confirmed",
        )
        self.assertEqual(
            result["role_evidence"]["execute"]["captured_trials"], 3,
        )

    def test_operand_candidate_may_confirm_one_dependency_family(self):
        trials = []
        observations = {}
        for index in range(6):
            family = "alu_to_alu" if index < 3 else "load_to_alu"
            trial_id = str(index)
            value = 0x510 + index
            observation = {
                "offset": 16, "role": "consumer", "rs1_value": value,
            }
            observations[trial_id] = [(observation, 5)]
            samples = []
            if family == "alu_to_alu":
                samples.append({
                    "cycle": 5, "phase": "pre_edge", "phase_order": 0,
                    "path": "dut.pipe.u_alu.a", "value": value,
                })
            trials.append({
                "trial_id": trial_id,
                "program": f"{family}_dependent_gap_0_variant_{index}",
                "signal_samples": samples,
            })
        score = _validate_data_candidate(
            "dut.pipe.u_alu.a", trials, observations, "rs1_value",
        )
        self.assertTrue(score["confirmed"])
        self.assertEqual(score["confirmed_trial_groups"], ["alu_to_alu"])
        self.assertEqual(score["missing_trial_ids"], [])

    def test_stall_control_requires_repeated_hold_and_release_correlation(self):
        trials = []
        observations = {}
        for trial_index in range(2):
            trial_id = str(trial_index)
            observations[trial_id] = {12: 2, 16: 4}
            trials.append({
                "trial_id": trial_id,
                "handshake_role": "delayed",
                "response_delay_cycles": 1,
                "operand_expectations": [{
                    "offset": 12, "role": "calibration_load",
                }],
                "transactions": [{
                    "cycle": 3, "kind": "load", "epoch_id": trial_index + 1,
                    "transaction_id": f"data:{trial_index + 1}:0",
                }],
                "events": [
                    {"cycle": 2, "offset": 12, "path": "dut.pipe.ex_pc"},
                    {"cycle": 3, "offset": 12, "path": "dut.pipe.ex_pc"},
                    {"cycle": 4, "offset": 16, "path": "dut.pipe.ex_pc"},
                ],
                "signal_samples": [
                    {"cycle": 1, "phase": "post_edge", "path": "dut.pipe.ex_stall", "value": 0},
                    {"cycle": 3, "phase": "post_edge", "path": "dut.pipe.ex_stall", "value": 1},
                    {"cycle": 4, "phase": "post_edge", "path": "dut.pipe.ex_stall", "value": 0},
                ],
            })
        validation = _validate_controls(
            {"pc_path": "dut.pipe.ex_pc"},
            trials,
            observations,
            {"candidates": {
                "valid": [],
                "stall": [{"path": "dut.pipe.ex_stall"}],
                "flush": [],
            }},
            forced_hold_supported=True,
        )
        self.assertEqual(validation["stall"]["state"], "confirmed")
        self.assertEqual(validation["stall"]["polarity"], "active_high")

    def test_active_low_enable_requires_repeated_hold_and_release_correlation(self):
        trials = []
        observations = {}
        for trial_index in range(2):
            trial_id = str(trial_index)
            observations[trial_id] = {12: 2, 16: 4}
            trials.append({
                "trial_id": trial_id,
                "handshake_role": "delayed",
                "response_delay_cycles": 1,
                "operand_expectations": [{
                    "offset": 12, "role": "calibration_load",
                }],
                "transactions": [{
                    "cycle": 3, "kind": "load", "epoch_id": trial_index + 1,
                    "transaction_id": f"data:{trial_index + 1}:0",
                }],
                "events": [
                    {"cycle": 2, "offset": 12, "path": "dut.pipe.ex_pc"},
                    {"cycle": 3, "offset": 12, "path": "dut.pipe.ex_pc"},
                    {"cycle": 4, "offset": 16, "path": "dut.pipe.ex_pc"},
                ],
                "signal_samples": [
                    {"cycle": 1, "phase": "post_edge", "path": "dut.pipe.ex_enable_n", "value": 1},
                    {"cycle": 3, "phase": "post_edge", "path": "dut.pipe.ex_enable_n", "value": 0},
                    {"cycle": 4, "phase": "post_edge", "path": "dut.pipe.ex_enable_n", "value": 1},
                ],
            })
        validation = _validate_controls(
            {"pc_path": "dut.pipe.ex_pc"}, trials, observations,
            {"candidates": {
                "valid": [], "stall": [{"path": "dut.pipe.ex_enable_n"}],
                "flush": [],
            }},
            forced_hold_supported=True,
        )
        self.assertEqual(validation["stall"]["state"], "confirmed")
        self.assertEqual(validation["stall"]["polarity"], "active_low_enable")

    def test_handshake_gate_requires_baseline_two_delays_and_recovery(self):
        trials = synthetic_trials(trial_count=6)
        for index, trial in enumerate(trials):
            if index < 3:
                trial["program"] = f"pipeline_calibration_handshake_{index}"
                trial["calibration_signature"] = {"state": "completed", "variant": index}
                trial["transactions"] = [{
                    "cycle": 5, "kind": "load", "epoch_id": index + 1,
                    "transaction_id": f"data:{index + 1}:0",
                }]
            else:
                trial["program"] = f"pipeline_calibration_flow_{index - 3}"
                trial["calibration_signature"] = {"state": "completed", "variant": index - 3}
                trial["transactions"].append({
                    "cycle": 4, "kind": "load", "epoch_id": index + 1,
                    "transaction_id": f"data:{index + 1}:recovery",
                })
        result = classify_pipeline_interface(trials)
        self.assertEqual(result["calibration"]["handshake"]["state"], "supported")
        self.assertTrue(result["calibration"]["handshake"]["recovery_complete"])
        self.assertEqual(result["calibration"]["forced_hold"], "completed")

    def test_incomplete_delayed_handshake_is_unsupported(self):
        trials = synthetic_trials(trial_count=4)
        for index, trial in enumerate(trials):
            if index < 3:
                trial["program"] = f"pipeline_calibration_handshake_{index}"
                trial["calibration_signature"] = {
                    "state": "completed" if index < 2 else "failed", "variant": index,
                }
                trial["transactions"] = [{
                    "cycle": 5, "kind": "load", "epoch_id": index + 1,
                    "transaction_id": f"data:{index + 1}:0",
                }]
            else:
                trial["program"] = "pipeline_calibration_flow_0"
                trial["calibration_signature"] = {"state": "completed", "variant": 0}
        result = classify_pipeline_interface(trials)
        self.assertEqual(result["calibration"]["handshake"]["state"], "unsupported")
        self.assertEqual(result["calibration"]["forced_hold"], "unsupported")

    def test_failed_recovery_prevents_forced_hold_completion(self):
        trials = synthetic_trials(trial_count=4)
        for index, trial in enumerate(trials):
            if index < 3:
                trial["program"] = f"pipeline_calibration_handshake_{index}"
                trial["handshake_role"] = (
                    "baseline" if index == 0 else "delayed"
                )
                trial["response_delay_cycles"] = 0 if index == 0 else 1
                trial["calibration_signature"] = {
                    "state": "completed", "variant": index,
                }
                trial["transactions"] = [{
                    "cycle": 5, "kind": "load", "epoch_id": index + 1,
                    "transaction_id": f"data:{index + 1}:0",
                }]
            else:
                trial["program"] = "pipeline_calibration_flow_0"
                trial["calibration_signature"] = {
                    "state": "failed", "variant": 0,
                }
        result = classify_pipeline_interface(trials)
        self.assertFalse(
            result["calibration"]["handshake"]["recovery_complete"]
        )
        self.assertEqual(
            result["calibration"]["handshake"]["state"], "unsupported",
        )
        self.assertEqual(result["calibration"]["forced_hold"], "unsupported")

    def test_unqualified_repeated_pc_cannot_confirm_stall(self):
        trials = [{
            "trial_id": str(index),
            "events": [
                {"cycle": 2, "offset": 12, "path": "dut.ex_pc"},
                {"cycle": 3, "offset": 12, "path": "dut.ex_pc"},
                {"cycle": 4, "offset": 16, "path": "dut.ex_pc"},
            ],
            "signal_samples": [
                {"cycle": 3, "phase": "post_edge", "path": "dut.stall",
                 "value": 1},
                {"cycle": 4, "phase": "post_edge", "path": "dut.stall",
                 "value": 0},
            ],
        } for index in range(3)]
        validation = _validate_controls(
            {"pc_path": "dut.ex_pc"}, trials,
            {str(index): {12: 2, 16: 4} for index in range(3)},
            {"candidates": {
                "valid": [], "stall": [{"path": "dut.stall"}], "flush": [],
            }},
            forced_hold_supported=False,
        )
        self.assertEqual(validation["stall"]["state"], "unexercised")

    def test_writeback_fallback_is_validated_from_id_data_and_enable(self):
        trials = synthetic_trials()
        for index, trial in enumerate(trials):
            register = 6 + index
            value = 0x350 + index
            commit_cycle = trial["commits"][0]["cycle"]
            trial["operand_expectations"] = [{
                "offset": 12, "role": "producer",
                "destination_register": register,
                "result_value": value,
            }]
            trial["signal_samples"] = [
                {"cycle": commit_cycle, "phase": "post_edge", "phase_order": 1,
                 "path": "dut.pipe.wb_rd", "candidate_role": "destination_id", "value": register},
                {"cycle": commit_cycle, "phase": "post_edge", "phase_order": 1,
                 "path": "dut.pipe.wb_data", "candidate_role": "wb_data", "value": value},
                {"cycle": commit_cycle, "phase": "post_edge", "phase_order": 1,
                 "path": "dut.pipe.wb_enable", "candidate_role": "wb_enable", "value": 1},
            ]
            trial["architectural_samples"] = []
            trial["writeback_samples"] = []
        discovery = {
            "candidates": {
                "source_id": [], "operand": [], "store_data": [],
                "valid": [], "stall": [], "flush": [],
                "destination_id": [{"path": "dut.pipe.wb_rd"}],
                "wb_data": [{"path": "dut.pipe.wb_data"}],
                "wb_enable": [{"path": "dut.pipe.wb_enable"}],
            },
            "search_truncated": False,
            "visited_scopes": 1,
        }
        result = classify_pipeline_interface(trials, discovery=discovery)
        self.assertEqual(result["selected_writeback_paths"]["write_data"], "dut.pipe.wb_data")
        self.assertEqual(
            result["producer_availability_observations"]["0"]["source"],
            "dynamically_validated_writeback_handshake",
        )
        self.assertTrue(result["capabilities"]["writeback_event"])

    def test_store_issue_capture_can_be_proved_without_a_memory_stage_pc(self):
        trials = synthetic_trials()
        for index, trial in enumerate(trials):
            trial["events"] = [
                event for event in trial["events"]
                if not event["path"].endswith("mem_pc")
            ]
            register = 3 + (index % 2)
            value = 0x470 + index
            request_cycle = trial["transactions"][0]["cycle"]
            trial["operand_expectations"] = [{
                "offset": 16, "role": "consumer",
                "rs2_register": register, "rs2_value": value,
                "rs2_use": "store_data",
            }]
            trial["signal_samples"] = [
                {"cycle": request_cycle, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.me_rs2", "candidate_role": "source_id", "value": register},
                {"cycle": request_cycle, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.inst_dout[20+:5]",
                 "parent_path": "dut.pipe.inst_dout",
                 "bit_offset": 20, "slice_width": 5, "packed": True,
                 "lane_id": None, "candidate_role": "source_id",
                 "value": register},
                {"cycle": request_cycle, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.PC.out[7+:5]",
                 "parent_path": "dut.PC.out",
                 "bit_offset": 7, "slice_width": 5, "packed": True,
                 "lane_id": None, "candidate_role": "source_id",
                 "value": register},
                {"cycle": request_cycle, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.alu_out[8+:5]",
                 "parent_path": "dut.alu_out",
                 "bit_offset": 8, "slice_width": 5, "packed": True,
                 "lane_id": None, "candidate_role": "source_id",
                 "value": register},
                {"cycle": request_cycle, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.btb.data_array[9+:5]",
                 "parent_path": "dut.btb.data_array",
                 "bit_offset": 9, "slice_width": 5, "packed": True,
                 "lane_id": None, "candidate_role": "source_id",
                 "value": register},
                {"cycle": request_cycle, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.me_store_data", "candidate_role": "store_data", "value": value},
                {"cycle": request_cycle, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.mem_wb_out[145+:32]",
                 "parent_path": "dut.mem_wb_out",
                 "bit_offset": 145, "slice_width": 32, "packed": True,
                 "lane_id": None, "candidate_role": "store_data",
                 "value": value},
                {"cycle": request_cycle, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.data_mem_rdata[0+:32]",
                 "parent_path": "dut.data_mem_rdata",
                 "bit_offset": 0, "slice_width": 32, "packed": True,
                 "lane_id": None, "candidate_role": "store_data",
                 "value": value},
            ]
            trial["architectural_samples"] = []
            trial["writeback_samples"] = []
        discovery = {
            "candidates": {
                "source_id": [{"path": "dut.pipe.me_rs2"}],
                "operand": [],
                "store_data": [{"path": "dut.pipe.me_store_data"}],
                "valid": [], "stall": [], "flush": [],
                "destination_id": [], "wb_data": [], "wb_enable": [],
            },
            "search_truncated": False,
            "visited_scopes": 1,
        }
        result = classify_pipeline_interface(trials, discovery=discovery)
        store_stage = next(
            stage for stage in result["stages"]
            if stage.get("observation_kind") == "transaction_aligned_operand_capture"
        )
        self.assertEqual(store_stage["operand_paths"]["store_data"], "dut.pipe.me_store_data")
        self.assertTrue(result["capabilities"]["store_data_capture"])
        store_node = next(
            node for node in result["stage_graph"]["nodes"]
            if node.get("kind") == "transaction_local_store"
        )
        self.assertTrue(store_node["exact_store_epochs"])
        self.assertEqual(
            len(store_node["exact_fetch_associations"]), len(trials),
        )
        self.assertEqual(
            result["requirement_observations"]["0"]["store_data"]["phase"],
            "pre_edge",
        )
        instruction_ids = [
            item for item in result["operand_candidate_scores"]
            if item.get("path") == "dut.pipe.inst_dout[20+:5]"
            and item.get("stage") == "store_issue"
        ]
        self.assertTrue(instruction_ids)
        self.assertTrue(all(
            not item.get("confirmed") for item in instruction_ids
        ))
        self.assertTrue(any(
            "instruction bits" in item.get("rejection_reason", "")
            for item in instruction_ids
        ))
        pc_ids = [
            item for item in result["operand_candidate_scores"]
            if item.get("path") == "dut.PC.out[7+:5]"
            and item.get("stage") == "store_issue"
        ]
        self.assertTrue(pc_ids)
        self.assertTrue(any(
            "PC bits" in item.get("rejection_reason", "")
            for item in pc_ids
        ))
        result_ids = [
            item for item in result["operand_candidate_scores"]
            if item.get("path") == "dut.alu_out[8+:5]"
            and item.get("stage") == "store_issue"
        ]
        self.assertTrue(any(
            "producer/result" in item.get("rejection_reason", "")
            for item in result_ids
        ))
        post_memory_data = [
            item for item in result["operand_candidate_scores"]
            if item.get("path") == "dut.mem_wb_out[145+:32]"
            and item.get("stage") == "store_issue"
        ]
        self.assertTrue(any(
            "post-memory" in item.get("rejection_reason", "")
            for item in post_memory_data
        ))
        predictor_ids = [
            item for item in result["operand_candidate_scores"]
            if item.get("path") == "dut.btb.data_array[9+:5]"
            and item.get("stage") == "store_issue"
        ]
        self.assertTrue(any(
            "predictor/cache" in item.get("rejection_reason", "")
            for item in predictor_ids
        ))
        read_data = [
            item for item in result["operand_candidate_scores"]
            if item.get("path") == "dut.data_mem_rdata[0+:32]"
            and item.get("stage") == "store_issue"
        ]
        self.assertTrue(any(
            "memory-read" in item.get("rejection_reason", "")
            for item in read_data
        ))

    def test_store_data_uses_memory_local_source_id_not_decode_match(self):
        trials = synthetic_trials()
        for index, trial in enumerate(trials):
            register = 3 + (index % 2)
            value = 0x580 + index
            trial["operand_expectations"] = [{
                "offset": 16, "role": "consumer",
                "rs2_register": register, "rs2_value": value,
                "rs2_use": "store_data", "poison_value": 0x155,
            }]
            trial["signal_samples"] = [
                {"cycle": 3, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.control_rom.rs2_id", "candidate_role": "source_id", "value": register},
                {"cycle": 5, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.mem_rs2", "candidate_role": "source_id", "value": register},
                {"cycle": 5, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.mem_store_data", "candidate_role": "store_data", "value": value},
            ]
            trial["architectural_samples"] = []
            trial["writeback_samples"] = []
        discovery = {
            "candidates": {
                "source_id": [
                    {"path": "dut.control_rom.rs2_id"},
                    {"path": "dut.pipe.mem_rs2"},
                ],
                "operand": [],
                "store_data": [{"path": "dut.pipe.mem_store_data"}],
                "valid": [], "stall": [], "flush": [],
                "destination_id": [], "wb_data": [], "wb_enable": [],
            },
            "search_truncated": False, "visited_scopes": 2,
        }
        result = classify_pipeline_interface(trials, discovery=discovery)
        memory = next(stage for stage in result["stages"] if stage["normalized_role"] == "memory")
        self.assertEqual(memory["operand_uses"]["store_data"]["source_id_path"], "dut.pipe.mem_rs2")
        self.assertNotEqual(memory["source_id_paths"]["rs2"], "dut.control_rom.rs2_id")

    def test_store_data_accepts_stable_packed_memory_source_id(self):
        trials = synthetic_trials()
        source_path = "dut.pipe.ex_mem_out[37+:5]"
        for index, trial in enumerate(trials):
            register = 3 + (index % 2)
            value = 0x5C0 + index
            cycle = trial["transactions"][0]["cycle"]
            trial["operand_expectations"] = [{
                "offset": 16, "role": "consumer",
                "rs2_register": register, "rs2_value": value,
                "rs2_use": "store_data",
            }]
            trial["signal_samples"] = [
                {
                    "cycle": cycle, "phase": "pre_edge",
                    "phase_order": 0, "path": source_path,
                    "parent_path": "dut.pipe.ex_mem_out",
                    "bit_offset": 37, "slice_width": 5,
                    "candidate_role": "source_id", "value": register,
                    "packed": True, "lane_id": None,
                },
                {
                    "cycle": cycle, "phase": "pre_edge",
                    "phase_order": 0,
                    "path": "dut.pipe.wb_mem_forward_MUX_out",
                    "candidate_role": "store_data", "value": value,
                },
            ]
            trial["architectural_samples"] = []
            trial["writeback_samples"] = []
        discovery = {
            "candidates": {
                "source_id": [], "operand": [],
                "store_data": [{
                    "path": "dut.pipe.wb_mem_forward_MUX_out",
                }],
                "valid": [], "stall": [], "flush": [],
                "destination_id": [], "wb_data": [], "wb_enable": [],
            },
            "search_truncated": False, "visited_scopes": 1,
        }
        result = classify_pipeline_interface(trials, discovery=discovery)
        memory = next(
            stage for stage in result["stages"]
            if stage["normalized_role"] == "memory"
        )
        use = memory["operand_uses"]["store_data"]
        self.assertEqual(use["state"], "confirmed")
        self.assertEqual(use["source_id_path"], source_path)
        self.assertEqual(
            use["source_id_packed_slice"]["bit_offset"], 37,
        )

    def test_store_data_value_without_role_local_source_id_is_rejected(self):
        trials = synthetic_trials()
        for index, trial in enumerate(trials):
            value = 0x5B0 + index
            trial["operand_expectations"] = [{
                "offset": 16, "role": "consumer", "rs2_register": 3,
                "rs2_value": value, "rs2_use": "store_data",
            }]
            cycle = trial["transactions"][0]["cycle"]
            trial["signal_samples"] = [
                {"cycle": cycle, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.mem_store_data", "candidate_role": "store_data",
                 "value": value},
            ]
        discovery = {
            "candidates": {
                "source_id": [], "operand": [],
                "store_data": [{"path": "dut.pipe.mem_store_data"}],
                "valid": [], "stall": [], "flush": [],
                "destination_id": [], "wb_data": [], "wb_enable": [],
            },
            "search_truncated": False, "visited_scopes": 1,
        }
        result = classify_pipeline_interface(trials, discovery=discovery)
        memory = next(stage for stage in result["stages"] if stage["normalized_role"] == "memory")
        self.assertEqual(memory["operand_uses"]["store_data"]["state"], "rejected")
        self.assertEqual(
            memory["operand_uses"]["store_data"]["rejection_reason"],
            "no role-local source ID candidate was confirmed",
        )
        self.assertFalse(result["capabilities"]["store_data_capture"])

    def test_store_capture_rejects_missing_transaction_epoch(self):
        trials = synthetic_trials()
        for index, trial in enumerate(trials):
            trial["events"] = [event for event in trial["events"] if not event["path"].endswith("mem_pc")]
            trial["transactions"][0].pop("epoch_id", None)
            trial["transactions"][0].pop("transaction_id", None)
            register = 3 + (index % 2)
            value = 0x590 + index
            cycle = trial["transactions"][0]["cycle"]
            trial["operand_expectations"] = [{
                "offset": 16, "role": "consumer",
                "rs2_register": register, "rs2_value": value, "rs2_use": "store_data",
            }]
            trial["signal_samples"] = [
                {"cycle": cycle, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.me_rs2", "candidate_role": "source_id", "value": register},
                {"cycle": cycle, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.me_store_data", "candidate_role": "store_data", "value": value},
            ]
        discovery = {
            "candidates": {
                "source_id": [{"path": "dut.pipe.me_rs2"}],
                "operand": [], "store_data": [{"path": "dut.pipe.me_store_data"}],
                "valid": [], "stall": [], "flush": [],
                "destination_id": [], "wb_data": [], "wb_enable": [],
            },
            "search_truncated": False, "visited_scopes": 1,
        }
        result = classify_pipeline_interface(trials, discovery=discovery)
        self.assertFalse(result["capabilities"]["store_data_capture"])

    def test_store_capture_rejects_wrong_transaction_address_or_value(self):
        for mismatch in ("address", "value"):
            with self.subTest(mismatch=mismatch):
                trials = synthetic_trials()
                for index, trial in enumerate(trials):
                    trial["events"] = [
                        event for event in trial["events"]
                        if not event["path"].endswith("mem_pc")
                    ]
                    register = 3 + (index % 2)
                    value = 0x690 + index
                    address = 0x180 + 4 * index
                    trial["expected_store_address"] = address
                    trial["expected_store_value"] = value
                    transaction = trial["transactions"][0]
                    transaction["address"] = (
                        address + 4 if mismatch == "address" else address
                    )
                    transaction["value"] = (
                        value ^ 1 if mismatch == "value" else value
                    )
                    cycle = transaction["cycle"]
                    trial["operand_expectations"] = [{
                        "offset": 16, "role": "consumer",
                        "rs2_register": register, "rs2_value": value,
                        "rs2_use": "store_data",
                    }]
                    trial["signal_samples"] = [
                        {"cycle": cycle, "phase": "pre_edge",
                         "path": "dut.me_rs2", "candidate_role": "source_id",
                         "value": register},
                        {"cycle": cycle, "phase": "pre_edge",
                         "path": "dut.me_data", "candidate_role": "store_data",
                         "value": value},
                    ]
                discovery = {
                    "candidates": {
                        "source_id": [{"path": "dut.me_rs2"}],
                        "operand": [],
                        "store_data": [{"path": "dut.me_data"}],
                        "valid": [], "stall": [], "flush": [],
                        "destination_id": [], "wb_data": [], "wb_enable": [],
                    },
                    "search_truncated": False, "visited_scopes": 1,
                }
                result = classify_pipeline_interface(
                    trials, discovery=discovery,
                )
                self.assertFalse(
                    result["capabilities"]["store_data_capture"]
                )

    def _superscalar_execute_result(self, writeback_lane):
        trials = synthetic_trials()
        for index, trial in enumerate(trials):
            register = 1 + index
            value = 0x720 + index
            trial["operand_expectations"] = [
                {
                    "offset": 12, "role": "producer",
                    "destination_register": register,
                    "result_value": value, "poison_value": 0x155,
                },
                {
                    "offset": 16, "role": "consumer",
                    "rs1_register": register, "rs1_value": value,
                    "rs1_use": "execute",
                },
            ]
            trial["signal_samples"] = [
                {"cycle": 4, "phase": "post_edge",
                 "phase_order": 1,
                 "path": "dut.pipe.lane0_rs1",
                 "candidate_role": "source_id", "value": register,
                 "lane_id": 0},
                {"cycle": 5, "phase": "pre_edge",
                 "phase_order": 0,
                 "path": "dut.pipe.lane0_operand",
                 "candidate_role": "operand", "value": value,
                 "lane_id": 0},
            ]
            trial["architectural_samples"] = []
            trial["writeback_samples"] = [] if writeback_lane is None else [{
                "cycle": 6, "phase": "post_edge", "phase_order": 1,
                "write_enable": 1, "write_addr": register,
                "write_data": value, "lane_id": writeback_lane,
                "paths": {
                    "write_enable": f"dut.pipe.lane{writeback_lane}_we",
                    "write_addr": f"dut.pipe.lane{writeback_lane}_rd",
                    "write_data": f"dut.pipe.lane{writeback_lane}_data",
                },
            }]
        discovery = {
            "candidates": {
                "source_id": [{
                    "path": "dut.pipe.lane0_rs1", "lane_id": 0,
                    "lane_hint": True,
                }],
                "operand": [{
                    "path": "dut.pipe.lane0_operand", "lane_id": 0,
                    "lane_hint": True,
                }],
                "store_data": [], "valid": [], "stall": [], "flush": [],
                "destination_id": [], "wb_data": [], "wb_enable": [],
            },
            "search_truncated": False, "visited_scopes": 1,
            "multi_lane_candidates": True,
        }
        return classify_pipeline_interface(trials, discovery=discovery)

    def test_superscalar_complete_lane_chain_is_confirmed(self):
        result = self._superscalar_execute_result(writeback_lane=0)
        self.assertTrue(result["capabilities"]["lane_identity"])
        chain = next(
            item for item in result["selected_lane_chains"]
            if item["use"] == "execute"
        )
        self.assertEqual(chain["state"], "confirmed")
        self.assertTrue(chain["links"]["transaction_or_writeback"])

    def test_superscalar_missing_or_cross_lane_writeback_is_unresolved(self):
        for writeback_lane in (None, 1):
            with self.subTest(writeback_lane=writeback_lane):
                result = self._superscalar_execute_result(writeback_lane)
                self.assertFalse(result["capabilities"]["lane_identity"])
                chain = next(
                    item for item in result["selected_lane_chains"]
                    if item["use"] == "execute"
                )
                self.assertEqual(chain["state"], "unresolved")
                self.assertIsNotNone(chain["rejection_reason"])

    def test_superscalar_lane_mismatch_does_not_confirm_store_capture(self):
        trials = synthetic_trials()
        for index, trial in enumerate(trials):
            trial["events"] = [event for event in trial["events"] if not event["path"].endswith("mem_pc")]
            register = 3 + (index % 2)
            value = 0x5A0 + index
            cycle = trial["transactions"][0]["cycle"]
            trial["operand_expectations"] = [{
                "offset": 16, "role": "consumer",
                "rs2_register": register, "rs2_value": value, "rs2_use": "store_data",
            }]
            trial["signal_samples"] = [
                {"cycle": cycle, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.i1_rs2", "candidate_role": "source_id", "value": register},
                {"cycle": cycle, "phase": "pre_edge", "phase_order": 0,
                 "path": "dut.pipe.i1_store_data", "candidate_role": "store_data", "value": value},
            ]
        discovery = {
            "candidates": {
                "source_id": [{"path": "dut.pipe.i1_rs2", "lane_id": 1, "lane_hint": True}],
                "operand": [],
                "store_data": [{"path": "dut.pipe.i1_store_data", "lane_id": 1, "lane_hint": True}],
                "valid": [], "stall": [], "flush": [],
                "destination_id": [], "wb_data": [], "wb_enable": [],
            },
            "search_truncated": False, "visited_scopes": 1,
            "multi_lane_candidates": True,
        }
        result = classify_pipeline_interface(trials, discovery=discovery)
        self.assertFalse(result["capabilities"]["store_data_capture"])
        self.assertFalse(result["capabilities"]["lane_identity"])


if __name__ == "__main__":
    unittest.main()
