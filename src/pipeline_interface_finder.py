"""Dynamic discovery of scalar pipeline-stage observation signals.

Signal names are used only to bound the VPI search.  A candidate becomes usable
only after its values follow known probe PCs consistently across independent
dependent/control executions.
"""

from __future__ import annotations

import json
import hashlib
import os
import re
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from statistics import median

try:
    from .regfile_finder import (
        _is_hierarchy_handle,
        _iter_sim_children,
        _safe_len,
        _safe_path,
        _safe_type,
        _safe_value_int,
    )
except ImportError:
    from regfile_finder import (
        _is_hierarchy_handle,
        _iter_sim_children,
        _safe_len,
        _safe_path,
        _safe_type,
        _safe_value_int,
    )


PIPELINE_INTERFACE_SCHEMA_VERSION = 4
PIPELINE_INTERFACE_DISCOVERY_VERSION = "dynamic-stage-signals-v4"
PIPELINE_INTERFACE_IMPLEMENTATION_REVISION = 11
DEFAULT_MAX_PC_CANDIDATES = 40
DEFAULT_MAX_INSTRUCTION_CANDIDATES = 24
DEFAULT_MAX_CONTROL_CANDIDATES = 32
DEFAULT_MAX_OPERAND_CANDIDATES = 48
DEFAULT_MAX_PACKED_PARENTS = 16
DEFAULT_MAX_PACKED_PARENTS_TOTAL = 128
MAX_PACKED_VIRTUAL_SLICES = 8
DEFAULT_MAX_DISCOVERY_SCOPES = 512
DEFAULT_MAX_DISCOVERY_OBJECTS = 20000
DEFAULT_MAX_CHILDREN_PER_SCOPE = 2048
DEFAULT_MAX_CENSUS_STAGE_CANDIDATES = 96
DEFAULT_MAX_CENSUS_DATA_CANDIDATES = 128
DEFAULT_MAX_CENSUS_ID_CANDIDATES = 96
DEFAULT_MAX_CENSUS_CONTROL_CANDIDATES = 64

PC_HINTS = (
    "stage_pc", "fetch_pc", "decode_pc", "execute_pc", "memory_pc", "writeback_pc",
    "if_pc", "id_pc", "ex_pc", "mem_pc", "wb_pc", "pc_if", "pc_id", "pc_ex",
    "pc_mem", "pc_wb", "pc_d", "pc_e", "pc_m", "pc_w", "pc_q", "pc_reg",
    "pc_val", "r_pc", "pc_out", "pc_pipe", "pipe_pc",
)
INSTRUCTION_HINTS = (
    "instruction", "instr", "insn", "inst_if", "inst_id", "inst_ex", "inst_mem",
    "inst_wb", "ir_q", "ir_reg", "if_ir", "id_ir", "ex_ir", "mem_ir", "wb_ir",
)
VALID_HINTS = ("valid", "vld", "occupied")
STALL_HINTS = ("stall", "hold", "ready", "enable", "en_")
FLUSH_HINTS = ("flush", "kill", "squash", "clear")
SOURCE_ID_HINTS = ("rs1", "rs2", "src1_addr", "src2_addr", "source1_id", "source2_id")
DESTINATION_ID_HINTS = ("rd_addr", "rd_id", "dest_addr", "dest_id", "write_addr", "wb_rd")
OPERAND_HINTS = (
    "operand", "op_a", "op_b", "opa", "opb", "src1", "src2", "rs1_data",
    "rs2_data", "rs1_dat", "rs2_dat", "regs_data1", "reg_data1", "rdata1",
    "rs1_out", "rs2_out", "reg_a_out", "reg_b_out", "forward_a_mux_out",
    "forward_b_mux_out", "forward_out_a", "forward_out_b",
    "alu_1_mux_out", "alu_2_mux_out",
    "mux1_o", "mux2_o", "mux3_o",
)
STORE_DATA_HINTS = (
    "store_data", "storedata", "store_value", "mem_wdata", "rs2_dat_d",
    "mem_data_out", "me_regs_data2", "mem_regs_data2", "me_rs2_data",
    "mem_rs2_data", "store_operand", "w_data_mem", "data_mem_pre",
    "mem_write_data", "write_data_mem", "wb_mem_forward_mux_out",
)
WB_DATA_HINTS = ("wb_data", "write_data", "wdata", "rd_wdata", "regfile_mux_out")
WB_ENABLE_HINTS = ("wb_enable", "wb_we", "write_enable", "regwrite", "reg_write", "load_regfile")
EXCLUDE_HINTS = ("clock", "clk", "reset", "rst", "jtag", "counter")
WRAPPER_STAGE_EXCLUSIONS = {
    "probe_fetch_pc", "probe_fetch_pc_hi", "probe_prediction_pc",
    "probe_redirect_pc", "probe_resolution_pc",
}
NON_STAGE_PC_HINTS = (
    "nxt_pc", "next_pc", "predict_pc", "predicted_pc", "redirect_pc",
    "target_pc", "resolution_pc", "mepc", "exception_pc", "exc_pc",
    "pc_add", "pc_off", "pc_mux",
)
MAX_STAGE_WINDOW_CYCLES = 16


def _basename(path):
    return str(path or "").rsplit(".", 1)[-1].lower()


def _parent(path):
    return str(path or "").rsplit(".", 1)[0] if "." in str(path or "") else ""


def _scope_distance(path, reference):
    if not reference:
        return 99
    left = str(path).split(".")
    right = str(reference).split(".")
    shared = 0
    for a, b in zip(left, right):
        if a != b:
            break
        shared += 1
    return (len(left) - shared) + (len(right) - shared)


def _name_matches(name, hints):
    return any(hint in name for hint in hints)


def _semantic_name_role(path):
    """Return a weak stage-name hint; dynamic timing remains authoritative."""
    def role(tokens):
        if tokens & {"wb", "writeback", "retire", "commit"}:
            return "writeback"
        if tokens & {"me", "mem", "memory", "lsu"}:
            return "memory"
        if tokens & {"ex", "exe", "execute", "alu"}:
            return "execute"
        if tokens & {"id", "decode", "operand"}:
            return "operand_read"
        if tokens & {"if", "fetch", "ifu"}:
            return "frontend"
        return None

    basename = _basename(path)
    if "memwb" in basename or "mem_wb" in basename:
        return "writeback"
    if "exmem" in basename or "ex_mem" in basename:
        return "memory"
    if "idex" in basename or "id_ex" in basename:
        return "execute"
    if "ifid" in basename or "if_id" in basename:
        return "operand_read"
    if basename in {"pc_i", "pc_o", "instr_i", "instr_o", "instruction_i", "instruction_o"}:
        return "frontend"
    basename_tokens = set(basename.replace("-", "_").split("_"))
    basename_role = role(basename_tokens)
    if basename_role:
        return basename_role
    name = str(path or "").lower()
    path_tokens = set(name.replace("-", "_").replace(".", "_").split("_"))
    path_role = role(path_tokens)
    if path_role:
        return path_role
    return None


def _lane_id(path):
    name = str(path or "").lower()
    patterns = (
        r"(?:^|[._\[])lane[_]?([0-9]+)",
        r"(?:^|[._\[])slot[_]?([0-9]+)",
        r"(?:^|[._\[])i([0-9]+)(?:[._\]]|$)",
        r"\[([0-9]+)\]",
    )
    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            return int(match.group(1))
    return None


def _looks_multilane(path):
    return _lane_id(path) is not None


def _looks_packed_parent(path, width):
    if width is None or not 9 <= int(width) <= 512:
        return False
    name = str(path or "").lower()
    if any(token in _basename(path) for token in ("pc", "instr", "insn", "instruction")):
        return False
    return any(token in name for token in (
        "pipe", "stage", "ctrl", "control", "exec", "execute", "mem",
        "writeback", "wb", "id_ex", "ex_mem", "mem_wb", "payload",
        "bundle", "record", "out",
    ))


def _looks_combined_execute_memory(path):
    tokens = set(_basename(path).replace("-", "_").split("_"))
    return bool(tokens & {"ex", "exe", "execute"}) and bool(tokens & {"mem", "memory"})


def _discovery_root_near_regfile(dut, regfile_path):
    """Prefer the core instance that owns the already validated regfile."""
    root = getattr(dut, "_target", dut)
    if not regfile_path:
        return root
    root_path = _safe_path(root)
    parts = str(regfile_path).split(".")
    root_name = _basename(root_path)
    try:
        root_index = [part.lower() for part in parts].index(root_name)
        descendants = parts[root_index + 1:]
    except (ValueError, AttributeError):
        descendants = parts
        if descendants and descendants[0].lower() == _basename(_safe_path(dut)):
            descendants = descendants[1:]
    # The first descendant is the core/module instance. Walking from there
    # avoids unrelated wrapper packages and malformed simulator aliases while
    # still covering every stage near the architectural register file.
    if len(descendants) >= 2:
        try:
            candidate = getattr(root, descendants[0])
            if _is_hierarchy_handle(candidate):
                return candidate
        except Exception:
            pass
    return root


def _candidate_role(path, width):
    name = _basename(path)
    if name in WRAPPER_STAGE_EXCLUSIONS:
        return None
    if any(hint in name for hint in EXCLUDE_HINTS):
        return None
    if name.startswith(("probe_", "data_mem_", "core_data")):
        return None
    if width == 1:
        if _name_matches(name, WB_ENABLE_HINTS):
            return "wb_enable"
        if _name_matches(name, VALID_HINTS):
            return "valid"
        if _name_matches(name, FLUSH_HINTS):
            return "flush"
        if _name_matches(name, STALL_HINTS):
            return "stall"
    pc_like = (
        name == "pc"
        or _name_matches(name, PC_HINTS)
        or (name.startswith("pc_") and len(name) > 3)
        or (name.endswith("_pc") and len(name) > 3)
    )
    if pc_like and any(hint in name for hint in NON_STAGE_PC_HINTS):
        return None
    if width is not None and 8 <= width <= 64 and pc_like:
        return "pc"
    if width in (16, 32, 64) and _name_matches(name, INSTRUCTION_HINTS):
        return "instruction"
    if width is not None and 4 <= width <= 8 and _name_matches(name, SOURCE_ID_HINTS):
        return "source_id"
    if width is not None and 4 <= width <= 8 and _name_matches(name, DESTINATION_ID_HINTS):
        return "destination_id"
    if width is not None and 16 <= width <= 64 and _name_matches(name, STORE_DATA_HINTS):
        return "store_data"
    if width is not None and 16 <= width <= 64 and _name_matches(name, WB_DATA_HINTS):
        return "wb_data"
    if width is not None and 16 <= width <= 64 and _name_matches(name, OPERAND_HINTS):
        return "operand"
    # A number of small scalar ALUs expose their *selected* inputs simply as
    # ``a`` and ``b``.  Those names are far too broad to search globally, but
    # are useful when the hierarchy itself establishes an execute/ALU scope.
    # Dynamic source-ID/value/token validation is still required before such a
    # signal can become evidence.
    if (
        width is not None and 16 <= width <= 64
        and name in {"a", "b"}
        and _semantic_name_role(_parent(path)) == "execute"
    ):
        return "operand"
    return None


def _behavioral_candidate_roles(path, width):
    """Return width-derived census roles without treating names as evidence.

    The old name classifier remains useful as a priority seed.  These roles
    make otherwise anonymous simulator-visible pipeline registers observable;
    only their behavior during known programs can promote them.
    """
    name = _basename(path)
    if (
        name in WRAPPER_STAGE_EXCLUSIONS
        or any(hint in name for hint in EXCLUDE_HINTS)
        or name.startswith(("probe_", "data_mem_", "core_data"))
        or width is None
    ):
        return ()
    width = int(width)
    if width == 1:
        return ("valid", "stall", "flush", "wb_enable")
    roles = []
    if 8 <= width <= 64:
        roles.append("pc")
    if width in (16, 32, 64):
        roles.append("instruction")
    if 4 <= width <= 8:
        roles.extend(("source_id", "destination_id"))
    if 16 <= width <= 64:
        roles.extend(("operand", "store_data", "wb_data"))
    if 9 <= width <= 512:
        roles.append("packed_parent")
    return tuple(roles)


def _limit_packed_parent_candidates(
    ordered, per_scope=DEFAULT_MAX_PACKED_PARENTS,
    total=DEFAULT_MAX_PACKED_PARENTS_TOTAL,
):
    grouped = defaultdict(list)
    for item in ordered:
        grouped[(
            item.get("name_role_hint") or "unknown",
            item.get("lane_id"),
        )].append(item)
    selected = []
    truncated_scopes = []
    for scope in sorted(grouped, key=lambda item: (item[0], str(item[1]))):
        group = grouped[scope]
        if len(group) > per_scope:
            truncated_scopes.append(scope)
        selected.extend(group[:per_scope])
    selected = sorted(
        selected, key=lambda item: (-item["static_rank"], item["path"])
    )
    total_truncated = len(selected) > total
    return selected[:total], truncated_scopes, total_truncated


def discover_pipeline_signal_candidates(
    dut, regfile_path=None, max_depth=25,
    max_scopes=DEFAULT_MAX_DISCOVERY_SCOPES,
    max_objects=DEFAULT_MAX_DISCOVERY_OBJECTS,
    max_children_per_scope=DEFAULT_MAX_CHILDREN_PER_SCOPE,
):
    """Return a bounded census set; names only affect deterministic priority."""
    limits = {
        "pc": DEFAULT_MAX_PC_CANDIDATES,
        "instruction": DEFAULT_MAX_INSTRUCTION_CANDIDATES,
        "valid": DEFAULT_MAX_CONTROL_CANDIDATES,
        "stall": DEFAULT_MAX_CONTROL_CANDIDATES,
        "flush": DEFAULT_MAX_CONTROL_CANDIDATES,
        "source_id": DEFAULT_MAX_OPERAND_CANDIDATES,
        "destination_id": DEFAULT_MAX_OPERAND_CANDIDATES,
        "operand": DEFAULT_MAX_OPERAND_CANDIDATES,
        "store_data": DEFAULT_MAX_OPERAND_CANDIDATES,
        "wb_data": DEFAULT_MAX_OPERAND_CANDIDATES,
        "wb_enable": DEFAULT_MAX_CONTROL_CANDIDATES,
        "packed_parent": DEFAULT_MAX_PACKED_PARENTS,
    }
    found = defaultdict(list)
    visited = set()
    discovery_root = _discovery_root_near_regfile(dut, regfile_path)
    stack = [(discovery_root, 0)]
    visited_objects = 0
    search_truncated = False
    truncation_reasons = set()
    while stack:
        if len(visited) >= int(max_scopes):
            search_truncated = True
            truncation_reasons.add("scope_limit")
            break
        if visited_objects >= int(max_objects):
            search_truncated = True
            truncation_reasons.add("object_limit")
            break
        scope, depth = stack.pop()
        if depth > max_depth:
            continue
        scope_path = _safe_path(scope, fallback=str(id(scope)))
        if scope_path in visited:
            continue
        visited.add(scope_path)
        children = []
        try:
            for child_index, child_pair in enumerate(_iter_sim_children(scope)):
                if child_index >= int(max_children_per_scope):
                    search_truncated = True
                    truncation_reasons.add("children_per_scope_limit")
                    break
                if visited_objects >= int(max_objects):
                    search_truncated = True
                    truncation_reasons.add("object_limit")
                    break
                children.append(child_pair)
                visited_objects += 1
        except Exception:
            continue
        for _, child in children:
            if _is_hierarchy_handle(child):
                if _safe_type(child) not in {"GPI_GENARRAY", "GPI_MODULE_ARRAY"}:
                    stack.append((child, depth + 1))
                continue
            path = _safe_path(child)
            width = _safe_len(child)
            named_role = _candidate_role(path, width)
            roles = set(_behavioral_candidate_roles(path, width))
            if _looks_packed_parent(path, width):
                roles.add("packed_parent")
            if named_role is not None:
                roles.add(named_role)
            if not roles:
                continue
            name = _basename(path)
            base_rank = 40 - min(30, 2 * _scope_distance(path, regfile_path))
            name_bonus = min(20, sum(5 for hint in {
                "pc", "stage", "pipe", "valid", "instr", "inst", "execute",
                "memory", "writeback",
            } if hint in name))
            for role in roles:
                name_seed = role == named_role
                rank = base_rank + name_bonus + (100 if name_seed else 0)
                found[role].append({
                    "path": path,
                    "scope": _parent(path),
                    "width": width,
                    "role": role,
                    "static_rank": rank,
                    "name_seed": name_seed,
                    "behavioral_census": not name_seed,
                    "name_role_hint": _semantic_name_role(path),
                    "lane_hint": _looks_multilane(path),
                    "lane_id": _lane_id(path),
                    "handle": child,
                })

    result = {
        "candidates": {}, "search_truncated": search_truncated,
        "visited_scopes": len(visited), "visited_objects": visited_objects,
        "discovery_root": _safe_path(discovery_root),
        "truncation_reasons": sorted(truncation_reasons),
        "multi_lane_candidates": False,
    }
    for role, limit in limits.items():
        if role == "packed_parent":
            nearby_semantic_paths = [
                item["path"]
                for candidate_role in (
                    "store_data", "source_id", "operand", "wb_data",
                )
                for item in found.get(candidate_role, [])
            ]
            for item in found.get(role, []):
                nearest = min(
                    (
                        _scope_distance(item["path"], path)
                        for path in nearby_semantic_paths
                    ),
                    default=99,
                )
                if nearest <= 6:
                    item["static_rank"] += 30 - 4 * nearest
                if item.get("name_role_hint") in {"memory", "writeback"}:
                    item["static_rank"] += 15
        ordered = sorted(found.get(role, []), key=lambda item: (-item["static_rank"], item["path"]))
        if role == "packed_parent":
            ordered, truncated_scopes, total_truncated = (
                _limit_packed_parent_candidates(ordered, per_scope=limit)
            )
            for scope in truncated_scopes:
                result["search_truncated"] = True
                result["truncation_reasons"].append(
                    f"candidate_limit:packed_parent:{scope[0]}:lane={scope[1]}"
                )
            if total_truncated:
                result["search_truncated"] = True
                result["truncation_reasons"].append(
                    "candidate_limit:packed_parent_total"
                )
            result["candidates"][role] = ordered
            result["multi_lane_candidates"] |= any(
                item.get("lane_hint") for item in ordered
            )
            continue
        census_limit = {
            "pc": DEFAULT_MAX_CENSUS_STAGE_CANDIDATES,
            "instruction": DEFAULT_MAX_CENSUS_STAGE_CANDIDATES,
            "source_id": DEFAULT_MAX_CENSUS_ID_CANDIDATES,
            "destination_id": DEFAULT_MAX_CENSUS_ID_CANDIDATES,
            "operand": DEFAULT_MAX_CENSUS_DATA_CANDIDATES,
            "store_data": DEFAULT_MAX_CENSUS_DATA_CANDIDATES,
            "wb_data": DEFAULT_MAX_CENSUS_DATA_CANDIDATES,
            "valid": DEFAULT_MAX_CENSUS_CONTROL_CANDIDATES,
            "stall": DEFAULT_MAX_CENSUS_CONTROL_CANDIDATES,
            "flush": DEFAULT_MAX_CENSUS_CONTROL_CANDIDATES,
            "wb_enable": DEFAULT_MAX_CENSUS_CONTROL_CANDIDATES,
        }.get(role, limit)
        if len(ordered) > census_limit:
            result["search_truncated"] = True
            result["truncation_reasons"].append(f"candidate_limit:{role}")
        result["candidates"][role] = ordered[:census_limit]
        result["multi_lane_candidates"] |= any(
            item.get("lane_hint") for item in ordered[:census_limit]
        )
    result["census_inventory"] = {
        role: {
            "discovered": len(found.get(role, [])),
            "retained": len(result["candidates"].get(role, [])),
            "name_seeds": sum(
                bool(item.get("name_seed"))
                for item in result["candidates"].get(role, [])
            ),
        }
        for role in limits
    }
    result["truncation_reasons"] = sorted(set(result["truncation_reasons"]))
    return result


def _program_offset(value, spec):
    if value is None:
        return None, None
    value = int(value)
    offsets = set(spec.instructions)
    bases = tuple(getattr(spec, "base_addresses", ()) or (0,))
    addresses = [(base + offset, offset) for base in bases for offset in offsets]
    for address, offset in addresses:
        if value == address:
            return offset, "byte"
    for address, offset in addresses:
        if value == (address >> 2):
            return offset, "word"
    for mask in (0xFFF, 0x3FF, 0xFF):
        for address, offset in addresses:
            if value == (address & mask):
                return offset, f"byte_low_{mask:x}"
    return None, None


def _instruction_offset(value, spec):
    """Map only unique instruction encodings to tokens; repeated NOPs are unsafe."""
    if value is None:
        return None
    matches = [offset for offset, encoding in spec.instructions.items() if int(encoding) == int(value)]
    return matches[0] if len(matches) == 1 else None


def _nearest_control(candidates, pc_path):
    pc_scope = _parent(pc_path)
    if not candidates:
        return None
    return min(candidates, key=lambda item: (_scope_distance(item["path"], pc_scope), -item["static_rank"]))


class PipelineSignalObserver:
    """Sample shortlisted internal signals during existing forwarding probes."""

    def __init__(
        self, dut, regfile_path=None, pipeline_depth=None,
        write_interface=None, register_reader=None, architectural_xlen=32,
    ):
        self.discovery_error = None
        try:
            dut._log.info("[pipeline_finder] Starting bounded signal discovery")
            self.discovery = discover_pipeline_signal_candidates(dut, regfile_path=regfile_path)
            dut._log.info(
                "[pipeline_finder] Discovery complete: scopes=%s objects=%s truncated=%s",
                self.discovery.get("visited_scopes"),
                self.discovery.get("visited_objects"),
                self.discovery.get("search_truncated"),
            )
        except Exception as exc:
            self.discovery = {"candidates": {}, "search_truncated": False, "visited_scopes": 0}
            self.discovery_error = str(exc)
        self._active = None
        self._trials = []
        self._next_id = 0
        self.pipeline_depth = pipeline_depth
        self.write_interface = write_interface or {}
        self.register_reader = register_reader
        self.architectural_xlen = 64 if int(architectural_xlen or 32) > 32 else 32
        self.stall_sampling_enabled = True
        self.discovery_phase = "census"
        self.census_summary = None
        self._census_reserve = {}
        self._focused_rescan_ran = False
        self.calibration_base_selection = {
            "state": "not_run",
            "policy": {
                "required_distinct_bases": 3,
                "stop_after_selected": 3,
            },
            "attempted": [],
            "selected_bases": [],
        }
        self.full_finalization_count = 0
        self.discarded_raw_trial_count = 0

    def set_stall_sampling_enabled(self, enabled):
        self.stall_sampling_enabled = bool(enabled)

    def set_calibration_base_selection(self, selection):
        self.calibration_base_selection = dict(selection or {})
        self.discovery["calibration_base_selection"] = dict(
            self.calibration_base_selection
        )

    def finalize_census(self):
        """Freeze behaviorally active candidates after calibration.

        Name seeds are retained only as bounded runners-up. Anonymous signals
        survive when they matched known tokens/values in multiple trials.
        """
        if not hasattr(self, "_census_reserve"):
            self._census_reserve = {}
        trials = [
            trial for trial in self._trials
            if str(trial.get("program", "")).startswith(
                "pipeline_calibration_"
            )
        ]
        event_paths = defaultdict(lambda: {"matches": 0, "trials": set()})
        sample_paths = defaultdict(
            lambda: {"matches": 0, "trials": set(), "values": set()}
        )
        packed_parents = defaultdict(
            lambda: {"matches": 0, "trials": set(), "values": set()}
        )
        for trial in trials:
            trial_id = str(trial.get("trial_id"))
            for event in trial.get("events", ()):
                item = event_paths[event.get("path")]
                item["matches"] += 1
                item["trials"].add(trial_id)
            for sample in trial.get("raw_stage_samples", ()):
                item = event_paths[sample.get("path")]
                item["matches"] += 1
                item["trials"].add(trial_id)
            for sample in trial.get("signal_samples", ()):
                item = sample_paths[sample.get("path")]
                item["matches"] += 1
                item["trials"].add(trial_id)
                item["values"].add(sample.get("value"))
                if sample.get("parent_path"):
                    parent = packed_parents[sample["parent_path"]]
                    parent["matches"] += 1
                    parent["trials"].add(trial_id)
                    parent["values"].add(sample.get("value"))

        affine_signatures = {}
        for candidate in self.discovery.get(
            "candidates", {}
        ).get("pc", ()):
            path = candidate.get("path")
            width = candidate.get("width")
            models = []
            for mode in ("byte", "word"):
                transform, events_by_trial = _fit_affine_stage_events(
                    path, trials, mode, width=width,
                )
                if transform is None:
                    continue
                matched_trials = sorted(
                    trial_id for trial_id, events in events_by_trial.items()
                    if events
                )
                offsets = sorted(
                    (
                        trial_id,
                        int(event.get("offset", -1)),
                        int(event.get("residence_entry_cycle", -1)),
                    )
                    for trial_id, events in events_by_trial.items()
                    for event in events
                )
                models.append({
                    **transform,
                    "matched_trials": matched_trials,
                    "matched_trial_count": len(matched_trials),
                    "matched_token_count": len(offsets),
                    "token_order_hash": hashlib.sha256(
                        json.dumps(
                            offsets, separators=(",", ":"),
                        ).encode("utf-8")
                    ).hexdigest()[:16],
                })
            affine_signatures[path] = (
                max(
                    models,
                    key=lambda item: (
                        item["matched_trial_count"],
                        item["matched_token_count"],
                        1 if item["mode"] == "byte" else 0,
                    ),
                ) if models else None
            )

        before = {}
        after = {}
        selected = {}
        for role, candidates in self.discovery.get("candidates", {}).items():
            before[role] = len(candidates)
            scored = []
            for candidate in candidates:
                path = candidate.get("path")
                activity = (
                    event_paths[path]
                    if role in {"pc", "instruction"}
                    else packed_parents[path]
                    if role == "packed_parent"
                    else sample_paths[path]
                )
                affine_signature = (
                    affine_signatures.get(path)
                    if role == "pc" else None
                )
                behavioral = (
                    (
                        affine_signature is not None
                        and affine_signature["matched_trial_count"] >= 2
                        and affine_signature["matched_token_count"] >= 3
                    )
                    if role == "pc" else
                    len(activity["trials"]) >= 2
                    and activity["matches"] >= 3
                    and (
                        role in {
                            "pc", "instruction", "valid", "stall", "flush",
                            "wb_enable",
                        }
                        or len(activity.get("values", ())) >= 2
                    )
                )
                item = dict(candidate)
                item.update({
                    "census_matches": activity["matches"],
                    "census_trials": len(activity["trials"]),
                    "census_distinct_values": len(
                        activity.get("values", ())
                    ),
                    "census_behavioral_match": behavioral,
                    "census_signature": affine_signature,
                })
                scored.append(item)
            scored.sort(key=lambda item: (
                0 if item.get("census_behavioral_match") else 1,
                -item.get("census_trials", 0),
                -item.get("census_matches", 0),
                str(item.get("scope", "")),
                str(item.get("lane_id")),
                0 if item.get("name_seed") else 1,
                -item.get("static_rank", 0),
                item.get("path", ""),
            ))
            fallback_limit = 8 if role in {"pc", "instruction"} else 12
            retained = [
                item for item in scored
                if item.get("census_behavioral_match")
            ]
            retained_paths = {item["path"] for item in retained}
            retained.extend(
                item for item in scored
                if item.get("name_seed") and item["path"] not in retained_paths
            )
            hard_limit = {
                "pc": DEFAULT_MAX_PC_CANDIDATES,
                "instruction": DEFAULT_MAX_INSTRUCTION_CANDIDATES,
                "valid": DEFAULT_MAX_CONTROL_CANDIDATES,
                "stall": DEFAULT_MAX_CONTROL_CANDIDATES,
                "flush": DEFAULT_MAX_CONTROL_CANDIDATES,
                "wb_enable": DEFAULT_MAX_CONTROL_CANDIDATES,
                "source_id": DEFAULT_MAX_OPERAND_CANDIDATES,
                "destination_id": DEFAULT_MAX_OPERAND_CANDIDATES,
                "operand": DEFAULT_MAX_OPERAND_CANDIDATES,
                "store_data": DEFAULT_MAX_OPERAND_CANDIDATES,
                "wb_data": DEFAULT_MAX_OPERAND_CANDIDATES,
                "packed_parent": DEFAULT_MAX_PACKED_PARENTS_TOTAL,
            }.get(role, fallback_limit)
            # Reserve one behaviorally qualified representative per
            # hierarchy/semantic-role/lane before filling by global score.
            reserve_groups = {}
            for item in retained:
                if not item.get("census_behavioral_match"):
                    continue
                key = (
                    _parent(item.get("path")),
                    item.get("lane_id"),
                )
                reserve_groups.setdefault(key, item)
            reserved = list(reserve_groups.values())[:hard_limit]
            reserved_paths = {item["path"] for item in reserved}
            retained = [
                *reserved,
                *(
                    item for item in retained
                    if item["path"] not in reserved_paths
                ),
            ][:hard_limit]
            selected[role] = retained
            after[role] = len(retained)
            retained_paths = {item["path"] for item in retained}
            reserve = [
                item for item in scored
                if item["path"] not in retained_paths
            ][:hard_limit]
            self._census_reserve[role] = reserve
        self.discovery["candidates"] = selected
        self.discovery_phase = "focused"
        self.census_summary = {
            "state": "completed" if trials else "unavailable",
            "calibration_trials": len(trials),
            "discovered": {
                role: int(values.get("discovered", 0))
                for role, values in self.discovery.get(
                    "census_inventory", {}
                ).items()
            },
            "candidate_counts_before": before,
            "candidate_counts_after": after,
            "signature_evaluated": before,
            "promoted": after,
            "detailed_traced": after,
            "truncated": bool(self.discovery.get("search_truncated")),
            "truncation_reasons": list(
                self.discovery.get("truncation_reasons", ())
            ),
            "selection_rule": (
                "behavioral token/value matches first; bounded name seeds "
                "retained only as runners-up"
            ),
            "reserve_counts": {
                role: len(items)
                for role, items in self._census_reserve.items()
            },
            "behaviorally_qualified_excluded": {
                role: sum(
                    bool(item.get("census_behavioral_match"))
                    for item in items
                )
                for role, items in self._census_reserve.items()
            },
            "absolute_traversal_exclusion": {
                "active": bool(
                    self.discovery.get("search_truncated")
                ),
                "reasons": [
                    reason for reason in self.discovery.get(
                        "truncation_reasons", ()
                    )
                    if reason in {
                        "scope_limit", "object_limit",
                        "children_per_scope_limit",
                    }
                ],
                "behavioral_qualification": (
                    "not_evaluable_because_candidate_was_not_reached"
                    if self.discovery.get("search_truncated")
                    else "not_applicable"
                ),
            },
        }
        self.discovery["behavioral_census"] = dict(self.census_summary)
        return dict(self.census_summary)

    def promote_focused_reserve(self, missing_by_path):
        """Promote only roles needed by the first adjacent proof-gap pass."""
        if self._focused_rescan_ran:
            return {
                "ran": False, "reason": "focused rescan already ran",
                "affected_paths": [], "promoted_counts": {},
            }
        self._focused_rescan_ran = True
        category_roles = {
            "stage_token": ("pc", "instruction"),
            "consumer_token": ("pc", "instruction"),
            "source_id": ("source_id", "packed_parent"),
            "operand_capture": ("operand", "store_data", "packed_parent"),
            "semantic_discriminator": (
                "operand", "store_data", "packed_parent",
            ),
            "producer_availability": (
                "destination_id", "wb_data", "wb_enable",
            ),
            "transaction_association": (
                "source_id", "store_data", "packed_parent",
            ),
            "lane_identity": (
                "pc", "instruction", "source_id", "operand",
                "store_data", "wb_data", "packed_parent",
            ),
            "phase_ordering": (
                "source_id", "operand", "store_data", "wb_data",
            ),
        }
        roles = {
            role
            for categories in missing_by_path.values()
            for category in categories
            for role in category_roles.get(category, ())
        }
        promoted_counts = {}
        budgets = {}
        truncated = False
        for role in sorted(roles):
            current = self.discovery.get("candidates", {}).setdefault(
                role, [],
            )
            normal_budget = {
                "pc": DEFAULT_MAX_PC_CANDIDATES,
                "instruction": DEFAULT_MAX_INSTRUCTION_CANDIDATES,
                "valid": DEFAULT_MAX_CONTROL_CANDIDATES,
                "stall": DEFAULT_MAX_CONTROL_CANDIDATES,
                "flush": DEFAULT_MAX_CONTROL_CANDIDATES,
                "wb_enable": DEFAULT_MAX_CONTROL_CANDIDATES,
                "source_id": DEFAULT_MAX_OPERAND_CANDIDATES,
                "destination_id": DEFAULT_MAX_OPERAND_CANDIDATES,
                "operand": DEFAULT_MAX_OPERAND_CANDIDATES,
                "store_data": DEFAULT_MAX_OPERAND_CANDIDATES,
                "wb_data": DEFAULT_MAX_OPERAND_CANDIDATES,
                "packed_parent": DEFAULT_MAX_PACKED_PARENTS_TOTAL,
            }.get(role, 0)
            capacity = max(0, 2 * normal_budget - len(current))
            reserve = self._census_reserve.get(role, [])
            promoted = reserve[:capacity]
            self.discovery["candidates"][role] = [*current, *promoted]
            self._census_reserve[role] = reserve[len(promoted):]
            promoted_counts[role] = len(promoted)
            budgets[role] = {
                "normal": normal_budget,
                "before": len(current),
                "after": len(current) + len(promoted),
                "maximum": 2 * normal_budget,
            }
            truncated |= len(reserve) > len(promoted)
        return {
            "ran": True,
            "missing_categories": {
                path: sorted(set(categories))
                for path, categories in sorted(missing_by_path.items())
            },
            "affected_paths": sorted(missing_by_path),
            "promoted_counts": promoted_counts,
            "budgets": budgets,
            "truncated": truncated,
            "resolved": {},
        }

    def mark_adjacent_trials_discovery_only(self, path_names):
        prefixes = tuple(f"{name}_" for name in path_names)
        marked = 0
        for trial in self._trials:
            program = str(trial.get("program", ""))
            if (
                program.startswith(prefixes)
                and "_gap_0" in program
                and trial.get("pair_role") in {"dependent", "control"}
            ):
                trial["discovery_only"] = True
                marked += 1
        return marked

    def start_trial(self, spec):
        trial_id = str(self._next_id)
        self._next_id += 1
        self._active = {
            "trial_id": trial_id,
            "program": spec.name,
            "pair_role": getattr(spec, "pair_role", None),
            "variant": getattr(spec, "forwarding_variant", None),
            "forwarding_gap": getattr(spec, "forwarding_gap", 0),
            "spacer_kind": getattr(spec, "spacer_kind", "nop"),
            "filler_registers": list(
                getattr(spec, "filler_registers", ())
            ),
            "filler_values": list(getattr(spec, "filler_values", ())),
            "calibration_kind": getattr(spec, "calibration_kind", None),
            "calibration_variant": getattr(spec, "calibration_variant", None),
            "calibration_relocation_base": getattr(
                spec, "calibration_relocation_base", None,
            ),
            "calibration_relocation_origin": getattr(
                spec, "calibration_relocation_origin", None,
            ),
            "calibration_requested_base": getattr(
                spec, "calibration_requested_base", None,
            ),
            "calibration_landing_index": getattr(
                spec, "calibration_landing_index", None,
            ),
            "handshake_role": getattr(spec, "handshake_role", None),
            "response_delay_cycles": getattr(spec, "response_delay_cycles", 0),
            "base_addresses": list(
                getattr(spec, "base_addresses", ())
            ),
            "producer_offset": getattr(spec, "producer_offset", None),
            "consumer_offset": getattr(spec, "consumer_offset", None),
            "expected_store_address": getattr(spec, "expected_store_address", None),
            "expected_store_value": getattr(spec, "expected_store_value", None),
            "control_flow": dict(getattr(spec, "control_flow", {}) or {}),
            "expected_write_count": len(getattr(spec, "expected_writes", ())),
            "events": [],
            "raw_stage_samples": [],
            "signal_samples": [],
            "architectural_samples": [],
            "writeback_samples": [],
            "operand_expectations": [
                asdict(item) if is_dataclass(item) else dict(item)
                for item in getattr(spec, "operand_observations", ())
            ],
            "instruction_by_offset": {
                int(offset): int(instruction)
                for offset, instruction in getattr(spec, "instructions", {}).items()
            },
            "spec": spec,
            "last_sample_values": {},
            "packed_sample_until": -1,
            "fetch_cursor": 0,
            "relocation_roles_permitted": bool(
                self.calibration_base_selection.get(
                    "relocation_roles_permitted", False
                )
            ),
        }
        return trial_id

    def note_fetch_events(self, fetch_events, cycle):
        """Open a bounded packed-record sampling window around known tokens."""
        active = self._active
        if active is None:
            return
        cursor = int(active.get("fetch_cursor", 0))
        relevant_offsets = {
            item.get("offset") for item in active.get("operand_expectations", [])
            if item.get("offset") is not None
        }
        for event in fetch_events[cursor:]:
            if event.get("offset") in relevant_offsets and not event.get("squashed"):
                window = max(4, int(self.pipeline_depth or 0) + 2)
                active["packed_sample_until"] = max(
                    int(active.get("packed_sample_until", -1)), int(cycle) + window,
                )
        active["fetch_cursor"] = len(fetch_events)

    def sample(self, cycle, phase="post_edge"):
        active = self._active
        if active is None:
            return
        spec = active["spec"]
        phase_order = 0 if phase == "pre_edge" else 1
        expectations = active.get("operand_expectations", [])
        expected_ids = {
            item.get(key) for item in expectations
            for key in ("rs1_register", "rs2_register", "destination_register")
            if item.get(key) is not None
        }
        expected_ids.update(
            int(register)
            for item in expectations
            for register in item.get("non_source_registers", ())
        )
        expected_values = {
            int(item.get(key)) & 0xFFFFFFFF for item in expectations
            for key in (
                "rs1_value", "rs2_value", "result_value", "poison_value",
                "immediate_value", "effective_address",
            )
            if item.get(key) is not None
        }
        expected_values.update(
            int(value) & 0xFFFFFFFF
            for item in expectations
            for value in item.get("forbidden_operand_values", ())
        )
        poison_values = {
            int(item.get("poison_value")) & ((1 << self.architectural_xlen) - 1)
            for item in expectations if item.get("poison_value") is not None
        }
        sampled_roles = (
            "source_id", "destination_id", "operand", "store_data",
            "wb_data", "wb_enable", "valid", "stall", "flush",
        ) if int(cycle) <= int(active.get("packed_sample_until", -1)) else ()
        value_cache = {}

        def candidate_value(candidate):
            path = candidate["path"]
            if path not in value_cache:
                value_cache[path] = _safe_value_int(candidate["handle"])
            return value_cache[path]

        for role in sampled_roles:
            if role == "stall" and not self.stall_sampling_enabled:
                continue
            for candidate in self.discovery.get("candidates", {}).get(role, []):
                value = candidate_value(candidate)
                if value is None:
                    continue
                discriminating = (
                    (role in {"source_id", "destination_id"} and value in expected_ids)
                    or (role in {"operand", "store_data", "wb_data"} and (value & 0xFFFFFFFF) in expected_values)
                )
                previous = active["last_sample_values"].get(candidate["path"])
                retain_change = role in {"wb_enable", "valid", "stall", "flush"}
                if discriminating or (retain_change and previous != value):
                    active["signal_samples"].append({
                        "cycle": cycle, "phase": phase, "phase_order": phase_order,
                        "path": candidate["path"], "candidate_role": role,
                        "value": value,
                    })
                active["last_sample_values"][candidate["path"]] = value

        # Packed structs are sampled once and expanded into sparse virtual
        # slices only when a known varied probe ID/value is present. This keeps
        # VPI sampling bounded while allowing opaque packed pipeline records.
        packed_ids = {int(value) & 0x1F for value in expected_ids if value not in (None, 0)}
        packed_values = {
            int(value) & ((1 << self.architectural_xlen) - 1)
            for value in expected_values | poison_values if int(value) != 0
        }
        packed_parents = (
            self.discovery.get("candidates", {}).get("packed_parent", [])
            if int(cycle) <= int(active.get("packed_sample_until", -1))
            else ()
        )
        for parent in packed_parents:
            raw = candidate_value(parent)
            width = int(parent.get("width") or 0)
            if raw is None or width <= 0:
                continue
            lane = parent.get("lane_id")
            for bit_offset in range(max(0, width - 5 + 1)):
                sliced = (int(raw) >> bit_offset) & 0x1F
                if sliced not in packed_ids:
                    continue
                for candidate_role in ("source_id", "destination_id"):
                    active["signal_samples"].append({
                        "cycle": cycle, "phase": phase, "phase_order": phase_order,
                        "path": f'{parent["path"]}[{bit_offset}+:5]',
                        "parent_path": parent["path"], "bit_offset": bit_offset,
                        "slice_width": 5, "candidate_role": candidate_role,
                        "value": sliced, "lane_id": lane, "packed": True,
                    })
            value_width = self.architectural_xlen
            mask = (1 << value_width) - 1
            for bit_offset in range(max(0, width - value_width + 1)):
                sliced = (int(raw) >> bit_offset) & mask
                if sliced not in packed_values:
                    continue
                for candidate_role in ("operand", "store_data", "wb_data"):
                    active["signal_samples"].append({
                        "cycle": cycle, "phase": phase, "phase_order": phase_order,
                        "path": f'{parent["path"]}[{bit_offset}+:{value_width}]',
                        "parent_path": parent["path"], "bit_offset": bit_offset,
                        "slice_width": value_width, "candidate_role": candidate_role,
                        "value": sliced, "lane_id": lane, "packed": True,
                    })

        semantic_window_active = int(cycle) <= int(active.get("packed_sample_until", -1))
        if self.write_interface and semantic_window_active:
            values = {
                role: _safe_value_int(self.write_interface.get(role))
                for role in ("write_enable", "write_addr", "write_data")
            }
            bit_offset = self.write_interface.get("_write_addr_bit_offset")
            if values.get("write_addr") is not None and bit_offset is not None:
                values["write_addr"] = (values["write_addr"] >> int(bit_offset)) & 0x1F
            if all(value is not None for value in values.values()):
                active["writeback_samples"].append({
                    "cycle": cycle, "phase": phase, "phase_order": phase_order,
                    **values,
                    "source": "validated_regfile_interface",
                    "paths": {
                        role: _safe_path(self.write_interface.get(role))
                        for role in ("write_enable", "write_addr", "write_data")
                    },
                    "lane_id": next((
                        lane for lane in (
                            _lane_id(_safe_path(self.write_interface.get(role)))
                            for role in ("write_enable", "write_addr", "write_data")
                        ) if lane is not None
                    ), None),
                })
        if self.register_reader is not None and semantic_window_active:
            for register in sorted({
                item.get("destination_register") for item in expectations
                if item.get("destination_register") is not None
            }):
                try:
                    value = self.register_reader(register)
                except Exception:
                    value = None
                if value is not None:
                    active["architectural_samples"].append({
                        "cycle": cycle, "phase": phase, "phase_order": phase_order,
                        "register": register, "value": int(value) & 0xFFFFFFFF,
                    })

        if phase != "post_edge" or not semantic_window_active:
            return
        instructions = self.discovery.get("candidates", {}).get("instruction", [])
        for candidate in self.discovery.get("candidates", {}).get("pc", []):
            value = candidate_value(candidate)
            if value is None:
                continue
            raw_sample = {
                "cycle": int(cycle),
                "phase": phase,
                "phase_order": phase_order,
                "path": candidate["path"],
                "value": int(value),
                "width": candidate.get("width"),
                "lane_id": candidate.get("lane_id"),
            }
            instruction = _nearest_control(instructions, candidate["path"])
            if instruction is not None:
                instruction_value = candidate_value(instruction)
                raw_sample.update({
                    "instruction_path": instruction["path"],
                    "instruction_value": instruction_value,
                })
            for control_role, field in (
                ("valid", "valid_value"),
                ("flush", "flush_value"),
            ):
                control = _nearest_control(
                    self.discovery.get("candidates", {}).get(
                        control_role, []
                    ),
                    candidate["path"],
                )
                if control is not None:
                    raw_sample[f"{control_role}_path"] = control["path"]
                    raw_sample[field] = candidate_value(control)
            active["raw_stage_samples"].append(raw_sample)
            offset, address_mode = _program_offset(value, spec)
            if offset is None:
                continue
            event = {
                "cycle": cycle, "path": candidate["path"], "offset": offset,
                "value": value, "address_mode": address_mode,
            }
            if instruction is not None:
                event["instruction_path"] = instruction["path"]
                event["instruction_matches"] = instruction_value == spec.instructions.get(offset)
            for control_role, field in (
                ("valid", "valid_value"),
                ("flush", "flush_value"),
            ):
                control = _nearest_control(
                    self.discovery.get("candidates", {}).get(
                        control_role, []
                    ),
                    candidate["path"],
                )
                if control is not None:
                    event[f"{control_role}_path"] = control["path"]
                    event[field] = candidate_value(control)
            active["events"].append(event)
        # A known, varied instruction stream can reveal stage registers even
        # when the core hides or truncates its internal PCs. Only unique probe
        # encodings are accepted so a runway NOP cannot create a false stage.
        for candidate in instructions:
            value = candidate_value(candidate)
            offset = _instruction_offset(value, spec)
            if offset is None:
                continue
            active["events"].append({
                "cycle": cycle,
                "path": candidate["path"],
                "offset": offset,
                "value": value,
                "address_mode": "instruction",
                "signal_kind": "instruction",
                "instruction_path": candidate["path"],
                "instruction_matches": True,
            })

    def finish_trial(self, fetch_events, commits, transactions, calibration_signature=None):
        if self._active is None:
            return
        record = dict(self._active)
        record.pop("spec", None)
        record.pop("last_sample_values", None)
        record.pop("packed_sample_until", None)
        record.pop("fetch_cursor", None)
        record["fetch_events"] = list(fetch_events)
        record["commits"] = list(commits)
        record["transactions"] = list(transactions)
        if calibration_signature is not None:
            record["calibration_signature"] = dict(calibration_signature)
        self._trials.append(record)
        self._active = None

    def abort_trial(self, reason, traceback_text=None):
        """Retain a failed calibration attempt without poisoning later trials."""
        if self._active is None:
            return
        record = dict(self._active)
        record.pop("spec", None)
        record.pop("last_sample_values", None)
        record.pop("packed_sample_until", None)
        record.pop("fetch_cursor", None)
        record.update({
            "fetch_events": [],
            "commits": [],
            "transactions": [],
            "calibration_error": str(reason),
            "calibration_error_type": type(reason).__name__,
            "calibration_traceback": traceback_text,
        })
        self._trials.append(record)
        self._active = None

    def finalize(self):
        if self.full_finalization_count >= 2:
            raise RuntimeError(
                "revision-11 permits at most two full pipeline "
                "classifications per core"
            )
        self.full_finalization_count += 1
        return classify_pipeline_interface(
            [
                trial for trial in self._trials
                if not trial.get("discovery_only")
            ],
            self.discovery,
            discovery_error=self.discovery_error,
            pipeline_depth=self.pipeline_depth,
        )

    def trial_cursor(self):
        """Return an opaque cursor for subsequent incremental enrichment."""
        return len(self._trials)

    def trials_since(self, cursor):
        """Return only completed trials added since ``cursor``."""
        return [
            trial for trial in self._trials[int(cursor):]
            if not trial.get("discovery_only")
        ]

    def discard_trials_since(self, cursor):
        """Release raw traces already compacted by frozen-chain validation."""
        cursor = int(cursor)
        removed = len(self._trials) - cursor
        del self._trials[cursor:]
        removed = max(0, removed)
        self.discarded_raw_trial_count += removed
        return removed


def _fetch_token(event, occurrence):
    epoch = event.get("epoch_id")
    transaction = event.get("transaction_id")
    slot = event.get("transaction_slot", 0)
    return f"{epoch}:{transaction}:{slot}:{occurrence}"


def _trial_stage_window(trial, pipeline_depth=None):
    """Bound stage propagation using observed retirement and estimated depth."""
    fetches = trial.get("fetch_events", [])
    latencies = []
    for commit in trial.get("commits", []):
        cycle = commit.get("cycle")
        preceding = [
            event.get("cycle") for event in fetches
            if event.get("offset") == commit.get("offset")
            and event.get("cycle") is not None and cycle is not None
            and event["cycle"] <= cycle
        ]
        if preceding:
            latencies.append(cycle - max(preceding))
    observed = int(max(latencies)) + 2 if latencies else 0
    depth_bound = int(pipeline_depth or 0) + 2
    return min(MAX_STAGE_WINDOW_CYCLES, max(4, observed, depth_bound))


def _scaled_pc(value, address_mode):
    value = int(value)
    return value >> 2 if address_mode == "word" else value


def _coalesced_affine_fetches(trial):
    """Collapse consecutive held requests without merging later PC replays."""
    fetches = [
        fetch for fetch in sorted(
            trial.get("fetch_events", ()),
            key=lambda item: (
                item.get("cycle", -1),
                item.get("transaction_slot", 0),
            ),
        )
        if fetch.get("canonical_pc") is not None
        and fetch.get("cycle") is not None
        and not fetch.get("squashed")
        and not fetch.get("terminal_loop")
    ]
    coalesced = []
    for fetch in fetches:
        previous = coalesced[-1] if coalesced else None
        if (
            previous is not None
            and fetch.get("canonical_pc")
            == previous.get("canonical_pc")
            and int(fetch.get("transaction_slot", 0))
            == int(previous.get("transaction_slot", 0))
            and fetch.get("epoch_id") == previous.get("epoch_id")
            and int(fetch["cycle"]) == int(
                previous.get("_held_exit_cycle", previous["cycle"])
            ) + 1
        ):
            previous["_held_exit_cycle"] = int(fetch["cycle"])
            previous["_held_fetch_count"] = int(
                previous.get("_held_fetch_count", 1)
            ) + 1
            continue
        coalesced.append({
            **fetch,
            "_held_exit_cycle": int(fetch["cycle"]),
            "_held_fetch_count": 1,
        })
    return coalesced


def _preferred_affine_owner(
    sample, fetches, mode, bias, modulus, window, preferred_lag,
):
    owners = [
        fetch for fetch in fetches
        if (
            _scaled_pc(fetch["canonical_pc"], mode) + bias
        ) % modulus == int(sample.get("value", -1)) % modulus
        and int(fetch["cycle"]) <= int(sample["cycle"])
        <= int(fetch["cycle"]) + window
    ]
    distances = [
        (
            abs(
                (int(sample["cycle"]) - int(fetch["cycle"]))
                - preferred_lag
            ),
            fetch,
        )
        for fetch in owners
    ]
    best_distance = min(
        (distance for distance, _ in distances), default=None,
    )
    best = [
        fetch for distance, fetch in distances
        if distance == best_distance
    ]
    return best[0] if len(best) == 1 else None


def _fit_affine_stage_events(path, trials, address_mode, width=None):
    """Fit one fixed byte/word bias and materialize token residences."""
    if address_mode not in {"byte", "word"}:
        return None, {}
    width = int(width or 64)
    modulus = 1 << min(max(width, 1), 64)
    bias_tokens = defaultdict(set)
    for trial in trials:
        window = _trial_stage_window(trial)
        samples = [
            item for item in trial.get("raw_stage_samples", ())
            if item.get("path") == path and item.get("cycle") is not None
        ]
        for fetch_index, fetch in enumerate(
            _coalesced_affine_fetches(trial)
        ):
            expected = _scaled_pc(
                fetch["canonical_pc"], address_mode,
            )
            for sample in samples:
                if (
                    int(fetch["cycle"])
                    <= int(sample["cycle"])
                    <= int(fetch["cycle"]) + window
                ):
                    bias = (int(sample["value"]) - expected) % modulus
                    bias_tokens[bias].add((
                        str(trial.get("trial_id")), fetch_index,
                    ))
    if not bias_tokens:
        return None, {}
    bias = max(
        bias_tokens,
        key=lambda item: (len(bias_tokens[item]), -int(item)),
    )
    unique_owner_lags = []
    for trial in trials:
        window = _trial_stage_window(trial)
        fetches = _coalesced_affine_fetches(trial)
        for sample in trial.get("raw_stage_samples", ()):
            if (
                sample.get("path") != path
                or sample.get("cycle") is None
            ):
                continue
            owners = [
                fetch for fetch in fetches
                if (
                    _scaled_pc(
                        fetch["canonical_pc"], address_mode,
                    ) + bias
                ) % modulus
                == int(sample.get("value", -1)) % modulus
                and int(fetch["cycle"]) <= int(sample["cycle"])
                <= int(fetch["cycle"]) + window
            ]
            if len(owners) == 1:
                unique_owner_lags.append(
                    int(sample["cycle"]) - int(owners[0]["cycle"])
                )
    preferred_lag = (
        median(unique_owner_lags) if unique_owner_lags else 0
    )
    by_trial = {}
    residence_ambiguity_count = 0
    for trial in trials:
        window = _trial_stage_window(trial)
        samples = [
            item for item in trial.get("raw_stage_samples", ())
            if item.get("path") == path and item.get("cycle") is not None
        ]
        used = set()
        events = []
        eligible_fetches = _coalesced_affine_fetches(trial)
        for fetch in eligible_fetches:
            expected_value = (
                _scaled_pc(fetch["canonical_pc"], address_mode) + bias
            ) % modulus
            matches = [
                item for item in samples
                if id(item) not in used
                and int(item.get("value", -1)) % modulus
                == expected_value
                and int(fetch["cycle"])
                <= int(item["cycle"])
                <= int(fetch["cycle"]) + window
            ]
            unambiguous = []
            for item in matches:
                owner = _preferred_affine_owner(
                    item, eligible_fetches, address_mode, bias,
                    modulus, window, preferred_lag,
                )
                if owner is fetch:
                    unambiguous.append(item)
                elif owner is None:
                    residence_ambiguity_count += 1
            matches = unambiguous
            if not matches:
                continue
            matches.sort(key=lambda item: int(item["cycle"]))
            residence = [matches[0]]
            for item in matches[1:]:
                if int(item["cycle"]) > int(residence[-1]["cycle"]) + 1:
                    break
                residence.append(item)
            used.update(id(item) for item in residence)
            first = residence[0]
            last = residence[-1]
            instruction_value = first.get("instruction_value")
            expected_instruction = (
                trial.get("instruction_by_offset", {})
                .get(int(fetch.get("offset")))
            )
            valid_states = sorted({
                bool(item.get("valid_value"))
                for item in residence
                if item.get("valid_value") is not None
            })
            events.append({
                **first,
                "offset": int(fetch.get("offset")),
                "address_mode": address_mode,
                "instruction_matches": (
                    None if first.get("instruction_path") is None
                    else instruction_value == expected_instruction
                ),
                "residence_entry_cycle": int(first["cycle"]),
                "residence_entry_phase": first.get("phase", "post_edge"),
                "residence_exit_cycle": int(last["cycle"]),
                "residence_exit_phase": last.get("phase", "post_edge"),
                "residence_hold_cycles": (
                    int(last["cycle"]) - int(first["cycle"])
                ),
                "residence_sample_count": len(residence),
                "residence_valid_states": valid_states,
                "residence_flush_outcome": any(
                    bool(item.get("flush_value"))
                    for item in residence
                ),
                "address_transform": {
                    "mode": address_mode,
                    "scale": "1/4" if address_mode == "word" else "1",
                    "bias": int(bias),
                    "width": width,
                },
            })
        by_trial[str(trial.get("trial_id"))] = events
    return {
        "mode": address_mode,
        "scale": "1/4" if address_mode == "word" else "1",
        "bias": int(bias),
        "width": width,
        "supporting_token_count": len(bias_tokens[bias]),
        "candidate_bias_count": len(bias_tokens),
        "preferred_lag": preferred_lag,
        "residence_ambiguity_count": residence_ambiguity_count,
    }, by_trial


def _materialize_affine_trial_events(path, trial, transform):
    """Apply a previously frozen transform to one incremental trial."""
    if not transform or transform.get("mode") not in {"byte", "word"}:
        return []
    width = int(transform.get("width") or 64)
    modulus = 1 << min(max(width, 1), 64)
    bias = int(transform.get("bias") or 0)
    mode = transform["mode"]
    window = _trial_stage_window(trial)
    samples = [
        item for item in trial.get("raw_stage_samples", ())
        if item.get("path") == path and item.get("cycle") is not None
    ]
    used = set()
    events = []
    eligible_fetches = _coalesced_affine_fetches(trial)
    preferred_lag = transform.get("preferred_lag")
    if preferred_lag is None:
        unique_lags = []
        for item in samples:
            owners = [
                other for other in eligible_fetches
                if (
                    _scaled_pc(other["canonical_pc"], mode) + bias
                ) % modulus
                == int(item.get("value", -1)) % modulus
                and int(other["cycle"]) <= int(item["cycle"])
                <= int(other["cycle"]) + window
            ]
            if len(owners) == 1:
                unique_lags.append(
                    int(item["cycle"]) - int(owners[0]["cycle"])
                )
        preferred_lag = median(unique_lags) if unique_lags else 0
    for fetch in eligible_fetches:
        expected = (
            _scaled_pc(fetch["canonical_pc"], mode) + bias
        ) % modulus
        matches = [
            item for item in samples
            if id(item) not in used
            and int(item.get("value", -1)) % modulus == expected
            and int(fetch["cycle"]) <= int(item["cycle"])
            <= int(fetch["cycle"]) + window
            and _preferred_affine_owner(
                item, eligible_fetches, mode, bias, modulus,
                window, preferred_lag,
            ) is fetch
        ]
        if not matches:
            continue
        matches.sort(key=lambda item: int(item["cycle"]))
        residence = [matches[0]]
        for item in matches[1:]:
            if int(item["cycle"]) > int(residence[-1]["cycle"]) + 1:
                break
            residence.append(item)
        used.update(id(item) for item in residence)
        first, last = residence[0], residence[-1]
        expected_instruction = trial.get(
            "instruction_by_offset", {}
        ).get(int(fetch.get("offset")))
        valid_states = sorted({
            bool(item.get("valid_value"))
            for item in residence
            if item.get("valid_value") is not None
        })
        events.append({
            **first,
            "offset": int(fetch.get("offset")),
            "address_mode": mode,
            "instruction_matches": (
                None if first.get("instruction_path") is None
                else first.get("instruction_value")
                == expected_instruction
            ),
            "residence_entry_cycle": int(first["cycle"]),
            "residence_entry_phase": first.get("phase", "post_edge"),
            "residence_exit_cycle": int(last["cycle"]),
            "residence_exit_phase": last.get("phase", "post_edge"),
            "residence_hold_cycles": (
                int(last["cycle"]) - int(first["cycle"])
            ),
            "residence_sample_count": len(residence),
            "residence_valid_states": valid_states,
            "residence_flush_outcome": any(
                bool(item.get("flush_value")) for item in residence
            ),
            "address_transform": dict(transform),
        })
    return events


def _pair_candidate_events(trial, events, window):
    """Associate one candidate occurrence with one accepted fetch transaction."""
    by_offset = defaultdict(list)
    for event in sorted(events, key=lambda item: item["cycle"]):
        by_offset[event.get("offset")].append(event)
    used = set()
    paired = []
    occurrences = defaultdict(int)
    terminal_cycles = [
        event.get("cycle") for event in trial.get("fetch_events", [])
        if event.get("terminal_loop") and event.get("cycle") is not None
    ]
    architectural_cycles = [
        item.get("cycle") for key in ("commits", "transactions")
        for item in trial.get(key, []) if item.get("cycle") is not None
    ]
    cutoff = min(terminal_cycles) if terminal_cycles else (
        max(architectural_cycles) + 2 if architectural_cycles else None
    )
    ordered_fetches = sorted(
        (
            event for event in trial.get("fetch_events", [])
            if not event.get("squashed") and not event.get("terminal_loop")
            and (cutoff is None or event.get("cycle", -1) <= cutoff)
        ),
        key=lambda item: (item.get("cycle", -1), item.get("transaction_slot", 0)),
    )
    # Forwarding probes are straight-line programs: an offset belongs to one
    # intended dynamic instruction. Later occurrences are replays after the
    # measured execution and must not create new stage tokens.
    fetches = []
    seen_fetch_offsets = set()
    for event in ordered_fetches:
        if event.get("offset") in seen_fetch_offsets:
            continue
        seen_fetch_offsets.add(event.get("offset"))
        fetches.append(event)
    for fetch in fetches:
        offset = fetch.get("offset")
        fetch_cycle = fetch.get("cycle")
        if fetch_cycle is None:
            continue
        occurrence = occurrences[offset]
        occurrences[offset] += 1
        match_index = next((
            index for index, event in enumerate(by_offset.get(offset, []))
            if id(event) not in used
            and fetch_cycle <= event.get("cycle", -1) <= fetch_cycle + window
        ), None)
        if match_index is None:
            continue
        event = by_offset[offset][match_index]
        used.add(id(event))
        paired.append({
            **event,
            "fetch_cycle": fetch_cycle,
            "fetch_token": _fetch_token(fetch, occurrence),
            "fetch_pc": fetch.get("pc"),
            "fetch_raw_pc": fetch.get("raw_pc"),
            "fetch_canonical_pc": fetch.get("canonical_pc"),
            "fetch_base_pc": fetch.get("base_pc"),
            "transaction_id": fetch.get("transaction_id"),
            "epoch_id": fetch.get("epoch_id"),
            "transaction_slot": fetch.get("transaction_slot", 0),
            "lag": event["cycle"] - fetch_cycle,
        })
    return paired


def _alignment_errors(trial, paired):
    commit_errors = []
    memory_errors = []
    for event in paired:
        commits = [
            item for item in trial.get("commits", [])
            if item.get("offset") == event.get("offset") and item.get("cycle") is not None
            and item["cycle"] >= event["cycle"]
        ]
        if commits:
            commit_errors.append(min(item["cycle"] - event["cycle"] for item in commits))
        program = str(trial.get("program") or "")
        wanted_kind = None
        wanted_offset = None
        if program.startswith("load_to_"):
            wanted_kind, wanted_offset = "load", trial.get("producer_offset")
        if "store_" in program or "_to_store" in program:
            wanted_kind, wanted_offset = "store", trial.get("consumer_offset")
        if event.get("offset") == wanted_offset:
            transactions = [
                item for item in trial.get("transactions", [])
                if item.get("kind") == wanted_kind and item.get("cycle") is not None
            ]
            if transactions:
                memory_errors.append(min(abs(item["cycle"] - event["cycle"]) for item in transactions))
    return commit_errors, memory_errors


def _stage_candidate_identity(candidate, trial_by_id):
    """Return compact, behavioral identity diagnostics for one stage stream."""
    paired_by_trial = candidate.get("paired_by_trial", {})
    signal_kind = candidate.get("signal_kind")
    address_mode = candidate.get("address_mode")
    address_transform = candidate.get("address_transform") or {}
    transform_width = int(address_transform.get("width") or 64)
    transform_modulus = 1 << min(max(transform_width, 1), 64)
    transform_bias = int(address_transform.get("bias") or 0)
    calibration_ids = [
        trial_id for trial_id, trial in trial_by_id.items()
        if str(trial.get("program", "")).startswith(
            "pipeline_calibration_flow_"
        )
    ]
    eligible_epochs = set()
    matched_epochs = set()
    rejections = {
        "address_mode": 0,
        "affine_fit_failure": 0,
        "insufficient_distinct_bases": 0,
        "relocation": 0,
        "redirect": 0,
        "instruction_companion": 0,
        "companion_rejection": 0,
        "valid_flush_state": 0,
        "transaction_slot": 0,
        "lane": 0,
        "residence_ambiguity": int(
            address_transform.get("residence_ambiguity_count") or 0
        ),
        "census_exclusion": 0,
        "graph_edge_mismatch": 0,
        "predecessor_current_stage_linkage": 0,
    }
    exact_by_trial = {}
    bases = set()
    redirect_trials = 0
    redirect_matches = 0
    redirect_source_matches = 0
    wrong_path_after_redirect = 0
    for trial_id in calibration_ids:
        trial = trial_by_id[trial_id]
        fetches = [
            item for item in trial.get("fetch_events", ())
            if not item.get("terminal_loop")
        ]
        for fetch in fetches:
            epoch = (
                str(fetch.get("epoch_id"))
                if fetch.get("epoch_id") is not None
                else str(fetch.get("transaction_id"))
            )
            eligible_epochs.add(f"{trial_id}:{epoch}")
        paired = paired_by_trial.get(trial_id, ())
        exact = []
        for event in paired:
            expected = event.get("fetch_canonical_pc")
            if expected is None:
                continue
            expected = (
                _scaled_pc(expected, address_mode) + transform_bias
            ) % transform_modulus
            if int(event.get("value", -1)) % transform_modulus != expected:
                rejections["relocation"] += 1
                continue
            if (
                event.get("instruction_path") is not None
                and event.get("instruction_matches") is not True
            ):
                rejections["instruction_companion"] += 1
                rejections["companion_rejection"] += 1
            if (
                event.get("valid_value") is not None
                and not bool(event.get("valid_value"))
            ) or bool(event.get("flush_value")):
                rejections["valid_flush_state"] += 1
            exact.append(event)
            epoch = (
                str(event.get("epoch_id"))
                if event.get("epoch_id") is not None
                else str(event.get("transaction_id"))
            )
            matched_epochs.add(f"{trial_id}:{epoch}")
            relocation_base = trial.get(
                "calibration_relocation_base",
                event.get("fetch_base_pc"),
            )
            if relocation_base is not None:
                bases.add(int(relocation_base))
            lane = candidate.get("lane_id")
            slot = int(event.get("transaction_slot", 0))
            if (
                (lane is not None and slot != int(lane))
                or (lane is None and slot != 0)
            ):
                rejections["lane"] += 1
                rejections["transaction_slot"] += 1
        exact_by_trial[trial_id] = exact
        control = trial.get("control_flow") or {}
        source_offset = control.get("redirect_offset")
        target_offset = control.get("target_offset")
        wrong_offsets = set(control.get("wrong_path_offsets", ()))
        if target_offset is not None:
            redirect_trials += 1
            target_events = [
                item for item in exact
                if item.get("offset") == target_offset
            ]
            source_fetches = [
                item for item in fetches
                if source_offset is None
                or item.get("offset") == source_offset
            ]
            target_fetches = [
                item for item in fetches
                if item.get("offset") == target_offset
                and not item.get("squashed")
            ]
            if source_fetches:
                redirect_source_matches += 1
            source_cycle = min(
                (
                    item.get("cycle")
                    for item in source_fetches
                    if item.get("cycle") is not None
                ),
                default=None,
            )
            target_fetch_cycle = min(
                (
                    item.get("cycle")
                    for item in target_fetches
                    if item.get("cycle") is not None
                ),
                default=None,
            )
            ordered_redirect = bool(
                source_cycle is not None
                and target_fetch_cycle is not None
                and int(source_cycle) <= int(target_fetch_cycle)
            )
            if target_events and ordered_redirect:
                redirect_matches += 1
                target_cycle = min(
                    item["cycle"] for item in target_events
                )
                wrong_path_after_redirect += sum(
                    item.get("offset") in wrong_offsets
                    and int(item.get("cycle", -1)) >= int(target_cycle)
                    for item in exact
                )
            else:
                rejections["redirect"] += 1

    relocation_required = bool(
        signal_kind == "pc" and calibration_ids
    )
    if signal_kind == "pc" and address_mode not in {"byte", "word"}:
        rejections["address_mode"] += max(1, len(calibration_ids))
    if signal_kind == "pc" and not address_transform:
        rejections["affine_fit_failure"] += max(1, len(calibration_ids))
    exact_trial_coverage = sum(
        len(values) >= 2 for values in exact_by_trial.values()
    )
    relocation_roles_permitted = bool(
        calibration_ids
        and all(
            trial_by_id[trial_id].get(
                "relocation_roles_permitted", True
            )
            for trial_id in calibration_ids
        )
    )
    affine_transform_required = any(
        "relocation_roles_permitted" in trial_by_id[trial_id]
        or bool(trial_by_id[trial_id].get("raw_stage_samples"))
        for trial_id in calibration_ids
    )
    distinct_transformed_bases = {
        _scaled_pc(base, address_mode) % transform_modulus
        for base in bases
    } if address_mode in {"byte", "word"} else set()
    relocation_delta_checks = 0
    relocation_delta_matches = 0
    calibration_maps = []
    for trial_id in calibration_ids:
        trial = trial_by_id[trial_id]
        origin = int(
            trial.get("calibration_relocation_origin") or 0
        )
        values = {
            int(item.get("offset")) - origin:
                int(item.get("value"))
            for item in exact_by_trial.get(trial_id, ())
            if item.get("offset") is not None
        }
        relocation_base = trial.get(
            "calibration_relocation_base"
        )
        if relocation_base is None:
            base_values = {
                int(item.get("fetch_base_pc"))
                for item in exact_by_trial.get(trial_id, ())
                if item.get("fetch_base_pc") is not None
            }
            relocation_base = (
                next(iter(base_values))
                if len(base_values) == 1 else None
            )
        if values and relocation_base is not None:
            calibration_maps.append((
                int(relocation_base), values,
            ))
    for left_index, (left_base, left_values) in enumerate(
        calibration_maps
    ):
        for right_base, right_values in calibration_maps[
            left_index + 1:
        ]:
            expected_delta = (
                _scaled_pc(right_base, address_mode)
                - _scaled_pc(left_base, address_mode)
            ) % transform_modulus
            for offset in set(left_values) & set(right_values):
                relocation_delta_checks += 1
                relocation_delta_matches += int(
                    (
                        int(right_values[offset])
                        - int(left_values[offset])
                    ) % transform_modulus == expected_delta
                )
    relocation_proven = bool(
        signal_kind == "pc"
        and address_mode in {"byte", "word"}
        and (
            not affine_transform_required
            or address_transform.get("mode") in {"byte", "word"}
        )
        and len(calibration_ids) == 3
        and len(bases) == 3
        and len(distinct_transformed_bases) == 3
        and relocation_roles_permitted
        and exact_trial_coverage == len(calibration_ids)
        and relocation_delta_checks > 0
        and relocation_delta_matches == relocation_delta_checks
        and (not redirect_trials or (
            redirect_matches == redirect_trials
            and wrong_path_after_redirect == 0
        ))
        and not rejections["lane"]
    )
    if (
        signal_kind == "pc"
        and (
            len(calibration_ids) < 3
            or len(distinct_transformed_bases) < 3
            or not relocation_roles_permitted
        )
    ):
        rejections["insufficient_distinct_bases"] += max(
            1, 3 - len(distinct_transformed_bases),
        )
    if signal_kind == "pc" and relocation_required and not relocation_proven:
        rejections["relocation"] += max(
            1, len(calibration_ids) - exact_trial_coverage
        )
    if signal_kind == "instruction":
        rejections["instruction_companion"] = 1
    primary_order = [
        "address_mode", "affine_fit_failure",
        "insufficient_distinct_bases", "relocation", "redirect",
        "residence_ambiguity",
        "transaction_slot", "lane",
    ]
    if signal_kind == "instruction":
        primary_order.insert(3, "instruction_companion")
    primary = next((
        name for name in (
            primary_order
        ) if rejections[name]
    ), None)
    return {
        "path": candidate.get("path"),
        "signal_kind": signal_kind,
        "address_mode": address_mode,
        "eligible_fetch_epochs": sorted(eligible_epochs),
        "exact_matched_fetch_epochs": sorted(matched_epochs),
        "eligible_epoch_count": len(eligible_epochs),
        "exact_matched_epoch_count": len(matched_epochs),
        "executed_bases": sorted(bases),
        "relocation_delta_checks": relocation_delta_checks,
        "relocation_delta_matches": relocation_delta_matches,
        "exact_calibration_trials": exact_trial_coverage,
        "eligible_calibration_trials": len(calibration_ids),
        "redirect_trials": redirect_trials,
        "redirect_matches": redirect_matches,
        "redirect_source_matches": redirect_source_matches,
        "wrong_path_after_redirect": wrong_path_after_redirect,
        "rejection_counts": rejections,
        "relocation_required": relocation_required,
        "relocation_roles_permitted": relocation_roles_permitted,
        "affine_transform_required": affine_transform_required,
        "distinct_transformed_base_count": len(
            distinct_transformed_bases
        ),
        "address_transform": {
            **address_transform,
            "delta_checks": relocation_delta_checks,
            "delta_matches": relocation_delta_matches,
            "distinct_base_count": len(distinct_transformed_bases),
            "rejection_reason": (
                None if relocation_proven
                else "insufficient_distinct_bases"
                if not relocation_roles_permitted
                or len(distinct_transformed_bases) < 3
                else "affine_fit_failure"
            ),
        } if signal_kind == "pc" else None,
        "relocation_proven": (
            relocation_proven if relocation_required else None
        ),
        "primary_rejection_reason": primary,
        "state": "scored",
    }


def _candidate_alias_groups(candidates):
    groups = []
    remaining = list(candidates)
    while remaining:
        first = remaining.pop(0)
        fingerprint = first["event_fingerprint"]
        aliases = [
            item for item in remaining
            if fingerprint and item["event_fingerprint"] == fingerprint
            and item.get("lane_id") == first.get("lane_id")
            and item.get("signal_kind") == first.get("signal_kind")
        ]
        remaining = [item for item in remaining if item not in aliases]
        group = [first, *aliases]
        group.sort(key=lambda item: (-item.get("score", 0), -item.get("static_rank", 0), item["path"]))
        canonical = group[0]
        canonical["alias_paths"] = [item["path"] for item in group[1:]]
        groups.append(canonical)
    return groups


def _behaviorally_equivalent_stage_stream(left, right):
    """Return true when two same-lane candidates identify the same tokens.

    Hierarchy aliases are not always bit-for-bit identical for the whole run:
    one view may retain an extra reset or terminal-loop sample.  What matters
    for a stage token is that every shared accepted fetch token is observed at
    the same cycle and that almost all measured tokens overlap.
    """
    if left.get("lane_id") != right.get("lane_id"):
        return False
    if left.get("signal_kind") != right.get("signal_kind"):
        return False
    if left.get("median_fetch_offset_cycles") != right.get(
        "median_fetch_offset_cycles"
    ):
        return False

    def token_cycles(candidate):
        return {
            # ``_pair_candidate_events`` has already bound this event to the
            # accepted fetch epoch.  Trial plus program offset is therefore
            # the stable dynamic-token identity even when two hierarchy views
            # expose different wrapper transaction labels.
            (str(trial_id), event.get("offset")):
            int(event["cycle"])
            for trial_id, events in candidate.get(
                "paired_by_trial", {}
            ).items()
            for event in events
            if event.get("fetch_token") is not None
            and event.get("cycle") is not None
        }

    left_tokens = token_cycles(left)
    right_tokens = token_cycles(right)
    shared = set(left_tokens) & set(right_tokens)
    union = set(left_tokens) | set(right_tokens)
    cycle_agreement = [
        left_tokens[token] == right_tokens[token] for token in shared
    ]
    bounded_disagreement = all(
        abs(left_tokens[token] - right_tokens[token]) <= 1
        for token in shared
    )
    return bool(
        len(shared) >= 3
        and union
        and len(shared) / len(union) >= 0.98
        and sum(cycle_agreement) / len(cycle_agreement) >= 0.98
        and bounded_disagreement
    )


def _better_alignment(candidate, frontend, key, maximum=2):
    value = candidate.get(key)
    if value is None or value > maximum:
        return False
    baseline = frontend.get(key)
    return baseline is None or value < baseline


def _same_stage_companions(left, right):
    """Recognize complementary PC/instruction views without calling them aliases."""
    if left.get("signal_kind") == right.get("signal_kind"):
        return False
    if left.get("lane_id") != right.get("lane_id"):
        return False
    if _scope_distance(_parent(left["path"]), _parent(right["path"])) > 4:
        return False
    if not left.get("name_role_hint") or left.get("name_role_hint") != right.get("name_role_hint"):
        return False
    left_events = {(trial, token): cycle for trial, token, cycle in left["event_fingerprint"]}
    right_events = {(trial, token): cycle for trial, token, cycle in right["event_fingerprint"]}
    shared = set(left_events) & set(right_events)
    return bool(shared) and all(abs(left_events[key] - right_events[key]) <= 1 for key in shared)


def _compose_stage_candidates(candidates):
    """Pair complementary PC/instruction streams before same-lag conflicts."""
    pcs = [item for item in candidates if item.get("signal_kind") == "pc"]
    instructions = [
        item for item in candidates if item.get("signal_kind") == "instruction"
    ]
    pairings = []
    rejected = []
    for pc in pcs:
        pc_events = {
            (trial, token): cycle
            for trial, token, cycle in pc.get("event_fingerprint", ())
        }
        for instruction in instructions:
            if pc.get("lane_id") != instruction.get("lane_id"):
                rejected.append({
                    "pc": pc["path"], "instruction": instruction["path"],
                    "reason": "lane mismatch",
                })
                continue
            role_pc = pc.get("name_role_hint")
            role_instruction = instruction.get("name_role_hint")
            if (
                role_pc and role_instruction
                and role_pc != role_instruction
            ):
                rejected.append({
                    "pc": pc["path"], "instruction": instruction["path"],
                    "reason": "semantic role mismatch",
                })
                continue
            distance = _scope_distance(
                _parent(pc["path"]), _parent(instruction["path"])
            )
            if distance > 6:
                rejected.append({
                    "pc": pc["path"], "instruction": instruction["path"],
                    "reason": "hierarchy scopes were too distant",
                })
                continue
            instruction_events = {
                (trial, token): cycle
                for trial, token, cycle in instruction.get(
                    "event_fingerprint", ()
                )
            }
            shared = sorted(set(pc_events) & set(instruction_events))
            deltas = [
                int(instruction_events[key]) - int(pc_events[key])
                for key in shared
            ]
            if len(shared) < 3:
                rejected.append({
                    "pc": pc["path"], "instruction": instruction["path"],
                    "reason": "fewer than three shared dynamic tokens",
                })
                continue
            if not deltas or any(abs(delta) > 1 for delta in deltas):
                rejected.append({
                    "pc": pc["path"], "instruction": instruction["path"],
                    "reason": "PC/instruction token timing was not adjacent",
                })
                continue
            if max(deltas) - min(deltas) > 1:
                rejected.append({
                    "pc": pc["path"], "instruction": instruction["path"],
                    "reason": "PC/instruction relative timing was unstable",
                })
                continue
            pairings.append({
                "pc": pc, "instruction": instruction,
                "shared": len(shared), "distance": distance,
                "role_match": int(
                    bool(role_pc) and role_pc == role_instruction
                ),
                "delta": median(deltas),
            })
    pairings.sort(key=lambda item: (
        -item["shared"], -item["role_match"], item["distance"],
        -item["pc"].get("score", 0),
        -item["instruction"].get("score", 0),
        item["pc"]["path"], item["instruction"]["path"],
    ))
    used_pc = set()
    used_instruction = set()
    composites = []
    accepted = []
    for pairing in pairings:
        pc = pairing["pc"]
        instruction = pairing["instruction"]
        if pc["path"] in used_pc or instruction["path"] in used_instruction:
            rejected.append({
                "pc": pc["path"],
                "instruction": instruction["path"],
                "reason": "one-to-one companion was already assigned",
            })
            continue
        used_pc.add(pc["path"])
        used_instruction.add(instruction["path"])
        composite = dict(pc)
        composite["instruction_path"] = instruction["path"]
        composite["companion_paths"] = [
            *pc.get("companion_paths", []), instruction["path"],
        ]
        composite["instruction_correlation"] = max(
            pc.get("instruction_correlation", 0),
            instruction.get("instruction_correlation", 0),
        )
        composite["coverage"] = min(
            pc.get("coverage", 0), instruction.get("coverage", 0)
        )
        composite["score"] = max(
            pc.get("score", 0), instruction.get("score", 0)
        )
        composite["name_role_hint"] = (
            pc.get("name_role_hint")
            or instruction.get("name_role_hint")
        )
        composites.append(composite)
        accepted.append({
            "canonical": pc["path"],
            "companions": [instruction["path"]],
            "shared_tokens": pairing["shared"],
            "relative_cycle_delta": pairing["delta"],
        })
    composites.extend(
        item for item in candidates
        if (
            item.get("signal_kind") == "pc"
            and item["path"] not in used_pc
        ) or (
            item.get("signal_kind") == "instruction"
            and item["path"] not in used_instruction
        )
    )
    return composites, accepted, rejected


def _build_stage_graph(candidates):
    """Build a compact token-progression graph independent of signal names."""
    nodes = []
    edges = []
    for item in candidates:
        nodes.append({
            "path": item["path"],
            "kind": item.get("signal_kind"),
            "lane_id": item.get("lane_id"),
            "lag": item.get("median_fetch_offset_cycles"),
            "coverage": item.get("coverage"),
            "instruction_path": item.get("instruction_path"),
            "anchors": {
                "memory": (
                    item.get("memory_alignment_error") is not None
                    and item.get("memory_alignment_error") <= 2
                ),
                "writeback": (
                    item.get("commit_alignment_error") is not None
                    and item.get("commit_alignment_error") <= 2
                ),
            },
        })
    for left in candidates:
        left_events = {
            (trial, token): (entry, exit_cycle)
            for trial, token, entry, exit_cycle in left.get(
                "residence_fingerprint", ()
            )
        } or {
            (trial, token): (cycle, cycle)
            for trial, token, cycle in left.get("event_fingerprint", ())
        }
        for right in candidates:
            if left is right or left.get("lane_id") != right.get("lane_id"):
                continue
            left_lag = left.get("median_fetch_offset_cycles")
            right_lag = right.get("median_fetch_offset_cycles")
            if (
                left_lag is None or right_lag is None
                or right_lag <= left_lag
            ):
                continue
            right_events = {
                (trial, token): (entry, exit_cycle)
                for trial, token, entry, exit_cycle in right.get(
                    "residence_fingerprint", ()
                )
            } or {
                (trial, token): (cycle, cycle)
                for trial, token, cycle in right.get(
                    "event_fingerprint", ()
                )
            }
            shared = sorted(set(left_events) & set(right_events))
            deltas = [
                int(right_events[key][0]) - int(left_events[key][0])
                for key in shared
            ]
            # An accepted progression edge requires exact tokens to preserve
            # order, but its latency need not be constant.  Backpressure and
            # flush recovery can legitimately stretch the same edge by more
            # than one cycle; rejecting that edge made the graph solver fall
            # back to a lag-only ordering even for real revision-11 traces.
            if len(shared) < 3 or not deltas or min(deltas) < 0:
                continue
            edges.append({
                "from": left["path"],
                "to": right["path"],
                "shared_tokens": len(shared),
                "median_cycle_delta": median(deltas),
                "cycle_delta_span": max(deltas) - min(deltas),
                "residence_ordered": all(
                    int(right_events[key][0])
                    >= int(left_events[key][0])
                    for key in shared
                ),
                "lane_id": left.get("lane_id"),
            })
    return {
        "nodes": nodes,
        "accepted_edges": sorted(
            edges,
            key=lambda item: (
                str(item.get("lane_id")), item["from"], item["to"]
            ),
        ),
    }


def _solve_stage_progression(candidates, graph):
    """Choose one globally ordered stage path from the accepted-token DAG."""
    if not candidates:
        return [], []
    by_path = {item["path"]: item for item in candidates}
    usable_edges = [
        edge for edge in graph.get("accepted_edges", ())
        if edge["from"] in by_path and edge["to"] in by_path
    ]
    incoming = defaultdict(set)
    outgoing = defaultdict(set)
    edge_weight = {}
    for edge in usable_edges:
        incoming[edge["to"]].add(edge["from"])
        outgoing[edge["from"]].add(edge["to"])
        edge_weight[(edge["from"], edge["to"])] = int(
            edge.get("shared_tokens", 0)
        )
    minimum_lag = min(
        item.get("median_fetch_offset_cycles")
        for item in candidates
        if item.get("median_fetch_offset_cycles") is not None
    )
    frontend_pool = [
        item for item in candidates
        if item.get("median_fetch_offset_cycles") == minimum_lag
        and not incoming.get(item["path"])
    ] or [
        item for item in candidates
        if item.get("median_fetch_offset_cycles") == minimum_lag
    ]
    frontend = max(frontend_pool, key=lambda item: (
        float(item.get("coverage", 0)),
        bool(item.get("instruction_path")),
        int(item.get("static_rank", 0)),
        tuple(-ord(char) for char in item["path"]),
    ))

    memo = {}

    def best_from(path):
        if path in memo:
            return memo[path]
        options = []
        for target in sorted(outgoing.get(path, ())):
            tail, shared = best_from(target)
            options.append(([path, *tail], shared + edge_weight[(path, target)]))
        if not options:
            result = ([path], 0)
        else:
            result = max(options, key=lambda value: (
                len(value[0]),
                sum(
                    bool(by_path[node].get("instruction_path"))
                    for node in value[0]
                ),
                sum(
                    bool(
                        by_path[node].get("memory_alignment_error")
                        is not None
                    ) + bool(
                        by_path[node].get("commit_alignment_error")
                        is not None
                    )
                    for node in value[0]
                ),
                value[1],
                tuple(value[0]),
            ))
        memo[path] = result
        return result

    selected_paths, _ = best_from(frontend["path"])
    # Legacy/synthetic traces may contain fewer than three shared tokens and
    # therefore no graph edges.  Keep their deterministic lag ordering, while
    # real revision-11 calibration always supplies the exact-token DAG.
    if (
        len(selected_paths) == 1 and not usable_edges
        and not any(
            item.get("address_transform") for item in candidates
        )
    ):
        selected = sorted(candidates, key=lambda item: (
            item.get("median_fetch_offset_cycles"),
            str(item.get("lane_id")),
            item["path"],
        ))
    else:
        selected = [by_path[path] for path in selected_paths]
    selected_set = {item["path"] for item in selected}
    return selected, [
        item for item in candidates if item["path"] not in selected_set
    ]


def _ordered_event(cycle, phase):
    return (int(cycle), 0 if phase == "pre_edge" else 1)


def _samples_for_path(trial, path):
    index = trial.get("_signal_samples_by_path")
    if index is not None:
        return index.get(path, ())
    return [item for item in trial.get("signal_samples", []) if item.get("path") == path]


def _candidate_pool(discovery, trials, role):
    """Return static and bounded behaviorally materialized packed candidates."""
    candidates = [dict(item) for item in discovery.get("candidates", {}).get(role, [])]
    by_path = {item["path"]: item for item in candidates}
    virtual = defaultdict(lambda: {"count": 0, "sample": None})
    for trial in trials:
        for sample in trial.get("signal_samples", []):
            if sample.get("candidate_role") != role or not sample.get("packed"):
                continue
            virtual[sample["path"]]["count"] += 1
            virtual[sample["path"]]["sample"] = sample
    by_parent = defaultdict(list)
    for path, item in virtual.items():
        sample = item["sample"]
        by_parent[sample.get("parent_path")].append((path, item))
    for parent, items in by_parent.items():
        for path, item in sorted(items, key=lambda pair: (-pair[1]["count"], pair[0])):
            sample = item["sample"]
            by_path[path] = {
                "path": path, "scope": _parent(parent), "width": sample.get("slice_width"),
                "role": role, "static_rank": 0,
                "name_role_hint": _semantic_name_role(parent),
                "lane_hint": sample.get("lane_id") is not None,
                "lane_id": sample.get("lane_id"), "packed": True,
                "parent_path": parent, "bit_offset": sample.get("bit_offset"),
                "slice_width": sample.get("slice_width"),
            }
    return list(by_path.values())


def _limit_virtual_candidates_for_use(candidates):
    """Retain at most eight behaviorally scored slices per packed parent/use."""
    scalar = [item for item in candidates if not item.get("packed_slice")]
    packed = defaultdict(list)
    for item in candidates:
        metadata = item.get("packed_slice")
        if metadata:
            packed[metadata.get("parent_path")].append(item)
    selected = list(scalar)
    for parent in sorted(packed, key=str):
        selected.extend(sorted(
            packed[parent],
            key=lambda item: (
                -item.get("coverage", 0),
                -item.get("phase_consistency", 0),
                item.get("path", ""),
            ),
        )[:MAX_PACKED_VIRTUAL_SLICES])
    return selected


def _sample_value_near(trial, path, cycle, expected, radius=1, preferred_phase=None):
    matches = [
        item for item in _samples_for_path(trial, path)
        if abs(int(item.get("cycle", -999)) - int(cycle)) <= radius
        and (int(item.get("value", 0)) & 0xFFFFFFFF) == (int(expected) & 0xFFFFFFFF)
    ]
    if preferred_phase is not None:
        preferred = [item for item in matches if item.get("phase") == preferred_phase]
        if preferred:
            matches = preferred
    return min(
        matches,
        key=lambda item: (
            abs(int(item["cycle"]) - int(cycle)),
            0 if item.get("phase") == preferred_phase else 1,
        ),
        default=None,
    )


def _last_sample_value(trial, path, cycle, phase="post_edge"):
    target = _ordered_event(cycle, phase)
    candidates = [
        item for item in _samples_for_path(trial, path)
        if _ordered_event(item.get("cycle", -1), item.get("phase")) <= target
    ]
    return max(
        candidates,
        key=lambda item: _ordered_event(item["cycle"], item.get("phase")),
        default=None,
    )


def _candidate_side(path):
    name = _basename(path)
    if "rs1" in name or "src1" in name or "source1" in name:
        return "rs1"
    if "rs2" in name or "src2" in name or "source2" in name:
        return "rs2"
    if "forward_out_a" in name:
        return "rs1"
    if "forward_out_b" in name:
        return "rs2"
    if any(token in name for token in (
        "operand_a", "operand1", "op_a", "opa",
    )):
        return "rs1"
    if any(token in name for token in (
        "operand_b", "operand2", "op_b", "opb",
    )):
        return "rs2"
    if name == "a" and _semantic_name_role(_parent(path)) == "execute":
        return "rs1"
    if name == "b" and _semantic_name_role(_parent(path)) == "execute":
        return "rs2"
    return None


def _operand_candidate_incompatible(path, use):
    """Reject signals whose semantics are producer/result rather than input.

    This is a rejection filter, not positive evidence.  In particular,
    ``alu_rd_dat``-style producer results can coincidentally equal a consumer
    operand across a small probe set, but they do not establish operand use.
    """
    if use not in {"execute", "store_address"}:
        return False
    name = _basename(path)
    return (
        name == "rd_dat"
        or _semantic_name_role(path) == "memory"
        or any(token in name for token in (
            "alu_rd", "add_res", "adder_result", "alu_result",
            "result_o", "result_out",
            "wb_data", "writeback_data", "dram_dout", "dmem_rdata",
            "memory_rdata", "load_response",
        ))
    )


def _source_id_candidate_incompatible(candidate, use):
    """Reject instruction/decode fields masquerading as captured source IDs."""
    path = candidate.get("path", "")
    parent = candidate.get("parent_path", path)
    name = _basename(parent)
    if any(token in name for token in (
        "waddr", "write_addr", "write_address", "destination",
        "dest_id", "dest_addr", "rd_addr", "rd_id",
    )):
        return (
            "destination/writeback register ID cannot prove a consumer "
            f"{use} source ID"
        )
    name_components = {
        component for component in name.replace("[", "_").split("_")
        if component
    }
    if any(token in name for token in (
        "funct", "opcode", "immediate", "imm_bits",
    )) or "imm" in name_components:
        return (
            "decoded instruction field cannot independently prove a captured "
            f"{use} source ID"
        )
    instruction_parent = (
        _name_matches(name, INSTRUCTION_HINTS)
        or name.startswith(("inst_", "instr_", "insn_"))
        or name.endswith(("_inst", "_instr", "_insn"))
    )
    if candidate.get("packed") and instruction_parent:
        return (
            "packed instruction bits cannot independently prove a captured "
            f"{use} source ID"
        )
    parent_components = {
        component.lower()
        for component in str(parent).replace("[", ".").split(".")
        if component
    }
    pc_parent = (
        "pc" in parent_components
        or _name_matches(name, PC_HINTS)
        or name.startswith("pc_")
        or name.endswith("_pc")
    )
    if candidate.get("packed") and pc_parent:
        return (
            "packed PC bits cannot independently prove a captured "
            f"{use} source ID"
        )
    result_parent = any(token in name for token in (
        "alu_out", "alu_result", "add_res", "result_out",
        "mem_wb", "wb_out", "writeback",
    ))
    if candidate.get("packed") and result_parent:
        return (
            "packed producer/result or writeback bits cannot prove a "
            f"captured {use} source ID"
        )
    if use == "store_data" and candidate.get("packed"):
        lowered_parent = str(parent).lower()
        if any(token in lowered_parent for token in (
            ".btb.", ".bht.", "predict", "cache", "icache", "dcache",
            "control_rom", "decode",
        )):
            return (
                "predictor/cache/decode packed fields cannot prove a memory-stage "
                "store source ID"
            )
        if any(token in lowered_parent for token in (
            "ex_mem_in", "execute_mem_in", "mem_stage_in", "mem_wb_in",
        )):
            return (
                "pipeline-register input belongs to the preceding stage and "
                "cannot identify the current memory-stage store token"
            )
        # An opaque packed parent is not rejected merely for lacking a
        # stage-like name. Same-transaction value/phase/lane validation is the
        # positive evidence for anonymous packed records.
    if use == "store_data" and _semantic_name_role(parent) in {
        "frontend", "operand_read",
    }:
        return "decode/frontend source ID cannot prove memory-stage store capture"
    return None


def _store_data_candidate_incompatible(candidate):
    """Reject fields whose observable semantics contradict store data."""
    parent = candidate.get("parent_path", candidate.get("path", ""))
    name = _basename(parent)
    lowered_parent = str(parent).lower()
    if any(token in name for token in (
        "addr", "address", "misalign", "rdata", "read_data",
        "load_data", "load_response", "alu_result", "add_res",
    )):
        return (
            "address, memory-read/load-response, or producer-result signal cannot prove "
            "store-data capture"
        )
    if not candidate.get("packed"):
        return None
    if _name_matches(name, INSTRUCTION_HINTS):
        return "packed instruction fields cannot prove store-data capture"
    if any(token in lowered_parent for token in (
        "mem_wb", "wb_out", "writeback", "alu_out", "alu_result",
        "add_res", "result_out",
    )):
        return (
            "packed producer/result or post-memory writeback field cannot "
            "prove store-data capture"
        )
    if any(token in lowered_parent for token in (
        "rdata", "read_data", "read_value", "load_data", "load_response",
    )):
        return (
            "packed memory-read/load-response data cannot prove store-data "
            "capture"
        )
    return None


def _dependency_consumer_sides(trial, observation, use):
    """Return the source sides carrying the producer RAW in this trial."""
    if "_dependent_" not in str(trial.get("program", "")):
        return set()
    producer = next((
        item for item in trial.get("operand_expectations", ())
        if item.get("role") == "producer"
        and item.get("destination_register") is not None
    ), None)
    if producer is None:
        return set()
    destination = int(producer["destination_register"])
    return {
        side for side in ("rs1", "rs2")
        if observation.get(f"{side}_use") == use
        and observation.get(f"{side}_register") is not None
        and int(observation[f"{side}_register"]) == destination
    }


def _dependency_family(trial):
    program = str(trial.get("program", ""))
    pair_role = trial.get("pair_role")
    return (
        program.split(f"_{pair_role}_", 1)[0]
        if pair_role in {"dependent", "control"} else program
    )


def _trial_eligibility_key(trial, use=None, side=None):
    """Return the immutable dependency-local denominator identity."""
    use = use or _forwarding_trial_use(trial)
    consumer = next((
        item for item in trial.get("operand_expectations", ())
        if item.get("role") == "consumer"
    ), None)
    eligible_sides = set()
    if consumer is not None and use is not None:
        eligible_sides = {
            name for name in ("rs1", "rs2")
            if consumer.get(f"{name}_use") == use
            and consumer.get(f"{name}_register") is not None
        }
        if trial.get("pair_role") == "dependent":
            dependent = _dependency_consumer_sides(
                trial, consumer, use,
            )
            if dependent:
                eligible_sides = dependent
    elif (
        consumer is None and side is not None
        and _forwarding_trial_use(trial) == use
    ):
        # Compatibility for compact synthetic fixtures. Runtime trials always
        # carry the immutable operand expectation on the trial itself.
        eligible_sides = {side}
    if side is not None and side not in eligible_sides:
        return None
    selected_side = side or (
        sorted(eligible_sides)[0] if len(eligible_sides) == 1 else None
    )
    if use is None or not eligible_sides:
        return None
    return (
        _dependency_family(trial),
        use,
        selected_side,
        trial.get("pair_role"),
        trial.get("spacer_kind", "nop"),
        int(trial.get("forwarding_gap", 0)),
        trial.get("variant"),
    )


def _trial_is_eligible(trial, use, side=None):
    paired = (
        trial.get("pair_role") in {"dependent", "control"}
        and trial.get("variant") is not None
    )
    legacy_fixture = (
        trial.get("pair_role") is None
        and trial.get("variant") is None
    )
    return bool(
        (paired or legacy_fixture)
        and _forwarding_trial_use(trial) == use
        and _trial_eligibility_key(trial, use, side) is not None
    )


def _requirement_candidate_rank(item):
    """Rank only candidates that have already passed dynamic validation."""
    path = str(item.get("path", "")).lower()
    name = _basename(path)
    return (
        1 if "forward" in name or name in {"a", "b"} else 0,
        1 if _semantic_name_role(path) == "execute" else 0,
        float(item.get("phase_consistency", 0)),
        int(item.get("matching_trial_count", 0)),
        # Stable deterministic tie breaker (smaller path wins).
        tuple(-ord(char) for char in path),
    )


def _validate_source_selector_candidate(
    candidate, trials, observations, side, use,
):
    """Validate a consumer source selector from matched dependent/control pairs.

    Unlike a general value matcher, this ledger proves that one fixed field
    selects the producer register only in the dependent program and changes to
    the independent source in the layout-matched control program.
    """
    path = candidate["path"]
    paired_variant_trials = [
        trial for trial in trials
        if trial.get("pair_role") in {"dependent", "control"}
        and trial.get("variant") is not None
        and _trial_is_eligible(trial, use, side)
    ]
    if not paired_variant_trials:
        legacy = _validate_data_candidate(
            path, trials, observations, f"{side}_register",
            minimum_distinct=2,
            reject_token_fields=bool(candidate.get("packed")),
        )
        legacy["validation_mode"] = "legacy_unpaired_fixture"
        legacy["rejection_category"] = (
            None if legacy.get("confirmed")
            else "insufficient_paired_selector_coverage"
        )
        return legacy
    attempted = []
    phase_lag_matches = defaultdict(list)
    expected_ids = set()
    forbidden_hits = defaultdict(set)
    paired_roles = defaultdict(lambda: defaultdict(set))

    for trial in trials:
        trial_id = trial["trial_id"]
        pair_role = trial.get("pair_role")
        program = str(trial.get("program", ""))
        if (
            not _trial_is_eligible(trial, use, side)
        ):
            continue
        family = _dependency_family(trial)
        variant = trial.get("variant")
        gap = int(trial.get("forwarding_gap", 0))
        spacer_kind = trial.get("spacer_kind", "nop")
        for observation, stage_cycle in observations.get(trial_id, []):
            if (
                observation.get("role") != "consumer"
                or observation.get(f"{side}_use") != use
                or observation.get(f"{side}_register") is None
            ):
                continue
            expected = int(observation[f"{side}_register"])
            expected_ids.add(expected)
            key = (
                family, use, side, spacer_kind, gap, variant,
            )
            paired_roles[key][pair_role].add(trial_id)
            attempted.append((
                trial, observation, int(stage_cycle), expected, key,
            ))
            forbidden_ids = {
                int(value) & 0x1F
                for value in observation.get("non_source_registers", ())
            }
            other_side = "rs2" if side == "rs1" else "rs1"
            if observation.get(f"{other_side}_register") is not None:
                forbidden_ids.add(
                    int(observation[f"{other_side}_register"]) & 0x1F
                )
            for key_name in (
                "immediate_value", "destination_register", "result_value",
                "poison_value", "effective_address",
            ):
                if observation.get(key_name) is not None:
                    forbidden_ids.add(int(observation[key_name]) & 0x1F)
            forbidden_ids.discard(expected)
            samples = _samples_for_path(trial, path)
            for phase in ("pre_edge", "post_edge"):
                # A transaction-aligned store selector can precede the
                # external request by one cycle. Exact paired IDs, phase, and
                # token association remain mandatory.
                for lag in range(-1, 3):
                    matches = [
                        item for item in samples
                        if item.get("phase") == phase
                        and int(item.get("cycle", -999))
                        == int(stage_cycle) + lag
                        and (int(item.get("value", -1)) & 0x1F) == expected
                    ]
                    if matches:
                        phase_lag_matches[(phase, lag)].append((
                            trial_id, observation, matches[0], stage_cycle,
                            expected, key, pair_role,
                        ))
                    if any(
                        item.get("phase") == phase
                        and int(item.get("cycle", -999))
                        == int(stage_cycle) + lag
                        and (int(item.get("value", -1)) & 0x1F)
                        in forbidden_ids
                        for item in samples
                    ):
                        forbidden_hits[(phase, lag)].add(trial_id)

    selected_phase_lag, selected_matches = max(
        phase_lag_matches.items(),
        key=lambda item: (
            len(item[1]), item[0][0] == "pre_edge", -abs(item[0][1]),
        ),
        default=((None, None), []),
    )
    phase, lag = selected_phase_lag
    matched_trials = {item[0] for item in selected_matches}
    eligible_pairs = {
        key for key, roles in paired_roles.items()
        if roles["dependent"] and roles["control"]
    }
    complete_pairs = {
        key for key in eligible_pairs
        if (
            paired_roles[key]["dependent"] <= matched_trials
            and paired_roles[key]["control"] <= matched_trials
        )
    }
    eligible_groups = defaultdict(set)
    complete_group_variants = defaultdict(set)
    for key in eligible_pairs:
        eligible_groups[key[:5]].add(key[5])
    for key in complete_pairs:
        complete_group_variants[key[:5]].add(key[5])
    required_groups = {
        group: variants for group, variants in eligible_groups.items()
        if len(variants) >= 3
    }
    validated_groups = {
        group for group, variants in required_groups.items()
        if variants <= complete_group_variants[group]
    }
    adjacent_groups = {
        group for group in required_groups
        if group[3] == "nop" and group[4] == 0
    }
    independent_groups = {
        group for group in required_groups
        if group[3] == "independent"
    }
    canonical_required_groups = {
        group: variants for group, variants in required_groups.items()
        if group[3] != "independent"
    }
    complete_variants = {
        variant for group in validated_groups
        for variant in complete_group_variants[group]
        if variant is not None
    }
    dependent_ids = {
        item[4] for item in selected_matches if item[6] == "dependent"
    }
    control_ids = {
        item[4] for item in selected_matches if item[6] == "control"
    }
    collision_trials = forbidden_hits.get(selected_phase_lag, set())
    confirmed = bool(
        len(complete_variants) >= 3
        and len(dependent_ids) >= 3
        and len(control_ids) >= 3
        and bool(adjacent_groups)
        and adjacent_groups <= validated_groups
        and set(canonical_required_groups) <= validated_groups
        and not collision_trials
    )
    if confirmed:
        rejection_category = None
        rejection_reason = None
    elif collision_trials:
        rejection_category = "forbidden_semantic_collision"
        rejection_reason = (
            "candidate followed a destination, other source, immediate, "
            "result, address, or poison discriminator"
        )
    elif not adjacent_groups:
        rejection_category = "insufficient_paired_selector_coverage"
        rejection_reason = (
            "fewer than three matched dependent/control selector variants "
            "were available"
        )
    elif adjacent_groups - validated_groups:
        rejection_category = "dependent_control_selector_mismatch"
        rejection_reason = (
            "candidate did not change from the dependent producer register "
            "to the matched control source"
        )
    else:
        rejection_category = "insufficient_distinct_source_ids"
        rejection_reason = "fewer than three distinct paired source IDs followed"
    ledger = defaultdict(list)
    for (
        trial_id, observation, sample, stage_cycle, expected,
        pair_key, pair_role,
    ) in selected_matches:
        ledger[trial_id].append({
            "probe": pair_key[0],
            "role": pair_key[1],
            "side": pair_key[2],
            "spacer_kind": pair_key[3],
            "gap": pair_key[4],
            "variant": pair_key[5],
            "pair_role": pair_role,
            "consumer_token": {
                "trial_id": trial_id,
                "offset": observation.get("offset"),
            },
            "consumer_offset": observation.get("offset"),
            "side": side,
            "use": use,
            "stage_cycle": stage_cycle,
            "cycle": int(sample["cycle"]),
            "phase": sample.get("phase"),
            "phase_order": sample.get(
                "phase_order",
                0 if sample.get("phase") == "pre_edge" else 1,
            ),
            "lag": int(sample["cycle"]) - stage_cycle,
            "lane_id": candidate.get("lane_id"),
            "value": int(sample.get("value", 0)) & 0x1F,
        })
    return {
        "path": path,
        "attempted": len(attempted),
        "matched": len(selected_matches),
        "matching_trial_count": len(matched_trials),
        "eligible_trial_count": len(attempted),
        "coverage": round(
            len(selected_matches) / max(1, len(attempted)), 3,
        ),
        "trial_coverage": round(
            len(matched_trials) / max(1, len(attempted)), 3,
        ),
        "distinct_expected_values": len(expected_ids),
        "distinct_dependent_source_ids": len(dependent_ids),
        "distinct_control_source_ids": len(control_ids),
        "paired_variants": len(complete_variants),
        "required_trial_groups": [
            {
                "probe": group[0], "role": group[1],
                "side": group[2], "spacer_kind": group[3],
                "gap": group[4],
                "required_variants": sorted(
                    canonical_required_groups[group]
                ),
                "missing_variants": sorted(
                    canonical_required_groups[group]
                    - complete_group_variants[group]
                ),
            }
            for group in sorted(canonical_required_groups)
        ],
        "validated_trial_groups": [
            {
                "probe": group[0], "role": group[1],
                "side": group[2], "spacer_kind": group[3],
                "gap": group[4],
                "validated_variants": sorted(
                    complete_group_variants[group]
                ),
            }
            for group in sorted(validated_groups)
        ],
        "independent_validation_required": bool(independent_groups),
        "independent_validated": bool(
            independent_groups
            and independent_groups <= validated_groups
        ),
        "phase": phase,
        "lag": lag,
        "phase_consistency": 1.0 if selected_matches else 0.0,
        "confirmed": confirmed,
        "rejection_category": rejection_category,
        "rejection_reason": rejection_reason,
        "capture_ledger": dict(ledger),
        "packed_slice": {
            "parent_path": candidate.get("parent_path"),
            "bit_offset": candidate.get("bit_offset"),
            "width": candidate.get("slice_width"),
        } if candidate.get("packed") else None,
    }


def _validate_data_candidate(
    path, trials, observations, value_key, minimum_distinct=3,
    source_id_path=None, register_key=None, reject_token_fields=False,
):
    trial_by_id = {trial["trial_id"]: trial for trial in trials}
    attempted = 0
    values = set()
    phase_matches = defaultdict(list)
    for trial in trials:
        trial_id = trial["trial_id"]
        for observation, stage_cycle in observations.get(trial_id, []):
            expected = observation.get(value_key)
            if expected is None:
                continue
            attempted += 1
            values.add(int(expected) & 0xFFFFFFFF)
            anchors = []
            expected_register = observation.get(register_key) if register_key else None
            if source_id_path and expected_register is not None:
                anchors = [
                    item for item in _samples_for_path(trial, source_id_path)
                    if abs(int(item.get("cycle", -999)) - int(stage_cycle)) <= 2
                    and int(item.get("value", -1)) == int(expected_register)
                ]
            # A pipeline register commonly remains stable on both sides of an
            # edge. Selecting the first matching sample per token made such a
            # signal appear to alternate phases based only on traversal order.
            # Retain one match per phase, then choose a single global phase by
            # token coverage after all trials have been examined.
            for phase in ("pre_edge", "post_edge"):
                samples = []
                if anchors:
                    for anchor in anchors:
                        radius = 0
                        samples.extend(
                            item for item in _samples_for_path(trial, path)
                            if item.get("phase") == phase
                            and int(item.get("cycle", -999)) == int(anchor["cycle"])
                            and (int(item.get("value", 0)) & 0xFFFFFFFF)
                            == (int(expected) & 0xFFFFFFFF)
                        )
                        if not samples:
                            radius = 1
                            samples.extend(
                                item for item in _samples_for_path(trial, path)
                                if item.get("phase") == phase
                                and abs(int(item.get("cycle", -999)) - int(anchor["cycle"])) <= radius
                                and (int(item.get("value", 0)) & 0xFFFFFFFF)
                                == (int(expected) & 0xFFFFFFFF)
                            )
                elif not source_id_path or expected_register is None:
                    samples = [
                        item for item in _samples_for_path(trial, path)
                        if item.get("phase") == phase
                        and abs(int(item.get("cycle", -999)) - int(stage_cycle)) <= 1
                        and (int(item.get("value", 0)) & 0xFFFFFFFF)
                        == (int(expected) & 0xFFFFFFFF)
                    ]
                if samples:
                    sample = min(
                        samples,
                        key=lambda item: abs(
                            int(item.get("cycle", -999)) - int(stage_cycle)
                        ),
                    )
                    source_sample = None
                    if anchors:
                        source_sample = min(
                            anchors,
                            key=lambda item: (
                                abs(
                                    int(item.get("cycle", -999))
                                    - int(sample.get("cycle", -999))
                                ),
                                item.get("phase") != sample.get("phase"),
                            ),
                        )
                    phase_matches[phase].append((
                        trial_id, observation, sample, stage_cycle,
                        source_sample,
                    ))
    selected_phase = max(
        ("pre_edge", "post_edge"),
        key=lambda phase: (len(phase_matches[phase]), phase == "pre_edge"),
    )
    selected_matches = phase_matches[selected_phase]
    matched = len(selected_matches)
    matches_by_trial = defaultdict(list)
    poison_tokens = set()
    instruction_like_tokens = set()
    pc_like_tokens = set()
    semantic_collision_tokens = set()
    semantic_collision_kinds = defaultdict(set)
    capture_ledger = defaultdict(list)
    for (
        trial_id, observation, sample, stage_cycle, source_sample
    ) in selected_matches:
        trial = trial_by_id[trial_id]
        matches_by_trial[trial_id].append(sample)
        capture_ledger[trial_id].append({
            "probe": str(trial.get("program", "")).split(
                f'_{trial.get("pair_role")}_', 1
            )[0],
            "spacer_kind": trial.get("spacer_kind", "nop"),
            "gap": int(trial.get("forwarding_gap", 0)),
            "variant": trial.get("variant"),
            "pair_role": trial.get("pair_role"),
            "consumer_token": {
                "trial_id": trial_id,
                "offset": observation.get("offset"),
            },
            "offset": observation.get("offset"),
            "role": observation.get("role"),
            "side": value_key.split("_", 1)[0],
            "use": observation.get(
                f"{value_key.split('_', 1)[0]}_use"
            ),
            "stage_cycle": int(stage_cycle),
            "cycle": int(sample.get("cycle")),
            "phase": sample.get("phase"),
            "phase_order": sample.get(
                "phase_order",
                0 if sample.get("phase") == "pre_edge" else 1,
            ),
            "value": int(sample.get("value", 0)) & 0xFFFFFFFF,
            "source_id_cycle": (
                None if source_sample is None
                else int(source_sample.get("cycle"))
            ),
            "source_id_phase": (
                None if source_sample is None
                else source_sample.get("phase")
            ),
            "source_id_value": (
                None if source_sample is None
                else int(source_sample.get("value", 0))
            ),
        })
    selected_cycles = defaultdict(list)
    for trial_id, observation, sample, _, _ in selected_matches:
        selected_cycles[(trial_id, observation.get("offset"))].append(
            int(sample["cycle"])
        )
    for trial in trials:
        trial_id = trial["trial_id"]
        for observation, stage_cycle in observations.get(trial_id, []):
            expected_register = (
                observation.get(register_key) if register_key else None
            )
            token_key = (trial_id, observation.get("offset"))
            centers = list(selected_cycles.get(token_key, ()))
            if not centers:
                centers = [int(stage_cycle)]
            if source_id_path and expected_register is not None:
                anchors = [
                    item for item in _samples_for_path(trial, source_id_path)
                    if abs(int(item.get("cycle", -999)) - int(stage_cycle)) <= 2
                    and int(item.get("value", -1)) == int(expected_register)
                ]
                if anchors and token_key not in selected_cycles:
                    centers = [int(item["cycle"]) for item in anchors]
            nearby = [
                item for item in _samples_for_path(trial, path)
                if item.get("phase") == selected_phase
                and any(
                    int(item.get("cycle", -999)) == center
                    for center in centers
                )
            ]
            # A producer observation carries the old destination value so the
            # later dependent consumer can be checked for staleness. That
            # value is not poison for the producer's own source operand
            # (typically x0 for ADDI), so only consumer-like captures may be
            # contaminated by it.
            poison = (
                None if observation.get("role") == "producer"
                else observation.get("poison_value")
            )
            if poison is not None and any(
                (int(item.get("value", 0)) & 0xFFFFFFFF)
                == (int(poison) & 0xFFFFFFFF)
                for item in nearby
            ):
                poison_tokens.add(token_key)
            forbidden_values = {
                int(value) & 0xFFFFFFFF
                for value in observation.get("forbidden_operand_values", ())
            }
            expected_value = observation.get(value_key)
            if expected_value is not None:
                forbidden_values.discard(int(expected_value) & 0xFFFFFFFF)
            explicit_discriminators = {
                "immediate": observation.get("immediate_value"),
                "consumer_result": observation.get("result_value"),
                "effective_address": observation.get("effective_address"),
            }
            for kind, value in explicit_discriminators.items():
                if value is None or (
                    expected_value is not None
                    and (int(value) & 0xFFFFFFFF)
                    == (int(expected_value) & 0xFFFFFFFF)
                ):
                    continue
                if any(
                    (int(item.get("value", 0)) & 0xFFFFFFFF)
                    == (int(value) & 0xFFFFFFFF)
                    for item in nearby
                ):
                    semantic_collision_tokens.add(token_key)
                    semantic_collision_kinds[token_key].add(kind)
            if forbidden_values and any(
                (int(item.get("value", 0)) & 0xFFFFFFFF)
                in forbidden_values
                for item in nearby
            ):
                semantic_collision_tokens.add(token_key)
                semantic_collision_kinds[token_key].add("forbidden_value")
            instruction = trial.get("instruction_by_offset", {}).get(
                int(observation.get("offset", -1))
            )
            if instruction is not None and any(
                (int(item.get("value", 0)) & 0xFFFFFFFF)
                == (int(instruction) & 0xFFFFFFFF)
                for item in nearby
            ):
                instruction_like_tokens.add(token_key)
            fetch = next((
                item for item in trial.get("fetch_events", [])
                if item.get("offset") == observation.get("offset")
                and not item.get("squashed")
            ), None)
            pc_values = set()
            if fetch is not None:
                pc_values.update(
                    int(fetch[key]) & 0xFFFFFFFF
                    for key in ("pc", "raw_pc", "canonical_pc")
                    if fetch.get(key) is not None
                )
                pc_values.add(int(fetch.get("offset", 0)) & 0xFFFFFFFF)
            if pc_values and any(
                (int(item.get("value", 0)) & 0xFFFFFFFF) in pc_values
                for item in nearby
            ):
                pc_like_tokens.add(token_key)

    poison_captures = len(poison_tokens)
    coverage = matched / attempted if attempted else 0.0
    tokens_with_any_phase = max(
        len({
            (trial_id, id(observation))
            for trial_id, observation, *_ in matches
        })
        for matches in phase_matches.values()
    ) if phase_matches else 0
    phase_consistency = matched / max(1, tokens_with_any_phase)
    eligible_trial_ids = {
        trial["trial_id"]
        for trial in trials
        if observations.get(trial["trial_id"], [])
    }
    def is_classifying_dependent(trial):
        program = str(trial.get("program", ""))
        return (
            "_dependent_" in program
            and ("_gap_" not in program or "_gap_0" in program)
        )

    consumer_match_trial_ids = {
        trial_id
        for trial_id, observation, *_ in selected_matches
        if observation.get("role") == "consumer"
    }
    required_trials_by_family = defaultdict(set)
    for trial in trials:
        if not is_classifying_dependent(trial) or not any(
            observation.get("role") == "consumer"
            for observation, _ in observations.get(trial["trial_id"], [])
        ):
            continue
        program = str(trial.get("program", ""))
        family = program.split("_dependent_", 1)[0]
        required_trials_by_family[family].add(trial["trial_id"])
    complete_required_families = sorted(
        family for family, trial_ids in required_trials_by_family.items()
        if len(trial_ids) >= 3 and trial_ids <= consumer_match_trial_ids
    )
    if complete_required_families:
        selected_required_family = max(
            complete_required_families,
            key=lambda family: (
                len(required_trials_by_family[family]),
                family,
            ),
        )
    else:
        selected_required_family = max(
            required_trials_by_family,
            key=lambda family: (
                len(
                    required_trials_by_family[family]
                    & consumer_match_trial_ids
                ),
                -len(required_trials_by_family[family]),
                family,
            ),
            default=None,
        )
    required_trial_ids = (
        set() if selected_required_family is None
        else required_trials_by_family[selected_required_family]
    )
    attempted_trials = len(eligible_trial_ids)
    matching_trial_count = len(matches_by_trial)
    missing_required_trials = sorted(
        required_trial_ids - consumer_match_trial_ids
    )
    trial_coverage = matching_trial_count / max(1, attempted_trials)
    required_capture_complete = bool(
        complete_required_families
    )
    paired_role_trials = defaultdict(lambda: defaultdict(set))
    paired_role_matches = defaultdict(lambda: defaultdict(set))
    for trial in trials:
        program = str(trial.get("program", ""))
        pair_role = trial.get("pair_role")
        if (
            pair_role not in {"dependent", "control"}
            or "_gap_0" not in program
        ):
            continue
        family = program.split(f"_{pair_role}_", 1)[0]
        if observations.get(trial["trial_id"], []):
            paired_role_trials[family][pair_role].add(trial["trial_id"])
    for trial_id in matches_by_trial:
        trial = next(
            (item for item in trials if item["trial_id"] == trial_id), None
        )
        if trial is None or trial.get("pair_role") not in {
            "dependent", "control",
        }:
            continue
        pair_role = trial["pair_role"]
        program = str(trial.get("program", ""))
        family = program.split(f"_{pair_role}_", 1)[0]
        paired_role_matches[family][pair_role].add(trial_id)
    eligible_differential_families = {
        family for family, roles in paired_role_trials.items()
        if len(roles["dependent"]) >= 3 and len(roles["control"]) >= 3
    }
    confirmed_differential_families = sorted(
        family for family in eligible_differential_families
        if (
            paired_role_trials[family]["dependent"]
            <= paired_role_matches[family]["dependent"]
            and paired_role_trials[family]["control"]
            <= paired_role_matches[family]["control"]
        )
    )
    differential_required = bool(eligible_differential_families)
    differential_validated = bool(confirmed_differential_families)
    relaxed_role_trials = defaultdict(set)
    relaxed_role_matches = defaultdict(set)
    for trial in trials:
        program = str(trial.get("program", ""))
        pair_role = trial.get("pair_role")
        if (
            pair_role not in {"dependent", "control"}
            or "_gap_" not in program
            or "_gap_0" in program
            or not observations.get(trial["trial_id"], [])
        ):
            continue
        family = program.split(f"_{pair_role}_", 1)[0]
        group = (
            family, trial.get("spacer_kind", "nop"),
            int(trial.get("forwarding_gap", 0)), pair_role,
        )
        relaxed_role_trials[group].add(trial["trial_id"])
        if trial["trial_id"] in matches_by_trial:
            relaxed_role_matches[group].add(trial["trial_id"])
    eligible_relaxed_groups = {
        key for key, trial_ids in relaxed_role_trials.items()
        if len(trial_ids) >= 3 and key[0] == selected_required_family
    }
    canonical_relaxed_groups = {
        key for key in eligible_relaxed_groups if key[1] != "independent"
    }
    confirmed_relaxed_groups = sorted(
        f"{family}:{spacer_kind}:gap={gap}:{pair_role}"
        for family, spacer_kind, gap, pair_role
        in canonical_relaxed_groups
        if (
            relaxed_role_trials[
                (family, spacer_kind, gap, pair_role)
            ]
            <= relaxed_role_matches[
                (family, spacer_kind, gap, pair_role)
            ]
        )
    )
    relaxed_validation_required = bool(canonical_relaxed_groups)
    relaxed_validated = bool(
        canonical_relaxed_groups
        and len(confirmed_relaxed_groups)
        == len(canonical_relaxed_groups)
    )
    independent_groups = {
        key for key in eligible_relaxed_groups if key[1] == "independent"
    }
    validated_independent_groups = {
        key for key in independent_groups
        if relaxed_role_trials[key] <= relaxed_role_matches[key]
    }
    independent_validation_required = bool(independent_groups)
    independent_validated = bool(
        independent_groups
        and independent_groups == validated_independent_groups
    )
    confirmed = (
        attempted >= 3
        and (coverage >= 0.6 or required_capture_complete)
        and len(values) >= minimum_distinct
        and matching_trial_count >= 3 and phase_consistency >= 0.8
        and not missing_required_trials
        and poison_captures == 0
        and not semantic_collision_tokens
        and (not reject_token_fields or len(instruction_like_tokens) < 3)
        and (not reject_token_fields or len(pc_like_tokens) < 3)
        and (not differential_required or differential_validated)
        and (
            not relaxed_validation_required
            or relaxed_validated
        )
    )
    rejection_reason = None
    if not confirmed:
        if poison_captures:
            rejection_reason = "poison value appeared at the selected capture"
        elif semantic_collision_tokens:
            kinds = sorted({
                kind for values in semantic_collision_kinds.values()
                for kind in values
            })
            rejection_reason = (
                "candidate carried a forbidden semantic discriminator: "
                + ", ".join(kinds)
            )
        elif reject_token_fields and len(instruction_like_tokens) >= 3:
            rejection_reason = "candidate followed instruction encodings"
        elif reject_token_fields and len(pc_like_tokens) >= 3:
            rejection_reason = "candidate followed PC values"
        elif len(values) < minimum_distinct:
            rejection_reason = "insufficient distinct expected values"
        elif matching_trial_count < 3:
            rejection_reason = "fewer than three trials matched"
        elif missing_required_trials:
            rejection_reason = (
                "selected candidate lacked captures for dependent trials: "
                + ", ".join(missing_required_trials)
            )
        elif phase_consistency < 0.8:
            rejection_reason = "capture phase was inconsistent"
        elif differential_required and not differential_validated:
            rejection_reason = (
                "candidate did not follow both matched dependent and control "
                "consumer values"
            )
        elif relaxed_validation_required and not relaxed_validated:
            rejection_reason = (
                "candidate matched the adjacent producer window but did not "
                "follow the consumer across relaxed-distance trials"
            )
        else:
            rejection_reason = "candidate coverage was insufficient"
    return {
        "path": path,
        "coverage": round(coverage, 3),
        "attempted": attempted,
        "matched": matched,
        "distinct_expected_values": len(values),
        "trial_coverage": round(trial_coverage, 3),
        "matching_trial_count": matching_trial_count,
        "eligible_trial_count": attempted_trials,
        "missing_trial_ids": missing_required_trials,
        "confirmed_trial_groups": complete_required_families,
        "differential_required": differential_required,
        "differential_validated": differential_validated,
        "differential_trial_groups": confirmed_differential_families,
        "relaxed_validation_required": relaxed_validation_required,
        "relaxed_validated": relaxed_validated,
        "relaxed_trial_groups": confirmed_relaxed_groups,
        "independent_validation_required": (
            independent_validation_required
        ),
        "independent_validated": independent_validated,
        "independent_trial_groups": [
            f"{family}:{spacer_kind}:gap={gap}:{pair_role}"
            for family, spacer_kind, gap, pair_role
            in sorted(validated_independent_groups)
        ],
        "selected_trial_group": selected_required_family,
        "phase": selected_phase if matched else None,
        "phase_consistency": round(phase_consistency, 3),
        "correct_value_captures": matched,
        "poison_captures": poison_captures,
        "instruction_like_captures": len(instruction_like_tokens),
        "pc_like_captures": len(pc_like_tokens),
        "semantic_collision_captures": len(semantic_collision_tokens),
        "semantic_collision_kinds": sorted({
            kind for values in semantic_collision_kinds.values()
            for kind in values
        }),
        "confirmed": confirmed,
        "rejection_reason": rejection_reason,
        "matches_by_trial": matches_by_trial,
        "capture_ledger": dict(capture_ledger),
    }


def _validate_controls(
    stage, trials, stage_observations, discovery,
    forced_hold_supported=False,
):
    validation = {}
    for role in ("valid", "stall", "flush"):
        candidates = discovery.get("candidates", {}).get(role, [])
        scored = []
        for candidate in candidates:
            if _scope_distance(candidate["path"], stage["pc_path"]) > 8:
                continue
            token_values = []
            non_token_values = []
            holds = []
            releases = []
            flush_hits = 0
            for trial in trials:
                samples = _samples_for_path(trial, candidate["path"])
                cycles = sorted(stage_observations.get(trial["trial_id"], {}).values())
                for cycle in cycles:
                    sample = _last_sample_value(trial, candidate["path"], cycle)
                    if sample is not None:
                        token_values.append(bool(sample.get("value")))
                raw = sorted(
                    (event for event in trial.get("events", []) if event.get("path") == stage["pc_path"]),
                    key=lambda item: item["cycle"],
                )
                load_observation = next((
                    item for item in trial.get("operand_expectations", [])
                    if item.get("role") == "calibration_load"
                ), None)
                accepted_load = next((
                    item for item in trial.get("transactions", [])
                    if item.get("kind") == "load"
                    and item.get("cycle") is not None
                    and item.get("epoch_id") is not None
                    and item.get("transaction_id") is not None
                ), None)
                qualified_hold_trial = bool(
                    forced_hold_supported
                    and trial.get("handshake_role") == "delayed"
                    and int(trial.get("response_delay_cycles") or 0) == 1
                    and load_observation is not None
                    and accepted_load is not None
                )
                trial_hold = None
                trial_release = None
                for previous, current in zip(raw, raw[1:]):
                    within_load_window = bool(
                        qualified_hold_trial
                        and current.get("offset") == load_observation.get("offset")
                        and int(accepted_load["cycle"]) - 4
                        <= int(current.get("cycle", -999))
                        <= int(accepted_load["cycle"]) + 1
                    )
                    if (
                        within_load_window
                        and current["cycle"] == previous["cycle"] + 1
                        and current["offset"] == previous["offset"]
                    ):
                        sample = _last_sample_value(trial, candidate["path"], current["cycle"])
                        value = None if sample is None else sample.get("value")
                        if value is not None:
                            trial_hold = bool(value)
                    elif (
                        trial_hold is not None
                        and current["cycle"] == previous["cycle"] + 1
                        and current["offset"] != previous["offset"]
                        and int(current["cycle"]) <= int(accepted_load["cycle"]) + 2
                    ):
                        sample = _last_sample_value(trial, candidate["path"], current["cycle"])
                        value = None if sample is None else sample.get("value")
                        if value is not None:
                            trial_release = bool(value)
                            break
                if trial_hold is not None and trial_release is not None:
                    holds.append(trial_hold)
                    releases.append(trial_release)
                wrong_offsets = set((trial.get("control_flow") or {}).get("wrong_path_offsets", ()))
                calibration_sections = (
                    trial.get("calibration_signature", {}).get("sections", {})
                )
                if (
                    str(trial.get("program", "")).startswith(
                        "pipeline_calibration_flow_"
                    )
                    and calibration_sections
                    and (
                        calibration_sections.get("redirect", {}).get("state")
                        != "completed"
                    )
                ):
                    wrong_offsets = set()
                if wrong_offsets:
                    wrong_cycles = [event["cycle"] for event in raw if event.get("offset") in wrong_offsets]
                    flush_hits += sum(
                        1 for sample in samples
                        if sample.get("value") and any(abs(sample["cycle"] - cycle) <= 1 for cycle in wrong_cycles)
                    )
                occupied = set(cycles)
                non_token_values.extend(
                    bool(item.get("value")) for item in samples
                    if item.get("cycle") not in occupied
                )
            state = "rejected"
            polarity = None
            score = 0.0
            if role == "valid" and token_values:
                high_ratio = sum(token_values) / len(token_values)
                if high_ratio >= 0.9 and any(value is False for value in non_token_values):
                    state, score = "confirmed", high_ratio
                elif high_ratio >= 0.9:
                    state, score = "assertion_only", high_ratio
            elif role == "stall":
                if not forced_hold_supported:
                    state = "unexercised"
                elif len(holds) >= 2 and len(releases) >= 2:
                    active_high = sum(holds) / len(holds)
                    release_high = sum(releases) / len(releases)
                    if active_high >= 0.8 and release_high <= 0.2:
                        state, polarity, score = "confirmed", "active_high", active_high
                    elif active_high <= 0.2 and release_high >= 0.8:
                        state, polarity, score = "confirmed", "active_low_enable", 1 - active_high
                    else:
                        state = "ambiguous"
                elif holds:
                    state = "unexercised"
            elif role == "flush":
                if flush_hits >= 2:
                    state, score = "confirmed", 1.0
                else:
                    state = "unexercised"
            scored.append({
                "path": candidate["path"], "state": state, "polarity": polarity,
                "score": round(score, 3), "hold_events": len(holds),
                "release_events": len(releases), "flush_hits": flush_hits,
            })
        scored.sort(key=lambda item: (-item["score"], item["path"]))
        selected = next((item for item in scored if item["state"] == "confirmed"), None)
        validation[role] = {
            "state": selected["state"] if selected else (
                scored[0]["state"] if scored else "unexercised"
            ),
            "path": selected["path"] if selected else None,
            "polarity": selected.get("polarity") if selected else None,
            "candidates": scored,
        }
    return validation


def _operand_use_record(selected, candidates):
    return {
        "state": "confirmed" if selected else "rejected",
        "side": None if selected is None else selected.get("side"),
        "operand_path": None if selected is None else selected.get("path"),
        "source_id_path": (
            None if selected is None else selected.get("source_id_path")
        ),
        "source_stage_path": (
            None if selected is None else selected.get("source_stage_path")
        ),
        "operand_stage_path": (
            None if selected is None else selected.get("operand_stage_path")
        ),
        "joining_edge": (
            None if selected is None else selected.get("joining_edge")
        ),
        "source_id_packed_slice": (
            None if selected is None
            else selected.get("source_id_packed_slice")
        ),
        "source_id_phase": (
            None if selected is None else selected.get("source_id_phase")
        ),
        "lane_id": None if selected is None else selected.get("lane_id"),
        "attempted": max(
            (item.get("attempted", 0) for item in candidates), default=0
        ),
        "matched": 0 if selected is None else selected.get("matched", 0),
        "eligible_trial_count": (
            0 if selected is None
            else selected.get("eligible_trial_count", 0)
        ),
        "matched_trial_count": (
            0 if selected is None
            else selected.get("matching_trial_count", 0)
        ),
        "missing_trial_ids": (
            [] if selected is None
            else list(selected.get("missing_trial_ids", ()))
        ),
        "distinct_values": (
            0 if selected is None
            else selected.get("distinct_expected_values", 0)
        ),
        "distinct_source_ids": (
            0 if selected is None else selected.get("distinct_source_ids", 0)
        ),
        "source_id_attempted": (
            0 if selected is None else selected.get("source_id_attempted", 0)
        ),
        "source_id_matched": (
            0 if selected is None else selected.get("source_id_matched", 0)
        ),
        "source_id_trial_coverage": (
            0 if selected is None
            else selected.get("source_id_trial_coverage", 0)
        ),
        "trial_coverage": (
            0 if selected is None else selected.get("trial_coverage", 0)
        ),
        "correct_value_captures": (
            0 if selected is None
            else selected.get("correct_value_captures", 0)
        ),
        "poison_captures": (
            0 if selected is None else selected.get("poison_captures", 0)
        ),
        "phase": None if selected is None else selected.get("phase"),
        "phase_consistency": (
            0 if selected is None else selected.get("phase_consistency", 0)
        ),
        "differential_validated": (
            None if selected is None
            else selected.get("differential_validated")
        ),
        "differential_required": (
            False if selected is None
            else selected.get("differential_required", False)
        ),
        "differential_trial_groups": (
            [] if selected is None
            else list(selected.get("differential_trial_groups", ()))
        ),
        "relaxed_validation_required": (
            False if selected is None
            else selected.get("relaxed_validation_required", False)
        ),
        "relaxed_validated": (
            False if selected is None
            else selected.get("relaxed_validated", False)
        ),
        "relaxed_trial_groups": (
            [] if selected is None
            else list(selected.get("relaxed_trial_groups", ()))
        ),
        "independent_validation_required": (
            False if selected is None
            else selected.get("independent_validation_required", False)
        ),
        "independent_validated": (
            False if selected is None
            else selected.get("independent_validated", False)
        ),
        "independent_trial_groups": (
            [] if selected is None
            else list(selected.get("independent_trial_groups", ()))
        ),
        "packed_slice": (
            None if selected is None else selected.get("packed_slice")
        ),
        "rejection_reason": None if selected else (
            candidates[0].get("rejection_reason")
            if candidates else "no role-local candidate"
        ),
    }


def _enrich_operand_and_control_evidence(base, trials, discovery):
    """Validate operand/WB/control signals against selected tokenized stages."""
    trial_map = {trial["trial_id"]: trial for trial in trials}
    requirement_observations = {}
    requirement_candidates = defaultdict(lambda: defaultdict(list))
    operand_scores = []
    control_scores = []
    canonical_link_diagnostics = []
    graph_edges = base.get("stage_graph", {}).get(
        "accepted_edges", ()
    )
    role_by_stage_path = {
        item.get("pc_path"): item.get("normalized_role")
        for item in base.get("stages", ())
        if item.get("pc_path")
    }
    for stage in base.get("stages", []):
        role = stage["normalized_role"]
        predecessor_paths = sorted({
            edge.get("from")
            for edge in graph_edges
            if edge.get("to") == stage.get("pc_path")
            and edge.get("from") in role_by_stage_path
        })
        source_stage_paths = [
            stage.get("pc_path"), *predecessor_paths,
        ]
        stage_observations = {
            trial_id: base.get("trial_observations", {}).get(trial_id, {}).get(role, {})
            for trial_id in trial_map
        }
        expected_by_trial = {}
        for trial_id, trial in trial_map.items():
            metadata = {str(item["offset"]): item for item in trial.get("operand_expectations", [])}
            expected_by_trial[trial_id] = [
                (metadata[offset], cycle)
                for offset, cycle in stage_observations.get(trial_id, {}).items()
                if offset in metadata
            ]

        use_kinds = {
            "execute": "operand",
            "store_address": "operand",
            "store_data": "store_data",
        }
        use_sides = {
            "execute": ("rs1", "rs2"),
            "store_address": ("rs1",),
            "store_data": ("rs2",),
        }
        source_paths = {"rs1": None, "rs2": None}
        operand_paths = {}
        operand_validations = {}
        operand_uses = {}
        selected_capture_candidates = {}
        for use, candidate_role in use_kinds.items():
            if use == "store_data" and role not in {"memory", "execute_memory"}:
                continue
            if use != "store_data" and role not in {
                "operand_read", "execute", "execute_memory", "memory",
            }:
                continue
            candidates = []
            selected_by_side = {}
            candidates_by_side = {}
            for side in use_sides[use]:
                filtered = {
                    trial_id: [
                        (item, cycle) for item, cycle in values
                        if item.get(f"{side}_use") == use
                        and (
                            trial_map[trial_id].get("pair_role")
                            not in {"dependent", "control"}
                            or _trial_is_eligible(
                                trial_map[trial_id], use, side,
                            )
                        )
                        and (
                            not str(
                                trial_map[trial_id].get("program", "")
                            ).startswith("pipeline_calibration_flow_")
                            or not trial_map[trial_id].get(
                                "calibration_signature", {}
                            ).get("sections")
                            or (
                                trial_map[trial_id].get(
                                    "calibration_signature", {}
                                ).get("sections", {}).get(
                                    "memory" if use in {
                                        "store_data", "store_address",
                                    }
                                    else "straight_line", {}
                                ).get("state")
                                == "completed"
                            )
                        )
                    ] for trial_id, values in expected_by_trial.items()
                }
                source_candidates = []
                for candidate in _candidate_pool(discovery, trials, "source_id"):
                    candidate_side = _candidate_side(candidate["path"])
                    if candidate_side not in (None, side):
                        continue
                    source_stage_path = min(
                        source_stage_paths,
                        key=lambda item: _scope_distance(
                            candidate.get(
                                "parent_path", candidate["path"]
                            ),
                            item,
                        ),
                    )
                    if _scope_distance(
                        candidate.get("parent_path", candidate["path"]),
                        source_stage_path,
                    ) > 8:
                        continue
                    score = _validate_source_selector_candidate(
                        candidate, trials, filtered, side, use,
                    )
                    score.update({
                        "side": side, "use": use,
                        "lane_id": candidate.get("lane_id"),
                        "source_stage_path": source_stage_path,
                        "operand_stage_path": stage.get("pc_path"),
                        "joining_edge": (
                            None if source_stage_path
                            == stage.get("pc_path")
                            else {
                                "from": source_stage_path,
                                "to": stage.get("pc_path"),
                            }
                        ),
                        "packed_slice": {
                            "parent_path": candidate.get("parent_path"),
                            "bit_offset": candidate.get("bit_offset"),
                            "width": candidate.get("slice_width"),
                        } if candidate.get("packed") else None,
                    })
                    incompatibility = _source_id_candidate_incompatible(
                        candidate, use
                    )
                    if score.get("confirmed") and incompatibility:
                        score["confirmed"] = False
                        score["rejection_reason"] = incompatibility
                    source_candidates.append(score)
                source_candidates.sort(key=lambda item: (
                    0 if item.get("confirmed") else 1,
                    -item["coverage"],
                    0 if _candidate_side(item["path"]) == side else 1,
                    0 if any(
                        token in _basename(
                            (item.get("packed_slice") or {}).get(
                                "parent_path", item["path"]
                            )
                        )
                        for token in ("ctrl", "control")
                    ) else 1,
                    _scope_distance(
                        (item.get("packed_slice") or {}).get(
                            "parent_path", item["path"]
                        ),
                        stage["pc_path"],
                    ),
                    0 if _semantic_name_role(item["path"]) == role else 1,
                    item["path"],
                ))
                source_candidates = _limit_virtual_candidates_for_use(
                    source_candidates
                )
                selected_source = next(
                    (item for item in source_candidates if item["confirmed"]), None
                )
                operand_scores.extend({
                    **item, "stage": role, "kind": f"{use}_{side}_id"
                } for item in source_candidates)

                side_candidates = []
                for candidate in _candidate_pool(discovery, trials, candidate_role):
                    candidate_side = _candidate_side(candidate["path"])
                    if (
                        candidate_side is not None
                        and candidate_side != side
                    ):
                        operand_scores.append({
                            "path": candidate["path"],
                            "stage": role,
                            "kind": use,
                            "side": side,
                            "confirmed": False,
                            "rejection_reason": (
                                f"candidate is explicitly associated with "
                                f"{candidate_side}, not consumer {side}"
                            ),
                        })
                        continue
                    if _scope_distance(candidate.get("parent_path", candidate["path"]), stage["pc_path"]) > 8:
                        continue
                    if _operand_candidate_incompatible(candidate["path"], use):
                        operand_scores.append({
                            "path": candidate["path"],
                            "stage": role,
                            "kind": use,
                            "side": side,
                            "confirmed": False,
                            "rejection_reason": (
                                "producer/result signal is incompatible with "
                                "consumer operand use"
                            ),
                        })
                        continue
                    if use == "store_data":
                        incompatibility = _store_data_candidate_incompatible(
                            candidate
                        )
                        if incompatibility:
                            operand_scores.append({
                                "path": candidate["path"],
                                "stage": role,
                                "kind": use,
                                "side": side,
                                "confirmed": False,
                                "rejection_reason": incompatibility,
                            })
                            continue
                    source_lane = None if selected_source is None else selected_source.get("lane_id")
                    candidate_lane = candidate.get("lane_id")
                    if source_lane is not None and candidate_lane is not None and source_lane != candidate_lane:
                        continue
                    score = _validate_data_candidate(
                        candidate["path"], trials, filtered,
                        f"{side}_value", minimum_distinct=3,
                        source_id_path=None if selected_source is None else selected_source["path"],
                        register_key=f"{side}_register",
                        reject_token_fields=bool(candidate.get("packed")),
                    )
                    phase_pair_consistent = bool(
                        selected_source is not None
                        and selected_source.get("phase") == score.get("phase")
                    )
                    if score.get("confirmed") and selected_source is None:
                        score["confirmed"] = False
                        score["rejection_reason"] = (
                            "no role-local source ID candidate was confirmed"
                        )
                    score.update({
                        "side": side, "use": use,
                        "source_id_path": None if selected_source is None else selected_source["path"],
                        "source_stage_path": (
                            None if selected_source is None
                            else selected_source.get("source_stage_path")
                        ),
                        "operand_stage_path": stage.get("pc_path"),
                        "joining_edge": (
                            None if selected_source is None
                            else selected_source.get("joining_edge")
                        ),
                        "source_id_phase": None if selected_source is None else selected_source.get("phase"),
                        "source_id_packed_slice": (
                            None if selected_source is None
                            else selected_source.get("packed_slice")
                        ),
                        "distinct_source_ids": (
                            0 if selected_source is None
                            else selected_source.get("distinct_expected_values", 0)
                        ),
                        "source_id_attempted": (
                            0 if selected_source is None
                            else selected_source.get("attempted", 0)
                        ),
                        "source_id_matched": (
                            0 if selected_source is None
                            else selected_source.get("matched", 0)
                        ),
                        "source_id_trial_coverage": (
                            0 if selected_source is None
                            else selected_source.get("trial_coverage", 0)
                        ),
                        "source_selector_ledger": (
                            {} if selected_source is None
                            else selected_source.get("capture_ledger", {})
                        ),
                        "source_selector_rejection_category": (
                            None if selected_source is None
                            else selected_source.get("rejection_category")
                        ),
                        "phase_pair_consistent": phase_pair_consistent,
                        "lane_id": candidate_lane if candidate_lane is not None else source_lane,
                        "packed_slice": {
                            "parent_path": candidate.get("parent_path"),
                            "bit_offset": candidate.get("bit_offset"),
                            "width": candidate.get("slice_width"),
                        } if candidate.get("packed") else None,
                    })
                    candidates.append(score)
                    side_candidates.append(score)
                side_candidates = _limit_virtual_candidates_for_use(
                    side_candidates
                )
                side_candidates.sort(key=lambda item: (
                    -item["coverage"],
                    -item.get("phase_consistency", 0),
                    0 if _semantic_name_role(item["path"]) == role else 1,
                    0 if (
                        use == "execute"
                        and (
                            "forward" in _basename(item["path"])
                            or _basename(item["path"]).endswith("_ex")
                        )
                    ) else 1,
                    item["path"],
                ))
                candidates_by_side[side] = side_candidates
                selected_by_side[side] = next((
                    item for item in side_candidates if item["confirmed"]
                ), None)
                if selected_by_side[side] is not None:
                    selected_capture_candidates[(use, side)] = (
                        selected_by_side[side]
                    )
            candidates = _limit_virtual_candidates_for_use(candidates)
            candidates.sort(key=lambda item: (
                -item["coverage"], -item.get("phase_consistency", 0),
                0 if _semantic_name_role(item["path"]) == role else 1,
                0 if (
                    use == "execute"
                    and (
                        "forward" in _basename(item["path"])
                        or _basename(item["path"]).endswith("_ex")
                    )
                ) else 1,
                item["path"],
            ))
            selected = next((item for item in candidates if item["confirmed"]), None)
            operand_paths[use] = selected["path"] if selected else None
            operand_validations[use] = selected
            for side, side_selected in selected_by_side.items():
                if side_selected is not None:
                    source_paths[side] = side_selected.get("source_id_path")
            operand_uses[use] = {
                **_operand_use_record(selected, candidates),
                "by_side": {
                    side: _operand_use_record(
                        selected_by_side.get(side),
                        candidates_by_side.get(side, []),
                    )
                    for side in use_sides[use]
                },
            }
            operand_scores.extend({**item, "stage": role, "kind": use} for item in candidates)

        controls = _validate_controls(
            stage, trials, stage_observations, discovery,
            forced_hold_supported=(
                base.get("calibration", {}).get("forced_hold") == "completed"
            ),
        )
        for control_role, control in controls.items():
            control_scores.extend({
                **candidate, "stage": role, "control_role": control_role,
            } for candidate in control.get("candidates", []))
        stage["source_id_paths"] = source_paths
        stage["operand_paths"] = operand_paths
        stage["operand_uses"] = operand_uses
        stage["operand_sides"] = {
            use: item.get("side") if item else None
            for use, item in operand_validations.items()
        }
        stage["control_validation"] = {
            key: {name: value for name, value in item.items() if name != "candidates"}
            for key, item in controls.items()
        }
        stage["valid_path"] = controls["valid"].get("path")
        stage["stall_path"] = controls["stall"].get("path")
        stage["flush_path"] = controls["flush"].get("path")
        if stage["valid_path"] and stage.get("evidence_quality") == "pc_only":
            stage["evidence_quality"] = "pc_valid_or_instruction"
            stage["confidence"] = 0.95
        stage["capabilities"] = {
            "source_ids": any(source_paths.values()),
            "operand_values": any(operand_paths.values()),
            "store_data_capture": bool(operand_paths.get("store_data")),
            "valid_control": controls["valid"]["state"] == "confirmed",
            "stall_control": controls["stall"]["state"] == "confirmed",
            "flush_control": controls["flush"]["state"] == "confirmed",
        }

        for (use, side), selected_candidate in (
            selected_capture_candidates.items()
        ):
            for trial_id, captures in selected_candidate.get(
                "capture_ledger", {}
            ).items():
                trial = trial_map.get(trial_id)
                if trial is None:
                    continue
                for capture in captures:
                    if capture.get("role") != "consumer":
                        continue
                    observation = next((
                        item for item in trial.get(
                            "operand_expectations", []
                        )
                        if item.get("offset") == capture.get("offset")
                        and item.get(f"{side}_use") == use
                    ), None)
                    if observation is None:
                        canonical_link_diagnostics.append({
                            "trial_id": trial_id, "role": use,
                            "side": side,
                            "mismatch": "consumer_expectation",
                        })
                        continue
                    dependency_sides = _dependency_consumer_sides(
                        trial, observation, use
                    )
                    if dependency_sides and side not in dependency_sides:
                        # Do not let an independent source side overwrite the
                        # exact side carrying the producer RAW dependency.
                        continue
                    fetch_event = next((
                        event for event in trial.get("fetch_events", [])
                        if event.get("offset") == capture.get("offset")
                        and not event.get("squashed")
                    ), None)
                    stage_anchor = (
                        base.get("stage_token_observations", {})
                        .get(trial_id, {}).get(role, {})
                        .get(str(capture.get("offset")))
                    )
                    source_capture = next((
                        item for item in (
                            selected_candidate.get(
                                "source_selector_ledger", {}
                            ).get(trial_id, [])
                        )
                        if item.get(
                            "consumer_offset", item.get("offset")
                        ) == capture.get("offset")
                        and item.get("side", side) == side
                        and item.get("use", use) == use
                    ), None)
                    expected_fetch_token = (
                        None if fetch_event is None
                        else _fetch_token(fetch_event, 0)
                    )
                    exact_token = bool(
                        stage_anchor is not None
                        and expected_fetch_token is not None
                        and stage_anchor.get("fetch_token")
                        == expected_fetch_token
                        and (
                            stage_anchor.get("signal_kind")
                            == "instruction"
                            or not stage.get("instruction_path")
                            or (
                                stage_anchor.get("instruction_path")
                                == stage.get("instruction_path")
                                and stage_anchor.get(
                                    "instruction_matches"
                                ) is True
                            )
                        )
                    )
                    legacy_trial = trial.get("variant") is None
                    residence_entry = (
                        None if stage_anchor is None
                        else stage_anchor.get(
                            "residence_entry_cycle",
                            stage_anchor.get("cycle"),
                        )
                    )
                    residence_exit = (
                        None if stage_anchor is None
                        else stage_anchor.get(
                            "residence_exit_cycle",
                            stage_anchor.get("cycle"),
                        )
                    )
                    stage_before_capture = bool(
                        stage_anchor is not None
                        and residence_entry is not None
                        and residence_exit is not None
                        and int(residence_entry)
                        <= int(capture.get("cycle"))
                        <= int(residence_exit) + 1
                    )
                    selector_linked = bool(
                        source_capture is not None
                        and source_capture.get("value")
                        == observation.get(f"{side}_register")
                        and abs(
                            int(source_capture.get("cycle"))
                            - int(capture.get("cycle"))
                        ) <= 1
                    )
                    if not (
                        exact_token and stage_before_capture
                        and selector_linked
                    ):
                        missing_links = []
                        if not exact_token:
                            missing_links.append("stage_token")
                        if not stage_before_capture:
                            missing_links.append("stage_operand_timing")
                        if not selector_linked:
                            missing_links.append("source_id")
                        canonical_link_diagnostics.append({
                            "trial_id": trial_id, "role": use,
                            "side": side,
                            "mismatch": ",".join(missing_links),
                            "stage_path": stage.get("pc_path"),
                            "source_id_path": selected_candidate.get(
                                "source_id_path"
                            ),
                            "operand_path": selected_candidate.get("path"),
                        })
                        continue
                    store_transaction = None
                    if use == "store_data":
                        matching_stores = [
                            item for item in trial.get("transactions", [])
                            if item.get("kind") == "store"
                            and item.get("epoch_id") is not None
                            and item.get("transaction_id") is not None
                            and (
                                trial.get("expected_store_address") is None
                                or item.get("address")
                                == trial.get("expected_store_address")
                            )
                            and (
                                trial.get("expected_store_value") is None
                                or (
                                    int(item.get("value", -1))
                                    & 0xFFFFFFFF
                                ) == (
                                    int(trial["expected_store_value"])
                                    & 0xFFFFFFFF
                                )
                            )
                        ]
                        if len(matching_stores) != 1:
                            canonical_link_diagnostics.append({
                                "trial_id": trial_id, "role": use,
                                "side": side,
                                "mismatch": "transaction_association",
                            })
                            continue
                        store_transaction = matching_stores[0]
                        request_cycle = store_transaction.get(
                            "observed_cycle",
                            store_transaction.get("cycle"),
                        )
                        if (
                            request_cycle is None
                            or not (
                                int(request_cycle) - 1
                                <= int(capture["cycle"])
                                <= int(request_cycle)
                            )
                        ):
                            canonical_link_diagnostics.append({
                                "trial_id": trial_id, "role": use,
                                "side": side,
                                "mismatch": "transaction_capture_timing",
                            })
                            continue
                    requirement_candidates[trial_id][use].append({
                        "cycle": capture["cycle"],
                        "phase": capture["phase"],
                        "phase_order": capture["phase_order"],
                        "path": selected_candidate["path"],
                        "source_id_path": selected_candidate.get(
                            "source_id_path"
                        ),
                        "packed_slice": selected_candidate.get(
                            "packed_slice"
                        ),
                        "source_id_packed_slice": selected_candidate.get(
                            "source_id_packed_slice"
                        ),
                        "source_selector_lag": (
                            int(source_capture.get("cycle"))
                            - int(capture.get("cycle"))
                        ),
                        "source_stage_path": selected_candidate.get(
                            "source_stage_path"
                        ),
                        "operand_stage_path": selected_candidate.get(
                            "operand_stage_path", stage.get("pc_path")
                        ),
                        "joining_edge": selected_candidate.get(
                            "joining_edge"
                        ),
                        "residence_relative_position": (
                            None if residence_entry is None
                            else int(capture["cycle"])
                            - int(residence_entry)
                        ),
                        "value": capture["value"],
                        "side": side,
                        "lane_id": selected_candidate.get("lane_id"),
                        "fetch_slot": (
                            None if fetch_event is None
                            else fetch_event.get("transaction_slot", 0)
                        ),
                        "lane_identity_confirmed": False,
                        "fetch_token": expected_fetch_token,
                        "stage_token": {
                            **stage_anchor,
                            "offset": capture.get("offset"),
                            "lane_id": stage.get("lane_id"),
                        },
                        "consumer_token_proof": True,
                        "source_selector_validation": True,
                        "operand_differential_validation": bool(
                            not selected_candidate.get(
                                "differential_required", False,
                            )
                            or selected_candidate.get(
                                "differential_validated", False,
                            )
                        ),
                        "semantic_discriminators_passed": not bool(
                            selected_candidate.get(
                                "semantic_collision_captures",
                            )
                        ),
                        "capture_source": "validated_candidate_ledger",
                        "role_evidence_state": "confirmed",
                        "candidate_differential_validated": (
                            selected_candidate.get(
                                "differential_validated", False
                            )
                        ),
                        "candidate_relaxed_validated": (
                            not selected_candidate.get(
                                "relaxed_validation_required", False
                            )
                            or selected_candidate.get(
                                "relaxed_validated", False
                            )
                        ),
                        "memory_epoch_id": (
                            None if store_transaction is None
                            else store_transaction.get("epoch_id")
                        ),
                        "memory_transaction_id": (
                            None if store_transaction is None
                            else store_transaction.get("transaction_id")
                        ),
                        "request_event": (
                            None if store_transaction is None
                            else {
                                "cycle": store_transaction.get(
                                    "observed_cycle",
                                    store_transaction.get("cycle"),
                                ),
                                "phase": "post_edge",
                                "epoch_id": store_transaction.get("epoch_id"),
                                "transaction_id": store_transaction.get(
                                    "transaction_id"
                                ),
                            }
                        ),
                        "_candidate_rank": _requirement_candidate_rank(
                            selected_candidate
                        ),
                    })

    # Requirement events are selected from the exact ledgers.  This closes
    # the old aggregate/per-trial gap and prevents a later unrelated source
    # side or stage from overwriting the dependency-side capture.
    for trial_id, uses in requirement_candidates.items():
        for use, candidates in uses.items():
            if not candidates:
                continue
            selected_event = max(
                candidates,
                key=lambda item: item.get("_candidate_rank", ()),
            )
            selected_event = {
                key: value for key, value in selected_event.items()
                if key != "_candidate_rank"
            }
            requirement_observations.setdefault(trial_id, {})[use] = (
                selected_event
            )

    # Some cores expose the memory store-data register and its source ID but
    # no memory-stage PC.  In that case the external store request supplies
    # the token epoch while the ID/value pair proves lane identity.
    if sum(
        "store_data" in observations
        for observations in requirement_observations.values()
    ) < 3:
        store_expected = {}
        store_requests = {}
        for trial_id, trial in trial_map.items():
            if not _trial_is_eligible(
                trial, "store_data", "rs2",
            ):
                continue
            calibration_sections = (
                trial.get("calibration_signature", {}).get("sections", {})
            )
            if (
                str(trial.get("program", "")).startswith(
                    "pipeline_calibration_flow_"
                )
                and calibration_sections
                and calibration_sections.get("memory", {}).get("state")
                != "completed"
            ):
                continue
            observation = next((
                item for item in trial.get("operand_expectations", [])
                if item.get("rs2_use") == "store_data"
            ), None)
            requests = [
                item for item in trial.get("transactions", [])
                if item.get("kind") == "store" and item.get("cycle") is not None
                and item.get("epoch_id") is not None and item.get("transaction_id") is not None
                and (
                    trial.get("expected_store_address") is None
                    or (int(item.get("address", -1)) & ~3)
                    == (int(trial["expected_store_address"]) & ~3)
                )
                and (
                    trial.get("expected_store_value") is None
                    or (int(item.get("value", 0)) & 0xFFFFFFFF)
                    == (int(trial["expected_store_value"]) & 0xFFFFFFFF)
                )
            ]
            request = requests[0] if len(requests) == 1 else None
            fetch_candidates = [
                item for item in trial.get("fetch_events", [])
                if observation is not None and item.get("offset") == observation.get("offset")
                and not item.get("squashed")
                and not item.get("terminal_loop")
                and item.get("cycle") is not None
                and request is not None
                and int(item["cycle"]) <= int(request["cycle"])
                and int(request["cycle"]) - int(item["cycle"])
                <= _trial_stage_window(trial)
            ]
            fetch = (
                fetch_candidates[0]
                if len(fetch_candidates) == 1 else None
            )
            if (
                observation is not None and len(requests) == 1 and fetch is not None
                and fetch.get("cycle") is not None and fetch["cycle"] <= requests[0]["cycle"]
            ):
                request = requests[0]
                store_expected[trial_id] = [(observation, request["cycle"])]
                store_requests[trial_id] = {"request": request, "fetch": fetch}
        source_candidates = []
        for candidate in _candidate_pool(discovery, trials, "source_id"):
            side = _candidate_side(candidate["path"])
            if side not in (None, "rs2"):
                continue
            score = _validate_source_selector_candidate(
                candidate, trials, store_expected, "rs2", "store_data",
            )
            score.update({
                "lane_id": candidate.get("lane_id"),
                "semantic_role": _semantic_name_role(
                    candidate.get("parent_path", candidate["path"])
                ),
                "packed_slice": {
                    "parent_path": candidate.get("parent_path"),
                    "bit_offset": candidate.get("bit_offset"),
                    "width": candidate.get("slice_width"),
                } if candidate.get("packed") else None,
            })
            incompatibility = _source_id_candidate_incompatible(
                candidate, "store_data"
            )
            if score["confirmed"] and incompatibility:
                score["confirmed"] = False
                score["rejection_reason"] = incompatibility
            if score["confirmed"]:
                source_candidates.append(score)
            operand_scores.append({**score, "stage": "store_issue", "kind": "rs2_id"})
        source_candidates = _limit_virtual_candidates_for_use(source_candidates)
        pairs = []
        for data_candidate in _candidate_pool(discovery, trials, "store_data"):
            data_incompatibility = _store_data_candidate_incompatible(
                data_candidate
            )
            if data_incompatibility:
                operand_scores.append({
                    "path": data_candidate["path"],
                    "stage": "store_issue",
                    "kind": "store_data",
                    "confirmed": False,
                    "rejection_reason": data_incompatibility,
                })
                continue
            for source in source_candidates:
                if _scope_distance(
                    data_candidate.get("parent_path", data_candidate["path"]), source["path"]
                ) > 8:
                    continue
                data_lane = data_candidate.get("lane_id")
                source_lane = source.get("lane_id")
                if data_lane is not None and source_lane is not None and data_lane != source_lane:
                    continue
                score = _validate_data_candidate(
                    data_candidate["path"], trials, store_expected,
                    "rs2_value", minimum_distinct=3,
                    source_id_path=source["path"], register_key="rs2_register",
                    reject_token_fields=bool(data_candidate.get("packed")),
                )
                phase_pair_consistent = source.get("phase") == score.get("phase")
                pairs.append({
                    **score, "source_id_path": source["path"],
                    "source_id_phase": source.get("phase"),
                    "source_id_packed_slice": source.get("packed_slice"),
                    "distinct_source_ids": source.get(
                        "distinct_expected_values", 0
                    ),
                    "source_id_attempted": source.get("attempted", 0),
                    "source_id_matched": source.get("matched", 0),
                    "source_id_trial_coverage": source.get(
                        "trial_coverage", 0
                    ),
                    "source_selector_ledger": source.get(
                        "capture_ledger", {}
                    ),
                    "phase_pair_consistent": phase_pair_consistent,
                    "lane_id": data_lane if data_lane is not None else source_lane,
                    "packed_slice": {
                        "parent_path": data_candidate.get("parent_path"),
                        "bit_offset": data_candidate.get("bit_offset"),
                        "width": data_candidate.get("slice_width"),
                    } if data_candidate.get("packed") else None,
                })
        pairs = _limit_virtual_candidates_for_use(pairs)
        pairs.sort(key=lambda item: (
            -item["coverage"],
            0 if _semantic_name_role(item["source_id_path"]) == "memory" else 1,
            item["path"], item["source_id_path"],
        ))
        selected_store = next((item for item in pairs if item["confirmed"]), None)
        operand_scores.extend({**item, "stage": "store_issue", "kind": "store_data"} for item in pairs)
        if selected_store is not None:
            for trial_id, values in store_expected.items():
                trial = trial_map[trial_id]
                observation, request_cycle = values[0]
                request_meta = store_requests[trial_id]
                request = request_meta["request"]
                fetch = request_meta["fetch"]
                capture = next((
                    item for item in selected_store.get(
                        "capture_ledger", {}
                    ).get(trial_id, [])
                    if item.get("offset") == observation.get("offset")
                    and item.get("source_id_value")
                    == observation.get("rs2_register")
                    and int(request_cycle) - 1
                    <= int(item.get("cycle", -999))
                    <= int(request_cycle)
                ), None)
                source_capture = next((
                    item for item in selected_store.get(
                        "source_selector_ledger", {}
                    ).get(trial_id, [])
                    if item.get(
                        "consumer_offset", item.get("offset")
                    ) == observation.get("offset")
                    and item.get("side", "rs2") == "rs2"
                    and item.get("use", "store_data") == "store_data"
                ), None)
                if capture is not None and (
                    _ordered_event(capture["cycle"], capture.get("phase"))
                    <= _ordered_event(request_cycle, "post_edge")
                ) and source_capture is not None and (
                    source_capture.get("value")
                    == observation.get("rs2_register")
                    and source_capture.get("phase")
                    == capture.get("phase")
                    and abs(
                        int(source_capture.get("cycle"))
                        - int(capture.get("cycle"))
                    ) <= 1
                ):
                    lane_id = selected_store.get("lane_id")
                    slot = fetch.get("transaction_slot", 0)
                    lane_matches = lane_id is None or int(lane_id) == int(slot)
                    if not lane_matches:
                        continue
                    requirement_observations.setdefault(trial_id, {})["store_data"] = {
                        "cycle": capture["cycle"],
                        "phase": capture["phase"],
                        "phase_order": capture["phase_order"],
                        "path": selected_store["path"],
                        "source_id_path": selected_store["source_id_path"],
                        "source_id_packed_slice": selected_store.get(
                            "source_id_packed_slice"
                        ),
                        "source_id_phase": selected_store.get(
                            "source_id_phase"
                        ),
                        "packed_slice": selected_store.get("packed_slice"),
                        "source_selector_lag": (
                            int(source_capture.get("cycle"))
                            - int(capture.get("cycle"))
                        ),
                        "value": int(capture["value"]) & 0xFFFFFFFF,
                        "side": "rs2",
                        "lane_id": lane_id,
                        "fetch_slot": fetch.get("transaction_slot", 0),
                        "lane_identity_confirmed": False,
                        "fetch_token": _fetch_token(fetch, 0),
                        "stage_token": {
                            "path": None,
                            "cycle": capture["cycle"],
                            "offset": observation.get("offset"),
                            "lane_id": lane_id,
                            "source": "transaction_aligned_operand_capture",
                        },
                        "capture_source": "validated_candidate_ledger",
                        "consumer_token_proof": True,
                        "source_selector_validation": True,
                        "operand_differential_validation": bool(
                            not selected_store.get(
                                "differential_required", False,
                            )
                            or selected_store.get(
                                "differential_validated", False,
                            )
                        ),
                        "semantic_discriminators_passed": not bool(
                            selected_store.get(
                                "semantic_collision_captures",
                            )
                        ),
                        "memory_epoch_id": request.get("epoch_id"),
                        "memory_transaction_id": request.get("transaction_id"),
                        "fetch_epoch_id": fetch.get("epoch_id"),
                        "fetch_transaction_id": fetch.get(
                            "transaction_id"
                        ),
                        "fetch_transaction_slot": fetch.get(
                            "transaction_slot", 0
                        ),
                        "request_event": {
                            "cycle": request_cycle, "phase": "post_edge",
                            "epoch_id": request.get("epoch_id"),
                            "transaction_id": request.get("transaction_id"),
                        },
                    }
            captured_trials = sum(
                "store_data" in requirement_observations.get(trial_id, {})
                for trial_id in store_expected
            )
            if captured_trials >= 3:
                transaction_node_id = (
                    "transaction:store_data:"
                    f"{selected_store.get('lane_id')}"
                )
                base["stages"].append({
                    "normalized_role": "memory",
                    "pc_path": None,
                    "graph_node_id": transaction_node_id,
                    "observation_kind": "transaction_aligned_operand_capture",
                    "evidence_quality": "operand_phase_correlated",
                    "confidence": 0.95,
                    "source_id_paths": {"rs1": None, "rs2": selected_store["source_id_path"]},
                    "operand_paths": {"store_data": selected_store["path"]},
                    "operand_sides": {"store_data": "rs2"},
                    "operand_uses": {"store_data": {
                        "state": "confirmed", "side": "rs2",
                        "operand_path": selected_store["path"],
                        "source_id_path": selected_store["source_id_path"],
                        "source_id_packed_slice": selected_store.get(
                            "source_id_packed_slice"
                        ),
                        "source_id_phase": selected_store.get(
                            "source_id_phase"
                        ),
                        "lane_id": selected_store.get("lane_id"),
                        "attempted": selected_store.get("attempted", 0),
                        "matched": selected_store.get("matched", 0),
                        "eligible_trial_count": selected_store.get(
                            "eligible_trial_count", 0
                        ),
                        "matched_trial_count": selected_store.get(
                            "matching_trial_count", 0
                        ),
                        "missing_trial_ids": list(
                            selected_store.get("missing_trial_ids", ())
                        ),
                        "distinct_values": selected_store.get("distinct_expected_values", 0),
                        "distinct_source_ids": selected_store.get(
                            "distinct_source_ids", 0
                        ),
                        "source_id_attempted": selected_store.get(
                            "source_id_attempted", 0
                        ),
                        "source_id_matched": selected_store.get(
                            "source_id_matched", 0
                        ),
                        "source_id_trial_coverage": selected_store.get(
                            "source_id_trial_coverage", 0
                        ),
                        "trial_coverage": selected_store.get("trial_coverage", 0),
                        "correct_value_captures": selected_store.get(
                            "correct_value_captures", 0
                        ),
                        "poison_captures": selected_store.get(
                            "poison_captures", 0
                        ),
                        "phase": selected_store.get("phase"),
                        "phase_consistency": selected_store.get("phase_consistency", 0),
                        "packed_slice": selected_store.get("packed_slice"),
                        "rejection_reason": None,
                    }},
                    "control_validation": {},
                    "capabilities": {
                        "source_ids": True, "operand_values": True,
                        "store_data_capture": True, "valid_control": False,
                        "stall_control": False, "flush_control": False,
                    },
                })
                base["capabilities"].update({
                    "consumer_stage_observable": True,
                    "memory_stage_observable": True,
                })
                stage_graph = base.setdefault(
                    "stage_graph",
                    {"nodes": [], "accepted_edges": []},
                )
                if not any(
                    node.get("path") == transaction_node_id
                    for node in stage_graph["nodes"]
                ):
                    stage_graph["nodes"].append({
                        "path": transaction_node_id,
                        "kind": "transaction_local_store",
                        "lane_id": selected_store.get("lane_id"),
                        "lag": None,
                        "coverage": round(
                            captured_trials / max(1, len(store_expected)),
                            3,
                        ),
                        "instruction_path": None,
                        "anchors": {
                            "memory": True, "writeback": False,
                        },
                        "exact_store_epochs": sorted({
                            str(
                                store_requests[trial_id]["request"].get(
                                    "epoch_id"
                                )
                            )
                            for trial_id in store_expected
                            if "store_data" in requirement_observations.get(
                                trial_id, {}
                            )
                        }),
                        "exact_fetch_associations": sorted({
                            (
                                str(
                                    store_requests[trial_id]["fetch"].get(
                                        "epoch_id"
                                    )
                                ),
                                str(
                                    store_requests[trial_id]["fetch"].get(
                                        "transaction_id"
                                    )
                                ),
                                int(
                                    store_requests[trial_id]["fetch"].get(
                                        "transaction_slot", 0
                                    )
                                ),
                                str(
                                    store_requests[trial_id]["request"].get(
                                        "transaction_id"
                                    )
                                ),
                            )
                            for trial_id in store_expected
                            if "store_data" in requirement_observations.get(
                                trial_id, {}
                            )
                        }),
                    })
                predecessor = next((
                    stage.get("pc_path")
                    for stage in reversed(base.get("stages", ())[:-1])
                    if stage.get("normalized_role") in {
                        "operand_read", "execute", "execute_memory",
                    }
                    and stage.get("pc_path") is not None
                ), None)
                if predecessor is not None:
                    edge = {
                        "from": predecessor,
                        "to": transaction_node_id,
                        "shared_tokens": captured_trials,
                        "median_cycle_delta": None,
                        "lane_id": selected_store.get("lane_id"),
                        "association": "exact_store_epoch",
                    }
                    if edge not in stage_graph["accepted_edges"]:
                        stage_graph["accepted_edges"].append(edge)
            else:
                # These are provisional per-trial matches.  A path is not a
                # validated transaction-anchored capture until it repeats in
                # at least three trials, so do not let isolated coincidences
                # reach the forwarding classifier as requirement evidence.
                for trial_id in store_expected:
                    observations = requirement_observations.get(trial_id, {})
                    candidate = observations.get("store_data")
                    if candidate is not None and (
                        candidate.get("path") == selected_store["path"]
                        and candidate.get("source_id_path")
                        == selected_store["source_id_path"]
                    ):
                        observations.pop("store_data", None)
                    if not observations:
                        requirement_observations.pop(trial_id, None)

    producer_events = {}
    for trial_id, trial in trial_map.items():
        producer = next((
            item for item in trial.get("operand_expectations", []) if item.get("role") == "producer"
        ), None)
        if producer is None:
            continue
        commit_cycle = next((
            item.get("cycle") for item in trial.get("commits", [])
            if item.get("offset") == producer.get("offset") and item.get("cycle") is not None
        ), None)
        if commit_cycle is not None:
            producer_events[trial_id] = [(producer, commit_cycle)]

    wb_candidate_scores = []
    selected_dynamic_wb = {"write_addr": None, "write_data": None, "write_enable": None}
    destination_scores = [
        {**_validate_data_candidate(
            candidate["path"], trials, producer_events,
            "destination_register", minimum_distinct=2,
            reject_token_fields=bool(candidate.get("packed")),
        ), "lane_id": candidate.get("lane_id")}
        for candidate in _candidate_pool(discovery, trials, "destination_id")
    ]
    data_scores = [
        {**_validate_data_candidate(
            candidate["path"], trials, producer_events,
            "result_value", minimum_distinct=3,
            reject_token_fields=bool(candidate.get("packed")),
        ), "lane_id": candidate.get("lane_id")}
        for candidate in _candidate_pool(discovery, trials, "wb_data")
    ]
    destination_scores.sort(key=lambda item: (-item["coverage"], item["path"]))
    data_scores.sort(key=lambda item: (-item["coverage"], item["path"]))
    wb_addr = next((item for item in destination_scores if item["confirmed"]), None)
    wb_data = next((
        item for item in data_scores
        if item["confirmed"] and (
            wb_addr is None or _scope_distance(item["path"], wb_addr["path"]) <= 6
        )
        and (
            wb_addr is None or item.get("lane_id") is None
            or wb_addr.get("lane_id") is None or item.get("lane_id") == wb_addr.get("lane_id")
        )
    ), None)
    wb_enable = None
    if wb_addr is not None and wb_data is not None:
        enable_scores = []
        for candidate in discovery.get("candidates", {}).get("wb_enable", []):
            if _scope_distance(candidate["path"], wb_data["path"]) > 6:
                continue
            attempted = matched = 0
            for trial_id, pairs in producer_events.items():
                trial = trial_map[trial_id]
                for _, commit_cycle in pairs:
                    attempted += 1
                    samples = [
                        item for item in _samples_for_path(trial, candidate["path"])
                        if abs(int(item.get("cycle", -999)) - int(commit_cycle)) <= 1
                        and bool(item.get("value"))
                    ]
                    matched += bool(samples)
            coverage = matched / attempted if attempted else 0.0
            enable_scores.append({
                "path": candidate["path"], "attempted": attempted, "matched": matched,
                "coverage": round(coverage, 3),
                "confirmed": attempted >= 3 and coverage >= 0.6,
                "lane_id": candidate.get("lane_id"),
            })
        enable_scores.sort(key=lambda item: (-item["coverage"], item["path"]))
        wb_enable = next((
            item for item in enable_scores
            if item["confirmed"] and (
                item.get("lane_id") is None
                or wb_data.get("lane_id") is None
                or item.get("lane_id") == wb_data.get("lane_id")
            )
        ), None)
        wb_candidate_scores.extend({**item, "kind": "write_enable"} for item in enable_scores)
    wb_candidate_scores.extend({**item, "kind": "destination_id"} for item in destination_scores)
    wb_candidate_scores.extend({**item, "kind": "write_data"} for item in data_scores)
    if wb_addr is not None and wb_data is not None and wb_enable is not None:
        selected_dynamic_wb = {
            "write_addr": wb_addr["path"],
            "write_data": wb_data["path"],
            "write_enable": wb_enable["path"],
            "lane_id": wb_data.get("lane_id") if wb_data.get("lane_id") is not None else wb_addr.get("lane_id"),
        }

    availability = {}
    writeback_capable = False
    phase_capable = False
    for trial_id, trial in trial_map.items():
        producer = next((
            item for item in trial.get("operand_expectations", []) if item.get("role") == "producer"
        ), None)
        if producer is None:
            continue
        register = producer.get("destination_register")
        expected = producer.get("result_value")
        poison = producer.get("poison_value")
        samples = [
            item for item in trial.get("architectural_samples", [])
            if item.get("register") == register
        ]
        samples.sort(key=lambda item: _ordered_event(item["cycle"], item["phase"]))
        prior_wrong = False
        chosen = None
        for sample in samples:
            if expected is not None and sample.get("value") == (int(expected) & 0xFFFFFFFF):
                if prior_wrong:
                    chosen = {**sample, "source": "register_storage_transition"}
                    phase_capable = True
                    break
            else:
                prior_wrong = True
        if chosen is None:
            for sample in trial.get("writeback_samples", []):
                if (
                    sample.get("write_enable")
                    and sample.get("write_addr") == register
                    and (sample.get("write_data", 0) & 0xFFFFFFFF) == (int(expected or 0) & 0xFFFFFFFF)
                ):
                    chosen = {
                        "cycle": sample["cycle"], "phase": "post_edge", "phase_order": 1,
                        "source": "validated_writeback_edge", "paths": sample.get("paths"),
                        "lane_id": sample.get("lane_id"),
                    }
                    writeback_capable = True
                    break
        if chosen is None and all(
            selected_dynamic_wb.get(key) for key in ("write_addr", "write_data", "write_enable")
        ):
            commit_cycle = next((
                cycle for item, cycle in producer_events.get(trial_id, [])
                if item.get("offset") == producer.get("offset")
            ), None)
            data_sample = _sample_value_near(
                trial, selected_dynamic_wb["write_data"], commit_cycle,
                expected, radius=1,
            ) if commit_cycle is not None else None
            addr_sample = _sample_value_near(
                trial, selected_dynamic_wb["write_addr"], commit_cycle,
                register, radius=1,
            ) if commit_cycle is not None else None
            enable_sample = _last_sample_value(
                trial, selected_dynamic_wb["write_enable"],
                data_sample["cycle"], data_sample.get("phase", "post_edge"),
            ) if data_sample is not None else None
            if data_sample is not None and addr_sample is not None and bool(
                (enable_sample or {}).get("value")
            ):
                chosen = {
                    "cycle": data_sample["cycle"],
                    "phase": data_sample.get("phase", "post_edge"),
                    "phase_order": data_sample.get("phase_order", 1),
                    "source": "dynamically_validated_writeback_handshake",
                    "precision": "writeback_only",
                    "paths": selected_dynamic_wb,
                    "lane_id": selected_dynamic_wb.get("lane_id"),
                }
                writeback_capable = True
        availability[trial_id] = chosen

    base["requirement_observations"] = requirement_observations
    grouped_links = defaultdict(list)
    for item in canonical_link_diagnostics:
        grouped_links[(
            item.get("role"), item.get("side"),
            item.get("mismatch"), item.get("stage_path"),
            item.get("source_id_path"), item.get("operand_path"),
        )].append(item)
    base["canonical_link_near_misses"] = [
        {
            "role": key[0], "side": key[1], "mismatch": key[2],
            "stage_path": key[3], "source_id_path": key[4],
            "operand_path": key[5], "eligible_trials": len(values),
            "trial_ids": sorted(
                item["trial_id"] for item in values
            )[:5],
        }
        for key, values in sorted(
            grouped_links.items(), key=lambda item: str(item[0])
        )
    ]
    failure_category = {
        "consumer_expectation": "semantic_discriminator",
        "stage_token": "stage_association",
        "stage_operand_timing": "lag",
        "source_id": "source_selector",
        "transaction_association": "transaction_association",
        "transaction_capture_timing": "transaction_association",
    }
    base["exact_capture_failures"] = [
        {
            **item,
            "failure_categories": sorted({
                failure_category.get(part, part)
                for part in str(item.get("mismatch", "")).split(",")
                if part
            }),
            "eligibility_key": list(
                _trial_eligibility_key(
                    trial_map.get(item.get("trial_id"), {}),
                    item.get("role"), item.get("side"),
                ) or ()
            ),
        }
        for item in canonical_link_diagnostics
    ]
    base["producer_availability_observations"] = availability
    base["operand_candidate_scores"] = operand_scores
    source_linkage = []
    for item in operand_scores:
        if not str(item.get("kind", "")).endswith("_id"):
            continue
        parent = (
            (item.get("packed_slice") or {}).get("parent_path")
            or item.get("path")
        )
        stage_path = next((
            stage.get("pc_path")
            for stage in base.get("stages", ())
            if stage.get("normalized_role") == item.get("stage")
        ), None)
        source_linkage.append({
            "stage": item.get("stage"),
            "role": item.get("use"),
            "side": item.get("side"),
            "candidate_path": item.get("path"),
            "candidate_locality": _scope_distance(
                parent, stage_path,
            ),
            "explicit_source_side": _candidate_side(
                item.get("path", "")
            ),
            "phase": item.get("phase"),
            "lag": item.get("lag"),
            "packed_slice": item.get("packed_slice"),
            "required_groups": list(
                item.get("required_trial_groups", ())
            ),
            "validated_groups": list(
                item.get("validated_trial_groups", ())
            ),
            "missing_variants": sorted({
                variant
                for group in item.get("required_trial_groups", ())
                for variant in group.get("missing_variants", ())
            }),
            "rejected_discriminator": item.get(
                "rejection_category"
            ),
            "state": (
                "confirmed" if item.get("confirmed")
                else "rejected"
            ),
            "rejection_reason": item.get("rejection_reason"),
        })
    base["source_id_linkage_diagnostics"] = sorted(
        source_linkage,
        key=lambda item: (
            item.get("role") or "", item.get("side") or "",
            item.get("candidate_path") or "",
        ),
    )
    # Preserve a bounded explanation of the strongest rejected role-local
    # candidates before non-debug finalization releases the full score and
    # capture ledgers.  This is intentionally diagnostic only: it never
    # participates in selection or lowers any confirmation threshold.
    grouped_candidate_near_misses = defaultdict(list)
    for item in operand_scores:
        if item.get("confirmed") is True:
            continue
        kind = str(item.get("kind", ""))
        candidate_type = (
            "source_id" if kind.endswith("_id") else "operand"
        )
        grouped_candidate_near_misses[(
            item.get("stage"),
            item.get("use") or item.get("kind"),
            item.get("side"),
            candidate_type,
        )].append(item)
    base["candidate_near_miss_diagnostics"] = []
    for (stage, use, side, candidate_type), items in sorted(
        grouped_candidate_near_misses.items(),
        key=lambda group: str(group[0]),
    ):
        ranked = sorted(
            items,
            key=lambda item: (
                0 if _semantic_name_role(
                    item.get("path", "")
                ) == stage else 1,
                -float(item.get("trial_coverage", 0) or 0),
                -int(item.get("matching_trial_count", 0) or 0),
                -float(item.get("coverage", 0) or 0),
                str(item.get("path", "")),
            ),
        )[:(12 if candidate_type == "source_id" else 3)]
        for item in ranked:
            base["candidate_near_miss_diagnostics"].append({
                "stage": stage,
                "use": use,
                "side": side,
                "candidate_type": candidate_type,
                "path": item.get("path"),
                "source_id_path": item.get("source_id_path"),
                "packed_slice": item.get("packed_slice"),
                "source_id_packed_slice": item.get(
                    "source_id_packed_slice"
                ),
                "phase": item.get("phase"),
                "source_id_phase": item.get("source_id_phase"),
                "eligible_trials": item.get("eligible_trial_count", 0),
                "matched_trials": item.get("matching_trial_count", 0),
                "missing_trials": list(
                    item.get("missing_trial_ids", ())
                )[:5],
                "missing_variants": sorted({
                    trial.get("variant")
                    for trial_id in item.get("missing_trial_ids", ())
                    for trial in trials
                    if trial.get("trial_id") == trial_id
                    and trial.get("variant") is not None
                })[:5],
                "selected_trial_group": item.get(
                    "selected_trial_group"
                ),
                "required_groups": list(
                    item.get("required_trial_groups", ())
                ),
                "validated_groups": list(
                    item.get("validated_trial_groups", ())
                ),
                "differential_required": item.get(
                    "differential_required", False
                ),
                "differential_validated": item.get(
                    "differential_validated"
                ),
                "nop_validation_required": item.get(
                    "relaxed_validation_required", False
                ),
                "nop_validated": item.get("relaxed_validated"),
                "validated_nop_groups": list(
                    item.get("relaxed_trial_groups", ())
                ),
                "rejected_discriminators": list(
                    item.get("semantic_collision_kinds", ())
                ),
                "rejection_category": item.get("rejection_category"),
                "rejection_reason": item.get("rejection_reason"),
            })
    base["control_candidate_scores"] = control_scores
    base["writeback_candidate_scores"] = wb_candidate_scores
    canonical_wb_paths = next((
        item.get("paths") for trial in trials for item in trial.get("writeback_samples", [])
        if item.get("paths")
    ), None)
    base["selected_writeback_paths"] = (canonical_wb_paths if writeback_capable else None) or (
        selected_dynamic_wb if all(
            selected_dynamic_wb.get(key) for key in ("write_addr", "write_data", "write_enable")
        ) else None
    )
    sampled_phases = {
        item.get("phase") for trial in trials
        for key in ("signal_samples", "architectural_samples", "writeback_samples")
        for item in trial.get(key, [])
    }
    base["capabilities"].update({
        "source_ids": any(
            any(stage.get("source_id_paths", {}).values()) for stage in base.get("stages", [])
        ),
        "operand_values": any(
            any(stage.get("operand_paths", {}).values()) for stage in base.get("stages", [])
        ),
        "store_data_capture": any(
            stage.get("operand_paths", {}).get("store_data") for stage in base.get("stages", [])
        ),
        "writeback_event": writeback_capable or phase_capable,
        "phase_ordering": phase_capable,
        "sampling_phases": {"pre_edge", "post_edge"}.issubset(sampled_phases),
    })

    lane_chains = []
    for stage in base.get("stages", []):
        for use, selected in stage.get("operand_uses", {}).items():
            if selected.get("state") != "confirmed":
                continue
            lane_id = selected.get("lane_id")
            matching = [
                observation
                for values in requirement_observations.values()
                for observed_use, observation in values.items()
                if observed_use == use
                and observation.get("path") == selected.get("operand_path")
                and observation.get("source_id_path") == selected.get("source_id_path")
            ]
            lane_matches = []
            complete_links = []
            rejection_reasons = set()
            for observation in matching:
                fetch_slot = observation.get("fetch_slot")
                if lane_id is None or fetch_slot is None:
                    rejection_reasons.add("fetch slot or operand lane is missing")
                    continue
                slot_matches = int(fetch_slot) == int(lane_id)
                lane_matches.append(slot_matches)
                if not slot_matches:
                    rejection_reasons.add("fetch slot and operand lane differ")
                    continue
                trial_id = next((
                    candidate_trial
                    for candidate_trial, values in requirement_observations.items()
                    if observation in values.values()
                ), None)
                availability_event = (
                    None if trial_id is None
                    else availability.get(trial_id)
                )
                transaction_terminal = bool(
                    observation.get("memory_epoch_id") is not None
                    and observation.get("memory_transaction_id") is not None
                )
                writeback_terminal = bool(
                    availability_event is not None
                    and availability_event.get("lane_id") is not None
                    and int(availability_event["lane_id"]) == int(lane_id)
                    and availability_event.get("paths")
                )
                complete = transaction_terminal or writeback_terminal
                complete_links.append(complete)
                if not complete:
                    rejection_reasons.add(
                        "no same-lane writeback or store transaction terminates the chain"
                    )
                observation["lane_identity_confirmed"] = complete
            confirmed_lane = (
                lane_id is not None
                and len(lane_matches) >= 3 and all(lane_matches)
                and len(complete_links) >= 3 and all(complete_links)
            )
            if confirmed_lane:
                for observation in matching:
                    observation["lane_identity_confirmed"] = True
            lane_chains.append({
                "stage": stage.get("normalized_role"), "use": use,
                "lane_id": lane_id, "operand_path": selected.get("operand_path"),
                "source_id_path": selected.get("source_id_path"),
                "matched_tokens": len(matching),
                "complete_tokens": sum(complete_links),
                "links": {
                    "fetch": True,
                    "stage": bool(stage.get("pc_path")) or use == "store_data",
                    "source_id": bool(selected.get("source_id_path")),
                    "operand": bool(selected.get("operand_path")),
                    "transaction_or_writeback": bool(
                        complete_links and all(complete_links)
                    ),
                },
                "rejection_reason": (
                    None if confirmed_lane
                    else "; ".join(sorted(rejection_reasons))
                    or "fewer than three complete lane tokens"
                ),
                "state": "confirmed" if confirmed_lane else "unresolved",
            })
    base["selected_lane_chains"] = lane_chains
    base["capabilities"]["lane_identity"] = (
        not base["capabilities"].get("multi_lane")
        or any(item["state"] == "confirmed" for item in lane_chains)
    )
    conflict_roles = {
        role
        for conflict in base.get(
            "candidate_summary", {}
        ).get("unresolved_stage_ties", {}).values()
        for role in conflict.get("roles", ())
    }
    role_evidence = {}
    for use, normalized_roles in {
        "execute": {
            "operand_read", "execute", "execute_memory", "memory",
        },
        "store_address": {
            "operand_read", "execute", "execute_memory", "memory",
        },
        "store_data": {"memory", "execute_memory"},
    }.items():
        selections = []
        selection_keys = set()
        for stage in base.get("stages", []):
            if stage.get("normalized_role") not in normalized_roles:
                continue
            aggregate = stage.get("operand_uses", {}).get(use, {})
            records = [aggregate, *aggregate.get("by_side", {}).values()]
            for record in records:
                if record.get("state") != "confirmed":
                    continue
                key = (
                    stage.get("normalized_role"),
                    stage.get("pc_path"),
                    record.get("operand_path"),
                    record.get("source_id_path"),
                    record.get("lane_id"),
                )
                if key in selection_keys:
                    continue
                selection_keys.add(key)
                selections.append((stage, record))
        def selection_key(selected):
            return (
                selected.get("operand_path"),
                selected.get("source_id_path"),
                selected.get("lane_id"),
            )

        canonical_counts = defaultdict(int)
        for trial_id, values in requirement_observations.items():
            observation = values.get(use)
            program = str(trial_map.get(trial_id, {}).get("program", ""))
            if (
                observation is not None
                and "_dependent_" in program
                and ("_gap_" not in program or "_gap_0" in program)
            ):
                canonical_counts[(
                    observation.get("path"),
                    observation.get("source_id_path"),
                    observation.get("lane_id"),
                )] += 1

        def selection_rank(pair):
            _, selected = pair
            path = selected.get("operand_path", "")
            return (
                canonical_counts.get(selection_key(selected), 0),
                selected.get("matched_trial_count", 0),
                selected.get("phase_consistency", 0),
                1 if (
                    "forward" in _basename(path)
                    or _basename(path) in {"a", "b"}
                ) else 0,
                1 if _semantic_name_role(path) in normalized_roles else 0,
                tuple(-ord(char) for char in str(path)),
            )

        selected_pair = max(selections, key=selection_rank) if selections else None
        stage, selected = selected_pair or (None, None)
        matches = [
            (trial_id, observation)
            for trial_id, values in requirement_observations.items()
            for observed_use, observation in values.items()
            if observed_use == use
            and selected is not None
            and observation.get("path") == selected.get("operand_path")
            and observation.get("source_id_path")
            == selected.get("source_id_path")
        ]
        qualifying_matches = [
            (trial_id, observation)
            for trial_id, observation in matches
            if "_dependent_" in str(
                trial_map.get(trial_id, {}).get("program", "")
            )
            and (
                "_gap_" not in str(
                    trial_map.get(trial_id, {}).get("program", "")
                )
                or "_gap_0" in str(
                    trial_map.get(trial_id, {}).get("program", "")
                )
            )
            and any(
                item.get("role") == "producer"
                for item in trial_map.get(
                    trial_id, {}
                ).get("operand_expectations", ())
            )
        ]
        availability_matches = [
            (trial_id, observation, availability.get(trial_id))
            for trial_id, observation in qualifying_matches
            if availability.get(trial_id) is not None
        ]
        exact_proof_matches = [
            (trial_id, observation)
            for trial_id, observation in qualifying_matches
            if all(
                observation.get(field) is True
                for field in (
                    "consumer_token_proof",
                    "source_selector_validation",
                    "operand_differential_validation",
                    "semantic_discriminators_passed",
                )
            )
        ]
        residence_positions = [
            int(observation["residence_relative_position"])
            for _, observation in qualifying_matches
            if observation.get("residence_relative_position") is not None
        ]
        residence_position_stable = bool(
            len(residence_positions) == len(qualifying_matches)
            and residence_positions
            and max(residence_positions) - min(residence_positions) <= 1
        )
        lane_complete = (
            not base["capabilities"].get("multi_lane")
            or all(
                observation.get("lane_identity_confirmed")
                for _, observation, _ in availability_matches
            )
        )
        conflicting = bool(
            "unknown" in conflict_roles
            or (
                stage is not None
                and stage.get("normalized_role") in conflict_roles
            )
            or (
                use in {"execute", "store_address"}
                and "execute" in conflict_roles
            )
            or (use == "store_data" and "memory" in conflict_roles)
        )
        confirmed_role = bool(
            selected is not None
            and (
                not selected.get("differential_required")
                or selected.get("differential_validated")
            )
            and len(qualifying_matches) >= 3
            and len(availability_matches) == len(qualifying_matches)
            and len(exact_proof_matches) == len(qualifying_matches)
            and residence_position_stable
            and lane_complete
            and not conflicting
        )
        if confirmed_role:
            rejection_reason = None
        elif selected is None:
            candidate_rejections = []
            for candidate_stage in base.get("stages", []):
                if candidate_stage.get("normalized_role") not in normalized_roles:
                    continue
                use_record = candidate_stage.get(
                    "operand_uses", {}
                ).get(use, {})
                records = [
                    use_record,
                    *use_record.get("by_side", {}).values(),
                ]
                candidate_rejections.extend(
                    record.get("rejection_reason")
                    for record in records
                    if record.get("rejection_reason")
                )
            details = "; ".join(dict.fromkeys(candidate_rejections))
            if not details:
                selected_roles = sorted({
                    candidate_stage.get("normalized_role")
                    for candidate_stage in base.get("stages", [])
                    if candidate_stage.get("normalized_role")
                })
                details = (
                    "no stage assigned one of the required normalized roles "
                    f"{sorted(normalized_roles)}; selected roles were "
                    f"{selected_roles or ['none']}"
                )
            rejection_reason = (
                "no role-local source-ID/operand chain was confirmed"
                + f": {details}"
            )
        elif len(qualifying_matches) < 3:
            rejection_reason = (
                "fewer than three exact per-trial operand captures were emitted"
            )
        elif (
            selected.get("differential_required")
            and not selected.get("differential_validated")
        ):
            rejection_reason = (
                "selected operand did not reproduce both dependent and "
                "matched-control consumer values"
            )
        elif len(availability_matches) != len(qualifying_matches):
            rejection_reason = (
                "producer availability was missing for a captured operand trial"
            )
        elif len(exact_proof_matches) != len(qualifying_matches):
            missing = sorted({
                field
                for _, observation in qualifying_matches
                for field in (
                    "consumer_token_proof",
                    "source_selector_validation",
                    "operand_differential_validation",
                    "semantic_discriminators_passed",
                )
                if observation.get(field) is not True
            })
            rejection_reason = (
                "exact consumer-local proof was incomplete: "
                + ", ".join(missing)
            )
        elif not residence_position_stable:
            rejection_reason = (
                "operand capture did not retain a bounded "
                "residence-relative position"
            )
        elif conflicting:
            rejection_reason = (
                "an unresolved candidate conflict affected this role"
            )
        else:
            rejection_reason = "lane identity was incomplete"
        independent_tested_gaps = sorted({
            int(trial.get("forwarding_gap", 0))
            for trial in trial_map.values()
            if trial.get("spacer_kind") == "independent"
            and any(
                observation.get("role") == "consumer"
                and (
                    observation.get("rs1_use") == use
                    or observation.get("rs2_use") == use
                )
                for observation in trial.get(
                    "operand_expectations", ()
                )
            )
        })
        role_evidence[use] = {
            "state": "confirmed" if confirmed_role else (
                "rejected" if selections else "unavailable"
            ),
            "stage": None if stage is None else stage.get("normalized_role"),
            "stage_path": None if stage is None else stage.get("pc_path"),
            "source_id_path": (
                None if selected is None
                else selected.get("source_id_path")
            ),
            "operand_path": (
                None if selected is None
                else selected.get("operand_path")
            ),
            "lane_id": None if selected is None else selected.get("lane_id"),
            "side": None if selected is None else selected.get("side"),
            "eligible_trials": (
                0 if selected is None
                else selected.get("eligible_trial_count", 0)
            ),
            "captured_trials": len(qualifying_matches),
            "availability_trials": len(availability_matches),
            "exact_proof_trials": len(exact_proof_matches),
            "differential_validated": (
                None if selected is None
                else selected.get("differential_validated")
            ),
            "differential_trial_groups": (
                [] if selected is None
                else selected.get("differential_trial_groups", [])
            ),
            "independent_corroboration": {
                "required": bool(independent_tested_gaps),
                "validated": bool(
                    selected is not None
                    and selected.get("independent_validated")
                ),
                "tested_gaps": independent_tested_gaps,
                "trial_groups": (
                    [] if selected is None
                    else list(selected.get("independent_trial_groups", ()))
                ),
                "fixed_stage_path": (
                    None if stage is None else stage.get("pc_path")
                ),
                "fixed_address_transform": (
                    None if stage is None
                    else stage.get("address_transform")
                ),
                "fixed_source_stage_path": (
                    None if selected is None
                    else selected.get("source_stage_path")
                ),
                "fixed_operand_stage_path": (
                    None if selected is None
                    else selected.get("operand_stage_path")
                ),
                "fixed_joining_edge": (
                    None if selected is None
                    else selected.get("joining_edge")
                ),
                "fixed_instruction_path": (
                    None if stage is None
                    else stage.get("instruction_path")
                ),
                "fixed_source_id_path": (
                    None if selected is None
                    else selected.get("source_id_path")
                ),
                "fixed_source_id_packed_slice": (
                    None if selected is None
                    else selected.get("source_id_packed_slice")
                ),
                "fixed_operand_path": (
                    None if selected is None
                    else selected.get("operand_path")
                ),
                "fixed_packed_slice": (
                    None if selected is None
                    else selected.get("packed_slice")
                ),
                "fixed_phase": (
                    None if selected is None else selected.get("phase")
                ),
                "fixed_source_id_phase": (
                    None if selected is None
                    else selected.get("source_id_phase")
                ),
                "fixed_source_selector_lag": next((
                    observation.get("source_selector_lag")
                    for _, observation in qualifying_matches
                    if observation.get("source_selector_lag") is not None
                ), None),
                "fixed_residence_position_bounds": (
                    None if not residence_positions else [
                        max(0, min(residence_positions) - 1),
                        max(residence_positions) + 1,
                    ]
                ),
                "fixed_lane_id": (
                    None if selected is None else selected.get("lane_id")
                ),
            },
            "rejection_reason": rejection_reason,
        }
        if confirmed_role:
            base["capabilities"]["consumer_stage_observable"] = True
            if use in {"execute", "store_address"}:
                base["capabilities"]["execute_stage_observable"] = True
            if use == "store_data":
                base["capabilities"]["memory_stage_observable"] = True
    base["role_evidence"] = role_evidence

    def coverage_record(attempted, matched, distinct=0, distinct_ids=0):
        state = "confirmed" if matched >= 3 else "partial" if matched else "unavailable"
        return {
            "attempted": int(attempted), "matched": int(matched),
            "distinct_values": int(distinct),
            "distinct_source_ids": int(distinct_ids),
            "trial_coverage": round(matched / attempted, 3) if attempted else 0.0,
            "state": state,
        }

    use_coverage = {}
    for use in ("execute", "store_address", "store_data"):
        entries = [
            stage.get("operand_uses", {}).get(use)
            for stage in base.get("stages", [])
            if stage.get("operand_uses", {}).get(use)
        ]
        attempted = max((item.get("attempted", 0) for item in entries), default=0)
        selected = next((item for item in entries if item.get("state") == "confirmed"), None)
        use_coverage[use] = coverage_record(
            attempted,
            0 if selected is None else selected.get("matched", 0),
            0 if selected is None else selected.get("distinct_values", 0),
            0 if selected is None else selected.get("distinct_source_ids", 0),
        )
        if selected is not None:
            use_coverage[use].update({
                "source_id_attempted": selected.get("source_id_attempted", 0),
                "source_id_matched": selected.get("source_id_matched", 0),
                "source_id_trial_coverage": selected.get(
                    "source_id_trial_coverage", 0
                ),
            })
    stage_eligible_trials = [
        trial for trial in trials
        if any(
            _trial_eligibility_key(trial, use) is not None
            for use in ("execute", "store_address", "store_data")
        )
    ]
    eligible_offsets = {
        trial["trial_id"]: {
            str(item.get("offset"))
            for item in trial.get("operand_expectations", ())
            if item.get("offset") is not None
            and item.get("role") == "consumer"
        }
        for trial in stage_eligible_trials
    }
    token_attempted = sum(
        len(offsets) for offsets in eligible_offsets.values()
    )
    token_matched = sum(
        len(
            eligible_offsets.get(trial_id, set())
            & {
                str(offset)
                for values in observations.values()
                for offset in values
            }
        )
        for trial_id, observations in base.get(
            "trial_observations", {}
        ).items()
        if trial_id in eligible_offsets
    )
    token_matched = min(token_attempted, token_matched)
    valid_confirmed = sum(
        stage.get("control_validation", {}).get("valid", {}).get("state") == "confirmed"
        for stage in base.get("stages", [])
    )
    stall_confirmed = sum(
        stage.get("control_validation", {}).get("stall", {}).get("state") == "confirmed"
        for stage in base.get("stages", [])
    )
    flush_confirmed = sum(
        stage.get("control_validation", {}).get("flush", {}).get("state") == "confirmed"
        for stage in base.get("stages", [])
    )
    base["calibration"]["capability_coverage"] = {
        "stage_tokens": coverage_record(token_attempted, token_matched),
        "source_ids": coverage_record(
            sum(item.get("source_id_attempted", 0) for item in use_coverage.values()),
            sum(item.get("source_id_matched", 0) for item in use_coverage.values()),
            0,
            sum(item.get("distinct_source_ids", 0) for item in use_coverage.values()),
        ),
        "execute_operands": use_coverage["execute"],
        "store_addresses": use_coverage["store_address"],
        "store_data": use_coverage["store_data"],
        "writeback": coverage_record(len(producer_events), sum(item is not None for item in availability.values())),
        "valid": coverage_record(len(base.get("stages", [])), valid_confirmed),
        "stall": coverage_record(len(base.get("stages", [])), stall_confirmed),
        "flush": coverage_record(len(base.get("stages", [])), flush_confirmed),
    }
    stage_group_coverage = {}
    for trial in stage_eligible_trials:
        use = _forwarding_trial_use(trial)
        key = _trial_eligibility_key(trial, use)
        if key is None:
            continue
        family_key = ":".join(str(value) for value in key[:3])
        record = stage_group_coverage.setdefault(
            family_key, {"attempted": 0, "matched": 0},
        )
        offsets = eligible_offsets.get(trial["trial_id"], set())
        observed = {
            str(offset)
            for values in base.get("trial_observations", {}).get(
                trial["trial_id"], {}
            ).values()
            for offset in values
        }
        record["attempted"] += len(offsets)
        record["matched"] += len(offsets & observed)
    base["calibration"]["capability_coverage"][
        "stage_tokens_by_dependency_group"
    ] = {
        key: coverage_record(
            value["attempted"], value["matched"],
        )
        for key, value in sorted(stage_group_coverage.items())
    }
    for section_name in ("straight_line", "memory", "redirect"):
        attempted = 0
        matched = 0
        covered_trials = set()
        attempted_trials = set()
        for trial in trials:
            signature = trial.get("calibration_signature") or {}
            section = signature.get("sections", {}).get(section_name)
            if not section:
                continue
            trial_id = str(trial.get("trial_id"))
            offsets = {
                str(item.get("offset"))
                for item in section.get("registers", [])
                if item.get("offset") is not None
            }
            attempted += len(offsets)
            if offsets:
                attempted_trials.add(trial_id)
            observed_offsets = {
                str(offset)
                for values in base.get(
                    "trial_observations", {}
                ).get(trial_id, {}).values()
                for offset in values
            }
            trial_matches = len(offsets & observed_offsets)
            matched += trial_matches
            if offsets and trial_matches == len(offsets):
                covered_trials.add(trial_id)
        section_coverage = coverage_record(attempted, matched)
        section_coverage["covered_trials"] = len(covered_trials)
        section_coverage["eligible_trials"] = len(attempted_trials)
        base["calibration"]["sections"][section_name][
            "token_coverage"
        ] = section_coverage


def classify_pipeline_interface(trials, discovery=None, discovery_error=None, pipeline_depth=None):
    """Validate transaction-scoped stage streams and assign evidence-backed roles."""
    discovery = discovery or {"candidates": {}, "search_truncated": False, "visited_scopes": 0}
    base = {
        "schema_version": PIPELINE_INTERFACE_SCHEMA_VERSION,
        "discovery_version": PIPELINE_INTERFACE_DISCOVERY_VERSION,
        "implementation_revision": PIPELINE_INTERFACE_IMPLEMENTATION_REVISION,
        "state": "unavailable",
        "search_truncated": bool(discovery.get("search_truncated")),
        "visited_scopes": discovery.get("visited_scopes", 0),
        "visited_objects": discovery.get("visited_objects", 0),
        "discovery_root": discovery.get("discovery_root"),
        "truncation_reasons": list(discovery.get("truncation_reasons", [])),
        "behavioral_census": discovery.get("behavioral_census", {
            "state": "not_run",
            "candidate_counts_before": {},
            "candidate_counts_after": {},
        }),
        "census_inventory": discovery.get("census_inventory", {}),
        "calibration_base_selection": discovery.get(
            "calibration_base_selection", {
                "state": "not_run", "attempted": [],
                "selected_bases": [],
            },
        ),
        "stage_graph": {"nodes": [], "accepted_edges": []},
        "stages": [],
        "capabilities": {
            "consumer_stage_observable": False,
            "execute_stage_observable": False,
            "memory_stage_observable": False,
            "multi_lane": bool(discovery.get("multi_lane_candidates")),
            "lane_identity": False,
            "source_ids": False,
            "operand_values": False,
            "store_data_capture": False,
            "writeback_event": False,
            "phase_ordering": False,
            "sampling_phases": False,
        },
        "candidate_scores": [],
        "stage_candidate_diagnostics": [],
        "source_id_linkage_diagnostics": [],
        "exact_capture_failures": [],
        "trial_observations": {},
        "stage_token_observations": {},
        "role_evidence": {
            use: {
                "state": "unavailable",
                "rejection_reason": "pipeline discovery did not complete",
            }
            for use in ("execute", "store_address", "store_data")
        },
        "calibration": {
            "state": "not_run",
            "execution_state": "not_run",
            "flow_trials": 0,
            "completed_flow_trials": 0,
            "forced_hold": "not_run",
            "architectural": {"variants": []},
            "sections": {
                name: {
                    "state": "not_run", "variants": [],
                    "token_coverage": {
                        "attempted": 0, "matched": 0,
                        "trial_coverage": 0, "state": "unavailable",
                    },
                }
                for name in ("straight_line", "memory", "redirect")
            },
            "capability_coverage": {},
            "handshake": {
                "state": "not_run", "baseline_complete": False,
                "delayed_trials_completed": 0, "recovery_complete": False,
            },
        },
    }

    def reject_unattempted_roles(stage_detail):
        role_stages = {
            "execute": "execute",
            "store_address": "execute",
            "store_data": "memory/store-issue",
        }
        for use, stage_name in role_stages.items():
            if base.get("role_evidence", {}).get(use, {}).get(
                "state"
            ) == "confirmed":
                continue
            base["role_evidence"][use] = {
                "state": "unavailable",
                "stage": None,
                "stage_path": None,
                "source_id_path": None,
                "operand_path": None,
                "lane_id": None,
                "side": None,
                "eligible_trials": 0,
                "captured_trials": 0,
                "availability_trials": 0,
                "rejection_reason": (
                    f"role-local {use} proof unavailable: no dynamically "
                    f"validated {stage_name} token stream; {stage_detail}"
                ),
            }

    if discovery_error:
        base.update({"state": "failed", "error": discovery_error})
        reject_unattempted_roles(
            f"hierarchy discovery failed: {discovery_error}"
        )
        return base
    if not trials:
        base["reason"] = "no forwarding trial traces were collected"
        reject_unattempted_roles(
            "no forwarding or calibration trials were collected"
        )
        return base

    # Operand/control validation asks for the same candidate path many times
    # across role-local token sets. Index once so large visible hierarchies do
    # not turn finalization into candidates × tokens × raw-samples rescanning.
    for trial in trials:
        samples_by_path = defaultdict(list)
        for sample in trial.get("signal_samples", []):
            samples_by_path[sample.get("path")].append(sample)
        trial["_signal_samples_by_path"] = samples_by_path

    calibration_trials = [
        trial for trial in trials if str(trial.get("program", "")).startswith("pipeline_calibration_flow_")
    ]
    if calibration_trials:
        execution_errors = [
            {
                "variant": trial.get("calibration_variant"),
                "error_type": trial.get("calibration_error_type"),
                "error": trial.get("calibration_error"),
                "traceback": trial.get("calibration_traceback"),
            }
            for trial in calibration_trials
            if trial.get("calibration_error")
        ]
        signatures = [
            trial.get("calibration_signature") or {
                "state": (
                    "execution_error"
                    if trial.get("calibration_error") else "unavailable"
                ),
                "error": trial.get("calibration_error"),
                "error_type": trial.get("calibration_error_type"),
                "variant": trial.get("calibration_variant"),
            }
            for trial in calibration_trials
        ]
        section_states = {}
        for section_name in ("straight_line", "memory", "redirect"):
            variants = [
                {
                    "variant": signature.get("variant"),
                    **(
                        signature.get("sections", {}).get(section_name)
                        or {
                            # Compatibility for in-memory callers and older
                            # synthetic fixtures. Revision-3 artifacts always
                            # emit explicit sections.
                            "state": signature.get("state", "unavailable"),
                            "failures": signature.get("failures", []),
                            "legacy_unsectioned": True,
                        }
                    ),
                }
                for signature in signatures
            ]
            states = [item.get("state") for item in variants]
            if states and all(item == "completed" for item in states):
                section_state = "completed"
            elif states and all(item == "unavailable" for item in states):
                section_state = "unavailable"
            elif states and all(item == "failed" for item in states):
                section_state = "failed"
            elif any(item == "execution_error" for item in states):
                section_state = "unavailable"
            else:
                section_state = "partial"
            section_states[section_name] = section_state
            base["calibration"]["sections"][section_name].update({
                "state": section_state,
                "variants": variants,
            })
        straight_line_state = section_states["straight_line"]
        explicit_straight_failure = any(
            (
                signature.get("sections", {})
                .get("straight_line", {}).get("state")
                == "failed"
            )
            for signature in signatures
        )
        if execution_errors:
            calibration_state = "unavailable"
        elif explicit_straight_failure:
            calibration_state = "failed"
        elif straight_line_state == "unavailable":
            calibration_state = "unavailable"
        elif straight_line_state == "failed":
            calibration_state = "failed"
        elif all(
            section_states[name] == "completed"
            for name in ("straight_line", "memory", "redirect")
        ):
            calibration_state = "completed"
        else:
            calibration_state = "partial"
        completed = sum(item.get("state") == "completed" for item in signatures)
        base["calibration"].update({
            "state": calibration_state,
            "execution_state": (
                "failed" if execution_errors else "completed"
            ),
            "execution_errors": execution_errors,
            "flow_trials": len(calibration_trials),
            "completed_flow_trials": completed,
        })
        base["calibration"]["architectural"] = {
            "state": calibration_state, "variants": signatures,
        }
    handshake_trials = [
        trial for trial in trials
        if str(trial.get("program", "")).startswith("pipeline_calibration_handshake_")
    ]
    if handshake_trials:
        baseline = handshake_trials[0]
        baseline_complete = (
            (baseline.get("calibration_signature") or {}).get("state") == "completed"
            and any(item.get("kind") == "load" for item in baseline.get("transactions", []))
        )
        delayed = handshake_trials[1:]
        delayed_completed = sum(
            (trial.get("calibration_signature") or {}).get("state") == "completed"
            and any(item.get("kind") == "load" for item in trial.get("transactions", []))
            for trial in delayed
        )
        recovery_signature = (
            calibration_trials[0].get("calibration_signature") or {}
        ) if calibration_trials else {}
        recovery_sections = recovery_signature.get("sections", {})
        recovery_state = (
            recovery_sections.get("memory", {}).get("state")
            if recovery_sections
            else recovery_signature.get("state")
        )
        recovery_complete = bool(
            calibration_trials
            and recovery_state == "completed"
            and any(
                item.get("kind") == "load"
                for item in calibration_trials[0].get("transactions", [])
            )
        )
        supported = (
            baseline_complete and len(delayed) == 2
            and delayed_completed == 2 and recovery_complete
        )
        trial_evidence = []
        for trial in handshake_trials:
            load_transaction = next((
                item for item in trial.get("transactions", [])
                if item.get("kind") == "load"
                and item.get("epoch_id") is not None
                and item.get("transaction_id") is not None
            ), None)
            load_expectation = next((
                item for item in trial.get("operand_expectations", [])
                if item.get("role") == "calibration_load"
            ), None)
            fetch = next((
                item for item in trial.get("fetch_events", [])
                if load_expectation is not None
                and item.get("offset") == load_expectation.get("offset")
                and not item.get("squashed")
                and not item.get("terminal_loop")
            ), None)
            trial_evidence.append({
                "trial_id": trial.get("trial_id"),
                "role": trial.get("handshake_role"),
                "response_delay_cycles": trial.get("response_delay_cycles", 0),
                "complete": (
                    (trial.get("calibration_signature") or {}).get("state")
                    == "completed"
                ),
                "fetch_token": None if fetch is None else _fetch_token(fetch, 0),
                "fetch_slot": None if fetch is None else fetch.get("transaction_slot", 0),
                "memory_epoch_id": (
                    None if load_transaction is None
                    else load_transaction.get("epoch_id")
                ),
                "memory_transaction_id": (
                    None if load_transaction is None
                    else load_transaction.get("transaction_id")
                ),
            })
        base["calibration"]["handshake"] = {
            "state": "supported" if supported else (
                "unsupported" if baseline_complete else "unavailable"
            ),
            "baseline_complete": baseline_complete,
            "delayed_trials_completed": delayed_completed,
            "recovery_complete": recovery_complete,
            "trials": trial_evidence,
        }
        base["calibration"]["forced_hold"] = "completed" if supported else "unsupported"
    elif calibration_trials:
        base["calibration"]["forced_hold"] = "unsupported"

    windows = {trial["trial_id"]: _trial_stage_window(trial, pipeline_depth) for trial in trials}
    base["stage_window_cycles"] = {
        "maximum": max(windows.values()) if windows else None,
        "per_trial": windows,
        "hard_limit": MAX_STAGE_WINDOW_CYCLES,
    }
    events_by_path = defaultdict(list)
    trial_by_id = {trial["trial_id"]: trial for trial in trials}
    raw_pc_paths = {
        sample.get("path")
        for trial in trials
        for sample in trial.get("raw_stage_samples", ())
        if sample.get("path")
    }
    for trial in trials:
        calibration_program = str(trial.get("program", "")).startswith(
            "pipeline_calibration_flow_"
        )
        sections = (
            trial.get("calibration_signature", {})
            .get("sections", {})
        )
        calibration_offsets = {
            item.get("offset")
            for section in sections.values()
            if section.get("state") == "completed"
            for item in section.get("registers", [])
        }
        control_flow = trial.get("control_flow") or {}
        # Redirect identity is a behavioral PC-stream check.  Keep the source
        # and taken-target offsets available even when the architectural
        # redirect signature failed; otherwise stage discovery circularly
        # removes the evidence needed to explain or recover that failure.
        if control_flow.get("target_offset") is not None:
            calibration_offsets.add(control_flow["target_offset"])
            if control_flow.get("redirect_offset") is not None:
                calibration_offsets.add(
                    control_flow["redirect_offset"]
                )
        calibration_offsets -= set(
            control_flow.get("wrong_path_offsets", ())
        )
        for event in trial.get("events", []):
            if (
                event.get("signal_kind", "pc") != "instruction"
                and event.get("path") in raw_pc_paths
            ):
                # Raw samples are normalized below using one transform shared
                # by every calibration base and forwarding trial.
                continue
            if calibration_program and sections and (
                event.get("offset") not in calibration_offsets
            ):
                continue
            events_by_path[(event["path"], event.get("address_mode", "byte"))].append({
                **event, "trial_id": trial["trial_id"]
            })
    candidate_by_path = {
        item.get("path"): item
        for item in discovery.get("candidates", {}).get("pc", ())
    }
    affine_transforms = {}
    for path in sorted(raw_pc_paths):
        candidate = candidate_by_path.get(path, {})
        for address_mode in ("byte", "word"):
            transform, materialized = _fit_affine_stage_events(
                path, trials, address_mode, candidate.get("width"),
            )
            if transform is None:
                continue
            affine_transforms[(path, address_mode)] = transform
            for trial_id, events in materialized.items():
                trial = trial_by_id.get(str(trial_id))
                if trial is None:
                    continue
                calibration_program = str(
                    trial.get("program", "")
                ).startswith("pipeline_calibration_flow_")
                sections = (
                    trial.get("calibration_signature", {})
                    .get("sections", {})
                )
                allowed_offsets = {
                    item.get("offset")
                    for section in sections.values()
                    if section.get("state") == "completed"
                    for item in section.get("registers", [])
                }
                control = trial.get("control_flow") or {}
                for key in ("redirect_offset", "target_offset"):
                    if control.get(key) is not None:
                        allowed_offsets.add(control[key])
                allowed_offsets -= set(
                    control.get("wrong_path_offsets", ())
                )
                for event in events:
                    if (
                        calibration_program and sections
                        and event.get("offset") not in allowed_offsets
                    ):
                        continue
                    events_by_path[(path, address_mode)].append({
                        **event, "trial_id": str(trial_id),
                    })
    if not events_by_path:
        base["stage_candidate_diagnostics"] = []
        for role in ("pc", "instruction"):
            for candidate in discovery.get(
                "candidates", {}
            ).get(role, ()):
                diagnostic = _stage_candidate_identity({
                    "path": candidate.get("path"),
                    "signal_kind": role,
                    "address_mode": (
                        "instruction" if role == "instruction"
                        else None
                    ),
                    "paired_by_trial": {},
                    "lane_id": candidate.get("lane_id"),
                }, trial_by_id)
                diagnostic.update({
                    "state": "rejected",
                    "primary_rejection_reason": (
                        "instruction_companion"
                        if role == "instruction"
                        else "relocation"
                    ),
                })
                base["stage_candidate_diagnostics"].append(
                    diagnostic
                )
        _enrich_operand_and_control_evidence(base, trials, discovery)
        base["state"] = (
            "partial" if base.get("stages") else "unavailable"
        )
        base["reason"] = (
            "transaction-local memory evidence recovered without a "
            "relocation-backed PC stream"
            if base.get("stages")
            else "no shortlisted internal PC or instruction signal "
            "followed a probe program"
        )
        candidate_count = sum(
            len(discovery.get("candidates", {}).get(role, ()))
            for role in ("pc", "instruction")
        )
        reject_unattempted_roles(
            f"{candidate_count} shortlisted PC/instruction candidates "
            "produced no transaction-scoped token matches"
        )
        return base

    scores = []
    trial_count = len(trials)
    for (path, address_mode), events in events_by_path.items():
        covered = set()
        lags = []
        ordered_trials = 0
        instruction_matches = []
        valid_samples = []
        commit_errors = []
        memory_errors = []
        fingerprints = []
        residence_fingerprints = []
        slot_matches = []
        paired_by_trial = {}
        for trial_id, trial in trial_by_id.items():
            path_events = [event for event in events if event["trial_id"] == trial_id]
            paired = _pair_candidate_events(trial, path_events, windows[trial_id])
            paired_by_trial[trial_id] = paired
            offsets = [event["offset"] for event in paired]
            needed = {getattr_trial_offset(trial, "producer"), getattr_trial_offset(trial, "consumer")}
            needed.discard(None)
            if needed and needed.issubset(set(offsets)):
                covered.add(trial_id)
            elif str(trial.get("program", "")).startswith("pipeline_calibration_"):
                calibration_offsets = {
                    item.get("offset") for item in trial.get("operand_expectations", [])
                    if item.get("role") not in {"wrong_path_poison", "calibration_redirect"}
                }
                calibration_offsets.discard(None)
                if calibration_offsets and len(calibration_offsets & set(offsets)) >= max(
                    3, int(0.7 * len(calibration_offsets))
                ):
                    covered.add(trial_id)
            first_cycles = {}
            for event in paired:
                first_cycles.setdefault(event["offset"], event["cycle"])
                lags.append(event["lag"])
                fingerprints.append((trial_id, event["fetch_token"], event["cycle"]))
                residence_fingerprints.append((
                    trial_id, event["fetch_token"],
                    event.get("residence_entry_cycle", event["cycle"]),
                    event.get("residence_exit_cycle", event["cycle"]),
                ))
                if event.get("instruction_matches") is not None:
                    instruction_matches.append(event["instruction_matches"])
                if event.get("valid_value") is not None:
                    valid_samples.append(bool(event["valid_value"]))
            if list(first_cycles.values()) == sorted(first_cycles.values()) and len(first_cycles) >= 2:
                ordered_trials += 1
            commit_trial_errors, memory_trial_errors = _alignment_errors(trial, paired)
            commit_errors.extend(commit_trial_errors)
            memory_errors.extend(memory_trial_errors)
        coverage = len(covered) / max(1, trial_count)
        stable_lag = bool(lags) and max(lags) - min(lags) <= 1
        instruction_ratio = sum(instruction_matches) / len(instruction_matches) if instruction_matches else 0.0
        valid_ratio = sum(valid_samples) / len(valid_samples) if valid_samples else 0.0
        order_ratio = ordered_trials / max(1, trial_count)
        alignment_bonus = (
            5 * int(bool(commit_errors) and median(commit_errors) <= 2)
            + 5 * int(bool(memory_errors) and median(memory_errors) <= 2)
        )
        score = round(
            50 * coverage + 25 * int(stable_lag) + 15 * order_ratio
            + 5 * instruction_ratio + 5 * valid_ratio + alignment_bonus,
            2,
        )
        sample = events[0]
        candidate_meta = next((
            item for role in ("pc", "instruction")
            for item in discovery.get("candidates", {}).get(role, []) if item["path"] == path
        ), {})
        candidate_lane = candidate_meta.get("lane_id")
        if candidate_lane is not None:
            slot_matches = [
                int(event.get("transaction_slot", 0)) == int(candidate_lane)
                for values in paired_by_trial.values() for event in values
            ]
        lane_match_ratio = (
            sum(slot_matches) / len(slot_matches) if slot_matches else None
        )
        scores.append({
            "path": path,
            "address_mode": address_mode,
            "score": score,
            "coverage": round(coverage, 3),
            "stable_lag": stable_lag,
            "median_fetch_offset_cycles": median(lags) if lags else None,
            "instruction_path": sample.get("instruction_path") if instruction_ratio >= 0.8 else None,
            "valid_path": sample.get("valid_path") if valid_ratio >= 0.8 else None,
            "stall_path": sample.get("stall_path"),
            "flush_path": sample.get("flush_path"),
            "instruction_correlation": round(instruction_ratio, 3),
            "valid_correlation": round(valid_ratio, 3),
            "sequence_consistency": round(order_ratio, 3),
            "commit_alignment_error": median(commit_errors) if commit_errors else None,
            "memory_alignment_error": median(memory_errors) if memory_errors else None,
            "signal_kind": "instruction" if address_mode == "instruction" else "pc",
            "name_role_hint": candidate_meta.get("name_role_hint") or _semantic_name_role(path),
            "lane_hint": bool(candidate_meta.get("lane_hint")) or _looks_multilane(path),
            "lane_id": candidate_lane,
            "lane_match_ratio": None if lane_match_ratio is None else round(lane_match_ratio, 3),
            "static_rank": candidate_meta.get("static_rank", 0),
            "event_fingerprint": tuple(sorted(fingerprints)),
            "residence_fingerprint": tuple(
                sorted(residence_fingerprints)
            ),
            "paired_by_trial": paired_by_trial,
            "address_transform": affine_transforms.get(
                (path, address_mode)
            ),
        })
        identity = _stage_candidate_identity(scores[-1], trial_by_id)
        scores[-1]["relocation_proven"] = identity[
            "relocation_proven"
        ]
        if identity.get("address_transform") is not None:
            scores[-1]["address_transform"] = identity[
                "address_transform"
            ]
        scores[-1]["identity_diagnostics"] = identity
    scores.sort(key=lambda item: (
        -item["score"],
        0 if item["address_mode"] == "byte" else 1,
        item["path"],
    ))
    # A physical PC signal may coincidentally match the word-addressed image
    # while executing the NOP runway. Keep only its strongest address model.
    best_mode_by_path = {}
    for item in scores:
        best_mode_by_path.setdefault(item["path"], item)
    scores = list(best_mode_by_path.values())
    scores.sort(key=lambda item: (-item["score"], item["path"]))
    # Exact same-kind fingerprints are hierarchy aliases. PC and instruction
    # streams are then paired into composite stage observations before any
    # same-lag ambiguity decision is made.
    all_scored_stage_diagnostics = {
        item["path"]: dict(item.get("identity_diagnostics", {}))
        for item in scores
    }
    for role in ("pc", "instruction"):
        for candidate in discovery.get(
            "candidates", {}
        ).get(role, ()):
            path = candidate.get("path")
            if path in all_scored_stage_diagnostics:
                continue
            diagnostic = _stage_candidate_identity({
                "path": path,
                "signal_kind": role,
                "address_mode": (
                    "instruction" if role == "instruction"
                    else None
                ),
                "paired_by_trial": {},
                "lane_id": candidate.get("lane_id"),
            }, trial_by_id)
            diagnostic["primary_rejection_reason"] = (
                "no_exact_token_matches"
            )
            all_scored_stage_diagnostics[path] = diagnostic
    scores = _candidate_alias_groups(scores)
    scores, instruction_companions, rejected_companions = (
        _compose_stage_candidates(scores)
    )
    scores.sort(key=lambda item: (-item["score"], item["path"]))
    base["candidate_scores"] = scores
    relocation_calibration_present = any(
        str(trial.get("program", "")).startswith(
            "pipeline_calibration_flow_"
        )
        for trial in trials
    )
    confirmed = [
        item for item in scores
        if item.get("signal_kind") == "pc"
        and (
            item.get("relocation_proven") is True
            or (
                not relocation_calibration_present
                and item.get("relocation_proven") is None
            )
        )
        and item["score"] >= 65
        and (
            item["score"] >= 70
            or (item.get("name_role_hint") and item.get("instruction_path"))
            or (
                item.get("name_role_hint")
                and item["coverage"] >= 0.8
                and item["sequence_consistency"] >= 0.95
                and (
                    item.get("commit_alignment_error") is not None
                    or item.get("memory_alignment_error") is not None
                )
            )
        )
        and item["coverage"] >= 0.4
        and (
            item["stable_lag"]
            or (
                item["sequence_consistency"] >= 0.8
                and (
                    item["instruction_correlation"] >= 0.8
                    or item["valid_correlation"] >= 0.95
                )
            )
            or (
                item.get("name_role_hint")
                and item["coverage"] >= 0.8
                and item["sequence_consistency"] >= 0.95
                and (
                    item.get("commit_alignment_error") is not None
                    or item.get("memory_alignment_error") is not None
                )
            )
        )
        and item["median_fetch_offset_cycles"] is not None
        and item["median_fetch_offset_cycles"] >= -1
        and item["median_fetch_offset_cycles"] <= max(windows.values())
        and (item.get("lane_match_ratio") is None or item["lane_match_ratio"] >= 0.8)
    ]
    confirmed_paths = {item["path"] for item in confirmed}
    companion_paths = {
        path for item in confirmed
        for path in item.get("companion_paths", ())
    }
    for path, diagnostic in all_scored_stage_diagnostics.items():
        if path in confirmed_paths:
            diagnostic.update({
                "state": "accepted",
                "primary_rejection_reason": None,
            })
        elif path in companion_paths:
            diagnostic.update({
                "state": "accepted_companion",
                "primary_rejection_reason": None,
            })
        else:
            diagnostic["state"] = "rejected"
            if diagnostic.get("primary_rejection_reason") is None:
                diagnostic["primary_rejection_reason"] = (
                    "dynamic_score_or_coverage"
                )
    base["stage_candidate_diagnostics"] = sorted(
        all_scored_stage_diagnostics.values(),
        key=lambda item: (item.get("path") or ""),
    )
    if not confirmed:
        _enrich_operand_and_control_evidence(base, trials, discovery)
        base.update({
            "state": "partial" if base.get("stages") else "ambiguous",
            "reason": (
                "transaction-local memory evidence recovered without a "
                "relocation-backed PC stream"
                if base.get("stages")
                else "no internal PC or instruction candidate passed "
                "dynamic validation"
            ),
        })
        best = scores[0] if scores else {}
        reject_unattempted_roles(
            f"{len(scores)} stage candidates were scored; best candidate "
            f"{best.get('path', 'none')} had score={best.get('score')} "
            f"coverage={best.get('coverage')} stable_lag="
            f"{best.get('stable_lag')}"
        )
        return base
    base["stage_graph"] = _build_stage_graph(confirmed)
    base["candidate_summary"] = {
        "scored": len(scores),
        "confirmed": len(confirmed),
        "best_score": scores[0]["score"],
        "runner_up_score": scores[1]["score"] if len(scores) > 1 else None,
        "ambiguous_best_score": bool(len(scores) > 1 and scores[0]["score"] == scores[1]["score"]),
    }

    # A same-lag tie is harmless only for exact aliases. Different token traces
    # are genuinely competing interpretations and cannot establish that stage.
    by_lag_lane = defaultdict(list)
    for item in confirmed:
        lag = item["median_fetch_offset_cycles"]
        by_lag_lane[(lag, item.get("lane_id"))].append(item)
    conflicts = {}
    conflict_alternatives = []
    ordered = []
    companion_groups = []
    for (lag, lane), lag_items in sorted(
        by_lag_lane.items(), key=lambda item: (item[0][0], str(item[0][1]))
    ):
        hinted_roles = {
            item.get("name_role_hint")
            for item in lag_items if item.get("name_role_hint")
        }
        scoped = defaultdict(list)
        for item in lag_items:
            role_scope = item.get("name_role_hint")
            if role_scope is None and len(hinted_roles) == 1:
                role_scope = next(iter(hinted_roles))
            scoped[role_scope or "unknown"].append(item)
        for role_scope, items in sorted(scoped.items()):
            if len(items) == 1:
                ordered.append(items[0])
                continue
            behavior_aliases = all(
                _behaviorally_equivalent_stage_stream(items[0], item)
                for item in items[1:]
            )
            if behavior_aliases:
                canonical = max(
                    items,
                    key=lambda item: (
                        item.get("static_rank", 0),
                        bool(item.get("name_role_hint")),
                        -len(item["path"]),
                        item["path"],
                    ),
                )
                canonical["alias_paths"] = sorted(set(
                    canonical.get("alias_paths", [])
                    + [
                        item["path"] for item in items
                        if item is not canonical
                    ]
                ))
                ordered.append(canonical)
                continue
            specific = [
                item for item in items
                if item.get("name_role_hint") == role_scope
            ]
            rejected = [item for item in items if item not in specific]
            if not specific:
                specific, rejected = items, []
            canonical = specific[0]
            companions = specific[1:]
            if all(
                _same_stage_companions(canonical, item)
                for item in companions
            ):
                canonical["companion_paths"] = [
                    item["path"] for item in companions
                ]
                instruction_companion = next(
                    (
                        item for item in companions
                        if item.get("signal_kind") == "instruction"
                    ),
                    None,
                )
                if instruction_companion is not None:
                    canonical["instruction_path"] = (
                        instruction_companion["path"]
                    )
                companion_groups.append({
                    "canonical": canonical["path"],
                    "companions": canonical["companion_paths"],
                    "lower_specificity_rejected": [
                        item["path"] for item in rejected
                    ],
                })
                ordered.append(canonical)
            else:
                outgoing_weight = defaultdict(int)
                for edge in base["stage_graph"].get(
                    "accepted_edges", ()
                ):
                    outgoing_weight[edge.get("from")] += int(
                        edge.get("shared_tokens", 0)
                    )
                # Keep one earliest exact alternative in the graph so a
                # downstream node can never be promoted to frontend merely
                # because two fetch-local streams tie.  The competing nodes
                # remain explicitly ambiguous and unassigned.
                representative = max(items, key=lambda item: (
                    float(item.get("coverage", 0)),
                    bool(item.get("instruction_path")),
                    outgoing_weight[item["path"]],
                    int(item.get("static_rank", 0)),
                    item["path"],
                ))
                ordered.append(representative)
                alternatives = [
                    item for item in items
                    if item is not representative
                ]
                conflict_alternatives.extend(alternatives)
                conflict_key = f"lag={lag}:role={role_scope}:lane={lane}"
                conflicts[conflict_key] = {
                    "paths": [item["path"] for item in items],
                    "roles": [role_scope],
                    "lanes": [str(lane)],
                    "selected_representative": representative["path"],
                    "retained_as_ambiguous": [
                        item["path"] for item in alternatives
                    ],
                }
    base["candidate_summary"].update({
        "alias_groups": [
            {"canonical": item["path"], "aliases": item.get("alias_paths", [])}
            for item in confirmed if item.get("alias_paths")
        ],
        "companion_groups": [*instruction_companions, *companion_groups],
        "rejected_companion_pair_count": len(rejected_companions),
        "rejected_companion_pairs": rejected_companions[:32],
        "unresolved_stage_ties": conflicts,
    })
    ordered, progression_unassigned = _solve_stage_progression(
        ordered, base["stage_graph"],
    )
    base["stage_graph"]["canonical_path"] = [
        item["path"] for item in ordered
    ]
    base["stage_graph"]["unassigned_nodes"] = sorted({
        item["path"]
        for item in [
            *progression_unassigned, *conflict_alternatives,
        ]
    })
    if len(ordered) < 2:
        base.update({"state": "partial", "reason": "fewer than two unambiguous stage streams were visible"})
        role_items = [("frontend", ordered[0])] if ordered else []
    else:
        frontend = ordered[0]
        later = ordered[1:]
        memory_pool = [
            item for item in later if _better_alignment(item, frontend, "memory_alignment_error")
        ]
        named_memory = [item for item in memory_pool if item.get("name_role_hint") == "memory"]
        untyped_memory = [item for item in memory_pool if item.get("name_role_hint") is None]
        memory = min(
            named_memory or untyped_memory,
            key=lambda item: (item["memory_alignment_error"], -item["median_fetch_offset_cycles"]),
            default=None,
        )
        writeback_pool = [
            item for item in later if _better_alignment(item, frontend, "commit_alignment_error")
        ]
        named_writeback = [item for item in writeback_pool if item.get("name_role_hint") == "writeback"]
        untyped_writeback = [
            item for item in writeback_pool
            if item.get("name_role_hint") is None and item.get("commit_alignment_error") <= 1
        ]
        writeback = min(
            named_writeback or untyped_writeback,
            key=lambda item: (item["commit_alignment_error"], -item["median_fetch_offset_cycles"]),
            default=None,
        )
        execute_pool = [
            item for item in later
            if item.get("commit_alignment_error") is not None
            and (
                frontend.get("commit_alignment_error") is None
                or item["commit_alignment_error"] < frontend["commit_alignment_error"]
            )
            and (memory is None or item["median_fetch_offset_cycles"] <= memory["median_fetch_offset_cycles"])
        ]
        named_execute = [item for item in execute_pool if item.get("name_role_hint") == "execute"]
        untyped_execute = [item for item in execute_pool if item.get("name_role_hint") is None]
        execute = (named_execute or untyped_execute or [None])[0]
        if execute is None:
            # A role-local operand proof must not depend on a globally complete
            # commit-aligned map. Use graph topology to expose one provisional
            # consumer stage; operand/source validation remains the proof.
            boundary = memory or writeback
            topology_execute = [
                item for item in later
                if boundary is None
                or item["median_fetch_offset_cycles"]
                <= boundary["median_fetch_offset_cycles"]
            ]
            topology_execute = [
                item for item in topology_execute
                if item is not writeback
            ]
            if topology_execute:
                execute = max(
                    topology_execute,
                    key=lambda item: (
                        item["median_fetch_offset_cycles"],
                        item.get("coverage", 0),
                    ),
                )
        if execute is None and memory is not None and len(ordered) == 2:
            if _looks_combined_execute_memory(memory["path"]):
                execute = memory
        role_items = [("frontend", frontend)]
        between = [
            item for item in later if execute is not None
            and item["median_fetch_offset_cycles"] < execute["median_fetch_offset_cycles"]
        ]
        if between:
            role_items.append(("operand_read", between[-1]))
        if execute is not None and execute is memory:
            role_items.append(("execute_memory", execute))
        elif execute is not None:
            role_items.append(("execute", execute))
        if memory is not None and memory is not execute:
            role_items.append(("memory", memory))
        if writeback is not None and writeback["path"] not in {item["path"] for _, item in role_items}:
            role_items.append(("writeback", writeback))

    stages = []
    for role, item in role_items:
        quality = "pc_valid_or_instruction" if item.get("valid_path") or item.get("instruction_path") else "pc_only"
        stages.append({
            "normalized_role": role,
            "pc_path": item["path"],
            "observation_kind": item.get("signal_kind", "pc"),
            "address_mode": item.get("address_mode"),
            "address_transform": item.get("address_transform"),
            "instruction_path": item.get("instruction_path"),
            "valid_path": item.get("valid_path"),
            "stall_path": item.get("stall_path"),
            "flush_path": item.get("flush_path"),
            "fetch_offset_cycles": item["median_fetch_offset_cycles"],
            "confidence": 0.95 if quality == "pc_valid_or_instruction" else 0.9,
            "evidence_quality": quality,
            "validation_coverage": item["coverage"],
            "commit_alignment_error": item.get("commit_alignment_error"),
            "memory_alignment_error": item.get("memory_alignment_error"),
            "name_role_hint": item.get("name_role_hint"),
            "alias_paths": item.get("alias_paths", []),
            "companion_paths": item.get("companion_paths", []),
            "lane_id": item.get("lane_id"),
            "relocation_proven": item.get("relocation_proven"),
            "identity_diagnostics": item.get(
                "identity_diagnostics", {}
            ),
        })
    base["stages"] = stages
    roles = {stage["normalized_role"] for stage in stages}
    base["capabilities"].update({
        "consumer_stage_observable": bool(roles & {"execute", "execute_memory", "memory"}),
        "execute_stage_observable": bool(roles & {"execute", "execute_memory"}),
        "memory_stage_observable": bool(roles & {"memory", "execute_memory"}),
    })
    base["state"] = (
        "confirmed" if base["capabilities"]["consumer_stage_observable"] and not conflicts
        else "ambiguous" if conflicts else "partial"
    )
    if conflicts:
        base["reason"] = "non-alias candidates produced unresolved same-stage token traces"
        affected_roles = {
            role
            for conflict in conflicts.values()
            for role in conflict.get("roles", ())
        }
        if "unknown" in affected_roles or affected_roles & {
            "execute", "memory", "writeback",
        }:
            base["capabilities"].update({
                "consumer_stage_observable": False,
                "execute_stage_observable": False,
                "memory_stage_observable": False,
            })
    elif base["state"] == "partial" and not base["capabilities"]["consumer_stage_observable"]:
        base["reason"] = "no candidate established an aligned execute or memory consumer stage"

    selected_paths = {stage["pc_path"] for stage in stages}
    for trial in trials:
        observations = {}
        token_observations = {}
        for stage in stages:
            candidate = next(item for item in confirmed if item["path"] == stage["pc_path"])
            matches = candidate.get("paired_by_trial", {}).get(trial["trial_id"], [])
            by_offset = {}
            tokens_by_offset = {}
            for event in matches:
                by_offset.setdefault(str(event["offset"]), event["cycle"])
                tokens_by_offset.setdefault(str(event["offset"]), {
                    "path": stage["pc_path"],
                    "cycle": event["cycle"],
                    "offset": event["offset"],
                    "fetch_cycle": event.get("fetch_cycle"),
                    "fetch_token": event.get("fetch_token"),
                    "epoch_id": event.get("epoch_id"),
                    "transaction_id": event.get("transaction_id"),
                    "transaction_slot": event.get(
                        "transaction_slot", 0,
                    ),
                    "signal_kind": event.get("signal_kind", "pc"),
                    "instruction_path": event.get("instruction_path"),
                    "instruction_matches": event.get(
                        "instruction_matches",
                    ),
                    "lane_id": stage.get("lane_id"),
                    "residence_entry_cycle": event.get(
                        "residence_entry_cycle", event.get("cycle")
                    ),
                    "residence_exit_cycle": event.get(
                        "residence_exit_cycle", event.get("cycle")
                    ),
                    "residence_hold_cycles": event.get(
                        "residence_hold_cycles", 0
                    ),
                })
            observations[stage["normalized_role"]] = by_offset
            token_observations[stage["normalized_role"]] = tokens_by_offset
        base["trial_observations"][trial["trial_id"]] = observations
        base["stage_token_observations"][trial["trial_id"]] = (
            token_observations
        )
    _enrich_operand_and_control_evidence(base, trials, discovery)
    roles_by_path = {
        stage.get("pc_path"): stage.get("normalized_role")
        for stage in base.get("stages", [])
        if stage.get("pc_path")
    }
    for node in base.get("stage_graph", {}).get("nodes", []):
        node["normalized_role"] = roles_by_path.get(node.get("path"))
    base["role_local_chains"] = [
        {
            "use": use,
            "state": evidence.get("state"),
            "stage_path": evidence.get("stage_path"),
            "source_id_path": evidence.get("source_id_path"),
            "operand_path": evidence.get("operand_path"),
            "lane_id": evidence.get("lane_id"),
            "captured_trials": evidence.get("captured_trials", 0),
            "availability_trials": evidence.get(
                "availability_trials", 0
            ),
            "differential_validated": evidence.get(
                "differential_validated"
            ),
            "rejection_reason": evidence.get("rejection_reason"),
        }
        for use, evidence in base.get("role_evidence", {}).items()
    ]
    differential_scores = [
        item for item in base.get("operand_candidate_scores", [])
        if item.get("differential_required")
    ]
    base["differential_candidate_coverage"] = {
        "attempted": len(differential_scores),
        "validated": sum(
            bool(item.get("differential_validated"))
            for item in differential_scores
        ),
        "trial_groups": sorted({
            group
            for item in differential_scores
            for group in item.get("differential_trial_groups", ())
        }),
    }
    source_selector_scores = [
        item for item in base.get("operand_candidate_scores", [])
        if str(item.get("kind", "")).endswith("_id")
    ]
    rejection_categories = defaultdict(int)
    for item in source_selector_scores:
        category = item.get("rejection_category")
        if category:
            rejection_categories[category] += 1
    base["paired_source_selector_coverage"] = {
        "attempted_candidates": len(source_selector_scores),
        "validated_candidates": sum(
            item.get("confirmed") is True
            and item.get("validation_mode")
            != "legacy_unpaired_fixture"
            for item in source_selector_scores
        ),
        "paired_variants": max(
            (item.get("paired_variants", 0) for item in source_selector_scores),
            default=0,
        ),
        "rejection_categories": dict(sorted(rejection_categories.items())),
    }
    base["trial_signal_traces"] = {
        trial["trial_id"]: {
            "signal_samples": trial.get("signal_samples", []),
            "architectural_samples": trial.get("architectural_samples", []),
            "writeback_samples": trial.get("writeback_samples", []),
        }
        for trial in trials
    }
    base["selected_paths"] = sorted(selected_paths)
    return base


def getattr_trial_offset(trial, role):
    if role == "producer":
        return trial.get("producer_offset")
    return trial.get("consumer_offset")


def _frozen_producer_availability(trial, selected_writeback_paths=None):
    producer = next((
        item for item in trial.get("operand_expectations", ())
        if item.get("role") == "producer"
    ), None)
    if producer is None:
        return None
    register = producer.get("destination_register")
    expected = producer.get("result_value")
    samples = sorted(
        (
            item for item in trial.get("architectural_samples", ())
            if item.get("register") == register
        ),
        key=lambda item: _ordered_event(
            item.get("cycle", -1), item.get("phase")
        ),
    )
    prior_wrong = False
    for sample in samples:
        if (
            expected is not None
            and (int(sample.get("value", 0)) & 0xFFFFFFFF)
            == (int(expected) & 0xFFFFFFFF)
        ):
            if prior_wrong:
                return {**sample, "source": "register_storage_transition"}
        else:
            prior_wrong = True
    for sample in trial.get("writeback_samples", ()):
        if (
            sample.get("write_enable")
            and sample.get("write_addr") == register
            and (int(sample.get("write_data", 0)) & 0xFFFFFFFF)
            == (int(expected or 0) & 0xFFFFFFFF)
        ):
            return {
                "cycle": sample.get("cycle"),
                "phase": "post_edge",
                "phase_order": 1,
                "source": "validated_writeback_edge",
                "paths": sample.get("paths"),
                "lane_id": sample.get("lane_id"),
            }
    paths = selected_writeback_paths or {}
    if all(paths.get(key) for key in ("write_addr", "write_data", "write_enable")):
        commit_cycle = next((
            item.get("cycle") for item in trial.get("commits", ())
            if item.get("offset") == producer.get("offset")
        ), None)
        data_sample = _sample_value_near(
            trial, paths["write_data"], commit_cycle, expected, radius=1,
        ) if commit_cycle is not None else None
        address_sample = _sample_value_near(
            trial, paths["write_addr"], commit_cycle, register, radius=1,
        ) if commit_cycle is not None else None
        enable_sample = _last_sample_value(
            trial, paths["write_enable"], data_sample["cycle"],
            data_sample.get("phase", "post_edge"),
        ) if data_sample is not None else None
        if (
            data_sample is not None and address_sample is not None
            and bool((enable_sample or {}).get("value"))
        ):
            return {
                "cycle": data_sample["cycle"],
                "phase": data_sample.get("phase", "post_edge"),
                "phase_order": data_sample.get("phase_order", 1),
                "source": "frozen_writeback_handshake",
                "paths": paths,
                "lane_id": paths.get("lane_id"),
            }
    return None


def _frozen_semantic_collision(
    trial, observation, operand_sample, selected_side,
):
    expected = int(operand_sample.get("value", 0)) & 0xFFFFFFFF
    forbidden = {
        int(value) & 0xFFFFFFFF
        for value in observation.get("forbidden_operand_values", ())
    }
    for key in (
        "immediate_value", "result_value", "poison_value",
        "effective_address",
    ):
        if observation.get(key) is not None:
            forbidden.add(int(observation[key]) & 0xFFFFFFFF)
    forbidden.discard(
        int(observation.get(
            f"{selected_side}_value", expected,
        )) & 0xFFFFFFFF
    )
    if expected in forbidden:
        return "forbidden_discriminator"
    instruction = trial.get("instruction_by_offset", {}).get(
        int(observation.get("offset", -1))
    )
    if instruction is not None and expected == (int(instruction) & 0xFFFFFFFF):
        return "instruction"
    fetch = next((
        item for item in trial.get("fetch_events", ())
        if item.get("offset") == observation.get("offset")
        and not item.get("squashed")
    ), None)
    if fetch is not None:
        pc_values = {
            int(fetch[key]) & 0xFFFFFFFF
            for key in ("pc", "raw_pc", "canonical_pc")
            if fetch.get(key) is not None
        }
        pc_values.add(int(fetch.get("offset", 0)) & 0xFFFFFFFF)
        if expected in pc_values:
            return "pc"
    return None


def _forwarding_trial_use(trial):
    program = str(trial.get("program", ""))
    pair_role = trial.get("pair_role")
    family = (
        program.split(f"_{pair_role}_", 1)[0]
        if pair_role in {"dependent", "control"} else program
    )
    if (
        family.endswith("_to_store_data")
        or "_to_store_data_" in family
    ):
        return "store_data"
    if (
        family.endswith("_to_store_address")
        or "_to_store_address_" in family
    ):
        return "store_address"
    if family.endswith("_to_alu") or "_to_alu_" in family:
        return "execute"
    return None


def _frozen_chain_root_cause(interface, use, evidence, fixed):
    """Preserve the upstream reason a canonical chain could not be frozen."""
    root = {
        "role_evidence_state": evidence.get("state"),
        "role_rejection_reason": evidence.get("rejection_reason"),
        "stage_candidate": None,
        "source_id_candidate": None,
    }
    categories = []
    stage_path = (
        fixed.get("fixed_stage_path")
        or evidence.get("stage_path")
    )
    stage_diagnostics = list(
        interface.get("stage_candidate_diagnostics", ())
    )
    candidate = next((
        item for item in stage_diagnostics
        if stage_path is not None and item.get("path") == stage_path
    ), None)
    if candidate is None and stage_diagnostics:
        candidate = max(stage_diagnostics, key=lambda item: (
            int(item.get("exact_matched_epoch_count", 0)),
            int(item.get("relocation_delta_matches", 0)),
            int(item.get("redirect_matches", 0)),
            item.get("path") or "",
        ))
    if candidate is not None:
        reason = (
            candidate.get("primary_rejection_reason")
            or (
                None if candidate.get("state") in {
                    "accepted", "accepted_companion",
                } else "dynamic_score_or_coverage"
            )
        )
        root["stage_candidate"] = {
            "path": candidate.get("path"),
            "state": candidate.get("state"),
            "primary_rejection_reason": reason,
            "eligible_epoch_count": candidate.get(
                "eligible_epoch_count", 0,
            ),
            "exact_matched_epoch_count": candidate.get(
                "exact_matched_epoch_count", 0,
            ),
            "rejection_counts": candidate.get(
                "rejection_counts", {},
            ),
        }
        if reason is not None:
            categories.append(f"stage_{reason}")
    source_candidates = [
        item for item in interface.get(
            "source_id_linkage_diagnostics", ()
        )
        if item.get("role") in {None, use}
    ]
    if source_candidates:
        source = max(source_candidates, key=lambda item: (
            len(item.get("validated_groups", ())),
            -len(item.get("missing_variants", ())),
            int(item.get("candidate_locality", 0)),
            item.get("candidate_path") or "",
        ))
        root["source_id_candidate"] = {
            "path": source.get("candidate_path"),
            "state": source.get("state"),
            "rejected_discriminator": source.get(
                "rejected_discriminator"
            ),
            "missing_variants": source.get("missing_variants", []),
            "phase": source.get("phase"),
            "lag": source.get("lag"),
        }
        if source.get("state") != "confirmed":
            categories.append(
                "source_id_"
                + str(
                    source.get("rejected_discriminator")
                    or "linkage"
                )
            )
    if not fixed.get("fixed_source_id_path"):
        categories.append("source_id_unavailable")
    if not fixed.get("fixed_operand_path"):
        categories.append("operand_capture_unavailable")
    root["failure_categories"] = sorted(set(categories)) or [
        "canonical_chain_unavailable"
    ]
    return root


def validate_frozen_forwarding_trials(
    interface, trials, pipeline_depth=None,
):
    """Incrementally validate new paired trials against the frozen topology.

    This deliberately performs no candidate discovery or ranking.  The exact
    stage/source/operand/slice/phase/lane chain selected by the second full
    classification is either reproduced by each new token or recorded as a
    role-local near miss.
    """
    requirements = interface.setdefault("requirement_observations", {})
    availability = interface.setdefault(
        "producer_availability_observations", {}
    )
    diagnostics = []
    for trial in trials:
        trial_id = trial["trial_id"]
        observations = trial.get("operand_expectations", ())
        consumer = next((
            item for item in observations
            if item.get("role") == "consumer"
        ), None)
        if consumer is None:
            continue
        producer = next((
            item for item in observations
            if item.get("role") == "producer"
        ), None)
        destination = (
            None if producer is None
            else producer.get("destination_register")
        )
        dependency_side = next((
            side for side in ("rs1", "rs2")
            if destination is not None
            and consumer.get(f"{side}_register") == destination
        ), None)
        use = _forwarding_trial_use(trial)
        if use is None and dependency_side is not None:
            use = consumer.get(f"{dependency_side}_use")
        evidence = interface.get("role_evidence", {}).get(use, {})
        fixed = evidence.get("independent_corroboration", {})
        side = evidence.get("side")
        if side not in {"rs1", "rs2"}:
            dependency_sides = _dependency_consumer_sides(
                trial, consumer, use,
            )
            side = (
                sorted(dependency_sides)[0]
                if dependency_sides else None
            )
        eligibility_key = _trial_eligibility_key(
            trial, use, side,
        )
        if not _trial_is_eligible(trial, use, side):
            continue
        group = {
            "probe": str(trial.get("program", "")).split(
                f'_{trial.get("pair_role")}_', 1
            )[0],
            "spacer_kind": trial.get("spacer_kind", "nop"),
            "gap": int(trial.get("forwarding_gap", 0)),
            "variant": trial.get("variant"),
            "pair_role": trial.get("pair_role"),
        }
        near_miss = {
            **group, "role": use, "trial_id": trial_id,
            "candidate_path": {
                "stage": fixed.get("fixed_stage_path"),
                "source_id": fixed.get("fixed_source_id_path"),
                "operand": fixed.get("fixed_operand_path"),
            },
            "eligible_trials": 1, "matched_trials": 0,
            "missing_variants": [],
            "rejected_discriminator": None,
            "failure_group": (
                "independent_gap"
                if group["spacer_kind"] == "independent"
                else "adjacent" if group["gap"] == 0 else "nop"
            ),
            "eligibility_key": list(eligibility_key or ()),
        }
        if (
            evidence.get("state") != "confirmed"
            or side is None
            or not fixed.get("fixed_source_id_path")
            or not fixed.get("fixed_operand_path")
        ):
            near_miss["mismatch"] = "frozen_chain_unavailable"
            near_miss["root_cause"] = _frozen_chain_root_cause(
                interface, use, evidence, fixed,
            )
            near_miss["failure_categories"] = [
                *near_miss["root_cause"]["failure_categories"],
                "frozen_chain_unavailable",
            ]
            diagnostics.append(near_miss)
            availability[trial_id] = _frozen_producer_availability(
                trial, interface.get("selected_writeback_paths"),
            )
            continue
        fetch = next((
            item for item in trial.get("fetch_events", ())
            if item.get("offset") == consumer.get("offset")
            and not item.get("squashed")
            and not item.get("terminal_loop")
        ), None)
        expected_fetch_token = (
            None if fetch is None else _fetch_token(fetch, 0)
        )
        stage_anchor = None
        stage_path = fixed.get("fixed_stage_path")
        store_transaction = None
        if stage_path is not None:
            stage_events = [
                item for item in trial.get("events", ())
                if item.get("path") == stage_path
            ]
            if fixed.get("fixed_address_transform"):
                stage_events = _materialize_affine_trial_events(
                    stage_path, trial,
                    fixed.get("fixed_address_transform"),
                )
            paired = _pair_candidate_events(
                trial, stage_events,
                _trial_stage_window(trial, pipeline_depth),
            )
            stage_anchor = next((
                item for item in paired
                if item.get("offset") == consumer.get("offset")
                and item.get("fetch_token") == expected_fetch_token
                and (
                    item.get("signal_kind") == "instruction"
                    or not fixed.get("fixed_instruction_path")
                    or (
                        item.get("instruction_path")
                        == fixed.get("fixed_instruction_path")
                        and item.get("instruction_matches") is True
                    )
                )
                and (
                    fetch is None
                    or (
                        item.get("epoch_id") == fetch.get("epoch_id")
                        and item.get("transaction_id")
                        == fetch.get("transaction_id")
                        and int(item.get("transaction_slot", 0))
                        == int(fetch.get("transaction_slot", 0))
                    )
                )
            ), None)
        elif use == "store_data":
            stores = [
                item for item in trial.get("transactions", ())
                if item.get("kind") == "store"
                and item.get("epoch_id") is not None
                and item.get("transaction_id") is not None
                and (
                    trial.get("expected_store_address") is None
                    or item.get("address")
                    == trial.get("expected_store_address")
                )
                and (
                    trial.get("expected_store_value") is None
                    or (int(item.get("value", -1)) & 0xFFFFFFFF)
                    == (int(trial["expected_store_value"]) & 0xFFFFFFFF)
                )
            ]
            if len(stores) == 1:
                store_transaction = stores[0]
                request_cycle = store_transaction.get(
                    "observed_cycle", store_transaction.get("cycle")
                )
                if request_cycle is not None:
                    stage_anchor = {
                        "path": None, "cycle": int(request_cycle) - 1,
                        "offset": consumer.get("offset"),
                        "fetch_token": expected_fetch_token,
                        "epoch_id": (
                            None if fetch is None else fetch.get("epoch_id")
                        ),
                        "transaction_id": (
                            None if fetch is None
                            else fetch.get("transaction_id")
                        ),
                        "transaction_slot": (
                            0 if fetch is None
                            else fetch.get("transaction_slot", 0)
                        ),
                        "signal_kind":
                            "transaction_aligned_operand_capture",
                    }
        if fetch is None or stage_anchor is None:
            near_miss["mismatch"] = (
                "fetch_epoch" if fetch is None
                else "stage_association"
            )
            diagnostics.append(near_miss)
            availability[trial_id] = _frozen_producer_availability(
                trial, interface.get("selected_writeback_paths"),
            )
            continue
        expected_register = consumer.get(f"{side}_register")
        expected_value = consumer.get(f"{side}_value")
        source_phase = (
            fixed.get("fixed_source_id_phase")
            or fixed.get("fixed_phase")
        )
        operand_phase = fixed.get("fixed_phase")
        residence_entry = int(
            stage_anchor.get(
                "residence_entry_cycle", stage_anchor["cycle"]
            )
        )
        residence_exit = int(
            stage_anchor.get(
                "residence_exit_cycle", stage_anchor["cycle"]
            )
        )
        all_source_samples = list(_samples_for_path(
            trial, fixed["fixed_source_id_path"]
        ))
        source_samples = [
            item for item in _samples_for_path(
                trial, fixed["fixed_source_id_path"]
            )
            if item.get("phase") == source_phase
            and (int(item.get("value", -1)) & 0x1F)
            == (int(expected_register) & 0x1F)
            and residence_entry - 2
            <= int(item.get("cycle", -999))
            <= residence_exit + 1
        ]
        if not source_samples:
            expected_source_samples = [
                item for item in all_source_samples
                if (int(item.get("value", -1)) & 0x1F)
                == (int(expected_register) & 0x1F)
            ]
            phase_source_samples = [
                item for item in expected_source_samples
                if item.get("phase") == source_phase
            ]
            near_miss["mismatch"] = (
                "source_selector" if not expected_source_samples
                else "phase" if not phase_source_samples
                else "lag"
            )
            diagnostics.append(near_miss)
            availability[trial_id] = _frozen_producer_availability(
                trial, interface.get("selected_writeback_paths"),
            )
            continue
        fixed_lag = fixed.get("fixed_source_selector_lag")
        candidates = []
        exact_operand_values = []
        phase_operand_values = []
        for source_sample in source_samples:
            for operand_sample in _samples_for_path(
                trial, fixed["fixed_operand_path"]
            ):
                if (
                    int(operand_sample.get("value", 0)) & 0xFFFFFFFF
                ) == (int(expected_value) & 0xFFFFFFFF):
                    exact_operand_values.append(operand_sample)
                    if operand_sample.get("phase") == operand_phase:
                        phase_operand_values.append(operand_sample)
                if (
                    operand_sample.get("phase") != operand_phase
                    or (int(operand_sample.get("value", 0)) & 0xFFFFFFFF)
                    != (int(expected_value) & 0xFFFFFFFF)
                ):
                    continue
                capture_lag = (
                    int(operand_sample["cycle"])
                    - residence_entry
                )
                selector_lag = (
                    int(source_sample["cycle"])
                    - int(operand_sample["cycle"])
                )
                if (
                    0 <= capture_lag
                    <= (residence_exit - residence_entry) + 1
                    and (
                        not fixed.get(
                            "fixed_residence_position_bounds"
                        )
                        or (
                            int(
                                fixed[
                                    "fixed_residence_position_bounds"
                                ][0]
                            )
                            <= capture_lag
                            <= int(
                                fixed[
                                    "fixed_residence_position_bounds"
                                ][1]
                            )
                        )
                    )
                    and abs(selector_lag) <= 1
                    and (
                        fixed_lag is None
                        or selector_lag == int(fixed_lag)
                    )
                ):
                    candidates.append((
                        operand_sample, source_sample, selector_lag,
                    ))
        if not candidates:
            near_miss["mismatch"] = (
                "operand_capture" if not exact_operand_values
                else "phase" if not phase_operand_values
                else "lag"
            )
            diagnostics.append(near_miss)
            availability[trial_id] = _frozen_producer_availability(
                trial, interface.get("selected_writeback_paths"),
            )
            continue
        operand_sample, source_sample, selector_lag = min(
            candidates,
            key=lambda item: (
                abs(int(item[0]["cycle"]) - int(stage_anchor["cycle"])),
                int(item[0]["cycle"]),
            ),
        )
        collision = _frozen_semantic_collision(
            trial, consumer, operand_sample, side,
        )
        if collision is not None:
            near_miss["mismatch"] = "semantic_discriminator"
            near_miss["rejected_discriminator"] = collision
            diagnostics.append(near_miss)
            availability[trial_id] = _frozen_producer_availability(
                trial, interface.get("selected_writeback_paths"),
            )
            continue
        lane_id = fixed.get("fixed_lane_id")
        if lane_id is not None and any(
            sample.get("lane_id") not in {None, lane_id}
            for sample in (source_sample, operand_sample)
        ):
            near_miss["mismatch"] = "lane"
            diagnostics.append(near_miss)
            availability[trial_id] = _frozen_producer_availability(
                trial, interface.get("selected_writeback_paths"),
            )
            continue
        event = {
            "cycle": int(operand_sample["cycle"]),
            "phase": operand_sample.get("phase"),
            "phase_order": operand_sample.get(
                "phase_order",
                0 if operand_sample.get("phase") == "pre_edge" else 1,
            ),
            "path": fixed["fixed_operand_path"],
            "source_id_path": fixed["fixed_source_id_path"],
            "packed_slice": fixed.get("fixed_packed_slice"),
            "source_id_packed_slice": fixed.get(
                "fixed_source_id_packed_slice"
            ),
            "source_selector_lag": selector_lag,
            "source_stage_path": fixed.get(
                "fixed_source_stage_path"
            ),
            "operand_stage_path": fixed.get(
                "fixed_operand_stage_path",
                fixed.get("fixed_stage_path"),
            ),
            "joining_edge": fixed.get("fixed_joining_edge"),
            "residence_relative_position": (
                int(operand_sample["cycle"]) - residence_entry
            ),
            "value": int(operand_sample.get("value", 0)) & 0xFFFFFFFF,
            "side": side,
            "lane_id": lane_id,
            "fetch_slot": fetch.get("transaction_slot", 0),
            "lane_identity_confirmed": True,
            "fetch_token": expected_fetch_token,
            "stage_token": {
                **stage_anchor, "offset": consumer.get("offset"),
                "lane_id": lane_id,
            },
            "consumer_token_proof": True,
            "source_selector_validation": True,
            "operand_differential_validation": True,
            "semantic_discriminators_passed": True,
            "capture_source": "frozen_chain_incremental_validation",
            "role_evidence_state": "confirmed",
            "memory_epoch_id": (
                None if store_transaction is None
                else store_transaction.get("epoch_id")
            ),
            "memory_transaction_id": (
                None if store_transaction is None
                else store_transaction.get("transaction_id")
            ),
        }
        requirements.setdefault(trial_id, {})[use] = event
        availability[trial_id] = _frozen_producer_availability(
            trial, interface.get("selected_writeback_paths"),
        )
        near_miss["matched_trials"] = 1
        near_miss["mismatch"] = None
        diagnostics.append(near_miss)

    interface.setdefault(
        "incremental_corroboration_diagnostics", []
    ).extend(diagnostics)
    interface.setdefault("exact_capture_failures", []).extend({
        "trial_id": item.get("trial_id"),
        "role": item.get("role"),
        "side": (
            item.get("eligibility_key", [None, None, None])[2]
            if len(item.get("eligibility_key", ())) >= 3 else None
        ),
        "failure_categories": item.get(
            "failure_categories", [item.get("mismatch")]
        ),
        "mismatch": item.get("mismatch"),
        "eligibility_key": item.get("eligibility_key", []),
        "candidate_path": item.get("candidate_path"),
        "rejected_discriminator": item.get(
            "rejected_discriminator"
        ),
        "root_cause": item.get("root_cause"),
        "failure_group": item.get("failure_group"),
        "gap": item.get("gap"),
        "variant": item.get("variant"),
    } for item in diagnostics if item.get("mismatch"))
    grouped_diagnostics = defaultdict(list)
    for item in interface["incremental_corroboration_diagnostics"]:
        grouped_diagnostics[(
            item.get("role"), item.get("probe"),
            item.get("failure_group"), item.get("spacer_kind"),
            item.get("gap"),
        )].append(item)
    interface["near_miss_diagnostics"] = [
        {
            "role": key[0], "probe": key[1],
            "group": key[2], "spacer_kind": key[3], "gap": key[4],
            "candidate_path": values[0].get("candidate_path"),
            "eligible_trials": len(values),
            "matched_trials": sum(
                item.get("matched_trials", 0) for item in values
            ),
            "missing_variants": sorted({
                item.get("variant") for item in values
                if not item.get("matched_trials")
                and item.get("variant") is not None
            }),
            "rejected_discriminator": sorted({
                item.get("rejected_discriminator") for item in values
                if item.get("rejected_discriminator")
            }) or None,
            "mismatches": sorted({
                item.get("mismatch") for item in values
                if item.get("mismatch")
            }),
        }
        for key, values in sorted(
            grouped_diagnostics.items(), key=lambda item: str(item[0])
        )
    ]
    for use, evidence in interface.get("role_evidence", {}).items():
        role_trials = [
            trial for trial in trials
            if _forwarding_trial_use(trial) == use
        ]
        if not role_trials:
            continue
        corroboration = evidence.setdefault(
            "independent_corroboration", {}
        )
        gaps = sorted({
            int(trial.get("forwarding_gap", 0))
            for trial in role_trials
            if trial.get("spacer_kind") == "independent"
        })
        corroboration["required"] = bool(
            corroboration.get("required") or gaps
        )
        corroboration["tested_gaps"] = sorted(set(
            corroboration.get("tested_gaps", ())
        ) | set(gaps))
        group_complete = bool(
            role_trials
            and all(
                requirements.get(trial["trial_id"], {}).get(use)
                is not None
                for trial in role_trials
            )
        )
        groups = corroboration.setdefault("trial_groups", [])
        pair_role = role_trials[0].get("pair_role")
        probe = str(role_trials[0].get("program", "")).split(
            f"_{pair_role}_", 1
        )[0]
        group_record = next((
            item for item in groups
            if item.get("probe") == probe
            and item.get("spacer_kind")
            == role_trials[0].get("spacer_kind", "nop")
            and int(item.get("gap", 0))
            == int(role_trials[0].get("forwarding_gap", 0))
        ), None)
        increment = {
            "probe": probe,
            "spacer_kind": role_trials[0].get("spacer_kind", "nop"),
            "gap": int(role_trials[0].get("forwarding_gap", 0)),
            "eligible_trials": len(role_trials),
            "matched_trials": sum(
                requirements.get(trial["trial_id"], {}).get(use)
                is not None
                for trial in role_trials
            ),
            "validated": group_complete,
        }
        if group_record is None:
            groups.append(increment)
        else:
            group_record["eligible_trials"] += increment[
                "eligible_trials"
            ]
            group_record["matched_trials"] += increment[
                "matched_trials"
            ]
            group_record["validated"] = (
                group_record["matched_trials"]
                == group_record["eligible_trials"]
            )
        independent_groups = [
            item for item in groups
            if item.get("spacer_kind") == "independent"
        ]
        corroboration["validated"] = bool(
            independent_groups
            and all(item.get("validated") for item in independent_groups)
        )
    return diagnostics


def _normalized_roles(count):
    if count == 2:
        return ["frontend", "execute_memory"]
    if count == 3:
        return ["frontend", "execute", "memory"]
    if count == 4:
        return ["frontend", "operand_read", "execute", "memory"]
    # More exposed stage registers are folded into the five semantic roles.
    if count >= 5:
        return ["frontend", "operand_read", "execute", "memory", "writeback"]
    return ["frontend"]


def consumer_stage_cycle(interface, trial_id, consumer_offset, required_role):
    if interface.get("state") is not None and interface.get("state") not in {"confirmed", "partial"}:
        return None, None
    observations = interface.get("trial_observations", {}).get(str(trial_id), {})
    roles = [required_role]
    if required_role in ("execute", "memory"):
        roles.append("execute_memory")
    for role in roles:
        cycle = observations.get(role, {}).get(str(consumer_offset))
        if cycle is not None:
            stage = next((item for item in interface.get("stages", []) if item["normalized_role"] == role), {})
            return cycle, stage
    return None, None


def compact_pipeline_interface(interface):
    """Remove per-trial and rejected-candidate traces from the public artifact."""
    compact = {
        key: value for key, value in interface.items()
        if key not in {
            "trial_observations", "candidate_scores", "operand_candidate_scores",
            "control_candidate_scores", "writeback_candidate_scores",
            "requirement_observations", "producer_availability_observations",
            "trial_signal_traces",
            "stage_token_observations",
            "incremental_corroboration_diagnostics",
        }
    }
    if isinstance(compact.get("stage_window_cycles"), dict):
        compact["stage_window_cycles"] = {
            key: value for key, value in compact["stage_window_cycles"].items()
            if key != "per_trial"
        }
    return compact


def write_pipeline_interface(output_dir, core_name, interface):
    path = os.path.join(output_dir, f"{core_name}_pipeline_interface.json")
    temporary = f"{path}.tmp"
    interface = {
        **interface,
        "implementation_revision": PIPELINE_INTERFACE_IMPLEMENTATION_REVISION,
    }
    with open(temporary, "w", encoding="utf-8") as stream:
        json.dump(compact_pipeline_interface(interface), stream, indent=4)
    os.replace(temporary, path)
    return path
