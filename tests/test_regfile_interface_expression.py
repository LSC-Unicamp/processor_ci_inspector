import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from src import _discovery_shared as shared
from src import regfile_finder as finder
from src.regfile_interface_expression import ExpressionHandle, evaluate_expression, expression_paths


def _candidate(path, width, role):
    return {
        "path": path,
        "name": path.rsplit(".", 1)[-1],
        "scope": "dut.core",
        "width": width,
        "role": role,
        "name_score": 10 if role != "write_enable" else 0,
        "name_reasons": [],
    }


def _trace(regs=(5, 6), values=(0x15, 0x26, 0x35), selector=(0, 1, 0)):
    first, second = regs
    update = {2: (first, values[0]), 5: (second, values[1]), 8: (first, values[2])}
    valid = [0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0]
    regwrite = [0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0]
    rd = [0, first, first, second, second, second, first, first, first, 0, 0]
    alu = [0] * 11
    load = [0] * 11
    sel = [0] * 11
    storage = {f"x{first}": 0, f"x{second}": 0}
    samples = []
    events = []
    for cycle in range(11):
        if cycle in update:
            reg, value = update[cycle]
            old = storage[f"x{reg}"]
            storage[f"x{reg}"] = value
            position = (2, 5, 8).index(cycle)
            sel[cycle] = selector[position]
            if sel[cycle]:
                load[cycle] = value
                alu[cycle] = value + 1
            else:
                alu[cycle] = value
                load[cycle] = value + 1
            events.append({"cycle": cycle, "reg_index": reg, "new_value": value, "old_value": old})
        samples.append({
            "cycle": cycle,
            "regfile_values": dict(storage),
            "signals": {
                "dut.core.valid": valid[cycle],
                "dut.core.regwrite": regwrite[cycle],
                "dut.core.rd": rd[cycle],
                "dut.core.wdata": update[cycle][1] if cycle in update else 0,
                "dut.core.alu_data": alu[cycle],
                "dut.core.load_data": load[cycle],
                "dut.core.wb_sel": sel[cycle],
            },
        })
    return {"ran": True, "samples": samples, "update_events": events}


def _candidates(include_mux=False):
    return {
        "word_width": 32,
        "write_enable_candidates": [
            _candidate("dut.core.valid", 1, "write_enable"),
            _candidate("dut.core.regwrite", 1, "write_enable"),
            _candidate("dut.core.wb_sel", 1, "write_enable"),
        ],
        "write_addr_candidates": [_candidate("dut.core.rd", 5, "write_addr")],
        "write_data_candidates": (
            [_candidate("dut.core.alu_data", 32, "write_data"),
             _candidate("dut.core.load_data", 32, "write_data")]
            if include_mux else [_candidate("dut.core.wdata", 32, "write_data")]
        ),
    }


class ExpressionTests(unittest.TestCase):
    def test_probe_programs_include_nonwriting_destination_lookalikes(self):
        first = finder.build_regfile_interface_probe_program()
        second = finder.build_regfile_interface_confirmation_program()
        self.assertEqual(first["program"][0x1C], finder.BEQ(0, 0, 4))
        self.assertEqual(second["program"][0x24], finder.BNE(0, 0, 4))
        self.assertNotEqual((first["program"][0x1C] >> 7) & 0x1F, 0)
        self.assertEqual([item["reg"] for item in second["write_sequence"]], ["x7", "x8", "x7", "x12", "x13"])
        self.assertEqual(second["program"][second["loop_pc"]], finder._jal(0, 0))

    def test_ast_operations_and_handle_facade(self):
        signals = {
            "dut.core.valid": SimpleNamespace(value=1),
            "dut.core.regwrite": SimpleNamespace(value=1),
            "dut.core.rd": SimpleNamespace(value=5),
        }
        expr = {"op": "and", "args": [
            {"op": "signal", "path": "dut.core.valid"},
            {"op": "signal", "path": "dut.core.regwrite"},
            {"op": "ne", "args": [
                {"op": "signal", "path": "dut.core.rd"},
                {"op": "constant", "value": 0},
            ]},
        ]}
        handle = ExpressionHandle(expr, signals.get, shared._safe_signal_int, "write_enable")
        self.assertEqual(shared._safe_signal_int(handle), 1)
        signals["dut.core.rd"].value = 0
        self.assertEqual(handle.value, 0)
        signals["dut.core.rd"].value = None
        self.assertIsNone(handle.value)
        self.assertEqual(evaluate_expression({"op": "slice", "args": [{"op": "constant", "value": 0xA5}], "lsb": 4, "width": 4}, {}), 0xA)
        self.assertEqual(evaluate_expression({"op": "concat", "args": [{"op": "constant", "value": 0xA}, {"op": "constant", "value": 5}], "widths": [4, 4]}, {}), 0xA5)
        self.assertEqual(evaluate_expression({"op": "mux", "args": [{"op": "constant", "value": 1}, {"op": "constant", "value": 7}, {"op": "constant", "value": 8}]}, {}), 7)
        with self.assertRaises(ValueError):
            expression_paths({"op": "mux", "args": [{"op": "constant", "value": 1}]})

    def test_synthesizes_three_predicate_enable_and_confirms(self):
        trace = _trace()
        candidates = _candidates()
        candidates["expression_candidates"] = finder.synthesize_regfile_interface_expressions(trace, candidates)
        selected = finder.classify_regfile_interface(trace, candidates)["selected"]
        self.assertEqual(selected["role_sources"]["write_enable"], "expression")
        self.assertEqual(selected["role_sources"]["write_addr"], "signal")
        self.assertEqual(selected["role_sources"]["write_data"], "signal")
        self.assertEqual(selected["expression_version"], 1)
        held_out = _trace(regs=(7, 8), values=(0x67, 0x28, 0x17))
        self.assertTrue(finder.validate_frozen_interface_expressions(selected, held_out, candidates)["passed"])
        compact = finder._compact_selected_interface(selected)
        self.assertIn("write_enable", compact["role_expressions"])
        self.assertEqual(finder._compat_regfile_interface(selected)["write_enable"], "__expression__:write_enable")

    def test_synthesizes_mux_and_rejects_changed_selection(self):
        trace = _trace()
        candidates = _candidates(include_mux=True)
        synthesized = finder.synthesize_regfile_interface_expressions(trace, candidates)
        self.assertTrue(synthesized["write_data"])
        selected = {
            "write_enable": "__storage_update_event__",
            "write_addr": "dut.core.rd",
            "write_data": "__expression__:write_data",
            "write_addr_timing_offset": 0,
            "write_data_timing_offset": 0,
            "role_expressions": {"write_data": synthesized["write_data"][0]["expression"]},
        }
        held_out = _trace(regs=(7, 8), values=(0x67, 0x28, 0x17))
        self.assertTrue(finder.validate_frozen_interface_expressions(selected, held_out, candidates)["passed"])
        held_out["samples"][5]["signals"]["dut.core.wb_sel"] = 0
        self.assertFalse(finder.validate_frozen_interface_expressions(selected, held_out, candidates)["passed"])

    def test_held_out_program_selects_next_frozen_formula(self):
        candidates = _candidates()
        trace = _trace()
        good = finder.synthesize_regfile_interface_expressions(trace, candidates)["write_enable"][0]
        bad = {
            "path": "__expression__:write_enable",
            "expression": {"op": "signal", "path": "dut.core.spur"},
            "timing_offset": 0,
            "score": 95,
        }
        candidates["expression_candidates"] = {"write_enable": [bad, good]}
        selected = {
            "write_enable": bad["path"],
            "write_addr": "dut.core.rd",
            "write_data": "dut.core.wdata",
            "write_enable_timing_offset": 0,
            "write_addr_timing_offset": 0,
            "write_data_timing_offset": 0,
            "role_expressions": {"write_enable": bad["expression"]},
        }
        held_out = _trace(regs=(7, 8), values=(0x67, 0x28, 0x17))
        for sample in held_out["samples"]:
            sample["signals"]["dut.core.spur"] = 0
        confirmed, result = finder.confirm_frozen_interface_expressions(selected, held_out, candidates)
        self.assertTrue(result["passed"])
        self.assertEqual(result["attempt_count"], 2)
        self.assertEqual(confirmed["role_expressions"]["write_enable"], good["expression"])

    def test_confirmation_requires_every_declared_write(self):
        trace = _trace(regs=(7, 8), values=(0x67, 0x28, 0x17))
        trace["expected_write_count"] = 5
        trace["reached_loop"] = True
        selected = {
            "write_enable": "__expression__:write_enable",
            "write_addr": "dut.core.rd",
            "write_data": "dut.core.wdata",
            "write_enable_timing_offset": 0,
            "write_addr_timing_offset": 0,
            "write_data_timing_offset": 0,
            "role_expressions": {"write_enable": {"op": "signal", "path": "dut.core.regwrite"}},
        }
        result = finder.validate_frozen_interface_expressions(selected, trace, _candidates())
        self.assertFalse(result["passed"])
        self.assertIn("write_enable", result["failed_roles"])

    def test_compact_expression_resolves_for_existing_consumers(self):
        expr = {"op": "and", "args": [
            {"op": "signal", "path": "processorci_top.Processor.valid"},
            {"op": "signal", "path": "processorci_top.Processor.regwrite"},
        ]}
        selected = {
            "status": "confirmed_interface",
            "write_enable": "__expression__:write_enable",
            "write_addr": "processorci_top.Processor.rd",
            "write_data": "processorci_top.Processor.wdata",
            "role_expressions": {"write_enable": expr},
            "expression_version": 1,
            "write_enable_timing_offset": -1,
            "write_addr_timing_offset": 0,
            "write_data_timing_offset": 0,
        }
        dut = SimpleNamespace(
            Processor=SimpleNamespace(
                valid=SimpleNamespace(value=1),
                regwrite=SimpleNamespace(value=1),
                rd=SimpleNamespace(value=5),
                wdata=SimpleNamespace(value=0x55),
            ),
            _log=SimpleNamespace(info=lambda *args: None, warning=lambda *args: None),
        )
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "demo_reg_file.json").write_text(json.dumps({
                "regfile_interface": finder._compat_regfile_interface(selected),
                "selected_regfile_interface": finder._compact_selected_interface(selected),
            }), encoding="utf-8")
            with mock.patch.dict(os.environ, {"OUTPUT_DIR": directory}):
                handles = shared._resolve_write_interface(dut, "demo", None)
        self.assertIsNotNone(handles)
        self.assertEqual(shared._safe_signal_int(handles["write_enable"]), 1)
        self.assertEqual(shared._safe_signal_int(handles["write_addr"]), 5)
        self.assertEqual(handles["_role_timing_offsets"]["write_enable"], -1)


if __name__ == "__main__":
    unittest.main()
