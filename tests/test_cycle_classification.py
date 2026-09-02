import unittest
import sys
import json
import os
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from src import Branch, Datapath, Forwarding
from src import _discovery_shared


class _DiscoveryModules:
    """Resolve legacy test references against their new owning module."""

    def __getattr__(self, name):
        for module in (Datapath, Forwarding, Branch, _discovery_shared):
            if hasattr(module, name):
                return getattr(module, name)
        raise AttributeError(name)


cycle = _DiscoveryModules()
from src.probe_programs import BRANCH_PREDICTION_PROBES, BRANCH_RESOLUTION_PROBES, CALIBRATION_LANDING_BASES, CYCLE_SIGNATURE, FORWARDING_PROBES, forwarding_distance_variant, forwarding_probe_pair, nested_ras_probe, pipeline_calibration_flow, pipeline_handshake_calibration, pipeline_relocation_landing, power_of_two_alias_sweep, store_to_load_hazard_probe, two_pc_alias_probe
from src.simulation import DataMemory
from src.simulation import DataMemory, ProgramMemory
from src.riscv.encoding import JAL, NOP


class FakeSignal:
    def __init__(self, value):
        self.value = value


class FakeRegfile:
    def __init__(self, values):
        self.values = [FakeSignal(value) for value in values]

    def __len__(self):
        return len(self.values)

    def __getitem__(self, index):
        return self.values[index]


class FakeHdlRegfile:
    def __init__(self, indices_to_values):
        self.range = tuple(indices_to_values)
        self.values = {
            index: FakeSignal(value)
            for index, value in indices_to_values.items()
        }

    def __len__(self):
        return len(self.values)

    def __getitem__(self, index):
        return self.values[index]


class FakeLog:
    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass


class FakeDut:
    def __init__(self):
        self._log = FakeLog()


class CycleClassificationTests(unittest.TestCase):
    def test_pipeline_calibration_has_unique_tokens_and_skipped_poison(self):
        spec = pipeline_calibration_flow(0)
        origin = spec.calibration_relocation_origin
        self.assertEqual(len(spec.instructions), len(set(spec.instructions.values())))
        self.assertEqual(
            spec.control_flow["wrong_path_offsets"], (origin + 44,),
        )
        self.assertNotIn(
            origin + 44, {item.offset for item in spec.expected_writes},
        )
        self.assertIn(
            origin + 48, {item.offset for item in spec.expected_writes},
        )
        self.assertEqual(spec.expected_store_address, 68)

    def test_pipeline_calibration_variants_change_values_not_layout(self):
        variants = [pipeline_calibration_flow(index) for index in range(3)]
        normalized_layouts = [
            {
                offset - item.calibration_relocation_origin
                for offset in item.instructions
            }
            for item in variants
        ]
        self.assertTrue(all(
            layout == normalized_layouts[0]
            for layout in normalized_layouts
        ))
        self.assertEqual(len({min(item.initial_memory) for item in variants}), 3)
        self.assertEqual(
            len({item.initial_memory[min(item.initial_memory)] for item in variants}),
            3,
        )
        self.assertEqual(len({item.expected_store_value for item in variants}), 3)
        self.assertEqual(
            len({
                item.calibration_relocation_base
                for item in variants
            }),
            3,
        )
        self.assertEqual(
            len({
                item.calibration_relocation_base % 0x100
                for item in variants
            }),
            3,
        )
        self.assertTrue(all(
            item.base_addresses == (0x40,) for item in variants
        ))

    def test_pipeline_calibration_runway_covers_reset_pc_60(self):
        spec = pipeline_calibration_flow(0, execution_base=0x98)
        image = spec.image()
        self.assertEqual(
            image[0x60], JAL(0, spec.calibration_relocation_base - 0x60),
        )
        self.assertEqual(
            image[0x98],
            spec.instructions[spec.calibration_relocation_origin],
        )
        self.assertNotEqual(image[0x98], JAL(0, 0))

    def test_relocation_landing_pool_and_unique_trampolines(self):
        self.assertEqual(
            CALIBRATION_LANDING_BASES,
            (0x40, 0x98, 0x184, 0x254, 0x34C, 0x4D8),
        )
        specs = [
            pipeline_relocation_landing(base, index)
            for index, base in enumerate(CALIBRATION_LANDING_BASES)
        ]
        self.assertEqual(
            len({item.expected_writes[-1].value for item in specs}),
            len(specs),
        )
        for spec in specs:
            image = spec.image()
            target = spec.calibration_requested_base
            self.assertEqual(spec.base_addresses, (0x40,))
            self.assertEqual(
                image[0], JAL(0, target),
            )
            self.assertEqual(
                image[target],
                spec.instructions[spec.calibration_relocation_origin],
            )

    def test_landing_allows_speculative_wrong_path_before_taken_target(self):
        spec = pipeline_relocation_landing(0x98, 1)
        origin = spec.calibration_relocation_origin
        control = spec.control_flow
        fetches = [
            {"cycle": 1, "offset": origin, "raw_pc": 0x80000098},
            {
                "cycle": 2,
                "offset": control["redirect_offset"],
                "raw_pc": 0x8000009C,
            },
            {
                "cycle": 3,
                "offset": control["wrong_path_offsets"][0],
                "raw_pc": 0x800000A0,
            },
            {
                "cycle": 4,
                "offset": control["target_offset"],
                "raw_pc": 0x800000A4,
            },
        ]
        record = Forwarding._relocation_landing_record(
            spec,
            {
                "architectural_complete": True,
                "calibration_signature": {
                    "completion_marker": {"state": "matched"},
                },
            },
            {"fetch_events": fetches},
            [],
        )
        self.assertTrue(record["accepted"])
        self.assertTrue(record["wrong_path_observed"])
        self.assertFalse(
            record["wrong_path_after_redirect_resolution"],
        )

    def test_calibration_final_signature_is_independent_of_commit_observation(self):
        spec = pipeline_calibration_flow(0)
        values = [0] * 32
        for entry in spec.expected_writes:
            values[entry.register] = entry.value
        values[17] = 0
        memory = DataMemory()
        memory.supported = True
        memory.reset(spec.initial_memory)
        memory.words[spec.expected_store_address] = spec.expected_store_value
        result = cycle._evaluate_calibration_signature(
            spec, FakeRegfile(values), {}, memory,
        )
        self.assertEqual(result["state"], "completed")
        self.assertEqual(result["memory"]["state"], "matched")

    def test_calibration_unobservable_memory_does_not_fail_register_signature(self):
        spec = pipeline_calibration_flow(1)
        values = [0] * 32
        for entry in spec.expected_writes:
            values[entry.register] = entry.value
        memory = DataMemory()
        memory.supported = False
        result = cycle._evaluate_calibration_signature(
            spec, FakeRegfile(values), {}, memory,
        )
        self.assertEqual(result["state"], "completed")
        self.assertEqual(result["memory"]["state"], "unobservable")

    def test_calibration_unreadable_nonmarker_register_reduces_coverage_only(self):
        spec = pipeline_calibration_flow(1)
        values = [0] * 32
        for entry in spec.expected_writes:
            values[entry.register] = entry.value
        regfile = FakeRegfile(values)
        regfile.values[10] = FakeSignal(None)
        memory = DataMemory()
        memory.supported = False
        result = cycle._evaluate_calibration_signature(spec, regfile, {}, memory)
        self.assertEqual(result["state"], "completed")
        self.assertEqual(result["unobservable_register_count"], 1)
        self.assertEqual(result["completion_marker"]["state"], "matched")

    def test_calibration_register_or_poison_mismatch_fails(self):
        spec = pipeline_calibration_flow(2)
        values = [0] * 32
        for entry in spec.expected_writes:
            values[entry.register] = entry.value
        values[17] = 0x6A2
        memory = DataMemory()
        memory.supported = False
        result = cycle._evaluate_calibration_signature(
            spec, FakeRegfile(values), {}, memory,
        )
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["wrong_path_poison"][0]["state"], "mismatched")

    def test_calibration_completion_and_store_failures_are_distinct(self):
        spec = pipeline_calibration_flow(0)
        good_values = [0] * 32
        for entry in spec.expected_writes:
            good_values[entry.register] = entry.value

        memory = DataMemory()
        memory.supported = True
        memory.reset(spec.initial_memory)
        memory.words[spec.expected_store_address] = (
            spec.expected_store_value ^ 1
        )
        store_failure = cycle._evaluate_calibration_signature(
            spec, FakeRegfile(good_values), {}, memory,
        )
        self.assertEqual(store_failure["state"], "failed")
        self.assertEqual(store_failure["memory"]["state"], "mismatched")

        completion_register = next(
            item.register for item in spec.expected_writes
            if item.role == "completion"
        )
        unreadable = FakeRegfile(list(good_values))
        unreadable.values[completion_register] = FakeSignal(None)
        memory.supported = False
        unavailable = cycle._evaluate_calibration_signature(
            spec, unreadable, {}, memory,
        )
        self.assertEqual(unavailable["state"], "unavailable")
        self.assertEqual(
            unavailable["completion_marker"]["state"], "unobservable",
        )

    def test_handshake_calibration_has_independent_load_and_marker(self):
        spec = pipeline_handshake_calibration(1)
        self.assertEqual(spec.calibration_kind, "handshake")
        self.assertEqual(spec.calibration_load_address, min(spec.initial_memory))
        self.assertEqual([item.role for item in spec.expected_writes][-1], "completion")

    def test_forwarding_pairs_publish_distinct_operand_metadata(self):
        dependent, control = forwarding_probe_pair("load_to_store_data", variant=1)
        dep = dependent.operand_entries()[dependent.consumer_offset]
        ctl = control.operand_entries()[control.consumer_offset]
        self.assertEqual(dep.rs2_use, "store_data")
        self.assertEqual(ctl.rs2_use, "store_data")
        self.assertNotEqual(dep.rs2_register, ctl.rs2_register)
        self.assertEqual(dep.rs1_register, 0)
        self.assertEqual(dep.rs1_value, 0)
        self.assertNotEqual(dep.rs2_value, ctl.rs2_value)
        address, _ = forwarding_probe_pair("load_to_store_address", variant=1)
        self.assertEqual(
            address.operand_entries()[address.consumer_offset].rs1_use,
            "store_address",
        )

    def test_revision7_five_variant_codebook_and_semantic_separation(self):
        names = (
            "alu_to_alu", "alu_to_store_data", "alu_to_store_address",
            "load_to_alu", "load_to_store_data",
            "load_to_store_address",
        )
        for variant, producer_register in enumerate((1, 4, 7, 10, 13)):
            for name in names:
                dependent, control = forwarding_probe_pair(
                    name, variant=variant,
                )
                dep = dependent.operand_entries()[
                    dependent.consumer_offset
                ]
                ctl = control.operand_entries()[control.consumer_offset]
                self.assertEqual(
                    dependent.forwarding_variant, variant,
                )
                dependency_side = (
                    "rs2" if name.endswith("store_data") else "rs1"
                )
                self.assertEqual(
                    getattr(dep, f"{dependency_side}_register"),
                    producer_register,
                )
                self.assertEqual(
                    getattr(ctl, f"{dependency_side}_register"),
                    producer_register + 1,
                )
                self.assertNotEqual(
                    getattr(dep, f"{dependency_side}_value"),
                    getattr(ctl, f"{dependency_side}_value"),
                )
                register_ids = {
                    producer_register,
                    producer_register + 1,
                    producer_register + 2,
                }
                semantic_values = {
                    value for observation in dependent.operand_observations
                    for value in (
                        observation.rs1_value,
                        observation.rs2_value,
                        observation.result_value,
                        observation.poison_value,
                        observation.immediate_value,
                    )
                    if value is not None
                }
                self.assertTrue(all(
                    (int(value) & 0x1F) not in register_ids
                    for value in semantic_values
                ))
                if name.endswith("store_address"):
                    self.assertNotEqual(
                        dep.immediate_value, ctl.immediate_value,
                    )
                    self.assertNotEqual(
                        dep.rs1_value, ctl.rs1_value,
                    )
                    self.assertEqual(
                        dep.effective_address, ctl.effective_address,
                    )
                    self.assertNotEqual(dep.immediate_value, 0)
                    self.assertNotEqual(ctl.immediate_value, 0)

    def test_independent_forwarding_fillers_cover_all_paths_variants_and_gaps(self):
        names = (
            "alu_to_alu", "alu_to_store_data", "alu_to_store_address",
            "load_to_alu", "load_to_store_data",
            "load_to_store_address",
        )
        for name in names:
            for variant in range(5):
                for gap in range(1, 9):
                    dependent, control = forwarding_probe_pair(
                        name, gap=gap, variant=variant,
                        spacer_kind="independent",
                    )
                    self.assertEqual(dependent.forwarding_gap, gap)
                    self.assertEqual(dependent.spacer_kind, "independent")
                    self.assertEqual(
                        dependent.filler_registers,
                        control.filler_registers,
                    )
                    self.assertEqual(
                        dependent.filler_values, control.filler_values,
                    )
                    self.assertEqual(
                        set(dependent.instructions),
                        set(control.instructions),
                    )
                    self.assertEqual(len(dependent.filler_registers), gap)
                    self.assertEqual(
                        len(set(dependent.filler_registers)), gap,
                    )
                    self.assertEqual(len(set(dependent.filler_values)), gap)
                    filler_writes = [
                        item for item in dependent.expected_writes
                        if item.role == "independent_filler"
                    ]
                    self.assertEqual(len(filler_writes), gap)
                    self.assertEqual(
                        [item.register for item in filler_writes],
                        list(dependent.filler_registers),
                    )
                    self.assertEqual(
                        [item.value for item in filler_writes],
                        list(dependent.filler_values),
                    )
                    filler_offsets = [item.offset for item in filler_writes]
                    self.assertEqual(
                        [dependent.instructions[offset]
                         for offset in filler_offsets],
                        [control.instructions[offset]
                         for offset in filler_offsets],
                    )
                    for observation in dependent.operand_observations:
                        architectural_registers = {
                            value for value in (
                                observation.rs1_register,
                                observation.rs2_register,
                                observation.destination_register,
                            )
                            if value is not None
                        }
                        semantic_values = {
                            value for value in (
                                observation.rs1_value,
                                observation.rs2_value,
                                observation.result_value,
                                observation.poison_value,
                                observation.immediate_value,
                                observation.effective_address,
                            )
                            if value is not None
                        }
                        self.assertTrue(
                            set(dependent.filler_registers).isdisjoint(
                                architectural_registers
                            )
                        )
                        self.assertTrue(
                            set(dependent.filler_values).isdisjoint(
                                semantic_values
                            )
                        )
                        self.assertTrue(
                            set(dependent.filler_registers).issubset(
                                observation.non_source_registers
                            )
                        )
                        self.assertTrue(
                            set(dependent.filler_values).issubset(
                                observation.forbidden_operand_values
                            )
                        )
                        self.assertNotIn(
                            observation.rs1_register,
                            dependent.filler_registers,
                        )
                        self.assertNotIn(
                            observation.rs2_register,
                            dependent.filler_registers,
                        )

    def test_independent_distance_policy_and_two_gap_stop(self):
        self.assertEqual(cycle._independent_sweep_limit(None), 5)
        self.assertEqual(cycle._independent_sweep_limit(1), 2)
        self.assertEqual(cycle._independent_sweep_limit(7), 8)
        self.assertEqual(cycle._independent_sweep_limit(30), 8)
        exact = [{
            "complete": True,
            "architectural_complete": True,
            "dependency_correct": True,
            "forwarding_required": False,
            "consumer_token_proof": True,
            "source_selector_validation": True,
            "operand_differential_validation": True,
            "semantic_discriminators_passed": True,
        } for _ in range(3)]
        self.assertTrue(cycle._independent_gap_settled(exact))
        consecutive, stopped = cycle._advance_independent_sweep(
            0, 1, exact,
        )
        self.assertEqual(consecutive, 1)
        self.assertFalse(stopped)
        consecutive, stopped = cycle._advance_independent_sweep(
            consecutive, 2, exact,
        )
        self.assertEqual(consecutive, 2)
        self.assertTrue(stopped)
        exact[0]["forwarding_required"] = True
        self.assertFalse(cycle._independent_gap_settled(exact))
        self.assertEqual(
            cycle._advance_independent_sweep(1, 3, exact),
            (0, False),
        )

    def test_revision7_positive_requires_independent_corroboration(self):
        def trial(required):
            return {
                "complete": True,
                "architectural_complete": True,
                "dependency_correct": True,
                "latency": 5,
                "forwarding_required": required,
                "consumer_token_proof": True,
                "source_selector_validation": True,
                "operand_differential_validation": True,
                "semantic_discriminators_passed": True,
                "stage_pc_path": "dut.ex_pc",
                "source_id_path": "dut.rs1",
                "operand_path": "dut.operand_a",
                "consumer_requirement_event": {
                    "phase": "post_edge",
                    "stage_token": {"path": "dut.ex_pc"},
                },
                "source_selector_lag": 0,
                "lane_id": 0,
                "observation_source": "dynamic_operand_capture",
                "evidence_quality": "operand_phase_correlated",
            }
        adjacent = [trial(True) for _ in range(3)]
        missing = cycle._classify_paired_forwarding(
            "alu_to_alu", adjacent, adjacent, independent={},
            pipeline_depth=4,
        )
        self.assertIsNone(missing["present"])
        self.assertEqual(
            missing["zero_delay_classification"], "possible_forwarding",
        )
        independent = {
            gap: (
                [dict(trial(False), forwarding_gap=gap,
                      spacer_kind="independent") for _ in range(3)],
                [dict(trial(False), forwarding_gap=gap,
                      spacer_kind="independent") for _ in range(3)],
            )
            for gap in (1, 2)
        }
        confirmed = cycle._classify_paired_forwarding(
            "alu_to_alu", adjacent, adjacent,
            independent=independent, pipeline_depth=4,
            sweep_policy={
                "nop_gap": 1,
                "stop_reason":
                    "two_consecutive_architecturally_available_gaps",
            },
            relaxed=(
                [dict(trial(False), latency=6) for _ in range(3)],
                [dict(trial(False), latency=5) for _ in range(3)],
            ),
        )
        self.assertTrue(confirmed["present"])
        sweep = confirmed["independent_distance_sweep"]
        self.assertEqual(sweep["tested_gaps"], [1, 2])
        self.assertEqual(
            sweep["corroboration"]["state"], "validated",
        )
        self.assertEqual(
            sweep["inferred_boundaries"][
                "first_gap_architecturally_available_before_use"
            ], 1,
        )
        self.assertTrue(
            sweep["nop_comparison"]["timing_divergence"],
        )
        self.assertEqual(
            sweep["nop_comparison"]["timing_comparison_state"],
            "comparable",
        )

        changed = {
            gap: ([dict(item) for item in pair[0]],
                  [dict(item) for item in pair[1]])
            for gap, pair in independent.items()
        }
        changed[2][0][0]["operand_path"] = "dut.other_operand"
        rejected = cycle._classify_paired_forwarding(
            "alu_to_alu", adjacent, adjacent,
            independent=changed, pipeline_depth=4,
        )
        self.assertIsNone(rejected["present"])
        self.assertFalse(
            rejected["independent_distance_sweep"][
                "corroboration"
            ]["fixed_chain"],
        )

        legacy_stage_label = dict(adjacent[0])
        legacy_stage_label["stage_pc_path"] = "dut.legacy_stage_alias"
        self.assertEqual(
            Forwarding._chain_signature(legacy_stage_label),
            Forwarding._chain_signature(adjacent[0]),
        )
        transaction_adjacent = dict(
            adjacent[0],
            stage_pc_path="dut.mem_pc",
            consumer_requirement_event={
                "phase": "pre_edge",
                "stage_token": {
                    "path": None,
                    "source": "transaction_aligned_operand_capture",
                },
            },
        )
        transaction_incremental = dict(
            transaction_adjacent,
            stage_pc_path=None,
            consumer_requirement_event={
                "phase": "pre_edge",
                "stage_token": {
                    "path": None,
                    "signal_kind":
                        "transaction_aligned_operand_capture",
                },
            },
        )
        self.assertEqual(
            Forwarding._chain_signature(transaction_adjacent),
            Forwarding._chain_signature(transaction_incremental),
        )

        unavailable_independent = {
            gap: (
                [
                    dict(
                        trial(False),
                        latency=None if index == 0 else 5,
                        forwarding_gap=gap,
                        spacer_kind="independent",
                    )
                    for index in range(3)
                ],
                [
                    dict(
                        trial(False), forwarding_gap=gap,
                        spacer_kind="independent",
                    )
                    for _ in range(3)
                ],
            )
            for gap in (1, 2)
        }
        unavailable = cycle._classify_paired_forwarding(
            "alu_to_alu", adjacent, adjacent,
            independent=unavailable_independent, pipeline_depth=4,
            sweep_policy={"nop_gap": 1},
            relaxed=(
                [dict(trial(False), latency=6) for _ in range(3)],
                [dict(trial(False), latency=5) for _ in range(3)],
            ),
        )["independent_distance_sweep"]["nop_comparison"]
        self.assertEqual(
            unavailable["timing_comparison_state"],
            "independent_timing_unavailable",
        )
        self.assertIsNone(unavailable["timing_divergence"])

        unavailable_nop = cycle._classify_paired_forwarding(
            "alu_to_alu", adjacent, adjacent,
            independent=independent, pipeline_depth=4,
            sweep_policy={"nop_gap": 1},
            relaxed=(
                [
                    dict(
                        trial(False),
                        latency=None if index == 0 else 5,
                    )
                    for index in range(3)
                ],
                [dict(trial(False), latency=5) for _ in range(3)],
            ),
        )["independent_distance_sweep"]["nop_comparison"]
        self.assertEqual(
            unavailable_nop["timing_comparison_state"],
            "nop_timing_unavailable",
        )
        self.assertIsNone(unavailable_nop["timing_divergence"])

    def test_data_memory_response_delay_configuration_restores(self):
        memory = DataMemory()
        memory.configure_response_delay(1, 65)
        self.assertEqual(memory.response_delay_cycles, 1)
        self.assertEqual(memory.response_delay_address, 64)
        memory.configure_response_delay(0)
        self.assertEqual(memory.response_delay_cycles, 0)
        self.assertIsNone(memory.response_delay_address)

    def test_data_memory_transactions_have_epoch_and_monotonic_ids(self):
        memory = DataMemory()
        memory.reset({0: 7})
        memory.read_word(0, cycle=1)
        memory.write_word(4, 9, cycle=2)
        self.assertEqual([item["epoch_id"] for item in memory.transactions], [memory.generation] * 2)
        self.assertNotEqual(
            memory.transactions[0]["transaction_id"],
            memory.transactions[1]["transaction_id"],
        )
    def test_source_grounded_forwarding_expectations_cover_adamriscv(self):
        expectation_file = Path(__file__).with_name("forwarding_source_expectations.json")
        expectations = json.loads(expectation_file.read_text(encoding="utf-8"))
        self.assertEqual(set(expectations), {
            "AdamRiscv", "RISCVPipelinedProcessor", "cv32e40p", "cve2", "mmRISC-1",
        })
        adam = expectations["AdamRiscv"]
        data = adam["behavioral_expectations"]["load_to_store_data"]
        address = adam["behavioral_expectations"]["load_to_store_address"]
        self.assertTrue(adam["structural_expectations"]["load_to_store_data"])
        self.assertEqual(data["allowed_statuses"], ["detected"])
        self.assertEqual(data["allowed_present"], [True])
        self.assertTrue(data["expected_forwarding_required"])
        self.assertEqual(
            data["maximum_raw_penalty_cycles"], 0
        )
        self.assertGreaterEqual(
            address["minimum_raw_penalty_cycles"], 1
        )
        self.assertEqual(address["allowed_present"], [False])
        self.assertEqual(set(adam["required_debug_events"]), {
            "fetch", "load_response", "store_request", "signature_commit",
        })

    def test_source_grounded_branch_expectations_cover_regression_cores(self):
        expectation_file = Path(__file__).with_name("branch_source_expectations.json")
        expectations = json.loads(expectation_file.read_text(encoding="utf-8"))
        self.assertEqual(set(expectations), {
            "Grande-Risco-5", "ZC-RISCV-CORE", "rv3n",
            "SuperScalar-RISCV-CPU", "yarvi",
            "RISCVPipelinedProcessor", "cve2",
        })
        self.assertEqual(expectations["Grande-Risco-5"]["direction"], "two_bit_saturating")
        self.assertEqual(expectations["rv3n"]["history_bits"], 5)
        self.assertEqual(expectations["yarvi"]["ras_depth"], 3)
        self.assertEqual(
            expectations["RISCVPipelinedProcessor"]["direction"],
            "local_global_tournament",
        )
        self.assertEqual(
            expectations["cve2"]["repository_optional_direction"], "static_btfnt"
        )
        self.assertEqual(expectations["cve2"]["direction"], "none_in_tested_configuration")
        self.assertFalse(expectations["cve2"]["present"])
        self.assertFalse(expectations["cve2"]["stateful"])

    def test_nested_ras_probe_has_declarative_depth_and_reachable_returns(self):
        spec = nested_ras_probe(depth=4, link_register=1, repetitions=3)
        metadata = spec.control_flow
        self.assertEqual(metadata["depth"], 4)
        self.assertEqual(len(metadata["sites"]), 4)
        for site in metadata["sites"].values():
            self.assertIn(site["offset"], spec.instructions)
            self.assertEqual(len(site["actual_targets"]), 3)
            self.assertTrue(all(target in spec.instructions for target in site["actual_targets"]))

    def test_standardized_frontend_fetch_and_redirect_are_recorded(self):
        dut = FakeDut()
        dut.probe_fetch_valid = FakeSignal(1)
        dut.probe_fetch_pc = FakeSignal(0x40)
        dut.probe_fetch_transaction = FakeSignal(7)
        dut.probe_fetch_squashed = FakeSignal(1)
        dut.probe_redirect_valid = FakeSignal(1)
        dut.probe_redirect_pc = FakeSignal(0x48)
        dut.probe_redirect_source_pc = FakeSignal(0x40)
        events, redirects = [], []

        cycle._record_probe_fetch(
            dut, 3, CYCLE_SIGNATURE, events, set(), redirect_events=redirects
        )

        self.assertEqual(events[0]["accepted_by"], "standardized_frontend")
        self.assertEqual(events[0]["transaction_id"], "7")
        self.assertTrue(events[0]["squashed"])
        self.assertEqual(redirects, [{
            "cycle": 3, "target_pc": 0x48, "source_pc": 0x40,
            "context_id": None, "epoch_id": None,
        }])

    def test_branch_resolution_pair_is_balanced_and_self_describing(self):
        taken, not_taken = BRANCH_RESOLUTION_PROBES
        for spec, expected in ((taken, True), (not_taken, False)):
            metadata = spec.control_flow
            site = metadata["sites"][metadata["primary_site"]]
            barrier = metadata["resolution_barrier"]
            self.assertEqual(metadata["family"], "branch_resolution_calibration")
            self.assertEqual(site["actual_outcomes"], (expected,))
            self.assertEqual(barrier["kind"], "dependency_load_response")
            self.assertEqual(barrier["address"], 0)
            self.assertEqual(metadata["minimum_occurrence_coverage"], 1.0)
            self.assertIn(site["offset"], spec.instructions)
            self.assertEqual(spec.loop_offset, spec.expected_writes[-1].offset + 4)
        self.assertEqual(set(taken.instructions), set(not_taken.instructions))
        self.assertNotEqual(taken.expected_writes[-1].value, not_taken.expected_writes[-1].value)

    def test_standardized_resolution_event_is_canonicalized(self):
        spec = BRANCH_RESOLUTION_PROBES[0]
        site = spec.control_flow["sites"][spec.control_flow["primary_site"]]
        dut = FakeDut()
        dut.probe_resolution_valid = FakeSignal(1)
        dut.probe_resolution_pc = FakeSignal(spec.base_addresses[0] + site["offset"])
        dut.probe_resolution_taken = FakeSignal(1)
        dut.probe_resolution_target = FakeSignal(
            spec.base_addresses[0] + site["actual_targets"][0]
        )
        dut.probe_resolution_context = FakeSignal(3)
        dut.probe_resolution_epoch = FakeSignal(8)
        events = []

        cycle._record_probe_resolution(dut, 11, spec, events)

        self.assertEqual(events[0]["offset"], site["offset"])
        self.assertEqual(events[0]["actual_target"], site["actual_targets"][0])
        self.assertEqual(events[0]["context_id"], 3)
        self.assertEqual(events[0]["epoch_id"], 8)

    def test_explicit_resolution_grades_only_strictly_earlier_fetches(self):
        site = {
            "kind": "conditional", "offset": 4, "target": 12,
            "fallthrough": 8, "targets": (12,),
            "actual_outcomes": (True,), "actual_targets": (12,), "warmup": 0,
        }
        resolution = [{
            "cycle": 3, "offset": 4, "actual_taken": True,
            "actual_target": 12, "context_id": 2, "epoch_id": 5,
        }]
        before = cycle._analyze_control_site([
            {"cycle": 1, "offset": 4, "context_id": 2, "epoch_id": 5},
            {"cycle": 2, "offset": 12, "context_id": 2, "epoch_id": 5},
        ], site, resolution_events=resolution)
        same_cycle = cycle._analyze_control_site([
            {"cycle": 1, "offset": 4, "context_id": 2, "epoch_id": 5},
            {"cycle": 3, "offset": 12, "context_id": 2, "epoch_id": 5},
        ], site, resolution_events=resolution)

        self.assertEqual(before["occurrences"][0]["evidence_grade"], "pre_resolution_accepted_fetch")
        self.assertEqual(before["occurrences"][0]["branch_to_resolution_latency"], 2)
        self.assertNotEqual(same_cycle["occurrences"][0]["evidence_grade"], "pre_resolution_accepted_fetch")

    def test_resolution_context_epoch_and_actual_result_must_match(self):
        site = {
            "kind": "conditional", "offset": 4, "target": 12,
            "fallthrough": 8, "targets": (12,),
            "actual_outcomes": (True,), "actual_targets": (12,), "warmup": 0,
        }
        fetches = [
            {"cycle": 1, "offset": 4, "context_id": 1, "epoch_id": 4},
            {"cycle": 2, "offset": 12, "context_id": 1, "epoch_id": 4},
        ]
        wrong_context = cycle._analyze_control_site(fetches, site, resolution_events=[{
            "cycle": 3, "offset": 4, "actual_taken": True,
            "actual_target": 12, "context_id": 2, "epoch_id": 4,
        }])
        wrong_result = cycle._analyze_control_site(fetches, site, resolution_events=[{
            "cycle": 3, "offset": 4, "actual_taken": False,
            "actual_target": 8, "context_id": 1, "epoch_id": 4,
        }])

        self.assertIsNone(wrong_context["occurrences"][0]["resolution_cycle"])
        self.assertTrue(wrong_result["occurrences"][0]["resolution_mismatch"])

    def test_dependency_barrier_grades_only_strictly_earlier_fetches(self):
        site = {
            "kind": "conditional", "offset": 4, "target": 12,
            "fallthrough": 8, "targets": (12,),
            "actual_outcomes": (True,), "actual_targets": (12,), "warmup": 0,
        }
        early = cycle._analyze_control_site([
            {"cycle": 1, "offset": 4}, {"cycle": 2, "offset": 12},
        ], site, dependency_barrier_cycle=3)
        late = cycle._analyze_control_site([
            {"cycle": 1, "offset": 4}, {"cycle": 3, "offset": 12},
        ], site, dependency_barrier_cycle=3)
        self.assertEqual(early["occurrences"][0]["evidence_grade"], "pre_resolution_accepted_fetch")
        self.assertNotEqual(late["occurrences"][0]["evidence_grade"], "pre_resolution_accepted_fetch")

    def test_speculation_visibility_requires_complete_calibration_pair(self):
        occurrence = {
            "evidence_grade": "pre_resolution_accepted_fetch",
            "branch_to_resolution_latency": 2,
        }
        valid = {
            "valid": True,
            "diagnostic": {"resolution_events": 1, "fetch_context_count": 1},
            "site_analysis": {"primary": {"occurrences": [occurrence]}},
        }
        invalid = {
            "valid": False,
            "diagnostic": {"failure_reason": "memory_interface_unavailable"},
            "site_analysis": {},
        }
        complete = cycle._classify_speculation_visibility([valid, valid])
        partial = cycle._classify_speculation_visibility([valid, invalid])
        self.assertTrue(complete["available"])
        self.assertEqual(complete["method"], "explicit_resolution")
        self.assertEqual(complete["resolution_latencies"], [2, 2])
        self.assertFalse(partial["available"])
        self.assertEqual(partial["failure_reason"], "calibration_pair_incomplete")

    def test_resolved_fetch_cadence_cannot_establish_history(self):
        trial = {
            "complete": True, "valid": True,
            "metadata": {"primary_site": "primary"},
            "site_analysis": {"primary": {"warmup": 0, "occurrences": [
                {
                    "correct": True, "actual_taken": index % 2 == 0,
                    "evidence_grade": "timing_only",
                }
                for index in range(20)
            ]}},
        }

        result = cycle._accuracy_capability([trial], label="global_history")

        self.assertEqual(result["status"], "not_observable")
        self.assertIsNone(result["present"])
        self.assertEqual(result["warm_predictions"], 0)

    def test_wrong_path_requires_redirect_or_squash_for_strong_evidence(self):
        site = {
            "kind": "conditional", "offset": 4, "target": 12,
            "fallthrough": 8, "actual_outcomes": (True,),
            "actual_targets": (12,), "warmup": 0,
        }
        events = [
            {"cycle": 1, "offset": 4, "context_id": 1},
            {"cycle": 2, "offset": 8, "context_id": 1},
            {"cycle": 4, "offset": 12, "context_id": 1},
        ]

        weak = cycle._analyze_control_site(events, site)
        strong = cycle._analyze_control_site(
            events, site, redirect_events=[{"cycle": 3, "context_id": 1}]
        )

        self.assertEqual(weak["occurrences"][0]["evidence_grade"], "timing_only")
        self.assertEqual(
            strong["occurrences"][0]["evidence_grade"],
            "same_context_wrong_path_then_redirect",
        )

    def test_control_reconstruction_ignores_other_fetch_contexts(self):
        site = {
            "kind": "conditional", "offset": 4, "target": 12,
            "fallthrough": 8, "actual_outcomes": (True,),
            "actual_targets": (12,), "warmup": 0,
        }
        events = [
            {"cycle": 1, "offset": 4, "context_id": 1},
            {"cycle": 2, "offset": 8, "context_id": 2},
            {"cycle": 3, "offset": 12, "context_id": 1},
        ]

        result = cycle._analyze_control_site(events, site)

        self.assertEqual(result["occurrences"][0]["predicted_target"], 12)
        self.assertEqual(result["occurrences"][0]["context_id"], 1)

    def test_redirect_is_recorded_without_a_same_cycle_fetch_accept(self):
        dut = FakeDut()
        dut.probe_fetch_valid = FakeSignal(0)
        dut.probe_fetch_pc = FakeSignal(0x40)
        dut.probe_redirect_valid = FakeSignal(1)
        dut.probe_redirect_pc = FakeSignal(0x80)
        redirects = []
        cycle._record_probe_fetch(
            dut, 5, CYCLE_SIGNATURE, [], set(), redirect_events=redirects
        )
        self.assertEqual(redirects[0]["target_pc"], 0x80)

    def test_explicit_prediction_overrides_ambiguous_fetch_path(self):
        site = {
            "kind": "conditional", "offset": 4, "fallthrough": 8,
            "target": 16, "targets": (16,), "actual_targets": (16,),
            "actual_outcomes": (True,), "warmup": 0,
        }
        fetches = [
            {"cycle": 1, "offset": 4, "transaction_id": "a"},
            {"cycle": 2, "offset": 8, "transaction_id": "b"},
            {"cycle": 2, "offset": 16, "transaction_id": "c"},
        ]
        analysis = cycle._analyze_control_site(
            fetches, site,
            [{"cycle": 1, "offset": 4, "predicted_taken": True}],
        )
        occurrence = analysis["occurrences"][0]
        self.assertTrue(occurrence["correct"])
        self.assertEqual(occurrence["prediction_source"], "standardized_prediction")

    def test_explicit_prediction_latency_is_calibrated_by_matching_pc(self):
        site = {
            "kind": "conditional", "offset": 4, "fallthrough": 8,
            "target": 16, "targets": (16,), "actual_targets": (16, 8),
            "actual_outcomes": (True, False), "warmup": 0,
        }
        fetches = [
            {"cycle": 7, "offset": 4}, {"cycle": 8, "offset": 16},
            {"cycle": 20, "offset": 4}, {"cycle": 21, "offset": 8},
        ]
        predictions = [
            {"cycle": 2, "offset": 4, "predicted_taken": True},
            {"cycle": 15, "offset": 4, "predicted_taken": False},
        ]

        analysis = cycle._analyze_control_site(fetches, site, predictions)

        self.assertEqual(analysis["prediction_latency_cycles"], 5)
        self.assertEqual(
            [item["evidence_grade"] for item in analysis["occurrences"]],
            ["explicit_prediction", "explicit_prediction"],
        )

    def test_sparse_prediction_is_not_reused_by_occurrence_index(self):
        site = {
            "kind": "conditional", "offset": 4, "fallthrough": 8,
            "target": 16, "targets": (16,), "actual_targets": (16, 16),
            "actual_outcomes": (True, True), "warmup": 0,
        }
        fetches = [
            {"cycle": 7, "offset": 4}, {"cycle": 8, "offset": 16},
            {"cycle": 20, "offset": 4}, {"cycle": 21, "offset": 16},
        ]
        predictions = [{"cycle": 2, "offset": 4, "predicted_taken": True}]

        analysis = cycle._analyze_control_site(fetches, site, predictions)

        self.assertEqual(analysis["occurrences"][0]["evidence_grade"], "explicit_prediction")
        self.assertNotEqual(analysis["occurrences"][1]["evidence_grade"], "explicit_prediction")

    def test_optional_branch_counter_delta_is_validity_gated(self):
        self.assertEqual(
            cycle._probe_counter_delta(None, {"branches": 4, "mispredicts": 1})["supported"],
            False,
        )
        evidence = cycle._probe_counter_delta(
            {"branches": 10, "mispredicts": 3},
            {"branches": 18, "mispredicts": 5},
        )
        self.assertEqual(evidence["branch_delta"], 8)
        self.assertEqual(evidence["mispredict_delta"], 2)
        self.assertTrue(evidence["valid"])

    def test_reset_retention_requires_changed_first_prediction(self):
        def trial(predicted_taken):
            return {
                "valid": True,
                "site_analysis": {"branch": {"occurrences": [{"predicted_taken": predicted_taken}]}},
            }

        detected = cycle._classify_reset_retention(
            [trial(False)], [trial(True)], [trial(True)]
        )
        stable = cycle._classify_reset_retention(
            [trial(False)], [trial(True)], [trial(False)]
        )
        self.assertTrue(detected["present"])
        self.assertFalse(stable["present"])

    def test_paired_timing_prefers_architectural_counter_evidence(self):
        def trial(cycles, misses):
            return {
                "valid": True,
                "diagnostic": {
                    "cycles_used": cycles,
                    "architectural_counters": {
                        "supported": True, "valid": True, "mispredict_delta": misses,
                    },
                },
            }

        result = cycle._classify_paired_branch_timing(
            [trial(100, 2)], [trial(100, 12)]
        )
        self.assertTrue(result["present"])
        self.assertEqual(result["counter_evidence"]["mispredict_advantage"], 10)

    def test_program_memory_selects_immutable_probe_images(self):
        memory = ProgramMemory(CYCLE_SIGNATURE)
        signature_instruction = memory.read(0x40)
        memory.select(FORWARDING_PROBES["load_to_alu"])

        self.assertNotEqual(memory.read(0x40), signature_instruction)
        self.assertEqual(memory.program.name, "load_to_alu")
        self.assertEqual(CYCLE_SIGNATURE.name, "cycle_signature")

    def test_stateful_data_memory_applies_byte_enables_and_records_transactions(self):
        memory = DataMemory()
        memory.reset({0: 0x11223344})
        memory.write_word(0, 0xAABBCCDD, byte_enable=0b0101, cycle=3)

        self.assertEqual(memory.read_word(0, cycle=4), 0x11BB33DD)
        self.assertEqual([item["kind"] for item in memory.transactions], ["store", "load"])

    def test_forwarding_programs_cover_each_dependency_type(self):
        self.assertEqual(set(FORWARDING_PROBES), {
            "alu_to_alu", "alu_to_store_data", "alu_to_store_address",
            "load_to_alu", "load_to_store_data", "load_to_store_address",
        })
        self.assertEqual(FORWARDING_PROBES["load_to_alu"].initial_memory, {0: 37})

    def test_forwarding_distance_variants_insert_requested_gap(self):
        variant = forwarding_distance_variant("load_to_alu", 2)

        self.assertEqual(variant.expected_writes[-1].offset, 24)
        self.assertEqual(variant.initial_memory, {0: 302})
        self.assertEqual(variant.name, "load_to_alu_gap_2")

    def test_paired_programs_have_matching_layouts(self):
        for name in ("alu_to_alu", "alu_to_store_data", "alu_to_store_address", "load_to_alu"):
            dependent, control = forwarding_probe_pair(name, 0)
            self.assertEqual(set(dependent.instructions), set(control.instructions))
            self.assertEqual(dependent.consumer_offset, control.consumer_offset)
            self.assertEqual(len(dependent.expected_writes), len(control.expected_writes))
            self.assertEqual(dependent.pair_role, "dependent")
            self.assertEqual(control.pair_role, "control")

    def test_probe_fetch_observer_does_not_alias_reset_pc_to_probe_base(self):
        dependent, _ = forwarding_probe_pair("alu_to_alu", 0)
        dut = FakeDut()
        dut.imem_fetch_addr = FakeSignal(0)
        events = []
        cycle._record_probe_fetch(dut, 0, dependent, events, set())
        self.assertEqual(events, [])

        dut.imem_fetch_addr.value = 0x80000044
        cycle._record_probe_fetch(dut, 7, dependent, events, set())
        self.assertEqual(events[0]["offset"], 4)
        self.assertEqual(events[0]["cycle"], 7)

    def test_probe_fetch_observer_preserves_repeated_dynamic_pc(self):
        spec = BRANCH_PREDICTION_PROBES["dynamic_one_bit"]
        dut = FakeDut()
        dut.imem_fetch_addr = FakeSignal(spec.base_addresses[0] + spec.consumer_offset)
        events = []
        seen = set()

        cycle._record_probe_fetch(dut, 4, spec, events, seen)
        cycle._record_probe_fetch(dut, 4, spec, events, seen)
        cycle._record_probe_fetch(dut, 5, spec, events, seen)

        self.assertEqual(len(events), 2)
        self.assertEqual([item["cycle"] for item in events], [4, 5])
        self.assertEqual(events[0]["accepted_by"], "direct_fetch")

    def test_large_branch_probe_uses_non_overlapping_boot_trampolines(self):
        spec = BRANCH_PREDICTION_PROBES["local_history"]
        self.assertEqual(spec.base_addresses, (0x400,))
        image = spec.image()
        for entry in (0x40, 0x80, 0x200):
            self.assertEqual(image[entry], JAL(0, 0x400 - entry))
        self.assertEqual(image[0x400 + spec.consumer_offset], spec.instructions[spec.consumer_offset])

    def test_wide_fetch_records_both_instruction_slots_as_one_transaction(self):
        spec = BRANCH_PREDICTION_PROBES["static_backward_taken"]
        dut = FakeDut()
        line_offset = spec.consumer_offset - 4
        dut.core_addr = FakeSignal(spec.base_addresses[0] + line_offset)
        dut.core_stb = FakeSignal(1)
        dut.core_ack = FakeSignal(1)
        dut.core_cyc = FakeSignal(1)
        dut.core_we = FakeSignal(0)
        dut.core_data_in_hi = FakeSignal(0)
        events = []

        cycle._record_probe_fetch(dut, 9, spec, events, set())

        self.assertEqual([item["offset"] for item in events], [line_offset, spec.consumer_offset])
        self.assertEqual(len({item["transaction_id"] for item in events}), 1)

    def test_wide_prediction_records_both_frontend_slots(self):
        spec = BRANCH_PREDICTION_PROBES["static_backward_taken"]
        low_offset = spec.consumer_offset - 4
        dut = FakeDut()
        dut.probe_prediction_valid = FakeSignal(1)
        dut.probe_prediction_pc = FakeSignal(spec.base_addresses[0] + low_offset)
        dut.probe_prediction_taken = FakeSignal(0)
        dut.probe_prediction_valid_hi = FakeSignal(1)
        dut.probe_prediction_pc_hi = FakeSignal(spec.base_addresses[0] + spec.consumer_offset)
        dut.probe_prediction_taken_hi = FakeSignal(1)
        events = []

        cycle._record_probe_prediction(dut, 12, spec, events)

        self.assertEqual([item["offset"] for item in events], [low_offset, spec.consumer_offset])
        self.assertEqual([item["predicted_taken"] for item in events], [False, True])
        self.assertEqual([item["transaction_slot"] for item in events], [0, 1])

    def test_same_wide_fetch_bundle_is_not_a_branch_path_prediction(self):
        site = {
            "kind": "conditional", "offset": 4, "target": 16,
            "fallthrough": 8, "actual_outcomes": (False,),
            "actual_targets": (8,), "warmup": 0,
        }
        events = [
            {"cycle": 1, "offset": 4, "transaction_id": "line-a"},
            {"cycle": 1, "offset": 8, "transaction_id": "line-a"},
            {"cycle": 3, "offset": 8, "transaction_id": "line-b"},
        ]

        result = cycle._analyze_control_site(events, site)

        self.assertEqual(result["occurrences"][0]["predicted_target"], 8)
        self.assertEqual(result["occurrences"][0]["path_latency"], 2)

    def test_branch_occurrences_are_bounded_by_next_branch_fetch(self):
        site = {
            "kind": "conditional", "offset": 4, "target": 12,
            "fallthrough": 8, "actual_outcomes": (True, False),
            "actual_targets": (12, 8), "warmup": 0,
        }
        events = [
            {"cycle": 1, "offset": 4}, {"cycle": 2, "offset": 8},
            {"cycle": 4, "offset": 12}, {"cycle": 5, "offset": 4},
            {"cycle": 6, "offset": 8},
        ]

        result = cycle._analyze_control_site(events, site)

        self.assertEqual(result["observed_occurrences"], 2)
        self.assertEqual(result["occurrence_coverage"], 1.0)
        self.assertFalse(result["occurrences"][0]["correct"])
        self.assertTrue(result["occurrences"][1]["correct"])

    def test_invalid_branch_trial_is_not_negative_evidence(self):
        trial = {
            "complete": False, "valid": False,
            "metadata": {"primary_site": "primary"},
            "site_analysis": {"primary": {"occurrences": [], "warmup": 0}},
        }
        result = cycle._accuracy_capability([trial], label="local")
        self.assertEqual(result["status"], "inconclusive")
        self.assertIsNone(result["present"])

    def test_partial_prediction_coverage_cannot_establish_history(self):
        occurrences = [
            {"correct": True, "actual_taken": index % 2 == 0}
            if index % 2 == 0 else
            {"correct": None, "actual_taken": index % 2 == 0}
            for index in range(20)
        ]
        trial = {
            "complete": True, "valid": True,
            "metadata": {"primary_site": "primary"},
            "site_analysis": {"primary": {"warmup": 0, "occurrences": occurrences}},
        }

        result = cycle._accuracy_capability([trial], label="local")

        self.assertEqual(result["status"], "not_observable")
        self.assertIsNone(result["present"])
        self.assertEqual(result["warm_prediction_coverage"], 0.5)

    @staticmethod
    def _hysteresis_trial(train_length, values):
        occurrences = [{"correct": value} for value in values]
        return {
            "complete": True,
            "valid": True,
            "metadata": {"primary_site": "primary", "train_length": train_length},
            "site_analysis": {"primary": {"occurrences": occurrences, "warmup": 0}},
        }

    def test_cve2_cv32e40p_and_superscalar_static_baseline_is_not_hysteresis(self):
        # cve2/cv32e40p/SCR1 regression: after taken training, an always-NT
        # baseline gets N right and the final T wrong in both probes.
        one = self._hysteresis_trial(2, [None, None, True, False])
        two = self._hysteresis_trial(2, [None, None, True, True, False])

        result = cycle._classify_counter_hysteresis([one], [two])

        self.assertEqual(result["status"], "not_detected")
        self.assertFalse(result["present"])
        self.assertEqual(result["classification"], "no_trained_direction_state")

    def test_biriscv_and_riscvpipelined_trained_transition_is_hysteresis(self):
        one = self._hysteresis_trial(2, [None, None, False, True])
        two = self._hysteresis_trial(2, [None, None, False, False, False])

        result = cycle._classify_counter_hysteresis([one], [two])

        self.assertTrue(result["present"])
        self.assertEqual(result["classification"], "two_bit_hysteresis")

    def test_rv12_and_yarvi_history_correlation_beats_bias_baseline(self):
        outcomes = [index % 2 == 0 for index in range(20)]
        occurrences = [
            {"correct": index not in (3, 17), "actual_taken": outcome}
            for index, outcome in enumerate(outcomes)
        ]
        trial = {
            "complete": True, "valid": True,
            "metadata": {"primary_site": "primary"},
            "site_analysis": {"primary": {"warmup": 0, "occurrences": occurrences}},
        }

        result = cycle._accuracy_capability(
            [trial], label="cross_branch_global_correlation"
        )

        self.assertEqual(result["status"], "detected")
        self.assertTrue(result["present"])
        self.assertGreater(result["warm_accuracy"], result["outcome_bias_baseline"])

    def test_yarvi_ras_requires_standard_link_advantage(self):
        def trial(correct_values):
            return {
                "complete": True, "valid": True,
                "metadata": {"primary_site": "primary"},
                "site_analysis": {"primary": {
                    "warmup": 0,
                    "occurrences": [{"correct": value} for value in correct_values],
                }},
            }

        result = cycle._classify_ras(
            [trial([True] * 9 + [False])],
            [trial([True] * 5 + [False] * 5)],
        )

        self.assertEqual(result["status"], "detected")
        self.assertTrue(result["present"])
        self.assertGreaterEqual(result["accuracy_advantage"], 0.2)

    def test_poor_ordinary_ras_accuracy_does_not_prove_absence(self):
        def trial(correct_values):
            return {
                "complete": True, "valid": True,
                "metadata": {"primary_site": "primary"},
                "site_analysis": {"primary": {
                    "warmup": 0,
                    "occurrences": [{"correct": value} for value in correct_values],
                }},
            }

        result = cycle._classify_ras(
            [trial([True] * 4 + [False] * 6)],
            [trial([True] * 4 + [False] * 6)],
        )

        self.assertEqual(result["status"], "inconclusive")
        self.assertIsNone(result["present"])

    def test_zc_riscv_resolved_jalr_paths_do_not_prove_indirect_prediction(self):
        def trial(correct_values):
            return {
                "complete": True, "valid": True,
                "metadata": {"primary_site": "primary"},
                "site_analysis": {"primary": {
                    "warmup": 0,
                    "occurrences": [{"correct": value} for value in correct_values],
                }},
            }

        result = cycle._classify_indirect_targets(
            [trial([True] * 8)], [trial([True] * 8)]
        )

        self.assertEqual(result["status"], "inconclusive")
        self.assertIsNone(result["present"])
        self.assertEqual(result["classification"], "resolved_target_not_distinguished")

    def test_visible_cold_jalr_miss_allows_indirect_prediction(self):
        def trial(correct_values):
            return {
                "complete": True, "valid": True,
                "metadata": {"primary_site": "primary"},
                "site_analysis": {"primary": {
                    "warmup": 1,
                    "occurrences": [{"correct": value} for value in correct_values],
                }},
            }

        result = cycle._classify_indirect_targets(
            [trial([False] + [True] * 8)], [trial([False] + [True] * 8)]
        )

        self.assertEqual(result["status"], "detected")
        self.assertTrue(result["present"])

    def test_branch_specs_produce_declarative_control_flow_metadata(self):
        for spec in BRANCH_PREDICTION_PROBES.values():
            metadata = cycle._probe_metadata(spec)
            self.assertIn("family", metadata)
            self.assertTrue(metadata["sites"])

    def test_two_pc_alias_probe_has_opposite_sites_and_requested_spacing(self):
        spec = two_pc_alias_probe(128, samples=8)
        metadata = cycle._probe_metadata(spec)

        self.assertEqual(metadata["spacing"], 128)
        self.assertEqual(metadata["sites"]["site_b"]["offset"] - metadata["sites"]["site_a"]["offset"], 128)
        self.assertTrue(all(metadata["sites"]["site_a"]["actual_outcomes"]))
        self.assertFalse(any(metadata["sites"]["site_b"]["actual_outcomes"]))

    def test_alias_sweep_uses_power_of_two_spacing(self):
        spacings = [cycle._probe_metadata(spec)["spacing"] for spec in power_of_two_alias_sweep()]
        self.assertEqual(spacings, [64, 128, 256, 512])

    def test_hierarchy_preserves_specific_dynamic_subtype(self):
        results = {
            "cold_direction_policy": {"present": True, "policy": "static_sequential"},
            "direction_hysteresis": {"present": True, "classification": "two_bit_hysteresis"},
            "pc_aliasing": {"present": True, "classification": "stateful_control_prediction_aliased", "aliasing_observed": True},
        }
        classification = cycle._hierarchical_branch_classification(results)
        self.assertEqual(classification["primary"], "two_bit_hysteresis")
        self.assertEqual(classification["direction_subtype"], "two_bit_hysteresis")

    def test_hierarchy_keeps_static_policy_detail(self):
        classification = cycle._hierarchical_branch_classification({
            "cold_direction_policy": {"present": True, "policy": "static_btfnt"},
            "direction_hysteresis": {"present": False},
            "pc_aliasing": {"present": False},
        })
        self.assertEqual(classification["primary"], "static_prediction_only")
        self.assertEqual(classification["static_policy"], "static_btfnt")

    def test_alias_classifier_falls_back_to_general_stateful_label(self):
        def trial(accuracy):
            values = [True] * int(accuracy * 20) + [False] * (20 - int(accuracy * 20))
            return {
                "complete": True, "valid": True,
                "diagnostic": {"cycles_used": 100},
                "metadata": {"primary_site": "site_a"},
                "site_analysis": {
                    "site_a": {"warmup": 4, "occurrences": [{"correct": value, "path_latency": 1} for value in values]},
                    "site_b": {"warmup": 4, "occurrences": [{"correct": value, "path_latency": 1} for value in values]},
                },
            }
        result = cycle._classify_alias_sweep({64: [trial(0.5)], 256: [trial(0.9)]})
        self.assertIsNone(result["present"])
        self.assertTrue(result["raw_stateful_interference"])
        result = cycle._classify_alias_sweep(
            {64: [trial(0.5)], 256: [trial(0.9)]},
            timing_evidence={"present": True},
        )
        self.assertTrue(result["present"])
        self.assertTrue(result["aliasing_observed"])
        self.assertEqual(result["classification"], "stateful_control_prediction_aliased")

    def test_paired_branch_timing_detects_equal_bias_learning_advantage(self):
        def trial(cycles):
            return {"valid": True, "diagnostic": {"cycles_used": cycles}}
        result = cycle._classify_paired_branch_timing(
            [trial(90), trial(91), trial(90)],
            [trial(110), trial(109), trial(110)],
        )
        self.assertTrue(result["present"])
        self.assertEqual(result["classification"], "stateful_direction_prediction_aliased_or_opaque")

    def test_hierarchy_uses_timing_only_when_specific_type_is_unknown(self):
        classification = cycle._hierarchical_branch_classification({
            "cold_direction_policy": {"present": True, "policy": "static_sequential"},
            "direction_hysteresis": {"present": None},
            "pc_aliasing": {"present": None},
            "paired_timing": {"present": True, "classification": "stateful_direction_prediction_aliased_or_opaque"},
        })
        self.assertEqual(classification["primary"], "stateful_direction_prediction_aliased_or_opaque")

    def test_paired_trials_extend_when_latency_varies(self):
        dependent = [{"complete": True, "latency": value} for value in (4, 5, 4)]
        control = [{"complete": True, "latency": 4} for _ in range(3)]
        self.assertTrue(cycle._paired_trials_need_extension(dependent, control))
        self.assertFalse(cycle._paired_trials_need_extension(control, control))

    def test_paired_trials_extend_when_overlap_or_store_signature_varies(self):
        control = [{"complete": True, "latency": 5, "producer_consumer_overlap": "overlapped"} for _ in range(3)]
        overlap = [dict(item) for item in control]
        overlap[-1]["producer_consumer_overlap"] = "same_cycle"
        self.assertTrue(cycle._paired_trials_need_extension(overlap, control))
        stores = [dict(item, observed_store={"address": 64, "value": value}) for item, value in zip(control, (1, 1, 2))]
        self.assertTrue(cycle._paired_trials_need_extension(stores, control))

    def test_paired_trials_extend_only_when_exact_chain_varies(self):
        stable = [{
            "forwarding_required": True,
            "consumer_required_stage_cycle": 3,
            "consumer_token_proof": True,
            "source_selector_validation": True,
            "operand_differential_validation": True,
            "semantic_discriminators_passed": True,
            "stage_pc_path": "dut.ex_pc",
            "source_id_path": "dut.rs1",
            "operand_path": "dut.operand_a",
            "source_selector_lag": 0,
        } for _ in range(3)]
        varying = [dict(item) for item in stable]
        varying[-1]["consumer_token_proof"] = False
        self.assertTrue(cycle._paired_stage_evidence_needs_extension(varying, stable))
        self.assertFalse(cycle._paired_stage_evidence_needs_extension(stable, stable))
        timing_only = [dict(item) for item in stable]
        timing_only[-1]["forwarding_required"] = None
        timing_only[-1]["consumer_required_stage_cycle"] = None
        self.assertFalse(
            cycle._paired_stage_evidence_needs_extension(
                timing_only, stable,
            )
        )

    def test_architectural_gap_failure_requires_monotonic_or_two_gaps(self):
        failed = [{
            "architectural_complete": False,
            "dependency_correct": False,
            "variant": variant,
            "failure_reason": "completion_marker_missing",
        } for variant in range(3)]
        record = cycle._architectural_gap_failure(failed, failed)
        self.assertEqual(
            record["category"],
            "failure_reason:completion_marker_missing",
        )
        self.assertFalse(record["monotonic"])
        monotonic = [
            dict(item, architectural_failure_monotonic=True)
            for item in failed
        ]
        self.assertTrue(
            cycle._architectural_gap_failure(
                monotonic, monotonic,
            )["monotonic"]
        )

    def test_paired_zero_penalty_detects_alu_forwarding(self):
        trials = [{
            "complete": True, "latency": 5, "forwarding_required": True,
            "observation_source": "dynamic_pipeline_stage",
            "evidence_quality": "pc_valid_or_instruction",
            "consumer_token_proof": True,
            "source_selector_validation": True,
            "operand_differential_validation": True,
            "semantic_discriminators_passed": True,
        } for _ in range(3)]
        result = cycle._classify_paired_forwarding("alu_to_alu", trials, trials)
        self.assertEqual(result["status"], "detected")
        self.assertEqual(result["raw_penalty_cycles"], 0)
        self.assertEqual(result["bypass_kind"], "alu_to_ex")

    def test_paired_positive_penalty_reports_stall_handled(self):
        dependent = [{"complete": True, "latency": 7} for _ in range(3)]
        control = [{"complete": True, "latency": 5} for _ in range(3)]
        result = cycle._classify_paired_forwarding("alu_to_store_data", dependent, control)
        self.assertEqual(result["status"], "stall_handled")
        self.assertFalse(result["present"])
        self.assertTrue(result["architectural_dependency_handled"])

    def test_load_one_cycle_interlock_is_handling_not_forwarding(self):
        dependent = [{"complete": True, "latency": 6} for _ in range(3)]
        control = [{"complete": True, "latency": 5} for _ in range(3)]
        relaxed = ([{"complete": True, "latency": 5}] * 3, [{"complete": True, "latency": 5}] * 3)
        result = cycle._classify_paired_forwarding("load_to_alu", dependent, control, relaxed)
        self.assertEqual(result["status"], "stall_handled")
        self.assertFalse(result["present"])
        self.assertIsNone(result["bypass_kind"])
        self.assertEqual(result["handling_kind"], "after_interlock")

    def test_load_to_store_address_one_cycle_interlock_is_handling(self):
        dependent = [{"complete": True, "latency": 6} for _ in range(3)]
        control = [{"complete": True, "latency": 5} for _ in range(3)]
        relaxed = ([{"complete": True, "latency": 5}] * 3, [{"complete": True, "latency": 5}] * 3)
        result = cycle._classify_paired_forwarding(
            "load_to_store_address", dependent, control, relaxed
        )
        self.assertEqual(result["status"], "stall_handled")
        self.assertFalse(result["present"])
        self.assertIsNone(result["bypass_kind"])
        self.assertEqual(result["handling_kind"], "after_interlock")

    def test_load_to_store_data_penalty_is_stall_handled(self):
        dependent = [{"complete": True, "latency": 6} for _ in range(3)]
        control = [{"complete": True, "latency": 5} for _ in range(3)]
        result = cycle._classify_paired_forwarding(
            "load_to_store_data", dependent, control
        )
        self.assertEqual(result["status"], "stall_handled")

    def test_adamriscv_load_store_data_and_address_regression(self):
        # AdamRiscv has an explicit WB-load -> MEM-store-data path and exempts
        # that dependency from its ordinary load-use stall. Store address still
        # takes the normal one-cycle interlock.
        data_dependent = [
            {
                "complete": True, "architectural_complete": True,
                "dependency_correct": True, "transaction_observable": True,
                "latency": 5, "forwarding_required": True,
                "observation_source": "dynamic_pipeline_stage",
                "evidence_quality": "pc_valid_or_instruction",
                "consumer_token_proof": True,
                "source_selector_validation": True,
                "operand_differential_validation": True,
                "semantic_discriminators_passed": True,
            }
            for _ in range(3)
        ]
        data_control = [dict(item) for item in data_dependent]
        data_result = cycle._classify_paired_forwarding(
            "load_to_store_data", data_dependent, data_control
        )
        self.assertEqual(data_result["status"], "detected")
        self.assertEqual(data_result["bypass_kind"], "load_to_store_data")

        address_dependent = [dict(item, latency=6) for item in data_dependent]
        address_control = [dict(item, latency=5) for item in data_dependent]
        relaxed = (
            [dict(item, latency=5) for item in data_dependent],
            [dict(item, latency=5) for item in data_dependent],
        )
        address_result = cycle._classify_paired_forwarding(
            "load_to_store_address", address_dependent, address_control, relaxed
        )
        self.assertEqual(address_result["status"], "stall_handled")
        self.assertFalse(address_result["present"])
        self.assertIsNone(address_result["bypass_kind"])
        self.assertEqual(address_result["handling_kind"], "after_interlock")

    def test_asymmetric_address_only_synthetic_behavior(self):
        base = [{
            "complete": True, "architectural_complete": True,
            "dependency_correct": True, "transaction_observable": True,
            "producer_consumer_overlap": "overlapped", "latency": 5,
            "forwarding_required": True,
            "observation_source": "dynamic_pipeline_stage",
            "evidence_quality": "pc_valid_or_instruction",
            "consumer_token_proof": True,
            "source_selector_validation": True,
            "operand_differential_validation": True,
            "semantic_discriminators_passed": True,
        } for _ in range(3)]
        data = cycle._classify_paired_forwarding(
            "load_to_store_data", [dict(item, latency=6) for item in base], base,
            ([dict(item) for item in base], [dict(item) for item in base]),
        )
        address = cycle._classify_paired_forwarding(
            "load_to_store_address", base, [dict(item) for item in base],
            ([dict(item) for item in base], [dict(item) for item in base]),
        )
        self.assertFalse(data["present"])
        self.assertEqual(data["status"], "stall_handled")
        self.assertTrue(address["present"])
        self.assertEqual(address["bypass_kind"], "load_to_store_address_zero_stall")

    def test_synthetic_both_store_paths_interlocked(self):
        control = [{"complete": True, "latency": 5} for _ in range(3)]
        dependent = [{"complete": True, "latency": 7} for _ in range(3)]
        for name in ("load_to_store_data", "load_to_store_address"):
            result = cycle._classify_paired_forwarding(name, dependent, control)
            self.assertEqual(result["status"], "stall_handled")
            self.assertFalse(result["present"])
            self.assertIsNone(result["bypass_kind"])

    def test_producer_available_before_consumer_does_not_claim_absence(self):
        dependent = [{
            "complete": True, "latency": 5,
            "producer_consumer_overlap": "producer_available_before_consumer",
            "forwarding_required": False,
            "observation_source": "dynamic_pipeline_stage",
            "evidence_quality": "pc_valid_or_instruction",
        } for _ in range(3)]
        control = [{"complete": True, "latency": 5} for _ in range(3)]
        result = cycle._classify_paired_forwarding("alu_to_alu", dependent, control)
        self.assertEqual(result["status"], "inconclusive")
        self.assertIsNone(result["present"])
        self.assertIsNone(result["bypass_kind"])
        self.assertEqual(
            result["zero_delay_classification"], "forwarding_not_required"
        )
        self.assertIn("already architecturally available", result["evidence"])

    def test_zero_penalty_without_consumer_stage_proof_is_unknown(self):
        trials = [{
            "complete": True, "latency": 5,
            "forwarding_required": None,
            "observation_source": "fetch_commit_fallback",
            "evidence_quality": "fetch_commit_only",
        } for _ in range(3)]
        result = cycle._classify_paired_forwarding("alu_to_alu", trials, trials)
        self.assertEqual(result["status"], "inconclusive")
        self.assertIsNone(result["present"])
        self.assertTrue(result["zero_delay_behavior_observed"])
        self.assertEqual(
            result["zero_delay_classification"], "possible_forwarding"
        )
        self.assertEqual(result["confidence"], 0.55)
        self.assertEqual(
            result["requirement_missing_proofs"], ["operand_capture"]
        )

    def test_confirmed_zero_delay_has_explicit_classification(self):
        trials = [{
            "complete": True, "latency": 5,
            "forwarding_required": True,
            "observation_source": "dynamic_operand_capture",
            "evidence_quality": "operand_phase_correlated",
            "consumer_token_proof": True,
            "source_selector_validation": True,
            "operand_differential_validation": True,
            "semantic_discriminators_passed": True,
        } for _ in range(3)]
        result = cycle._classify_paired_forwarding("alu_to_alu", trials, trials)
        self.assertTrue(result["present"])
        self.assertEqual(
            result["zero_delay_classification"], "confirmed_forwarding"
        )

    def test_rejected_path_role_cannot_confirm_forwarding(self):
        trials = [{
            "complete": True,
            "latency": 5,
            "forwarding_required": True,
            "path_role_evidence_state": "rejected",
            "aggregate_role_evidence_state": "rejected",
            "observation_source": "dynamic_operand_capture",
            "evidence_quality": "operand_phase_correlated",
        } for _ in range(3)]
        result = cycle._classify_paired_forwarding(
            "alu_to_alu", trials, trials,
        )
        self.assertEqual(result["status"], "inconclusive")
        self.assertIsNone(result["present"])
        self.assertEqual(
            result["zero_delay_classification"], "possible_forwarding",
        )
        self.assertIn(
            "operand_capture", result["requirement_missing_proofs"],
        )

    def test_stage_pc_timing_alone_cannot_prove_operand_requirement(self):
        interface = {
            "stages": [{
                "normalized_role": "execute", "pc_path": "dut.ex_pc",
                "valid_path": "dut.ex_valid", "instruction_path": None,
                "evidence_quality": "pc_valid_or_instruction",
            }],
            "trial_observations": {
                "before": {"execute": {"16": 3}},
                "after": {"execute": {"16": 7}},
                "same": {"execute": {"16": 5}},
            },
        }
        outcomes = {}
        for trial_id in ("before", "after", "same"):
            trial = {
                "pipeline_trial_id": trial_id,
                "consumer_offset": 16,
                "producer_available_cycle": 5,
            }
            outcomes[trial_id] = cycle._enrich_forwarding_requirement(
                "load_to_store_address", trial, interface
            )["forwarding_required"]
        self.assertTrue(all(value is None for value in outcomes.values()))

    def test_store_data_pc_observation_retains_memory_role_but_not_requirement_proof(self):
        interface = {
            "stages": [{
                "normalized_role": "memory", "pc_path": "dut.mem_pc",
                "valid_path": None, "instruction_path": "dut.mem_insn",
                "evidence_quality": "pc_valid_or_instruction",
            }],
            "trial_observations": {"trial": {"memory": {"16": 4}}},
        }
        trial = {
            "pipeline_trial_id": "trial", "consumer_offset": 16,
            "producer_available_cycle": 6,
        }
        result = cycle._enrich_forwarding_requirement(
            "load_to_store_data", trial, interface
        )
        self.assertEqual(result["consumer_required_stage"], "memory")
        self.assertIsNone(result["forwarding_required"])

    def test_operand_pre_edge_before_same_cycle_writeback_proves_requirement(self):
        interface = {
            "state": "confirmed",
            "stages": [{
                "normalized_role": "memory", "pc_path": "dut.mem_pc",
                "evidence_quality": "operand_phase_correlated",
            }],
            "trial_observations": {"trial": {"memory": {"16": 8}}},
            "requirement_observations": {"trial": {"store_data": {
                "cycle": 9, "phase": "pre_edge", "phase_order": 0,
                "path": "dut.store_data", "source_id_path": "dut.rs2_mem", "value": 61,
            }}},
            "producer_availability_observations": {"trial": {
                "cycle": 9, "phase": "post_edge", "phase_order": 1,
                "source": "register_storage_transition",
            }},
        }
        trial = {
            "pipeline_trial_id": "trial", "consumer_offset": 16,
            "producer_available_cycle": 9,
        }
        result = cycle._enrich_forwarding_requirement("load_to_store_data", trial, interface)
        self.assertTrue(result["forwarding_required"])
        self.assertEqual(result["same_cycle_ordering"], "consumer_before_writeback")
        self.assertEqual(result["observation_source"], "dynamic_operand_capture")
        self.assertEqual(result["operand_path"], "dut.store_data")

    def test_operand_and_writeback_same_phase_remain_ambiguous(self):
        interface = {
            "state": "confirmed",
            "stages": [{"normalized_role": "execute", "pc_path": "dut.ex_pc"}],
            "trial_observations": {"trial": {"execute": {"16": 8}}},
            "requirement_observations": {"trial": {"execute": {
                "cycle": 9, "phase": "post_edge", "phase_order": 1,
                "path": "dut.operand", "value": 10,
            }}},
            "producer_availability_observations": {"trial": {
                "cycle": 9, "phase": "post_edge", "phase_order": 1,
            }},
        }
        result = cycle._enrich_forwarding_requirement(
            "alu_to_alu",
            {"pipeline_trial_id": "trial", "consumer_offset": 16, "producer_available_cycle": 9},
            interface,
        )
        self.assertIsNone(result["forwarding_required"])
        self.assertEqual(result["same_cycle_ordering"], "same_phase_ambiguous")

    def test_same_cycle_overlap_is_inconclusive(self):
        dependent = [{
            "complete": True, "latency": 5,
            "producer_consumer_overlap": "same_cycle",
        } for _ in range(3)]
        control = [{"complete": True, "latency": 5} for _ in range(3)]
        result = cycle._classify_paired_forwarding("alu_to_alu", dependent, control)
        self.assertIsNone(result["present"])
        self.assertEqual(result["status"], "inconclusive")

    def test_negative_raw_penalty_is_inconclusive(self):
        dependent = [{"complete": True, "latency": 4} for _ in range(3)]
        control = [{"complete": True, "latency": 5} for _ in range(3)]
        result = cycle._classify_paired_forwarding("alu_to_alu", dependent, control)
        self.assertIsNone(result["present"])
        self.assertIsNone(result["bypass_kind"])
        self.assertIn("lower", result["evidence"])

    def test_load_to_store_latency_uses_store_request(self):
        spec, _ = forwarding_probe_pair("load_to_store_data")
        latency = cycle._trial_latency(
            "load_to_store_data",
            spec,
            [{"cycle": 4, "offset": spec.consumer_offset}],
            [],
            [{
                "cycle": 8, "kind": "store",
                "address": spec.expected_store_address,
                "value": spec.expected_store_value,
            }],
        )
        self.assertEqual(latency, 4)

    def test_missing_store_observation_is_inconclusive_not_failure(self):
        dependent = [{
            "complete": True,
            "architectural_complete": True,
            "dependency_correct": False,
            "transaction_observable": False,
            "observed_store": None,
            "latency": None,
        } for _ in range(5)]
        control = [{
            "complete": True,
            "architectural_complete": True,
            "dependency_correct": True,
            "transaction_observable": True,
            "observed_store": {"address": 64, "value": 61},
            "latency": 5,
        } for _ in range(5)]

        result = cycle._classify_paired_forwarding(
            "load_to_store_data", dependent, control
        )

        self.assertEqual(result["status"], "inconclusive")
        self.assertIsNone(result["present"])
        self.assertTrue(all(result["dependent_program_completion"]))
        self.assertIn("not observable", result["evidence"])

    def test_stable_observable_wrong_store_can_be_not_detected(self):
        dependent = [{
            "complete": True,
            "architectural_complete": True,
            "dependency_correct": False,
            "transaction_observable": True,
            "observed_store": {"address": 64, "value": 0},
            "latency": None,
        } for _ in range(5)]
        control = [{
            "complete": True,
            "architectural_complete": True,
            "dependency_correct": True,
            "transaction_observable": True,
            "observed_store": {"address": 64, "value": 61},
            "latency": 5,
        } for _ in range(5)]

        result = cycle._classify_paired_forwarding(
            "load_to_store_data", dependent, control
        )

        self.assertEqual(result["status"], "not_detected")
        self.assertFalse(result["present"])
        self.assertTrue(result["absence_evidence_validated"])
        self.assertIn("observable incorrect store", result["evidence"])

    def test_fetched_store_stably_dropped_after_load_can_be_not_detected(self):
        dependent = [{
            "complete": True,
            "architectural_complete": True,
            "dependency_correct": False,
            "transaction_observable": False,
            "store_absence_architecturally_observable": True,
            "observed_store": None,
            "latency": None,
        } for _ in range(5)]
        control = [{
            "complete": True,
            "architectural_complete": True,
            "dependency_correct": True,
            "transaction_observable": True,
            "store_absence_architecturally_observable": False,
            "observed_store": {"address": 64, "value": 61},
            "latency": 5,
        } for _ in range(5)]
        relaxed = (
            [{
                "complete": True, "architectural_complete": True,
                "dependency_correct": True, "transaction_observable": True,
                "latency": 5,
            } for _ in range(3)],
            [{
                "complete": True, "architectural_complete": True,
                "dependency_correct": True, "transaction_observable": True,
                "latency": 5,
            } for _ in range(3)],
        )

        result = cycle._classify_paired_forwarding(
            "load_to_store_data", dependent, control, relaxed
        )

        self.assertEqual(result["status"], "not_detected")
        self.assertTrue(result["absence_evidence_validated"])
        self.assertTrue(result["relaxed_dependency_handled"])
        self.assertEqual(result["relaxed_raw_penalty_cycles"], 0)
        self.assertIn("stably dropped", result["evidence"])

    def test_forwarding_event_trace_keeps_all_observation_classes(self):
        trace = cycle._forwarding_event_trace(
            [{"cycle": 1, "offset": 4}],
            [{"cycle": 4, "offset": 8, "role": "completion"}],
            [
                {"cycle": 2, "kind": "load", "address": 0, "value": 61},
                {"cycle": 3, "kind": "store", "address": 64, "value": 61},
            ],
        )
        self.assertEqual([item["event"] for item in trace], [
            "fetch", "load_response", "store_request", "signature_commit",
        ])

    def test_unstable_final_timing_is_inconclusive(self):
        dependent = [{"complete": True, "latency": value} for value in (4, 6, 5, 4, 6)]
        control = [{"complete": True, "latency": 4} for _ in range(5)]
        result = cycle._classify_paired_forwarding("alu_to_alu", dependent, control)
        self.assertEqual(result["status"], "inconclusive")
        self.assertFalse(result["timing_stable"])

    def test_missing_relaxed_timing_does_not_erase_stable_adjacent_evidence(self):
        zero = [{
            "complete": True, "latency": 5, "forwarding_required": True,
            "observation_source": "dynamic_pipeline_stage",
            "evidence_quality": "pc_only",
            "consumer_token_proof": True,
            "source_selector_validation": True,
            "operand_differential_validation": True,
            "semantic_discriminators_passed": True,
        } for _ in range(3)]
        missing = ([{"complete": True, "latency": None}] * 5, [{"complete": True, "latency": None}] * 5)
        forwarded = cycle._classify_paired_forwarding("alu_to_alu", zero, zero, missing)
        self.assertEqual(forwarded["status"], "detected")
        self.assertTrue(forwarded["present"])
        self.assertFalse(forwarded["relaxed_timing_stable"])

        stalled = cycle._classify_paired_forwarding(
            "load_to_alu", [dict(item, latency=6) for item in zero], zero, missing
        )
        self.assertEqual(stalled["status"], "stall_handled")
        self.assertFalse(stalled["present"])
        self.assertEqual(stalled["handling_kind"], "interlock_or_stall")
        self.assertIsNone(stalled["bypass_kind"])

    def test_store_to_load_is_labeled_memory_ordering(self):
        result = {"category": "memory_ordering", "register_forwarding_test": False}
        self.assertEqual(result["category"], "memory_ordering")
        self.assertFalse(result["register_forwarding_test"])

    def test_store_to_load_program_is_not_a_forwarding_probe(self):
        spec = store_to_load_hazard_probe()
        self.assertNotIn("store_to_load", FORWARDING_PROBES)
        self.assertEqual(spec.dependency_kind, "memory_ordering_hazard")

    def test_store_to_load_hazard_uses_architectural_completion(self):
        result = cycle._classify_store_to_load_hazard(
            {"complete": True},
            {"present": False, "transaction_distance": -1, "memory_transactions": []},
        )
        self.assertEqual(result["status"], "handled")
        self.assertTrue(result["architectural_dependency_handled"])
        self.assertFalse(result["external_transaction_order_observed"])
        self.assertFalse(result["true_store_to_load_forwarding_observable"])

    def test_store_forwarding_pairs_do_not_contain_verification_loads(self):
        for name in ("alu_to_store_data", "alu_to_store_address"):
            dependent, control = forwarding_probe_pair(name)
            for spec in (dependent, control):
                opcodes = {instruction & 0x7F for instruction in spec.instructions.values()}
                self.assertNotIn(0x03, opcodes)
                self.assertIsNotNone(spec.expected_store_address)
                self.assertIsNotNone(spec.expected_store_value)

    def test_forwarding_pairs_poison_producer_and_use_matched_layouts(self):
        for name in (
            "alu_to_alu", "alu_to_store_data", "alu_to_store_address",
            "load_to_alu", "load_to_store_data", "load_to_store_address",
        ):
            dependent, control = forwarding_probe_pair(name, gap=2, variant=1)
            self.assertEqual(set(dependent.instructions), set(control.instructions))
            self.assertEqual(dependent.producer_offset, control.producer_offset)
            self.assertEqual(dependent.consumer_offset, control.consumer_offset)
            differing_offsets = {
                offset for offset in dependent.instructions
                if dependent.instructions[offset] != control.instructions[offset]
            }
            self.assertEqual(differing_offsets, {dependent.consumer_offset})
            self.assertEqual(
                dependent.instructions[dependent.producer_offset],
                control.instructions[control.producer_offset],
            )
            self.assertEqual(dependent.initial_memory, control.initial_memory)
            self.assertEqual(
                dependent.expected_writes[0], control.expected_writes[0]
            )
            self.assertEqual(
                dependent.expected_store_address, control.expected_store_address
            )
            if name.endswith("store_data"):
                self.assertNotEqual(
                    dependent.expected_store_value,
                    control.expected_store_value,
                )
            else:
                self.assertEqual(
                    dependent.expected_store_value,
                    control.expected_store_value,
                )
            self.assertLess(0, dependent.producer_offset)
            producer_register = (
                dependent.operand_entries()[
                    dependent.producer_offset
                ].destination_register
            )
            poison = dependent.instructions[0]
            self.assertEqual((poison >> 7) & 0x1F, producer_register)

    def test_store_pairs_seed_destination_sentinels(self):
        for name in (
            "alu_to_store_data", "alu_to_store_address",
            "load_to_store_data", "load_to_store_address",
        ):
            dependent, control = forwarding_probe_pair(name)
            self.assertIn(dependent.expected_store_address, dependent.initial_memory)
            self.assertIn(control.expected_store_address, control.initial_memory)

    def test_compact_experiments_retain_audit_evidence(self):
        trial = {
            "complete": True, "architectural_complete": True,
            "dependency_correct": True, "latency": 5,
            "producer_consumer_overlap": "overlapped",
            "producer_available_cycle": 4, "consumer_fetch_cycle": 2,
            "consumer_effect_cycle": 7, "store_request_cycle": 7,
            "observed_store": {"address": 64, "value": 61},
        }
        result = cycle._classify_paired_forwarding(
            "load_to_store_data", [trial] * 3, [trial] * 3
        )
        compact = result["experiments"]["adjacent"]["dependent"][0]
        self.assertEqual(compact["producer_consumer_overlap"], "overlapped")
        self.assertEqual(compact["store_request_cycle"], 7)
        self.assertEqual(compact["observed_store"], {"address": 64, "value": 61})

    def test_store_address_pair_uses_x0_as_store_data(self):
        dependent, control = forwarding_probe_pair("alu_to_store_address")
        for spec in (dependent, control):
            instruction = spec.instructions[spec.consumer_offset]
            self.assertEqual((instruction >> 20) & 0x1F, 0)

    def test_load_to_store_data_pair_isolates_store_data(self):
        dependent, control = forwarding_probe_pair("load_to_store_data")
        dep_store = dependent.instructions[dependent.consumer_offset]
        ctl_store = control.instructions[control.consumer_offset]
        self.assertEqual((dep_store >> 20) & 0x1F, 1)
        self.assertEqual((ctl_store >> 20) & 0x1F, 2)
        self.assertEqual(((dep_store >> 15) & 0x1F), 0)
        self.assertEqual(dependent.expected_store_address, 128)

    def test_load_to_store_address_pair_isolates_store_address(self):
        dependent, control = forwarding_probe_pair("load_to_store_address")
        dep_store = dependent.instructions[dependent.consumer_offset]
        ctl_store = control.instructions[control.consumer_offset]
        self.assertEqual((dep_store >> 20) & 0x1F, 0)
        self.assertEqual((ctl_store >> 20) & 0x1F, 0)
        self.assertEqual((dep_store >> 15) & 0x1F, 1)
        self.assertEqual((ctl_store >> 15) & 0x1F, 2)

    def test_adjacent_alu_distance_variant_detects_zero_stall_forwarding(self):
        spec = forwarding_distance_variant("alu_to_alu", 0)
        commits = [
            {"cycle": 5, "offset": 0, "role": "producer"},
            {"cycle": 6, "offset": 4, "role": "dependent"},
        ]

        result = cycle._classify_forwarding_probe(spec, commits, None, 0, 5)

        self.assertTrue(result["present"])
        self.assertEqual(result["stall_cycles"], 0)

    def test_memory_probe_is_inconclusive_without_transaction_interface(self):
        spec = forwarding_distance_variant("alu_to_store_data", 0)
        commits = [
            {"cycle": 5, "offset": 0, "role": "producer"},
            {"cycle": 7, "offset": 8, "role": "verification"},
        ]
        memory = DataMemory()
        memory.supported = False

        result = cycle._classify_forwarding_probe(spec, commits, memory, 0, 5)

        self.assertIsNone(result["present"])
        self.assertEqual(result["status"], "inconclusive")
        self.assertIn("unavailable", result["reason"])

    def test_store_data_probe_does_not_treat_request_timing_as_absence_evidence(self):
        spec = forwarding_distance_variant("alu_to_store_data", 0)
        commits = [
            {"cycle": 5, "offset": 0, "role": "producer"},
            {"cycle": 7, "offset": 8, "role": "verification"},
        ]
        memory = DataMemory()
        memory.supported = True
        memory.transactions = [
            {"cycle": 16, "kind": "store", "address": 0, "value": 51},
            {"cycle": 17, "kind": "load", "address": 0, "value": 51},
        ]

        result = cycle._classify_forwarding_probe(spec, commits, memory, 10, 5)

        self.assertIsNone(result["present"])
        self.assertEqual(result["status"], "inconclusive")
        self.assertTrue(result["architectural_dependency_handled"])
        self.assertEqual(result["store_request_relative_to_producer_commit"], 1)

    def test_distance_sweep_subtracts_fixed_structural_delay(self):
        classified = {
            gap: {
                "present": False,
                "status": "not_detected",
                "stall_cycles": 1,
            }
            for gap in range(4)
        }

        result = cycle._summarize_forwarding_distance_sweep(
            "alu_to_alu", classified, 5
        )

        self.assertTrue(result["present"])
        self.assertEqual(result["status"], "detected")
        self.assertEqual(result["structural_stall_floor"], 1)
        self.assertEqual(result["raw_dependency_penalty"], 0)

    def test_distance_sweep_preserves_dependency_specific_negative_result(self):
        classified = {
            gap: {
                "present": False,
                "status": "not_detected",
                "stall_cycles": stalls,
            }
            for gap, stalls in enumerate((4, 3, 2, 1))
        }

        result = cycle._summarize_forwarding_distance_sweep(
            "alu_to_alu", classified, 5
        )

        self.assertFalse(result["present"])
        self.assertEqual(result["raw_dependency_penalty"], 3)
        self.assertEqual(result["raw_dependency_penalty_sweep"], [3, 2, 1, 0])

    def test_load_use_probe_reports_forwarded_one_cycle_bubble(self):
        spec = forwarding_distance_variant("load_to_alu", 0)
        commits = [
            {"cycle": 5, "offset": 0, "role": "producer"},
            {"cycle": 7, "offset": 4, "role": "dependent"},
        ]

        result = cycle._classify_forwarding_probe(spec, commits, None, 0, 5)

        self.assertTrue(result["present"])
        self.assertEqual(result["stall_cycles"], 1)

    def test_alu_forwarding_classifier_reports_bubbles(self):
        spec = FORWARDING_PROBES["alu_to_alu"]
        commits = [
            {"cycle": cycle_number, "offset": item.offset, "role": item.role}
            for cycle_number, item in zip((0, 1, 2, 4, 6, 8), spec.expected_writes)
        ]

        result = cycle._classify_forwarding_probe(spec, commits, None, 0, 5)

        self.assertFalse(result["present"])
        self.assertEqual(result["dependent_commit_intervals"], [2, 2, 2])
        self.assertEqual(result["stall_cycles"], 3)

    def test_bit_sliced_regfile_gets_bit_serial_measurement_budget(self):
        self.assertEqual(cycle._measurement_cycle_budget({"kind": "bit_sliced_array"}), 2000)
        self.assertEqual(cycle._measurement_cycle_budget({"kind": "array_of_words"}), 300)

    def test_cycle_program_overwrites_prior_regfile_probe_loop(self):
        self.assertEqual(cycle.prog[0x20], cycle.NOP_INSTRUCTION)
        self.assertEqual(cycle.prog[0x2C], cycle.NOP_INSTRUCTION)

    def test_forwarding_probe_is_only_enabled_for_positive_pipeline_result(self):
        self.assertTrue(cycle._is_pipeline_classification({"depth_estimate": 5}))
        self.assertFalse(cycle._is_pipeline_classification(False))
        self.assertFalse(cycle._is_pipeline_classification(None))

    def test_forwarding_probe_is_a_chain_of_immediate_raw_dependencies(self):
        expected = [(entry["reg"], entry["value"]) for entry in cycle.HAZARD_WRITE_TEMPLATE]
        self.assertEqual(expected, [
            (1, 10), (2, 20), (3, 30), (4, 20),
            (5, 50), (6, 51),
        ])
        for base_pc in cycle.HAZARD_BASE_PCS:
            self.assertEqual(cycle.hazard_prog[base_pc + 0x20], cycle._jal(0, 0))

    def test_relocated_program_address_serves_signature_instruction(self):
        self.assertEqual(
            cycle._cycle_program_instruction(0x1040),
            cycle._addi(5, 0, 0x135),
        )

    def test_boot_offset_program_address_serves_signature_instruction(self):
        self.assertEqual(
            cycle._cycle_program_instruction(0xC0),
            cycle._addi(5, 0, 0x135),
        )

    def test_relocated_fetch_pc_is_recorded_canonically(self):
        dut = FakeDut()
        dut.imem_fetch_addr = FakeSignal(0x1044)
        fetch_events = []
        seen_fetch_pcs = set()

        cycle._record_signature_fetch(dut, 0, fetch_events, seen_fetch_pcs)

        self.assertEqual(fetch_events, [
            {"cycle": -1, "pc": 0x40},
            {"cycle": 0, "pc": 0x44},
        ])
        self.assertEqual(seen_fetch_pcs, {0x40, 0x44})

    def test_boot_offset_fetch_pc_is_recorded_canonically(self):
        dut = FakeDut()
        dut.imem_fetch_addr = FakeSignal(0xC0)
        fetch_events = []
        seen_fetch_pcs = set()

        cycle._record_signature_fetch(dut, 0, fetch_events, seen_fetch_pcs)

        self.assertEqual(fetch_events, [{"cycle": 0, "pc": 0x40}])

    def test_signature_commit_is_deduplicated_across_address_aliases(self):
        first = cycle._signature_entry_for(
            5,
            0x135,
            fetched_pcs={0x40},
            seen_commit_pcs=set(),
        )
        duplicate = cycle._signature_entry_for(
            5,
            0x135,
            fetched_pcs={0x40},
            seen_commit_pcs={first["pc"]},
        )

        self.assertEqual(first["pc"], 0x40)
        self.assertIsNone(duplicate)

    def test_signature_program_is_served_at_rv3n_reset_base(self):
        entry = cycle.SIGNATURE_BY_PC[0x200]

        self.assertEqual(entry["reg"], 5)
        self.assertEqual(cycle.prog[0x200], cycle._addi(5, 0, 0x135))
        self.assertEqual(cycle.prog[0x230], cycle._jal(0, 0))
        self.assertEqual(
            cycle._signature_entry_for(
                5,
                0x135,
                fetched_pcs={0x200},
                seen_commit_pcs=set(),
            )["pc"],
            0x200,
        )

    def test_signature_program_is_reachable_from_nonzero_low_reset_vector(self):
        self.assertEqual(cycle.prog[0x70], cycle.NOP_INSTRUCTION)
        self.assertEqual(cycle.prog[0x80], cycle._addi(5, 0, 0x135))
        self.assertEqual(cycle.prog[0xB0], cycle._jal(0, 0))

    def test_signature_fetch_backfills_prior_same_base_pcs(self):
        dut = FakeDut()
        dut.core_addr = FakeSignal(0x204)
        dut.core_cyc = FakeSignal(1)
        dut.core_stb = FakeSignal(1)
        dut.core_ack = FakeSignal(1)
        dut.core_we = FakeSignal(0)
        fetch_events = []
        seen_fetch_pcs = set()

        cycle._record_signature_fetch(dut, 0, fetch_events, seen_fetch_pcs)

        self.assertEqual(fetch_events, [
            {"cycle": -1, "pc": 0x200},
            {"cycle": 0, "pc": 0x204},
        ])
        self.assertEqual(seen_fetch_pcs, {0x200, 0x204})

    def test_pipeline_classification_uses_modal_latency_plus_one(self):
        fetches = [{"pc": pc, "cycle": i} for i, pc in enumerate(range(0, 24, 4))]
        commits = [
            {"pc": pc, "cycle": i + 4, "reg": 5 + i, "value": 0x100 + i}
            for i, pc in enumerate(range(0, 24, 4))
        ]

        compact, debug = cycle._build_cycle_measurement(fetches, commits, method="interface")

        self.assertEqual(compact["fetch_to_commit_latencies"], [4, 4, 4, 4, 4, 4])
        self.assertEqual(compact["commit_intervals"], [1, 1, 1, 1, 1])
        self.assertEqual(compact["fetch_intervals"], [1, 1, 1, 1, 1])
        self.assertEqual(
            compact["classification"]["pipeline"],
            {"depth_estimate": 5, "depth_estimate_source": "write_interface"},
        )
        self.assertFalse(compact["classification"]["single_cycle"])
        self.assertFalse(compact["classification"]["multicycle"])
        self.assertEqual(compact["classification"]["confidence"], 0.91)
        self.assertEqual(debug["depth_estimate"], 5)
        self.assertEqual(
            sorted(compact.keys()),
            ["classification", "commit_intervals", "fetch_intervals", "fetch_to_commit_latencies"],
        )
        self.assertIn("paired_events", debug)
        self.assertIn("confidence_penalties", debug)
        self.assertEqual(debug["commit_observation_offset"], 0)
        self.assertEqual(debug["raw_fetch_to_commit_latencies"], [4, 4, 4, 4, 4, 4])
        self.assertEqual(debug["corrected_fetch_to_commit_latencies"], [4, 4, 4, 4, 4, 4])

    def test_regfile_observation_uses_raw_storage_latency(self):
        fetches = [{"pc": pc, "cycle": i} for i, pc in enumerate(range(0, 24, 4))]
        commits = [
            {"pc": pc, "cycle": i + 3, "reg": 5 + i, "value": 0x500 + i}
            for i, pc in enumerate(range(0, 24, 4))
        ]

        compact, debug = cycle._build_cycle_measurement(fetches, commits, method="regfile_observation")

        self.assertEqual(compact["fetch_to_commit_latencies"], [3, 3, 3, 3, 3, 3])
        self.assertEqual(
            compact["classification"]["pipeline"],
            {
                "depth_estimate": 4,
                "depth_estimate_source": "regfile_observation",
            },
        )
        self.assertEqual(debug["commit_observation_offset"], 0)
        self.assertEqual(debug["raw_fetch_to_commit_latencies"], [3, 3, 3, 3, 3, 3])
        self.assertEqual(debug["corrected_fetch_to_commit_latencies"], [3, 3, 3, 3, 3, 3])

    def test_interface_timing_offset_corrects_depth_estimate(self):
        fetches = [{"pc": pc, "cycle": i} for i, pc in enumerate(range(0, 24, 4))]
        commits = [
            {"pc": pc, "cycle": i + 5, "reg": 5 + i, "value": 0x600 + i}
            for i, pc in enumerate(range(0, 24, 4))
        ]

        compact, debug = cycle._build_cycle_measurement(
            fetches,
            commits,
            method="interface",
            commit_observation_offset=-1,
        )

        self.assertEqual(compact["fetch_to_commit_latencies"], [4, 4, 4, 4, 4, 4])
        self.assertEqual(
            compact["classification"]["pipeline"],
            {
                "depth_estimate": 5,
                "depth_estimate_source": "write_interface_timing_corrected",
                "raw_depth_estimate": 6,
            },
        )
        self.assertEqual(debug["commit_observation_offset"], -1)
        self.assertEqual(debug["raw_fetch_to_commit_latencies"], [5, 5, 5, 5, 5, 5])
        self.assertEqual(debug["corrected_fetch_to_commit_latencies"], [4, 4, 4, 4, 4, 4])

    def test_regfile_observation_latency_one_can_be_registered_single_cycle(self):
        fetches = [{"pc": pc, "cycle": 15 + i} for i, pc in enumerate(range(0x40, 0x58, 4))]
        commits = [
            {"pc": pc, "cycle": 17 + i, "reg": 5 + i, "value": 0x700 + i}
            for i, pc in enumerate(range(0x40, 0x58, 4))
        ]

        compact, debug = cycle._build_cycle_measurement(
            fetches,
            commits,
            method="regfile_observation",
            interface_incomplete=True,
        )

        self.assertEqual(compact["fetch_to_commit_latencies"], [2, 2, 2, 2, 2, 2])
        self.assertTrue(compact["classification"]["single_cycle"])
        self.assertFalse(compact["classification"]["multicycle"])
        self.assertFalse(compact["classification"]["pipeline"])
        self.assertIn("registered instruction delivery", debug["classification_reason"])

    def test_single_cycle_classification_requires_zero_latency(self):
        fetches = [{"pc": pc, "cycle": i} for i, pc in enumerate(range(0, 16, 4))]
        commits = [
            {"pc": pc, "cycle": i, "reg": 5 + i, "value": 0x200 + i}
            for i, pc in enumerate(range(0, 16, 4))
        ]

        compact, _ = cycle._build_cycle_measurement(fetches, commits, method="interface")

        self.assertTrue(compact["classification"]["single_cycle"])
        self.assertFalse(compact["classification"]["multicycle"])
        self.assertFalse(compact["classification"]["pipeline"])

    def test_multicycle_classification_uses_commit_intervals_not_fetch_intervals(self):
        fetches = [{"pc": pc, "cycle": i} for i, pc in enumerate(range(0, 16, 4))]
        commits = [
            {"pc": pc, "cycle": i * 3 + 5, "reg": 5 + i, "value": 0x300 + i}
            for i, pc in enumerate(range(0, 16, 4))
        ]

        compact, _ = cycle._build_cycle_measurement(fetches, commits, method="interface")

        self.assertEqual(compact["fetch_intervals"], [1, 1, 1])
        self.assertEqual(compact["commit_intervals"], [3, 3, 3])
        self.assertFalse(compact["classification"]["single_cycle"])
        self.assertTrue(compact["classification"]["multicycle"])
        self.assertFalse(compact["classification"]["pipeline"])

    def test_spaced_commits_with_stable_latency_remain_multicycle(self):
        fetches = [
            {"pc": pc, "cycle": 80 + i * 5}
            for i, pc in enumerate(range(0x40, 0x58, 4))
        ]
        commits = [
            {"pc": pc, "cycle": 86 + i * 5, "reg": 5 + i, "value": 0x300 + i}
            for i, pc in enumerate(range(0x40, 0x58, 4))
        ]

        compact, debug = cycle._build_cycle_measurement(fetches, commits, method="interface")

        self.assertEqual(compact["fetch_intervals"], [5, 5, 5, 5, 5])
        self.assertEqual(compact["commit_intervals"], [5, 5, 5, 5, 5])
        self.assertEqual(compact["fetch_to_commit_latencies"], [6, 6, 6, 6, 6, 6])
        self.assertFalse(compact["classification"]["single_cycle"])
        self.assertTrue(compact["classification"]["multicycle"])
        self.assertFalse(compact["classification"]["pipeline"])
        self.assertEqual(
            debug["classification_reason"],
            "architectural commits are spaced by multiple cycles",
        )

    def test_unstable_latency_is_ambiguous_with_lower_confidence(self):
        fetches = [{"pc": pc, "cycle": i} for i, pc in enumerate(range(0, 16, 4))]
        commits = [
            {"pc": 0x00, "cycle": 4, "reg": 5, "value": 0x401},
            {"pc": 0x04, "cycle": 5, "reg": 6, "value": 0x402},
            {"pc": 0x08, "cycle": 6, "reg": 7, "value": 0x403},
            {"pc": 0x0C, "cycle": 7, "reg": 8, "value": 0x404},
        ]
        fetches[2]["cycle"] = 1

        compact, debug = cycle._build_cycle_measurement(fetches, commits, method="interface")

        self.assertIsNone(compact["classification"]["single_cycle"])
        self.assertIsNone(compact["classification"]["multicycle"])
        self.assertIsNone(compact["classification"]["pipeline"])
        self.assertLess(compact["classification"]["confidence"], 0.91)
        self.assertTrue(debug["unstable_latency"])

    def test_single_boundary_bubble_uses_dominant_cadence(self):
        fetches = [
            {"pc": pc, "cycle": cycle_number}
            for pc, cycle_number in zip(range(0x40, 0x58, 4), (10, 11, 12, 13, 14, 15))
        ]
        commits = [
            {"pc": pc, "cycle": cycle_number, "reg": 5 + index, "value": 0x500 + index}
            for index, (pc, cycle_number) in enumerate(
                zip(range(0x40, 0x58, 4), (10, 11, 12, 13, 14, 16))
            )
        ]

        compact, debug = cycle._build_cycle_measurement(fetches, commits, method="interface")

        self.assertTrue(compact["classification"]["single_cycle"])
        self.assertEqual(compact["commit_intervals"], [1, 1, 1, 1, 2])
        self.assertTrue(debug["mixed_commit_intervals"])
        self.assertTrue(debug["unstable_latency"])

    def test_same_cycle_commit_bursts_are_pipeline_evidence(self):
        fetches = [
            {"pc": pc, "cycle": fetch_cycle}
            for pc, fetch_cycle in zip(range(0x40, 0x58, 4), (10, 10, 11, 11, 12, 12))
        ]
        commits = [
            {"pc": pc, "cycle": commit_cycle, "reg": 5 + index, "value": 0x600 + index}
            for index, (pc, commit_cycle) in enumerate(
                zip(range(0x40, 0x58, 4), (15, 15, 16, 16, 17, 17))
            )
        ]

        compact, debug = cycle._build_cycle_measurement(fetches, commits, method="interface")

        self.assertFalse(compact["classification"]["single_cycle"])
        self.assertFalse(compact["classification"]["multicycle"])
        self.assertTrue(compact["classification"]["pipeline"]["superscalar_commit_evidence"])
        self.assertIn(0, compact["commit_intervals"])
        self.assertIn("multiple architectural commits", debug["classification_reason"])

    def test_variable_but_always_spaced_commits_are_multicycle(self):
        fetches = [
            {"pc": pc, "cycle": fetch_cycle}
            for pc, fetch_cycle in zip(range(0x40, 0x58, 4), (10, 45, 80, 115, 150, 185))
        ]
        commits = [
            {"pc": pc, "cycle": commit_cycle, "reg": 5 + index, "value": 0x700 + index}
            for index, (pc, commit_cycle) in enumerate(
                zip(range(0x40, 0x58, 4), (24, 59, 94, 149, 166, 201))
            )
        ]

        compact, debug = cycle._build_cycle_measurement(fetches, commits, method="regfile_observation")

        self.assertTrue(compact["classification"]["multicycle"])
        self.assertTrue(all(interval > 1 for interval in compact["commit_intervals"]))
        self.assertIn("consistently spaced", debug["classification_reason"])

    def test_regfile_storage_index_supports_x0_omitted_files(self):
        regfile = FakeRegfile([100 + index for index in range(31)])
        metadata = {"depth": 31}

        self.assertIsNone(cycle._regfile_storage_index(0, metadata, regfile))
        self.assertEqual(cycle._regfile_storage_index(1, metadata, regfile), 0)
        self.assertEqual(cycle._regfile_storage_index(31, metadata, regfile), 30)
        self.assertEqual(cycle._get_regfile_reg_value(regfile, 5, metadata), 104)

    def test_regfile_storage_index_preserves_hdl_declared_indices(self):
        regfile = FakeHdlRegfile({index: index * 100 for index in range(1, 32)})
        metadata = {"depth": 31, "mapping_order": "direct"}

        self.assertIsNone(cycle._regfile_storage_index(0, metadata, regfile))
        self.assertEqual(cycle._regfile_storage_index(1, metadata, regfile), 1)
        self.assertEqual(cycle._regfile_storage_index(31, metadata, regfile), 31)
        self.assertEqual(cycle._get_regfile_reg_value(regfile, 5, metadata), 500)

    def test_regfile_storage_index_applies_selected_adjacent_mapping(self):
        regfile = FakeHdlRegfile({index: index * 100 for index in range(32)})

        plus_metadata = {"depth": 32, "mapping_order": "physical_index_plus_1"}
        minus_metadata = {"depth": 32, "mapping_order": "physical_index_minus_1"}

        self.assertEqual(cycle._regfile_storage_index(5, plus_metadata, regfile), 6)
        self.assertEqual(cycle._get_regfile_reg_value(regfile, 5, plus_metadata), 600)
        self.assertEqual(cycle._regfile_storage_index(5, minus_metadata, regfile), 4)
        self.assertEqual(cycle._get_regfile_reg_value(regfile, 5, minus_metadata), 400)

    def test_current_rejected_interface_blocks_legacy_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_file = Path(temp_dir) / "AUK-V-Aethia_reg_file.json"
            metadata_file.write_text(json.dumps({
                "regfile_interface": {
                    "write_enable": None,
                    "write_addr": None,
                    "write_data": None,
                },
                "selected_regfile_interface": {
                    "status": "rejected_interface",
                    "write_enable": None,
                    "write_addr": None,
                    "write_data": None,
                },
            }), encoding="utf-8")

            with mock.patch.dict(os.environ, {"OUTPUT_DIR": temp_dir}):
                with mock.patch.object(cycle, "load_regfile_interface", return_value={
                    "write_enable": "processorci_top.Processor.RF0.i_we",
                    "write_addr": "processorci_top.Processor.RF0.i_rd_addr",
                    "write_data": "processorci_top.Processor.RF0.i_rd_data",
                }) as load_cached:
                    handles = cycle._resolve_write_interface(FakeDut(), "AUK-V-Aethia", None)

            self.assertIsNone(handles)
            load_cached.assert_not_called()

    def test_current_derived_interface_blocks_legacy_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_file = Path(temp_dir) / "core_reg_file.json"
            metadata_file.write_text(json.dumps({
                "regfile_interface": {
                    "write_enable": "__storage_update_event__",
                    "write_addr": "processorci_top.Processor.DPTR",
                    "write_data": "__storage_update_value__",
                },
                "selected_regfile_interface": {
                    "status": "likely_interface",
                    "write_enable": "__storage_update_event__",
                    "write_addr": "processorci_top.Processor.DPTR",
                    "write_data": "__storage_update_value__",
                },
            }), encoding="utf-8")

            with mock.patch.dict(os.environ, {"OUTPUT_DIR": temp_dir}):
                with mock.patch.object(cycle, "load_regfile_interface", return_value={
                    "write_enable": "legacy.we",
                    "write_addr": "legacy.rd",
                    "write_data": "legacy.data",
                }) as load_cached:
                    handles = cycle._resolve_write_interface(FakeDut(), "core", None)

            self.assertIsNone(handles)
            load_cached.assert_not_called()

    def test_current_interface_preserves_selected_timing_offset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_file = Path(temp_dir) / "RISC-V_reg_file.json"
            metadata_file.write_text(json.dumps({
                "regfile_interface": {
                    "write_enable": "processorci_top.Processor.we",
                    "write_addr": "processorci_top.Processor.rd",
                    "write_data": "processorci_top.Processor.wdata",
                },
                "selected_regfile_interface": {
                    "status": "confirmed_interface",
                    "write_enable": "processorci_top.Processor.we",
                    "write_addr": "processorci_top.Processor.rd",
                    "write_data": "processorci_top.Processor.wdata",
                    "timing_offset": -1,
                    "write_enable_timing_offset": -1,
                    "write_addr_timing_offset": 0,
                    "write_data_timing_offset": 0,
                },
            }), encoding="utf-8")

            with mock.patch.dict(os.environ, {"OUTPUT_DIR": temp_dir}):
                state, interface = cycle._current_regfile_interface_state("RISC-V")

            self.assertEqual(state, "usable")
            self.assertEqual(interface["timing_offset"], -1)
            self.assertEqual(interface["write_enable_timing_offset"], -1)
            self.assertEqual(interface["write_addr_timing_offset"], 0)
            self.assertEqual(interface["write_data_timing_offset"], 0)

    def test_interface_samples_align_independent_role_offsets(self):
        samples = {
            9: {"write_enable": 1, "write_addr": 4, "write_data": 0x44},
            10: {"write_enable": 0, "write_addr": 5, "write_data": 0x55},
        }

        aligned = cycle._aligned_interface_values(
            samples,
            reference_cycle=10,
            reference_offset=0,
            role_offsets={
                "write_enable": -1,
                "write_addr": 0,
                "write_data": 0,
            },
        )

        self.assertEqual(aligned, {
            "write_enable": 1,
            "write_addr": 5,
            "write_data": 0x55,
        })

    def test_interface_alignment_supports_future_role_sample(self):
        samples = {
            10: {"write_enable": 0, "write_addr": 5, "write_data": 0x55},
            11: {"write_enable": 1, "write_addr": 6, "write_data": 0x66},
        }

        aligned = cycle._aligned_interface_values(
            samples,
            reference_cycle=10,
            reference_offset=-1,
            role_offsets={
                "write_enable": 0,
                "write_addr": -1,
                "write_data": -1,
            },
        )

        self.assertEqual(aligned, {
            "write_enable": 1,
            "write_addr": 5,
            "write_data": 0x55,
        })

    def test_regfile_storage_index_supports_full_32_entry_files(self):
        regfile = FakeRegfile([200 + index for index in range(32)])
        metadata = {"depth": 32}

        self.assertEqual(cycle._regfile_storage_index(0, metadata, regfile), 0)
        self.assertEqual(cycle._regfile_storage_index(5, metadata, regfile), 5)
        self.assertEqual(cycle._get_regfile_reg_value(regfile, 5, metadata), 205)


if __name__ == "__main__":
    unittest.main()
