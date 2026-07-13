import unittest
import sys
import json
import os
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from src import cycle


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


class FakeLog:
    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass


class FakeDut:
    def __init__(self):
        self._log = FakeLog()


class CycleClassificationTests(unittest.TestCase):
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

    def test_regfile_storage_index_supports_x0_omitted_files(self):
        regfile = FakeRegfile([100 + index for index in range(31)])
        metadata = {"depth": 31}

        self.assertIsNone(cycle._regfile_storage_index(0, metadata, regfile))
        self.assertEqual(cycle._regfile_storage_index(1, metadata, regfile), 0)
        self.assertEqual(cycle._regfile_storage_index(31, metadata, regfile), 30)
        self.assertEqual(cycle._get_regfile_reg_value(regfile, 5, metadata), 104)

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
                },
            }), encoding="utf-8")

            with mock.patch.dict(os.environ, {"OUTPUT_DIR": temp_dir}):
                state, interface = cycle._current_regfile_interface_state("RISC-V")

            self.assertEqual(state, "usable")
            self.assertEqual(interface["timing_offset"], -1)

    def test_regfile_storage_index_supports_full_32_entry_files(self):
        regfile = FakeRegfile([200 + index for index in range(32)])
        metadata = {"depth": 32}

        self.assertEqual(cycle._regfile_storage_index(0, metadata, regfile), 0)
        self.assertEqual(cycle._regfile_storage_index(5, metadata, regfile), 5)
        self.assertEqual(cycle._get_regfile_reg_value(regfile, 5, metadata), 205)


if __name__ == "__main__":
    unittest.main()
