import unittest
import sys
import tempfile
from pathlib import Path
from unittest import mock

from src import regfile_finder_protoype_2 as finder

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import cocotb_makefile_creator


class FakeSignal:
    def __init__(self, path, width=1, handle_type="GPI_REGISTER", value=0):
        self._path = path
        self._type = handle_type
        self.value = value
        self._width = width

    def __len__(self):
        return self._width


class FakeArray:
    def __init__(self, path, elements, handle_type="GPI_ARRAY"):
        self._path = path
        self._type = handle_type
        self._elements = list(elements)
        self.range = range(len(self._elements))

    def __len__(self):
        return len(self._elements)

    def __getitem__(self, index):
        return self._elements[index]


class FakeModule:
    def __init__(self, path, **children):
        self._path = path
        self._type = "GPI_MODULE"
        self._children = children
        for name, child in children.items():
            setattr(self, name, child)

    def __dir__(self):
        return sorted(set(super().__dir__()) | set(self._children))


class Phase1DiscoveryTests(unittest.TestCase):
    def test_discovers_unpacked_array_of_words(self):
        elements = [FakeSignal(f"dut.core.regs.{i}", 32) for i in range(32)]
        dut = FakeModule("dut", core=FakeModule("dut.core", regs=FakeArray("dut.core.regs", elements)))

        candidates = finder.discover_regfile_array_candidates(dut)

        self.assertTrue(any(c["kind"] == "array_of_words" and c["path"] == "dut.core.regs" for c in candidates))

    def test_discovers_packed_flat_vector(self):
        dut = FakeModule("dut", core=FakeModule("dut.core", regs=FakeSignal("dut.core.regs", 1024)))

        candidates = finder.discover_regfile_array_candidates(dut)

        self.assertTrue(any(c["kind"] == "packed_flat_vector" and c["path"] == "dut.core.regs" for c in candidates))

    def test_discovers_same_scope_vector_group(self):
        regs = {f"x{i}": FakeSignal(f"dut.core.rf.x{i}", 32) for i in range(32)}
        dut = FakeModule("dut", core=FakeModule("dut.core", rf=FakeModule("dut.core.rf", **regs)))

        candidates = finder.discover_regfile_array_candidates(dut)
        vector_group = next(c for c in candidates if c["kind"] == "vector_group")

        self.assertEqual(vector_group["scope"], "dut.core.rf")
        self.assertEqual(vector_group["depth"], 32)
        self.assertEqual(vector_group["word_width"], 32)
        self.assertEqual(len(vector_group["members"]), 32)

    def test_discovers_x1_to_x31_vector_group(self):
        regs = {f"gpr_{i}": FakeSignal(f"dut.core.rf.gpr_{i}", 64) for i in range(1, 32)}
        dut = FakeModule("dut", core=FakeModule("dut.core", rf=FakeModule("dut.core.rf", **regs)))

        candidates = finder.discover_regfile_array_candidates(dut)
        vector_group = next(c for c in candidates if c["kind"] == "vector_group")

        self.assertEqual(vector_group["depth"], 31)
        self.assertEqual(vector_group["word_width"], 64)
        self.assertEqual(vector_group["members"][0]["reg_index"], 1)

    def test_discovers_scalar_bit_cluster(self):
        bits = {}
        for reg_index in range(32):
            for bit_index in range(32):
                name = f"x{reg_index}_b{bit_index}"
                bits[name] = FakeSignal(f"dut.core.bits.{name}", 1)
        dut = FakeModule("dut", core=FakeModule("dut.core", bits=FakeModule("dut.core.bits", **bits)))

        candidates = finder.discover_regfile_array_candidates(dut)
        bit_cluster = next(c for c in candidates if c["kind"] == "scalar_bit_cluster")

        self.assertEqual(bit_cluster["scope"], "dut.core.bits")
        self.assertEqual(bit_cluster["depth"], 32)
        self.assertEqual(bit_cluster["word_width"], 32)
        self.assertEqual(len(bit_cluster["members"]), 1024)

    def test_name_scoring_prefers_register_names_over_memory_names(self):
        reg_score, _ = finder._path_name_score("dut.core.regfile.regs")
        mem_score, _ = finder._path_name_score("dut.core.dcache.mem")

        self.assertGreater(reg_score, mem_score)


class Phase2VisibilityTests(unittest.TestCase):
    def test_visible_array_candidate(self):
        elements = [FakeSignal(f"dut.core.regs.{i}", 32) for i in range(32)]
        dut = FakeModule("dut", core=FakeModule("dut.core", regs=FakeArray("dut.core.regs", elements)))
        candidate = {
            "path": "dut.core.regs",
            "kind": "array_of_words",
            "sample_indices": [0, 1, 31],
        }

        annotated = finder.check_candidate_visibility(dut, candidate)

        self.assertTrue(annotated["visible"])
        self.assertEqual(annotated["visibility_status"], "visible")

    def test_visible_packed_vector_candidate(self):
        dut = FakeModule("dut", core=FakeModule("dut.core", regs=FakeSignal("dut.core.regs", 1024)))
        candidate = {
            "path": "dut.core.regs",
            "kind": "packed_flat_vector",
        }

        annotated = finder.check_candidate_visibility(dut, candidate)

        self.assertTrue(annotated["visible"])
        self.assertEqual(annotated["visibility_status"], "visible")

    def test_visible_vector_group_candidate(self):
        regs = {f"x{i}": FakeSignal(f"dut.core.rf.x{i}", 32) for i in range(32)}
        dut = FakeModule("dut", core=FakeModule("dut.core", rf=FakeModule("dut.core.rf", **regs)))
        candidate = {
            "path": "dut.core.rf.x",
            "kind": "vector_group",
            "members": [
                {"path": f"dut.core.rf.x{i}", "name": f"x{i}", "handle_type": "GPI_REGISTER", "width": 32}
                for i in range(32)
            ],
        }

        annotated = finder.check_candidate_visibility(dut, candidate)

        self.assertTrue(annotated["visible"])
        self.assertEqual(annotated["visibility_status"], "visible")

    def test_missing_member_candidate_is_partial(self):
        regs = {"x0": FakeSignal("dut.core.rf.x0", 32)}
        dut = FakeModule("dut", core=FakeModule("dut.core", rf=FakeModule("dut.core.rf", **regs)))
        candidate = {
            "path": "dut.core.rf.x",
            "kind": "vector_group",
            "members": [
                {"path": "dut.core.rf.x0", "name": "x0", "handle_type": "GPI_REGISTER", "width": 32},
                {"path": "dut.core.rf.x1", "name": "x1", "handle_type": "GPI_REGISTER", "width": 32},
            ],
        }

        annotated = finder.check_candidate_visibility(dut, candidate)

        self.assertFalse(annotated["visible"])
        self.assertEqual(annotated["visibility_status"], "partial")


class Phase3ProgramTests(unittest.TestCase):
    def test_program_generation_has_loop_and_expected_registers(self):
        metadata = finder.build_regfile_write_program()

        self.assertEqual(metadata["program"][metadata["loop_pc"]], finder._jal(0, 0))
        self.assertTrue(all(addr % 4 == 0 for addr in metadata["program"]))
        self.assertEqual(metadata["expected_registers"]["x0"], 0)
        self.assertIn("x1", metadata["written_registers"])
        self.assertEqual(metadata["expected_registers"]["x8"], 0x12345678)

    def test_verilator_makefile_contains_visibility_flags(self):
        config = {
            "include_dirs": [],
            "files": [],
            "top_module": "core_top",
            "language_version": "1800-2012",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            makefile_path = Path(temp_dir) / "core.mk"
            makefile_path.write_text("", encoding="utf-8")

            with mock.patch.object(cocotb_makefile_creator, "load_config", return_value=config):
                cocotb_makefile_creator.standard_makefile(
                    "core",
                    "SystemVerilog",
                    "config",
                    temp_dir,
                    str(makefile_path),
                    "/cores/core",
                )

            makefile_text = makefile_path.read_text(encoding="utf-8")
            self.assertIn("--public-flat-rw", makefile_text)
            self.assertIn("--trace-structs", makefile_text)
            self.assertIn("--trace-underscore", makefile_text)


class Phase4SamplingTests(unittest.TestCase):
    def test_samples_array_candidate_by_register_index(self):
        elements = [FakeSignal(f"dut.core.regs.{i}", 32, value=i + 10) for i in range(32)]
        dut = FakeModule("dut", core=FakeModule("dut.core", regs=FakeArray("dut.core.regs", elements)))
        candidate = {"path": "dut.core.regs", "kind": "array_of_words", "depth": 32}

        values = finder.sample_candidate_value(dut, candidate)

        self.assertEqual(values["x1"], 11)
        self.assertEqual(values["x31"], 41)

    def test_samples_vector_group_by_member_register_index(self):
        regs = {f"x{i}": FakeSignal(f"dut.core.rf.x{i}", 32, value=i * 3) for i in range(4)}
        dut = FakeModule("dut", core=FakeModule("dut.core", rf=FakeModule("dut.core.rf", **regs)))
        candidate = {
            "path": "dut.core.rf.x",
            "kind": "vector_group",
            "members": [
                {"path": f"dut.core.rf.x{i}", "reg_index": i, "handle_type": "GPI_REGISTER", "width": 32}
                for i in range(4)
            ],
        }

        values = finder.sample_candidate_value(dut, candidate)

        self.assertEqual(values["x2"], 6)

    def test_reconstructs_scalar_bit_cluster_words(self):
        bits = {}
        members = []
        for reg_index, word in [(0, 0), (1, 0b1010)]:
            for bit_index in range(4):
                name = f"x{reg_index}_b{bit_index}"
                bits[name] = FakeSignal(f"dut.core.bits.{name}", 1, value=(word >> bit_index) & 1)
                members.append({
                    "path": f"dut.core.bits.{name}",
                    "reg_index": reg_index,
                    "bit_index": bit_index,
                    "handle_type": "GPI_REGISTER",
                    "width": 1,
                })
        dut = FakeModule("dut", core=FakeModule("dut.core", bits=FakeModule("dut.core.bits", **bits)))
        candidate = {
            "path": "dut.core.bits.x",
            "kind": "scalar_bit_cluster",
            "word_width": 4,
            "members": members,
        }

        values = finder.sample_candidate_value(dut, candidate)

        self.assertEqual(values["x1"], 0b1010)

    def test_decodes_packed_vector_in_both_orders(self):
        raw = (0x11 << 8) | 0x22
        dut = FakeModule("dut", core=FakeModule("dut.core", regs=FakeSignal("dut.core.regs", 16, value=raw)))
        candidate = {
            "path": "dut.core.regs",
            "kind": "packed_flat_vector",
            "depth": 2,
            "word_width": 8,
        }

        values = finder.sample_candidate_value(dut, candidate)

        self.assertEqual(values["raw"], raw)
        self.assertEqual(values["packed_lsb_reg0"]["x0"], 0x22)
        self.assertEqual(values["packed_msb_reg0"]["x0"], 0x11)


def _trace_for_values(values_by_cycle, kind="array_of_words", candidate_path="dut.core.regs"):
    samples = []
    for cycle, values in enumerate(values_by_cycle):
        samples.append({
            "cycle": cycle,
            "pc": 0x2C if cycle >= len(values_by_cycle) - 3 else cycle * 4,
            "in_loop": cycle >= len(values_by_cycle) - 3,
            "values": values,
        })
    return {
        "candidate_traces": [{
            "candidate_path": candidate_path,
            "kind": kind,
            "samples": samples,
        }]
    }


class Phase5ClassificationTests(unittest.TestCase):
    def test_classifies_perfect_match_as_likely_candidate(self):
        program = finder.build_regfile_write_program()
        zero_values = {reg: 0 for reg in program["expected_registers"]}
        final_values = dict(program["expected_registers"])
        trace = _trace_for_values([zero_values, final_values, final_values, final_values])

        result = finder.classify_regfile_candidates(trace, program)[0]

        self.assertEqual(result["status"], "likely_candidate")
        self.assertGreaterEqual(result["score"], 70)
        self.assertIn("x8", result["mapped_registers"])

    def test_rejects_x0_mismatch(self):
        program = finder.build_regfile_write_program()
        values = dict(program["expected_registers"])
        values["x0"] = 123
        trace = _trace_for_values([{reg: 0 for reg in values}, values, values, values])

        result = finder.classify_regfile_candidates(trace, program)[0]

        self.assertEqual(result["status"], "rejected_candidate")
        self.assertIn("x0 behavior mismatch", result["failed_checks"])

    def test_detects_missing_persistence(self):
        program = finder.build_regfile_write_program()
        zero_values = {reg: 0 for reg in program["expected_registers"]}
        expected = dict(program["expected_registers"])
        changed = dict(expected)
        changed["x1"] = 0x99
        trace = _trace_for_values([zero_values, expected, changed, expected])

        result = finder.classify_regfile_candidates(trace, program)[0]

        self.assertIn("matched values did not persist through loop window", result["failed_checks"])

    def test_classifies_packed_lsb_mapping(self):
        program = finder.build_regfile_write_program()
        zero_values = {reg: 0 for reg in program["expected_registers"]}
        expected = dict(program["expected_registers"])
        samples = []
        for cycle, direct_values in enumerate([zero_values, expected, expected, expected]):
            samples.append({
                "cycle": cycle,
                "pc": 0x2C,
                "in_loop": cycle >= 1,
                "values": {
                    "raw": 0,
                    "packed_lsb_reg0": direct_values,
                    "packed_msb_reg0": {reg: 0 for reg in direct_values},
                },
            })
        trace = {
            "candidate_traces": [{
                "candidate_path": "dut.core.regs",
                "kind": "packed_flat_vector",
                "samples": samples,
            }]
        }

        result = finder.classify_regfile_candidates(trace, program)[0]

        self.assertEqual(result["mapping_order"], "packed_lsb_reg0")
        self.assertGreaterEqual(result["score"], 70)

    def test_rejects_mirrored_false_positive(self):
        program = finder.build_regfile_write_program()
        mirrored = {reg: 0x11 for reg in program["expected_registers"]}
        trace = _trace_for_values([{reg: 0 for reg in mirrored}, mirrored, mirrored, mirrored])

        result = finder.classify_regfile_candidates(trace, program)[0]

        self.assertEqual(result["status"], "rejected_candidate")


class Phase6ConfirmationTests(unittest.TestCase):
    def test_confirms_same_candidate_and_mapping(self):
        phase5 = [{
            "candidate_path": "dut.core.regs",
            "kind": "array_of_words",
            "score": 90,
            "mapping_order": "direct",
            "mapped_registers": {"x0": 0, "x1": 1},
        }]
        confirmation = [{
            "candidate_path": "dut.core.regs",
            "kind": "array_of_words",
            "score": 88,
            "mapping_order": "direct",
            "mapped_registers": {"x0": 0, "x1": 2},
            "reasons": [],
            "failed_checks": [],
        }]

        result = finder._confirm_classification_results(phase5, confirmation)[0]

        self.assertEqual(result["status"], "confirmed_candidate")

    def test_rejects_confirmation_when_second_program_fails(self):
        phase5 = [{
            "candidate_path": "dut.core.regs",
            "kind": "array_of_words",
            "score": 90,
            "mapping_order": "direct",
            "mapped_registers": {"x0": 0, "x1": 1},
        }]
        confirmation = [{
            "candidate_path": "dut.core.regs",
            "kind": "array_of_words",
            "score": 45,
            "mapping_order": "direct",
            "mapped_registers": {"x0": 0},
            "reasons": [],
            "failed_checks": ["no expected register values matched"],
        }]

        result = finder._confirm_classification_results(phase5, confirmation)[0]

        self.assertEqual(result["status"], "rejected_candidate")

    def test_rejects_confirmation_when_mapping_changes(self):
        phase5 = [{
            "candidate_path": "dut.core.regs",
            "kind": "packed_flat_vector",
            "score": 90,
            "mapping_order": "packed_lsb_reg0",
            "mapped_registers": {"x0": 0, "x1": 1},
        }]
        confirmation = [{
            "candidate_path": "dut.core.regs",
            "kind": "packed_flat_vector",
            "score": 88,
            "mapping_order": "packed_msb_reg0",
            "mapped_registers": {"x0": 0, "x1": 2},
            "reasons": [],
            "failed_checks": [],
        }]

        result = finder._confirm_classification_results(phase5, confirmation)[0]

        self.assertNotEqual(result["status"], "confirmed_candidate")
        self.assertIn("confirmation mapping did not match Phase 5", result["failed_checks"])


class InterfaceDiscoveryTests(unittest.TestCase):
    def test_collects_nearby_write_interface_candidates(self):
        elements = [FakeSignal(f"dut.core.REGS.{i}", 32) for i in range(32)]
        child = FakeModule("dut.core.wb", wb_data=FakeSignal("dut.core.wb.wb_data", 32))
        core = FakeModule(
            "dut.core",
            REGS=FakeArray("dut.core.REGS", elements),
            wen=FakeSignal("dut.core.wen", 1),
            rd=FakeSignal("dut.core.rd", 5),
            random_bus=FakeSignal("dut.core.random_bus", 9),
            wb=child,
        )
        dut = FakeModule("dut", core=core)
        selected = {"path": "dut.core.REGS", "kind": "array_of_words", "depth": 32, "word_width": 32}

        candidates = finder.collect_nearby_regfile_interface_candidates(dut, selected)

        self.assertEqual(candidates["parent_scope"], "dut.core")
        self.assertTrue(any(c["path"] == "dut.core.wen" for c in candidates["write_enable_candidates"]))
        self.assertTrue(any(c["path"] == "dut.core.rd" for c in candidates["write_addr_candidates"]))
        self.assertTrue(any(c["path"] == "dut.core.wb.wb_data" for c in candidates["write_data_candidates"]))
        self.assertTrue(any(c["path"] == "dut.core.random_bus" for c in candidates["unclassified_candidates"]))

    def test_interface_probe_program_has_expected_writes_and_loop(self):
        metadata = finder.build_regfile_interface_probe_program()

        self.assertEqual(metadata["program"][metadata["loop_pc"]], finder._jal(0, 0))
        self.assertTrue(all(addr % 4 == 0 for addr in metadata["program"]))
        self.assertEqual([w["reg"] for w in metadata["write_sequence"]], ["x5", "x6", "x5", "x6"])
        self.assertEqual([w["opclass"] for w in metadata["write_sequence"]], ["r_alu", "i_alu_overlap", "lui", "i_alu_xor"])
        self.assertEqual(metadata["expected_registers"], {"x5": 0x00012000, "x6": 0x04})
        self.assertEqual(metadata["overwrite_register"], "x5")

    def test_detects_expected_storage_update_events(self):
        program = finder.build_regfile_interface_probe_program()
        samples = [
            {"cycle": 0, "pc": 0x00, "regfile_values": {"x5": 0, "x6": 0}},
            {"cycle": 1, "pc": 0x08, "regfile_values": {"x5": 0x0C, "x6": 0}},
            {"cycle": 2, "pc": 0x0C, "regfile_values": {"x5": 0x0C, "x6": 0x07}},
            {"cycle": 3, "pc": 0x10, "regfile_values": {"x5": 0x00012000, "x6": 0x07}},
            {"cycle": 4, "pc": 0x14, "regfile_values": {"x5": 0x00012000, "x6": 0x04}},
            {"cycle": 5, "pc": 0x1C, "regfile_values": {"x5": 0x00012000, "x6": 0x04}},
        ]

        events = finder.detect_regfile_storage_update_events(samples, program)

        self.assertEqual([(e["reg_index"], e["new_value"]) for e in events], [(5, 0x0C), (6, 0x07), (5, 0x00012000), (6, 0x04)])
        self.assertEqual(events[2]["old_value"], 0x0C)

    def test_classifies_perfect_interface_tuple(self):
        trace = _interface_trace(
            [
                (0, 0, 0, 0, 0, 0),
                (1, 5, 0x0C, 1, 0x0C, 0),
                (2, 6, 0x07, 1, 0x0C, 0x07),
                (3, 5, 0x00012000, 1, 0x00012000, 0x07),
                (4, 6, 0x04, 1, 0x00012000, 0x04),
                (5, 0, 0, 0, 0x00012000, 0x04),
            ]
        )
        candidates = _interface_candidates()

        result = finder.classify_regfile_interface(trace, candidates)["selected"]

        self.assertEqual(result["status"], "confirmed_interface")
        self.assertEqual(result["write_enable"], "dut.core.wen")
        self.assertEqual(result["write_addr"], "dut.core.rd")
        self.assertEqual(result["write_data"], "dut.core.wdata")

    def test_penalizes_stuck_high_write_enable(self):
        trace = _interface_trace(
            [
                (0, 0, 0, 1, 0, 0),
                (1, 5, 0x0C, 1, 0x0C, 0),
                (2, 6, 0x07, 1, 0x0C, 0x07),
                (3, 5, 0x00012000, 1, 0x00012000, 0x07),
                (4, 6, 0x04, 1, 0x00012000, 0x04),
                (5, 0, 0, 1, 0x00012000, 0x04),
            ]
        )

        result = finder.classify_regfile_interface(trace, _interface_candidates())["selected"]

        self.assertEqual(result["write_enable"], finder.DERIVED_WRITE_ENABLE_PATH)
        self.assertEqual(result["status"], "likely_interface")

    def test_rejects_wrong_write_addr(self):
        trace = _interface_trace(
            [
                (0, 0, 0, 0, 0, 0),
                (1, 1, 0x0C, 1, 0x0C, 0),
                (2, 1, 0x07, 1, 0x0C, 0x07),
                (3, 1, 0x00012000, 1, 0x00012000, 0x07),
                (4, 1, 0x04, 1, 0x00012000, 0x04),
                (5, 0, 0, 0, 0x00012000, 0x04),
            ]
        )

        result = finder.classify_regfile_interface(trace, _interface_candidates())["selected"]

        self.assertEqual(result["status"], "rejected_interface")

    def test_ambiguous_when_write_data_only_matches_one_value(self):
        trace = _interface_trace(
            [
                (0, 0, 0, 0, 0, 0),
                (1, 5, 0x0C, 1, 0x0C, 0),
                (2, 6, 0x0C, 1, 0x0C, 0x07),
                (3, 5, 0x0C, 1, 0x00012000, 0x07),
                (4, 6, 0x0C, 1, 0x00012000, 0x04),
                (5, 0, 0, 0, 0x00012000, 0x04),
            ]
        )

        result = finder.classify_regfile_interface(trace, _interface_candidates())["selected"]

        self.assertEqual(result["write_data"], finder.DERIVED_WRITE_DATA_PATH)
        self.assertEqual(result["status"], "likely_interface")

    def test_allows_one_cycle_timing_offset(self):
        trace = _interface_trace(
            [
                (0, 5, 0x0C, 1, 0, 0),
                (1, 6, 0x07, 1, 0x0C, 0),
                (2, 5, 0x00012000, 1, 0x0C, 0x07),
                (3, 6, 0x04, 1, 0x00012000, 0x07),
                (4, 0, 0, 0, 0x00012000, 0x04),
                (5, 0, 0, 0, 0x00012000, 0x04),
            ]
        )

        result = finder.classify_regfile_interface(trace, _interface_candidates())["selected"]

        self.assertGreaterEqual(result["score"], 70)
        self.assertEqual(result["timing_offset"], -1)

    def test_prefers_same_scope_tuple_when_equivalent(self):
        trace = _interface_trace(
            [
                (0, 0, 0, 0, 0, 0),
                (1, 5, 0x0C, 1, 0x0C, 0),
                (2, 6, 0x07, 1, 0x0C, 0x07),
                (3, 5, 0x00012000, 1, 0x00012000, 0x07),
                (4, 6, 0x04, 1, 0x00012000, 0x04),
                (5, 0, 0, 0, 0x00012000, 0x04),
            ],
            extra_signals={"dut.other.wdata": [0, 0x0C, 0x07, 0x00012000, 0x04, 0]},
        )
        candidates = _interface_candidates()
        candidates["write_data_candidates"].insert(0, {
            "path": "dut.other.wdata",
            "name": "wdata",
            "scope": "dut.other",
            "width": 32,
            "handle_type": "GPI_REGISTER",
            "name_score": 0,
            "name_reasons": [],
        })

        result = finder.classify_regfile_interface(trace, candidates)["selected"]

        self.assertEqual(result["write_data"], "dut.core.wdata")
        self.assertIn("all selected signals are in the same scope", result["reasons"])


def _interface_candidates():
    return {
        "write_enable_candidates": [{
            "path": "dut.core.wen",
            "name": "wen",
            "scope": "dut.core",
            "width": 1,
            "handle_type": "GPI_REGISTER",
            "name_score": 10,
            "name_reasons": ["write_enable name hint(s): wen"],
        }],
        "write_addr_candidates": [{
            "path": "dut.core.rd",
            "name": "rd",
            "scope": "dut.core",
            "width": 5,
            "handle_type": "GPI_REGISTER",
            "name_score": 10,
            "name_reasons": ["write_addr name hint(s): rd"],
        }],
        "write_data_candidates": [{
            "path": "dut.core.wdata",
            "name": "wdata",
            "scope": "dut.core",
            "width": 32,
            "handle_type": "GPI_REGISTER",
            "name_score": 10,
            "name_reasons": ["write_data name hint(s): wdata"],
        }],
    }


def _interface_trace(rows, extra_signals=None):
    program = finder.build_regfile_interface_probe_program()
    samples = []
    for cycle, rd, wdata, wen, x5, x6 in rows:
        signals = {
            "dut.core.wen": wen,
            "dut.core.rd": rd,
            "dut.core.wdata": wdata,
        }
        for path, values in (extra_signals or {}).items():
            signals[path] = values[cycle] if cycle < len(values) else None
        samples.append({
            "cycle": cycle,
            "pc": cycle * 4,
            "in_loop": cycle >= len(rows) - 2,
            "regfile_values": {"x5": x5, "x6": x6},
            "signals": signals,
        })
    return {
        "samples": samples,
        "update_events": finder.detect_regfile_storage_update_events(samples, program),
    }


if __name__ == "__main__":
    unittest.main()
