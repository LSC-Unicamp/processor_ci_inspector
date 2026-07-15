import unittest
import sys
import json
import os
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from src import cycle
from src.probe_programs import CYCLE_SIGNATURE, FORWARDING_PROBES, forwarding_distance_variant, forwarding_probe_pair
from src.simulation import DataMemory, ProgramMemory


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
            "load_to_alu", "store_to_load",
        })
        self.assertEqual(FORWARDING_PROBES["load_to_alu"].initial_memory, {0: 37})

    def test_forwarding_distance_variants_insert_requested_gap(self):
        variant = forwarding_distance_variant("load_to_alu", 2)

        self.assertEqual(variant.expected_writes[-1].offset, 12)
        self.assertEqual(variant.initial_memory, {0: 39})
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

    def test_paired_trials_extend_when_latency_varies(self):
        dependent = [{"complete": True, "latency": value} for value in (4, 5, 4)]
        control = [{"complete": True, "latency": 4} for _ in range(3)]
        self.assertTrue(cycle._paired_trials_need_extension(dependent, control))
        self.assertFalse(cycle._paired_trials_need_extension(control, control))

    def test_paired_zero_penalty_detects_alu_forwarding(self):
        trials = [{"complete": True, "latency": 5} for _ in range(3)]
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

    def test_load_one_cycle_interlock_is_detected_with_relaxed_pair(self):
        dependent = [{"complete": True, "latency": 6} for _ in range(3)]
        control = [{"complete": True, "latency": 5} for _ in range(3)]
        relaxed = ([{"complete": True, "latency": 5}] * 3, [{"complete": True, "latency": 5}] * 3)
        result = cycle._classify_paired_forwarding("load_to_alu", dependent, control, relaxed)
        self.assertEqual(result["status"], "detected")
        self.assertEqual(result["bypass_kind"], "load_to_ex_after_interlock")

    def test_unstable_final_timing_is_inconclusive(self):
        dependent = [{"complete": True, "latency": value} for value in (4, 6, 5, 4, 6)]
        control = [{"complete": True, "latency": 4} for _ in range(5)]
        result = cycle._classify_paired_forwarding("alu_to_alu", dependent, control)
        self.assertEqual(result["status"], "inconclusive")
        self.assertFalse(result["timing_stable"])

    def test_store_to_load_is_labeled_memory_ordering(self):
        result = {"category": "memory_ordering", "register_forwarding_test": False}
        self.assertEqual(result["category"], "memory_ordering")
        self.assertFalse(result["register_forwarding_test"])

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
