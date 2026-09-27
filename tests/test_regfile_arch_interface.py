import copy
import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from src import _discovery_shared as shared
from src import regfile_arch_interface as arch
from src import regfile_finder as finder
from src.regfile_interface_expression import (
    ExpressionHandle, evaluate_expression, expression_paths,
)


FLAGS = {
    "alu_imm": "dut.core.MCC", "alu_reg": "dut.core.RCC",
    "lui": "dut.core.LUI", "auipc": "dut.core.AUIPC",
    "jal": "dut.core.JAL", "jalr": "dut.core.JALR", "load": "dut.core.LCC",
}
DATA = {
    "alu_imm": "dut.core.RMDATA", "alu_reg": "dut.core.RMDATA",
    "lui": "dut.core.SIMM", "auipc": "dut.core.PCSIMM",
    "jal": "dut.core.NXPC", "jalr": "dut.core.NXPC",
    "load": "dut.core.LDATA",
}


def _candidate(path, width):
    return {"path": path, "name": path.rsplit(".", 1)[-1],
            "width": width, "name_score": 10}


def _fixture(held_out=False, width=32, load_delay=0, stall_cycles=0):
    program = arch.build_architectural_write_program(held_out=held_out)
    base = 0x80000000 if width == 64 else 0x1000
    program["_runtime_base_address"] = base
    fetch_cycles = {pc: 4 * (pc // 4) for pc in program["program"]}
    idempotent_pc = next(entry["pc"] for entry in program["write_sequence"]
                         if entry["idempotent"])
    if stall_cycles:
        fetch_cycles = {pc: cycle + (stall_cycles if pc >= idempotent_pc else 0)
                        for pc, cycle in fetch_cycles.items()}
    last = fetch_cycles[program["loop_pc"]] + 12
    signal_paths = set(FLAGS.values()) | set(DATA.values()) | {"dut.core.DPTR", "dut.core.HLT"}
    regs = {f"x{entry['reg_index']}": 0 for entry in program["write_sequence"]}
    regs["x0"] = 0
    samples = [{"cycle": cycle, "pc": None, "fetch_valid": False,
                "signals": {path: 0 for path in signal_paths}, "regfile_values": {}}
               for cycle in range(last + 1)]
    for pc, cycle in fetch_cycles.items():
        samples[cycle]["pc"] = pc
        samples[cycle]["fetch_valid"] = True
    for cycle in range(fetch_cycles[idempotent_pc] + 1,
                       fetch_cycles[idempotent_pc] + stall_cycles + 1):
        samples[cycle]["pc"] = idempotent_pc
        samples[cycle]["fetch_valid"] = True
    updates = {}
    for entry in program["write_sequence"]:
        value = arch._expected(entry, base, (1 << width) - 1)
        fetch = fetch_cycles[entry["pc"]]
        update = fetch + 2 + (
            load_delay if entry["opclass"] == "load" else
            stall_cycles if entry["idempotent"] else 0
        )
        slot = samples[update - 1]["signals"]
        slot[FLAGS[entry["opclass"]]] = 1
        slot["dut.core.DPTR"] = entry["reg_index"]
        slot[DATA[entry["opclass"]]] = value
        if not entry["idempotent"]:
            updates[update] = (entry["reg"], value)
        if entry["opclass"] == "load" and stall_cycles:
            for held in range(update - stall_cycles - 1, update - 1):
                stalled = samples[held]["signals"]
                stalled[FLAGS["load"]] = 1
                stalled["dut.core.DPTR"] = entry["reg_index"]
                stalled[DATA["load"]] = value
                stalled["dut.core.HLT"] = 1
    for control in program["negative_controls"]:
        if control["kind"] == "x0":
            slot = samples[fetch_cycles[control["pc"]] + 1]["signals"]
            slot[FLAGS["alu_imm"]] = 1
            slot["dut.core.DPTR"] = 0
    for cycle in range(len(samples)):
        if cycle in updates:
            reg, value = updates[cycle]
            regs[reg] = value
        samples[cycle]["regfile_values"] = dict(regs)
    candidates = {
        "regfile_path": "dut.core.REGS", "word_width": width,
        "write_enable_candidates": [_candidate(path, 1)
                                    for path in set(FLAGS.values()) | {"dut.core.HLT"}],
        "write_addr_candidates": [_candidate("dut.core.DPTR", 5)],
        "write_data_candidates": [_candidate(path, width) for path in set(DATA.values())],
        "unclassified_candidates": [],
    }
    trace = {"ran": True, "reached_loop": True, "samples": samples,
             "data_memory": {"supported": True, "load_verified": True,
                             "store_verified": True}}
    return program, trace, candidates


class ArchitecturalInterfaceTests(unittest.TestCase):
    def test_program_covers_all_classes_and_controls(self):
        first = arch.build_architectural_write_program()
        second = arch.build_architectural_write_program(held_out=True)
        self.assertEqual({entry["opclass"] for entry in first["write_sequence"]}, set(arch.WRITE_CLASSES))
        self.assertEqual(first["program"][first["loop_pc"]], arch.JAL(0, 0))
        self.assertEqual({item["kind"] for item in first["negative_controls"]},
                         {"x0", "store", "branch", "nop"})
        self.assertTrue(all(pc % 4 == 0 for pc in first["program"]))
        self.assertTrue(all(entry["reg_index"] <= 15 for entry in first["write_sequence"]))
        self.assertNotEqual(first["data_memory_initial"], second["data_memory_initial"])

    def test_unified_bus_transaction_is_acknowledged_once_per_request(self):
        memory = finder.DataMemory()
        memory.reset({0x100: 0x51A21})
        value, token = finder._serve_unified_data_transaction(
            memory, 0x100, False, None, 4, None
        )
        self.assertEqual(value, 0x51A21)
        _, token = finder._serve_unified_data_transaction(
            memory, 0x100, False, None, 5, token
        )
        self.assertEqual([tx["kind"] for tx in memory.transactions], ["load"])
        _, token = finder._serve_unified_data_transaction(
            memory, 0x104, True, 0x34, 8, None
        )
        _, token = finder._serve_unified_data_transaction(
            memory, 0x104, True, 0x34, 9, token
        )
        self.assertEqual(memory.read_word(0x104), 0x34)
        self.assertEqual([tx["kind"] for tx in memory.transactions], ["load", "store"])

    def test_priority_mux_order_unresolved_and_bounds(self):
        expr = {"op": "priority_mux", "cases": [
            {"when": arch._signal("dut.a"), "value": arch._constant(3)},
            {"when": arch._signal("dut.b"), "value": arch._constant(4)},
        ], "default": arch._constant(0)}
        self.assertEqual(expression_paths(expr, version=2), {"dut.a", "dut.b"})
        self.assertEqual(evaluate_expression(expr, {"dut.a": 1, "dut.b": 1}), 3)
        self.assertEqual(evaluate_expression(expr, {"dut.a": 0, "dut.b": 1}), 4)
        self.assertEqual(evaluate_expression(expr, {"dut.a": 0, "dut.b": 0}), 0)
        self.assertIsNone(evaluate_expression(expr, {"dut.a": None, "dut.b": 1}))
        with self.assertRaises(ValueError):
            expression_paths(expr)
        with self.assertRaises(ValueError):
            expression_paths({**expr, "cases": expr["cases"] * 4}, version=2)
        too_many = {"op": "priority_mux", "cases": [
            {"when": arch._signal(f"dut.flag{i}"),
             "value": arch._binary("or", arch._signal(f"dut.a{i}"), arch._signal(f"dut.b{i}"))}
            for i in range(7)
        ], "default": arch._constant(0)}
        with self.assertRaises(ValueError):
            expression_paths(too_many, version=2)

    def test_darkriscv_shaped_trace_synthesizes_and_confirms(self):
        program, trace, candidates = _fixture(load_delay=3)
        evidence = arch.analyze_architectural_trace(trace, program, 32)
        self.assertTrue(evidence["passed"], evidence["failed_checks"])
        self.assertEqual(evidence["expected_registers"]["x6"],
                         program["_runtime_base_address"] + 0x34)
        self.assertEqual(len(evidence["records"]), len(program["write_sequence"]))
        self.assertEqual(evidence["changed_update_count"], len(program["write_sequence"]) - 1)
        frozen, discovery = arch.synthesize_architectural_interface(trace, evidence, candidates, 32)
        self.assertIsNotNone(frozen, discovery)
        self.assertTrue(discovery["passed"])
        self.assertEqual(frozen["write_data_timing_offset"], -1)
        held_out, second_trace, _ = _fixture(held_out=True, load_delay=2, stall_cycles=2)
        confirmation = arch.analyze_architectural_trace(second_trace, held_out, 32)
        self.assertEqual(next(record for record in confirmation["records"]
                              if record["idempotent"])["fetch_hold_cycles"], 2)
        self.assertTrue(confirmation["passed"], confirmation["failed_checks"])
        self.assertTrue(arch.validate_architectural_interface(frozen, second_trace, confirmation, 32)["passed"])
        compact = finder._compact_selected_interface(frozen)
        self.assertEqual(compact["interface_semantics"], "architectural_write")
        self.assertEqual(compact["expression_version"], 2)
        self.assertEqual(len(compact["validated_instruction_classes"]), 7)
        self.assertEqual(finder._compat_regfile_interface(frozen)["write_addr"],
                         "__expression__:write_addr")
        with tempfile.TemporaryDirectory() as directory:
            compact_output = finder._compact_regfile_output({
                "selected_regfile": {"candidate_path": "dut.core.REGS", "status": "confirmed_candidate"},
                "selected_regfile_interface": frozen,
            })
            with open(os.path.join(directory, "core_reg_file.json"), "w", encoding="utf-8") as stream:
                json.dump(compact_output, stream)
            with mock.patch.dict(os.environ, {"OUTPUT_DIR": directory}):
                state, loaded = shared._current_regfile_interface_state("core")
            self.assertEqual(state, "usable")
            self.assertEqual(loaded["_expression_version"], 2)
            event = next(record for record in evidence["records"] if record["opclass"] == "load")
            values = trace["samples"][event["cycle"] - 1]["signals"]
            handles = {path: SimpleNamespace(value=value) for path, value in values.items()}
            facade = ExpressionHandle(
                frozen["role_expressions"]["write_data"], handles.get,
                shared._safe_signal_int, "write_data", version=2,
            )
            self.assertEqual(facade.value, event["value"])

    def test_missing_load_wrong_branch_and_false_enable_reject(self):
        program, trace, candidates = _fixture()
        evidence = arch.analyze_architectural_trace(trace, program, 32)
        frozen, result = arch.synthesize_architectural_interface(trace, evidence, candidates, 32)
        self.assertIsNotNone(frozen, result)
        unserved = copy.deepcopy(trace)
        unserved["data_memory"]["load_verified"] = False
        self.assertFalse(arch.analyze_architectural_trace(unserved, program, 32)["passed"])
        unserved_store = copy.deepcopy(trace)
        unserved_store["data_memory"]["store_verified"] = False
        self.assertFalse(arch.analyze_architectural_trace(unserved_store, program, 32)["passed"])
        wrong = copy.deepcopy(trace)
        load_record = next(record for record in evidence["records"] if record["opclass"] == "load")
        wrong["samples"][load_record["cycle"] - 1]["signals"]["dut.core.LDATA"] ^= 1
        self.assertFalse(arch.validate_architectural_interface(frozen, wrong, evidence, 32)["passed"])
        unresolved = copy.deepcopy(trace)
        unresolved["samples"][load_record["cycle"] - 1]["signals"]["dut.core.LDATA"] = None
        self.assertFalse(arch.validate_architectural_interface(frozen, unresolved, evidence, 32)["passed"])
        false_enable = copy.deepcopy(trace)
        false_enable["samples"][2]["signals"]["dut.core.MCC"] = 1
        false_enable["samples"][2]["signals"]["dut.core.DPTR"] = 5
        self.assertFalse(arch.validate_architectural_interface(frozen, false_enable, evidence, 32)["passed"])
        changed_address = copy.deepcopy(trace)
        changed_address["samples"][load_record["cycle"] - 1]["signals"]["dut.core.DPTR"] = 10
        self.assertFalse(arch.validate_architectural_interface(frozen, changed_address, evidence, 32)["passed"])

    def test_inconsistent_load_timing_and_missing_class_reject(self):
        program, trace, candidates = _fixture()
        evidence = arch.analyze_architectural_trace(trace, program, 32)
        shifted = copy.deepcopy(trace)
        load_record = next(record for record in evidence["records"] if record["opclass"] == "load")
        source = "dut.core.LDATA"
        shifted["samples"][load_record["cycle"]]["signals"][source] = load_record["value"]
        shifted["samples"][load_record["cycle"] - 1]["signals"][source] = 0
        frozen, synthesis = arch.synthesize_architectural_interface(shifted, evidence, candidates, 32)
        self.assertIsNone(frozen, synthesis)
        missing = copy.deepcopy(trace)
        for sample in missing["samples"]:
            sample["regfile_values"].pop("x9", None)
        self.assertFalse(arch.analyze_architectural_trace(missing, program, 32)["passed"])

    def test_rv64_mask_and_v1_expression_unchanged(self):
        program, trace, candidates = _fixture(width=64)
        evidence = arch.analyze_architectural_trace(trace, program, 64)
        frozen, result = arch.synthesize_architectural_interface(trace, evidence, candidates, 64)
        self.assertIsNotNone(frozen, result)
        self.assertTrue(arch.validate_architectural_interface(frozen, trace, evidence, 64)["passed"])
        v1 = {"op": "mux", "args": [arch._constant(1), arch._constant(7), arch._constant(8)]}
        self.assertEqual(evaluate_expression(v1, {}), 7)
        self.assertEqual(expression_paths(v1), set())

    def test_partial_interface_when_memory_transport_is_unavailable(self):
        program, trace, candidates = _fixture()
        trace["data_memory"] = {
            "supported": False, "load_verified": False, "store_verified": False,
        }
        load = next(entry for entry in program["write_sequence"]
                    if entry["opclass"] == "load")
        for sample in trace["samples"]:
            sample["regfile_values"][load["reg"]] = 0

        evidence = arch.analyze_architectural_trace(trace, program, 32)
        self.assertFalse(evidence["passed"])
        self.assertTrue(evidence["partial_passed"])
        self.assertEqual(evidence["class_states"]["load"]["state"], "unavailable")
        frozen, validation = arch.synthesize_architectural_interface(
            trace, evidence, candidates, 32
        )

        self.assertTrue(validation["passed"], validation["failed_checks"])
        self.assertEqual(frozen["interface_semantics"], "validated_write_interface")
        self.assertEqual(frozen["missing_instruction_classes"], ["load"])
        self.assertNotIn("load", frozen["validated_instruction_classes"])

    def test_partial_interface_may_stop_at_unavailable_load(self):
        program, trace, candidates = _fixture()
        load = next(entry for entry in program["write_sequence"]
                    if entry["opclass"] == "load")
        load_fetch_cycle = next(
            sample["cycle"] for sample in trace["samples"]
            if sample.get("pc") == load["pc"]
        )
        trace["samples"] = [
            sample for sample in trace["samples"]
            if sample["cycle"] <= load_fetch_cycle
        ]
        trace["reached_loop"] = False
        trace["loop_cycle"] = None
        trace["data_memory"] = {
            "supported": False, "load_verified": False, "store_verified": False,
        }
        for sample in trace["samples"]:
            sample["regfile_values"][load["reg"]] = 0

        evidence = arch.analyze_architectural_trace(trace, program, 32)
        frozen, validation = arch.synthesize_architectural_interface(
            trace, evidence, candidates, 32
        )

        self.assertTrue(evidence["partial_passed"], evidence["failed_checks"])
        self.assertNotIn("self-loop was not reached", evidence["hard_failed_checks"])
        self.assertIsNotNone(frozen, validation)
        self.assertEqual(frozen["interface_semantics"], "validated_write_interface")

    def test_fetched_wrong_write_is_not_partial_coverage(self):
        program, trace, candidates = _fixture()
        alu_record = next(entry for entry in program["write_sequence"]
                          if entry["opclass"] == "alu_reg")
        for sample in trace["samples"]:
            if sample["regfile_values"].get(alu_record["reg"]) == alu_record["value"]:
                sample["regfile_values"][alu_record["reg"]] ^= 1

        evidence = arch.analyze_architectural_trace(trace, program, 32)
        frozen, validation = arch.synthesize_architectural_interface(
            trace, evidence, candidates, 32
        )

        self.assertFalse(evidence["partial_passed"])
        self.assertEqual(evidence["class_states"]["alu_reg"]["state"], "failed")
        self.assertIsNone(frozen)
        self.assertFalse(validation["passed"])

    def test_roles_can_use_independent_offsets(self):
        program, trace, candidates = _fixture()
        evidence = arch.analyze_architectural_trace(trace, program, 32)
        data_paths = set(DATA.values())
        for record in evidence["records"]:
            source_cycle = record["cycle"] - 1
            address = trace["samples"][source_cycle]["signals"].pop("dut.core.DPTR")
            trace["samples"][record["cycle"] - 2]["signals"]["dut.core.DPTR"] = address
            for path in data_paths:
                value = trace["samples"][source_cycle]["signals"].pop(path)
                trace["samples"][record["cycle"]]["signals"][path] = value
            for path in FLAGS.values():
                trace["samples"][record["cycle"]]["signals"][path] = (
                    1 if path == FLAGS[record["opclass"]] else 0
                )

        frozen, validation = arch.synthesize_architectural_interface(
            trace, evidence, candidates, 32
        )

        self.assertIsNotNone(frozen, validation)
        self.assertEqual(frozen["write_addr_timing_offset"], -2)
        self.assertEqual(frozen["write_data_timing_offset"], 0)
        self.assertNotEqual(
            frozen["write_addr_timing_offset"], frozen["write_data_timing_offset"]
        )
        self.assertEqual(
            frozen["timing_offset"], frozen["write_enable_timing_offset"]
        )

    def test_confirmed_real_role_is_seeded_before_synthesis(self):
        program, trace, candidates = _fixture()
        evidence = arch.analyze_architectural_trace(trace, program, 32)
        path = "dut.core.legacy_wen"
        for sample in trace["samples"]:
            sample["signals"][path] = 0
        for record in evidence["records"]:
            trace["samples"][record["cycle"] - 1]["signals"][path] = 1
        candidates["write_enable_candidates"].append(_candidate(path, 1))
        seed = {"status": "confirmed_interface", "write_enable": path}

        frozen, validation = arch.synthesize_architectural_interface(
            trace, evidence, candidates, 32, seed=seed
        )

        self.assertIsNotNone(frozen, validation)
        self.assertEqual(
            frozen["role_expressions"]["write_enable"], arch._signal(path)
        )
        self.assertEqual(frozen["write_enable_timing_offset"], -1)

    def test_pc_relative_value_bias_is_calibrated_consistently(self):
        program, trace, candidates = _fixture()
        mask = (1 << 32) - 1
        for entry in program["write_sequence"]:
            if not isinstance(entry["value"], tuple):
                continue
            nominal = arch._expected(
                entry, program["_runtime_base_address"], mask
            )
            adjusted = (nominal - 4) & mask
            changed = False
            for sample in trace["samples"]:
                values = sample["regfile_values"]
                if values.get(entry["reg"]) == nominal:
                    values[entry["reg"]] = adjusted
                    changed = True
                signals = sample["signals"]
                source = DATA[entry["opclass"]]
                if signals.get(source) == nominal:
                    signals[source] = adjusted
            self.assertTrue(changed)

        evidence = arch.analyze_architectural_trace(trace, program, 32)
        frozen, validation = arch.synthesize_architectural_interface(
            trace, evidence, candidates, 32
        )

        self.assertEqual(evidence["pc_value_bias"], -4)
        self.assertTrue(evidence["passed"], evidence["failed_checks"])
        self.assertIsNotNone(frozen, validation)

    def test_wide_fetch_lines_cover_both_instruction_slots(self):
        program, trace, _ = _fixture()
        trace["fetch_width_bytes"] = 8
        for sample in trace["samples"]:
            if sample.get("pc") is not None and sample["pc"] % 8 == 4:
                sample["fetch_valid"] = False

        evidence = arch.analyze_architectural_trace(trace, program, 32)

        self.assertTrue(evidence["passed"], evidence["failed_checks"])
        self.assertTrue(all(
            "fetch not observed" not in reason
            for reason in evidence["failed_checks"]
        ))

    def test_simultaneous_updates_are_rejected_as_multiport(self):
        program, trace, _ = _fixture()
        evidence = arch.analyze_architectural_trace(trace, program, 32)
        update_cycle = evidence["records"][0]["cycle"]
        for sample in trace["samples"]:
            sample["regfile_values"]["x15"] = (
                0x77 if sample["cycle"] >= update_cycle else 0
            )

        rejected = arch.analyze_architectural_trace(trace, program, 32)

        self.assertEqual(rejected["topology"], "unsupported_multiport")
        self.assertFalse(rejected["partial_passed"])
        self.assertIn(
            "simultaneous GPR updates require a multi-port interface",
            rejected["hard_failed_checks"],
        )

    def test_virtual_interface_selection_precedence(self):
        full = {
            "status": "confirmed_interface",
            "interface_semantics": "architectural_write",
        }
        partial = {
            "status": "confirmed_interface",
            "interface_semantics": "validated_write_interface",
        }
        direct = {
            "status": "confirmed_interface",
            "write_enable": "dut.core.wen",
            "write_addr": "dut.core.rd",
            "write_data": "dut.core.wdata",
        }
        storage = {
            "status": "confirmed_interface",
            "write_enable": "__storage_event__",
            "write_addr": "__storage_reg_index__",
            "write_data": "__storage_new_value__",
        }

        self.assertTrue(finder._prefer_virtual_interface(direct, full))
        self.assertFalse(finder._prefer_virtual_interface(direct, partial))
        self.assertTrue(finder._prefer_virtual_interface(storage, partial))
        self.assertTrue(finder._prefer_virtual_interface(None, partial))


if __name__ == "__main__":
    unittest.main()
