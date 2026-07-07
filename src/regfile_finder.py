import cocotb
import argparse
import json
import os
import subprocess
import logging
import re
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# -----------------------------------------------------------------------------
# Static register-file discovery
# -----------------------------------------------------------------------------
# This stage does not try to prove that an object is the architectural register
# file.  It only finds HDL objects whose *shape* is compatible with a RISC-V GPR
# file.  Dynamic confirmation should be done afterwards with an instruction test.

# RISC-V full GPR file has 32 entries.  Some cores expose x1..x31 only, and RV32E
# style cores may expose 16 entries.
REGFILE_DEPTHS = {16, 31, 32}
REGFILE_WORD_WIDTHS = {32, 64}

# cocotb/GPI type strings vary a little between simulators and cocotb versions.
# Keep this intentionally permissive because this is a discovery heuristic.
HIERARCHY_TYPES = {
    "GPI_MODULE",
    "GPI_PACKAGE",
    "GPI_INTERFACE",
    "GPI_STRUCT",
    "GPI_STRUCTURE",
    "GPI_GENARRAY",
    "GPI_MODULE_ARRAY",
}
ARRAY_TYPES = {
    "GPI_ARRAY",
    "GPI_MEMORY",
    "GPI_REGISTER_ARRAY",
    "GPI_REG_ARRAY",
    "GPI_NET_ARRAY",
}
VECTOR_TYPES = {
    "GPI_REGISTER",
    "GPI_NET",
    "GPI_LOGIC",
    "GPI_INTEGER",
    "GPI_PARAMETER",
    "GPI_CONSTANT",
}

REGFILE_NAME_HINTS = (
    "regfile", "reg_file", "register_file", "registers", "regs",
    "gpr", "gprs", "rf", "xreg", "xregs", "int_reg", "integer_file",
    "regbank", "reg_bank", "bank",
)
NON_REGFILE_NAME_HINTS = (
    "cache", "icache", "dcache", "mem", "memory", "ram", "rom", "bootrom",
    "imem", "dmem", "sram", "dram", "fifo", "queue", "buffer", "buf",
    "tlb", "csr", "scoreboard",
)

NOP_INSTRUCTION = 0x00000013
REGFILE_WRITE_LOOP_PC = 0x0000002C
REGFILE_WRITE_MAX_CYCLES = 300
REGFILE_LOOP_QUIESCENCE_CYCLES = 8
REGFILE_INTERFACE_LOOP_PC = 0x0000001C
REGFILE_INTERFACE_TIMING_OFFSETS = (-2, -1, 0, 1)
DERIVED_WRITE_ENABLE_PATH = "__storage_update_event__"
DERIVED_WRITE_DATA_PATH = "__storage_update_value__"


def _safe_type(handle):
    """Return the simulator/GPI type string, or an empty string if unavailable."""
    try:
        return str(getattr(handle, "_type", "") or "")
    except Exception:
        return ""


def _safe_path(handle, fallback=""):
    """Return a stable hierarchical path for a handle."""
    for attr in ("_path", "path", "name"):
        try:
            value = getattr(handle, attr)
            if value is not None:
                return str(value)
        except Exception:
            pass
    return fallback


def _safe_len(handle):
    """Best-effort width/element-count query for cocotb handles and values."""
    try:
        return len(handle)
    except Exception:
        pass

    # cocotb SimHandleBase wraps a raw GPI handle that can expose get_num_elems().
    try:
        raw_handle = getattr(handle, "_handle", None)
        if raw_handle is not None and hasattr(raw_handle, "get_num_elems"):
            n = raw_handle.get_num_elems()
            if n is not None:
                return int(n)
    except Exception:
        pass

    # Some older cocotb value objects expose n_bits.
    try:
        value = getattr(handle, "value")
        n_bits = getattr(value, "n_bits", None)
        if n_bits is not None:
            return int(n_bits)
    except Exception:
        pass

    return None


def _safe_get_child(handle, index):
    try:
        return handle[index]
    except Exception:
        return None


def _value_to_int(value):
    try:
        is_resolvable = getattr(value, "is_resolvable", True)
        if not is_resolvable:
            return None
    except Exception:
        pass

    try:
        return int(value)
    except Exception:
        pass

    try:
        return int(value.integer)
    except Exception:
        pass

    return None


def _safe_value_int(handle):
    try:
        return _value_to_int(getattr(handle, "value"))
    except Exception:
        return None


def _iter_range_indices(handle, limit=8):
    """Return likely legal indices for HDL arrays with arbitrary left/right bounds."""
    indices = []

    # cocotb ArrayObject/LogicArrayObject commonly expose .range, .left, .right.
    try:
        hdl_range = getattr(handle, "range")
        for i, idx in enumerate(hdl_range):
            if i >= limit:
                break
            indices.append(int(idx))
    except Exception:
        pass

    for attr in ("left", "right"):
        try:
            idx = int(getattr(handle, attr))
            indices.append(idx)
        except Exception:
            pass

    n = _safe_len(handle)
    if n is not None:
        # Covers common Verilog [0:N-1], [N-1:0], and VHDL 1 to N styles.
        indices.extend([0, 1, n - 1, n, 15, 16, 30, 31])

    # Preserve order while deduplicating.
    deduped = []
    seen = set()
    for idx in indices:
        if idx not in seen:
            deduped.append(idx)
            seen.add(idx)
    return deduped[:limit]


def _sample_array_elements(handle, limit=4):
    """Return [(index, child_handle), ...] for legal-looking array indices."""
    samples = []
    for idx in _iter_range_indices(handle, limit=12):
        child = _safe_get_child(handle, idx)
        if child is not None:
            samples.append((idx, child))
        if len(samples) >= limit:
            break
    return samples


def _word_width_from_samples(samples):
    """Infer the element width of an unpacked array from a few sampled children."""
    widths = []
    for _, child in samples:
        width = _safe_len(child)
        if width is not None:
            widths.append(width)

    if not widths:
        return None

    # Use the most common sampled width.  Register-file arrays should be uniform.
    return max(set(widths), key=widths.count)


def _path_name_score(path):
    path_l = path.lower()
    score = 0
    reasons = []

    matched_good = [hint for hint in REGFILE_NAME_HINTS if hint in path_l]
    matched_bad = [hint for hint in NON_REGFILE_NAME_HINTS if hint in path_l]

    if matched_good:
        score += min(25, 8 * len(matched_good))
        reasons.append(f"name hint(s): {', '.join(matched_good[:4])}")
    if matched_bad:
        score -= min(30, 10 * len(matched_bad))
        reasons.append(f"non-regfile name hint(s): {', '.join(matched_bad[:4])}")

    return score, reasons


def _score_array_shape(depth, word_width, kind, path, valid_word_widths=None):
    if valid_word_widths is None:
        valid_word_widths = REGFILE_WORD_WIDTHS

    score = 0
    reasons = []

    if kind == "array_of_words":
        score += 25
        reasons.append("unpacked/indexable array")
    elif kind == "packed_flat_vector":
        score += 12
        reasons.append("packed vector with register-file-sized total width")
    elif kind == "vector_group":
        score += 18
        reasons.append("same-scope group of XLEN-sized vectors")
    elif kind == "scalar_bit_cluster":
        score += 10
        reasons.append("same-scope cluster of scalar bits")

    if depth == 32:
        score += 35
        reasons.append("32 entries")
    elif depth == 31:
        score += 30
        reasons.append("31 entries, likely x1..x31 without x0")
    elif depth == 16:
        score += 20
        reasons.append("16 entries, possible RV32E/RV64E-style file")
    elif depth is not None:
        score -= 20
        reasons.append(f"unusual depth {depth}")

    if word_width in valid_word_widths:
        score += 35
        reasons.append(f"XLEN-sized words ({word_width})")
    elif word_width is not None:
        score -= 15
        reasons.append(f"unusual word width {word_width}")

    name_score, name_reasons = _path_name_score(path)
    score += name_score
    reasons.extend(name_reasons)

    return score, reasons


def _classify_array_like_candidate(handle, depths=None, word_widths=None):
    """
    Return a JSON-serializable candidate dict if handle has a register-file-like
    array shape; otherwise return None.
    """
    if depths is None:
        depths = REGFILE_DEPTHS
    if word_widths is None:
        word_widths = REGFILE_WORD_WIDTHS

    handle_type = _safe_type(handle)
    path = _safe_path(handle)
    n = _safe_len(handle)

    # Case 1: HDL unpacked array / memory: regs[0:31], regs(0 to 31), etc.
    if handle_type in ARRAY_TYPES or "ARRAY" in handle_type or "MEMORY" in handle_type:
        samples = _sample_array_elements(handle)
        word_width = _word_width_from_samples(samples)
        depth = n

        if depth in depths and word_width in word_widths:
            score, reasons = _score_array_shape(depth, word_width, "array_of_words", path, word_widths)
            return {
                "path": path,
                "kind": "array_of_words",
                "handle_type": handle_type,
                "depth": depth,
                "word_width": word_width,
                "total_width": depth * word_width,
                "sample_indices": [idx for idx, _ in samples],
                "score": score,
                "reasons": reasons,
            }

        # Some simulators expose a packed vector as GPI_ARRAY.  Treat it as a
        # flat vector only when indexing looks bit-like or unavailable.  Do not
        # reinterpret a true memory depth, e.g. 1024 x 32, as a 32 x 32 packed
        # register file just because len(memory) == 1024.
        if not samples or word_width in (None, 1):
            flat = _classify_flat_vector_candidate(handle, handle_type, path, n, depths, word_widths)
            if flat is not None:
                return flat

    # Case 2: one packed vector containing all registers: [1023:0], [991:0], etc.
    if handle_type in VECTOR_TYPES or n is not None:
        return _classify_flat_vector_candidate(handle, handle_type, path, n, depths, word_widths)

    return None


def _classify_flat_vector_candidate(handle, handle_type=None, path=None, width=None, depths=None, word_widths=None):
    if depths is None:
        depths = REGFILE_DEPTHS
    if word_widths is None:
        word_widths = REGFILE_WORD_WIDTHS

    if handle_type is None:
        handle_type = _safe_type(handle)
    if path is None:
        path = _safe_path(handle)
    if width is None:
        width = _safe_len(handle)

    if width is None:
        return None

    for word_width in sorted(word_widths):
        if width % word_width != 0:
            continue
        depth = width // word_width
        if depth not in depths:
            continue

        score, reasons = _score_array_shape(depth, word_width, "packed_flat_vector", path, word_widths)
        return {
            "path": path,
            "kind": "packed_flat_vector",
            "handle_type": handle_type,
            "depth": depth,
            "word_width": word_width,
            "total_width": width,
            "slice_order": "unknown_static_only",
            "score": score,
            "reasons": reasons,
        }

    return None


def _leaf_basename(path):
    return str(path).split(".")[-1]


def _common_scope(path):
    parts = str(path).split(".")
    if len(parts) <= 1:
        return ""
    return ".".join(parts[:-1])


def _normalize_group_prefix(prefix):
    return re.sub(r"[\W_]+$", "", prefix or "").lower()


def _parse_trailing_index(name):
    """
    Return (prefix, index) for common register-vector names:
    x0, x_0, regs_0, rf31, r[12], gpr[3].
    """
    patterns = (
        r"^(.+?)[\[_](\d+)\]?$",
        r"^([A-Za-z_][A-Za-z_]*)(\d+)$",
    )
    for pattern in patterns:
        match = re.match(pattern, name)
        if match:
            return _normalize_group_prefix(match.group(1)), int(match.group(2))
    return None, None


def _parse_reg_bit_indices(name):
    """
    Return (prefix, reg_index, bit_index) for scalarized names such as:
    regs_0_31, regs[0][31], x0_b31, rf31_bit0.
    """
    patterns = (
        r"^(.+?)[\[_](\d+)\]?\[(\d+)\]$",
        r"^(.+?)[\[_](\d+)\]?[_.-]b(?:it)?_?(\d+)$",
        r"^(.+?)[\[_](\d+)[_.-](\d+)\]?$",
        r"^([A-Za-z_]+)(\d+)[_.-]b(?:it)?_?(\d+)$",
    )
    for pattern in patterns:
        match = re.match(pattern, name)
        if match:
            return (
                _normalize_group_prefix(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
            )
    return None, None, None


def _member_record(leaf, include_bit=False):
    record = {
        "name": leaf["name"],
        "path": leaf["path"],
        "handle_type": leaf["handle_type"],
        "width": leaf["width"],
    }
    if leaf.get("reg_index") is not None:
        record["reg_index"] = leaf["reg_index"]
    if include_bit and leaf.get("bit_index") is not None:
        record["bit_index"] = leaf["bit_index"]
    return record


def _indices_match_depth(indices, depth):
    sorted_indices = sorted(indices)
    if depth == 31:
        return sorted_indices == list(range(1, 32)) or sorted_indices == list(range(31))
    return sorted_indices == list(range(depth))


def _classify_vector_group(scope, leaves, depths=None, word_widths=None):
    if depths is None:
        depths = REGFILE_DEPTHS
    if word_widths is None:
        word_widths = REGFILE_WORD_WIDTHS

    candidates = []
    grouped = {}

    for leaf in leaves:
        width = leaf["width"]
        if width not in word_widths:
            continue
        prefix, index = _parse_trailing_index(leaf["name"])
        if prefix is None:
            continue
        leaf = dict(leaf)
        leaf["reg_index"] = index
        grouped.setdefault((prefix, width), []).append(leaf)

    for (prefix, word_width), group in grouped.items():
        unique_by_index = {}
        for leaf in group:
            unique_by_index.setdefault(leaf["reg_index"], leaf)

        depth = len(unique_by_index)
        if depth not in depths or not _indices_match_depth(unique_by_index.keys(), depth):
            continue

        ordered = [unique_by_index[idx] for idx in sorted(unique_by_index)]
        score_path = f"{scope}.{prefix}" if scope else prefix
        score, reasons = _score_array_shape(depth, word_width, "vector_group", score_path, word_widths)
        reasons.append(f"common prefix: {prefix}")
        candidates.append({
            "path": score_path,
            "scope": scope,
            "kind": "vector_group",
            "depth": depth,
            "word_width": word_width,
            "total_width": depth * word_width,
            "index_order": "ascending_name_index",
            "bit_order": "native_vector_order",
            "members": [_member_record(leaf) for leaf in ordered],
            "score": score,
            "reasons": reasons,
        })

    return candidates


def _classify_scalar_bit_clusters(scope, leaves, depths=None, word_widths=None):
    if depths is None:
        depths = REGFILE_DEPTHS
    if word_widths is None:
        word_widths = REGFILE_WORD_WIDTHS

    candidates = []
    grouped = {}

    for leaf in leaves:
        if leaf["width"] != 1:
            continue
        prefix, reg_index, bit_index = _parse_reg_bit_indices(leaf["name"])
        if prefix is None:
            continue
        leaf = dict(leaf)
        leaf["reg_index"] = reg_index
        leaf["bit_index"] = bit_index
        grouped.setdefault(prefix, []).append(leaf)

    for prefix, group in grouped.items():
        bits_by_reg = {}
        for leaf in group:
            bits_by_reg.setdefault(leaf["reg_index"], {})[leaf["bit_index"]] = leaf

        depth = len(bits_by_reg)
        if depth not in depths or not _indices_match_depth(bits_by_reg.keys(), depth):
            continue

        for word_width in sorted(word_widths):
            expected_bits = set(range(word_width))
            if not all(set(bits.keys()) == expected_bits for bits in bits_by_reg.values()):
                continue

            ordered = []
            for reg_index in sorted(bits_by_reg):
                for bit_index in sorted(bits_by_reg[reg_index]):
                    ordered.append(bits_by_reg[reg_index][bit_index])

            score_path = f"{scope}.{prefix}" if scope else prefix
            score, reasons = _score_array_shape(depth, word_width, "scalar_bit_cluster", score_path, word_widths)
            reasons.append(f"common prefix: {prefix}")
            candidates.append({
                "path": score_path,
                "scope": scope,
                "kind": "scalar_bit_cluster",
                "depth": depth,
                "word_width": word_width,
                "total_width": depth * word_width,
                "index_order": "ascending_name_index",
                "bit_order": "ascending_name_bit_index",
                "members": [_member_record(leaf, include_bit=True) for leaf in ordered],
                "score": score,
                "reasons": reasons,
            })
            break

    return candidates


def _is_hierarchy_handle(handle):
    handle_type = _safe_type(handle)
    if handle_type in HIERARCHY_TYPES:
        return True

    # Fallback: modules usually do not have a value, leaves usually do.
    try:
        getattr(handle, "value")
        return False
    except Exception:
        return bool(handle_type) and handle_type not in (ARRAY_TYPES | VECTOR_TYPES)


def _iter_sim_children(module):
    """Yield (name, child_handle) pairs discovered through cocotb attribute access."""
    seen_paths = set()

    for name in dir(module):
        if name.startswith("_"):
            continue
        try:
            child = getattr(module, name)
        except Exception:
            continue

        # Skip normal Python methods/properties, but keep simulator handles.
        if callable(child) and not hasattr(child, "_type"):
            continue

        child_type = _safe_type(child)
        if not child_type:
            continue

        child_path = _safe_path(child, fallback=name)
        if child_path in seen_paths:
            continue
        seen_paths.add(child_path)
        yield name, child


def discover_regfile_array_candidates(root, max_depth=25, depths=None, word_widths=None):
    """
    Walk the visible simulation hierarchy and find static array-like register-file
    candidates.  Returns a ranked list of dicts.

    This detects:
      * unpacked arrays/memories with 16/31/32 elements of 32/64-bit words;
      * packed flat vectors with width 16/31/32 * 32/64 bits.
      * same-scope groups of 16/31/32 XLEN-sized vectors;
      * same-scope scalar-bit clusters that form 16/31/32 XLEN-sized words.

    It intentionally does not decide correctness.  A later dynamic phase should
    confirm that writes to xN update the candidate and persist.
    """
    if depths is None:
        depths = REGFILE_DEPTHS
    else:
        depths = set(depths)
    if word_widths is None:
        word_widths = REGFILE_WORD_WIDTHS
    else:
        word_widths = set(word_widths)

    candidates = []
    visited = set()
    stack = [(root, 0)]

    while stack:
        module, depth = stack.pop()
        if depth > max_depth:
            continue

        module_key = _safe_path(module, fallback=str(id(module)))
        if module_key in visited:
            continue
        visited.add(module_key)

        scope_leaves = []

        for _, child in _iter_sim_children(module):
            child_path = _safe_path(child)
            child_type = _safe_type(child)
            child_width = _safe_len(child)

            candidate = _classify_array_like_candidate(child, depths, word_widths)
            if candidate is not None:
                candidates.append(candidate)

            if _is_hierarchy_handle(child):
                stack.append((child, depth + 1))
                continue

            scope_leaves.append({
                "name": _leaf_basename(child_path),
                "path": child_path,
                "handle_type": child_type,
                "width": child_width,
            })

            # Generate arrays / arrays of instances may be indexable.  Only recurse
            # into sampled children that are themselves hierarchy handles.
            if child_type in ARRAY_TYPES or "ARRAY" in child_type:
                for _, sampled_child in _sample_array_elements(child, limit=8):
                    if _is_hierarchy_handle(sampled_child):
                        stack.append((sampled_child, depth + 1))

        scope = _safe_path(module, fallback="")
        candidates.extend(_classify_vector_group(scope, scope_leaves, depths, word_widths))
        candidates.extend(_classify_scalar_bit_clusters(scope, scope_leaves, depths, word_widths))

    # Remove duplicates by path, preserving the highest score.
    best_by_path = {}
    for c in candidates:
        path = c["path"]
        if path not in best_by_path or c["score"] > best_by_path[path]["score"]:
            best_by_path[path] = c

    ranked = sorted(best_by_path.values(), key=lambda c: c["score"], reverse=True)
    return ranked


def get_arrays_current_module(module):
    """
    Compatibility wrapper for the old code path.

    Returns:
        arrays: [[handle, path], ...] for array-like/flat-vector objects in this
                module only.  These are not yet filtered as register files.
        submodules: [name, ...]
    """
    submodules = []
    arrays = []

    for name, obj_handle in _iter_sim_children(module):
        obj_type = _safe_type(obj_handle)
        obj_path = _safe_path(obj_handle, fallback=name)

        if _is_hierarchy_handle(obj_handle):
            submodules.append(name)
        elif obj_type in ARRAY_TYPES or "ARRAY" in obj_type or "MEMORY" in obj_type:
            arrays.append([obj_handle, obj_path])
        else:
            width = _safe_len(obj_handle)
            if _classify_flat_vector_candidate(obj_handle, obj_type, obj_path, width) is not None:
                arrays.append([obj_handle, obj_path])

    return arrays, submodules


def get_arrays_hierarchy(module, regfile_candidates=None):
    """
    Backward-compatible API: return only candidate paths.

    Prefer discover_regfile_array_candidates() for the completed static-discovery
    metadata used by the first pipeline stage.
    """
    if regfile_candidates is None:
        regfile_candidates = []

    for candidate in discover_regfile_array_candidates(module):
        regfile_candidates.append(candidate["path"])

    return regfile_candidates


# -----------------------------------------------------------------------------
# Phase 2: candidate visibility checks
# -----------------------------------------------------------------------------

def _resolve_path(root, path):
    """Resolve a dotted cocotb path with optional array indices."""
    if not path:
        return None

    parts = str(path).split(".")
    root_names = {
        _leaf_basename(_safe_path(root)),
        str(getattr(root, "_name", "")),
        str(getattr(root, "name", "")),
    }
    if parts and parts[0] in root_names:
        parts = parts[1:]

    current = root
    for part in parts:
        if not part:
            continue

        match = re.match(r"^([^\[]+)((?:\[-?\d+\])*)$", part)
        if not match:
            return None

        name, indices = match.groups()
        try:
            current = getattr(current, name)
        except Exception:
            return None

        for idx in re.findall(r"\[(-?\d+)\]", indices):
            current = _safe_get_child(current, int(idx))
            if current is None:
                return None

    return current


def _can_sample_value(handle):
    try:
        getattr(handle, "value")
        return True, "value readable"
    except Exception as exc:
        return False, f"value not readable: {exc}"


def _check_single_candidate_visibility(dut, candidate):
    path = candidate.get("path")
    handle = _resolve_path(dut, path)
    if handle is None:
        return False, "invisible", [f"path not resolvable: {path}"]

    kind = candidate.get("kind")
    reasons = [f"path resolvable: {path}"]

    if kind == "array_of_words":
        sample_indices = candidate.get("sample_indices") or _iter_range_indices(handle, limit=4)
        if not sample_indices:
            return False, "invisible", reasons + ["array has no sampled indices"]

        visible = 0
        for idx in sample_indices:
            child = _safe_get_child(handle, idx)
            if child is None:
                reasons.append(f"index {idx} not resolvable")
                continue
            ok, reason = _can_sample_value(child)
            reasons.append(f"index {idx}: {reason}")
            if ok:
                visible += 1

        if visible == len(sample_indices):
            return True, "visible", reasons
        if visible:
            return False, "partial", reasons
        return False, "invisible", reasons

    ok, reason = _can_sample_value(handle)
    reasons.append(reason)
    return ok, "visible" if ok else "invisible", reasons


def _check_group_candidate_visibility(dut, candidate):
    members = candidate.get("members") or []
    if not members:
        return False, "invisible", ["group candidate has no members"]

    visible = 0
    reasons = []
    for member in members:
        path = member.get("path")
        handle = _resolve_path(dut, path)
        if handle is None:
            reasons.append(f"member not resolvable: {path}")
            continue
        ok, reason = _can_sample_value(handle)
        reasons.append(f"{path}: {reason}")
        if ok:
            visible += 1

    if visible == len(members):
        return True, "visible", reasons
    if visible:
        return False, "partial", reasons
    return False, "invisible", reasons


def check_candidate_visibility(dut, candidate):
    """
    Return a copy of candidate annotated with Phase 2 visibility fields.
    """
    annotated = dict(candidate)
    kind = candidate.get("kind")

    if kind in ("vector_group", "scalar_bit_cluster"):
        visible, status, reasons = _check_group_candidate_visibility(dut, candidate)
    else:
        visible, status, reasons = _check_single_candidate_visibility(dut, candidate)

    annotated["visible"] = visible
    annotated["visibility_status"] = status
    annotated["visibility_reasons"] = reasons
    return annotated


def check_regfile_candidate_visibility(dut, candidates):
    annotated = [check_candidate_visibility(dut, candidate) for candidate in candidates]
    summary = {
        "visible": sum(1 for c in annotated if c.get("visibility_status") == "visible"),
        "invisible": sum(1 for c in annotated if c.get("visibility_status") == "invisible"),
        "partial": sum(1 for c in annotated if c.get("visibility_status") == "partial"),
        "total": len(annotated),
    }
    return annotated, summary


# -----------------------------------------------------------------------------
# Phase 3: deterministic register-write program
# -----------------------------------------------------------------------------

def _encode_i_type(imm, rs1, funct3, rd, opcode):
    return ((imm & 0xFFF) << 20) | ((rs1 & 0x1F) << 15) | ((funct3 & 0x7) << 12) | ((rd & 0x1F) << 7) | (opcode & 0x7F)


def _encode_u_type(imm20, rd, opcode):
    return ((imm20 & 0xFFFFF) << 12) | ((rd & 0x1F) << 7) | (opcode & 0x7F)


def _encode_r_type(funct7, rs2, rs1, funct3, rd, opcode):
    return (
        ((funct7 & 0x7F) << 25)
        | ((rs2 & 0x1F) << 20)
        | ((rs1 & 0x1F) << 15)
        | ((funct3 & 0x7) << 12)
        | ((rd & 0x1F) << 7)
        | (opcode & 0x7F)
    )


def _encode_j_type(offset, rd, opcode=0x6F):
    imm = offset & 0x1FFFFF
    bit20 = (imm >> 20) & 0x1
    bits10_1 = (imm >> 1) & 0x3FF
    bit11 = (imm >> 11) & 0x1
    bits19_12 = (imm >> 12) & 0xFF
    return (bit20 << 31) | (bits10_1 << 21) | (bit11 << 20) | (bits19_12 << 12) | ((rd & 0x1F) << 7) | opcode


def _addi(rd, rs1, imm):
    return _encode_i_type(imm, rs1, 0x0, rd, 0x13)


def _ori(rd, rs1, imm):
    return _encode_i_type(imm, rs1, 0x6, rd, 0x13)


def _xori(rd, rs1, imm):
    return _encode_i_type(imm, rs1, 0x4, rd, 0x13)


def _add(rd, rs1, rs2):
    return _encode_r_type(0x00, rs2, rs1, 0x0, rd, 0x33)


def _lui(rd, imm20):
    return _encode_u_type(imm20, rd, 0x37)


def _jal(rd, offset):
    return _encode_j_type(offset, rd)


def build_regfile_write_program(max_cycles=REGFILE_WRITE_MAX_CYCLES):
    """
    Build a small RV32I program that writes distinctive architectural registers
    and then parks at a self-loop.
    """
    program = {
        0x00: _addi(0, 0, 123),       # x0 must remain zero
        0x04: _addi(1, 0, 0x11),
        0x08: _addi(2, 0, 0x22),
        0x0C: _addi(3, 0, 0x33),
        0x10: _addi(4, 0, 0x44),
        0x14: _addi(5, 0, 0x55),
        0x18: _addi(6, 0, 0x66),
        0x1C: _addi(7, 0, 0x77),
        0x20: _lui(8, 0x12345),
        0x24: _ori(8, 8, 0x678),
        0x28: NOP_INSTRUCTION,
        REGFILE_WRITE_LOOP_PC: _jal(0, 0),
    }
    expected_registers = {
        "x0": 0,
        "x1": 0x11,
        "x2": 0x22,
        "x3": 0x33,
        "x4": 0x44,
        "x5": 0x55,
        "x6": 0x66,
        "x7": 0x77,
        "x8": 0x12345678,
    }
    return {
        "program_name": "regfile_write_probe_v1",
        "program": program,
        "loop_pc": REGFILE_WRITE_LOOP_PC,
        "expected_registers": expected_registers,
        "written_registers": ["x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8"],
        "x0_expected": 0,
        "max_cycles": max_cycles,
        "default_instruction": NOP_INSTRUCTION,
    }


async def regfile_write_instr_mem_driver(dut, program_metadata):
    program = program_metadata.get("program", program_metadata)
    default_instruction = program_metadata.get("default_instruction", NOP_INSTRUCTION)

    while True:
        await RisingEdge(dut.sys_clk)
        await Timer(0.001, unit="ns")

        try:
            dut.core_ack.value = 1
            addr = _safe_value_int(dut.core_addr)
            if addr is not None:
                dut.core_data_in.value = program.get(addr, default_instruction)
            else:
                dut.core_data_in.value = default_instruction
        except Exception:
            return


async def run_regfile_write_program(dut, program_metadata):
    """
    Best-effort execution of the Phase 3 program. Later phases consume the
    resulting metadata and trace data for classification.
    """
    result = {
        "ran": False,
        "reached_loop": False,
        "loop_cycle": None,
        "error": None,
    }

    required = ("sys_clk", "core_addr", "core_data_in", "core_ack")
    missing = [name for name in required if not hasattr(dut, name)]
    if missing:
        result["error"] = f"missing wrapper signal(s): {', '.join(missing)}"
        return result

    try:
        cocotb.start_soon(Clock(dut.sys_clk, 10, unit="ns").start())
        cocotb.start_soon(regfile_write_instr_mem_driver(dut, program_metadata))

        if hasattr(dut, "rst_n"):
            dut.rst_n.value = 0
        if hasattr(dut, "reset_core"):
            dut.reset_core.value = 1
        dut.core_ack.value = 0
        dut.core_data_in.value = NOP_INSTRUCTION
        await Timer(50, unit="ns")
        if hasattr(dut, "rst_n"):
            dut.rst_n.value = 1
        if hasattr(dut, "reset_core"):
            dut.reset_core.value = 0

        loop_pc = program_metadata["loop_pc"]
        max_cycles = program_metadata["max_cycles"]
        first_loop_cycle = None
        result["ran"] = True

        for cycle in range(max_cycles):
            await RisingEdge(dut.sys_clk)
            await Timer(0.001, unit="ns")

            pc = _safe_value_int(dut.core_addr)
            if pc is None:
                continue
            transaction_ok = True
            if hasattr(dut, "core_stb"):
                transaction_ok = bool(dut.core_stb.value)
            if pc == loop_pc and transaction_ok:
                if first_loop_cycle is None:
                    first_loop_cycle = cycle
                    result["loop_cycle"] = cycle

            if first_loop_cycle is not None and cycle - first_loop_cycle >= REGFILE_LOOP_QUIESCENCE_CYCLES:
                result["reached_loop"] = True
                return result

        result["error"] = f"loop PC 0x{loop_pc:08x} not reached within {max_cycles} cycles"
        return result
    except Exception as exc:
        result["error"] = str(exc)
        return result


# -----------------------------------------------------------------------------
# Phases 4 and 5: trace visible candidates and classify dynamic behavior
# -----------------------------------------------------------------------------

def _register_key(index):
    return f"x{int(index)}"


def _candidate_id(candidate):
    return candidate.get("path") or candidate.get("scope") or "<unknown>"


def _candidate_signature(candidate_or_result):
    return (candidate_or_result.get("candidate_path"), candidate_or_result.get("kind"))


def _candidate_sample_indices(candidate):
    depth = candidate.get("depth")
    if depth is None:
        return []

    if depth == 31:
        return list(range(1, 32))
    return list(range(depth))


def _sample_array_candidate(dut, candidate):
    handle = _resolve_path(dut, candidate.get("path"))
    if handle is None:
        return None

    values = {}
    for index in _candidate_sample_indices(candidate):
        child = _safe_get_child(handle, index)
        if child is None and candidate.get("depth") == 31:
            child = _safe_get_child(handle, index - 1)
        value = _safe_value_int(child) if child is not None else None
        if value is not None:
            values[_register_key(index)] = value
    return values


def _sample_vector_group_candidate(dut, candidate):
    values = {}
    for member in candidate.get("members", []):
        reg_index = member.get("reg_index")
        if reg_index is None:
            continue
        handle = _resolve_path(dut, member.get("path"))
        value = _safe_value_int(handle) if handle is not None else None
        if value is not None:
            values[_register_key(reg_index)] = value
    return values


def _sample_scalar_bit_cluster_candidate(dut, candidate):
    bits_by_reg = {}
    for member in candidate.get("members", []):
        reg_index = member.get("reg_index")
        bit_index = member.get("bit_index")
        if reg_index is None or bit_index is None:
            continue
        handle = _resolve_path(dut, member.get("path"))
        bit_value = _safe_value_int(handle) if handle is not None else None
        if bit_value is None:
            continue
        bits_by_reg.setdefault(reg_index, {})[bit_index] = bit_value & 1

    values = {}
    word_width = candidate.get("word_width") or 0
    for reg_index, bits in bits_by_reg.items():
        if word_width and len(bits) < word_width:
            continue
        word = 0
        for bit_index, bit_value in bits.items():
            word |= (bit_value & 1) << int(bit_index)
        values[_register_key(reg_index)] = word
    return values


def _decode_packed_registers(raw_value, depth, word_width, msb_reg0=False):
    values = {}
    mask = (1 << word_width) - 1
    for reg_index in range(depth):
        slice_index = depth - 1 - reg_index if msb_reg0 else reg_index
        values[_register_key(reg_index)] = (raw_value >> (slice_index * word_width)) & mask
    return values


def _sample_packed_flat_vector_candidate(dut, candidate):
    handle = _resolve_path(dut, candidate.get("path"))
    raw_value = _safe_value_int(handle) if handle is not None else None
    if raw_value is None:
        return None

    depth = candidate.get("depth")
    word_width = candidate.get("word_width")
    if depth is None or word_width is None:
        return {"raw": raw_value}

    return {
        "raw": raw_value,
        "packed_lsb_reg0": _decode_packed_registers(raw_value, depth, word_width, msb_reg0=False),
        "packed_msb_reg0": _decode_packed_registers(raw_value, depth, word_width, msb_reg0=True),
    }


def sample_candidate_value(dut, candidate):
    kind = candidate.get("kind")
    if kind == "array_of_words":
        return _sample_array_candidate(dut, candidate)
    if kind == "vector_group":
        return _sample_vector_group_candidate(dut, candidate)
    if kind == "scalar_bit_cluster":
        return _sample_scalar_bit_cluster_candidate(dut, candidate)
    if kind == "packed_flat_vector":
        return _sample_packed_flat_vector_candidate(dut, candidate)
    return None


def _candidate_mapping_views(candidate_trace):
    kind = candidate_trace.get("kind")
    samples = candidate_trace.get("samples", [])
    if kind != "packed_flat_vector":
        return [("direct", samples)]

    views = []
    for mapping_order in ("packed_lsb_reg0", "packed_msb_reg0"):
        mapped_samples = []
        for sample in samples:
            values = sample.get("values") or {}
            mapped_values = values.get(mapping_order)
            if mapped_values is None:
                continue
            mapped_sample = dict(sample)
            mapped_sample["values"] = mapped_values
            mapped_samples.append(mapped_sample)
        views.append((mapping_order, mapped_samples))
    return views


def _values_match(values, expected_registers):
    if not values:
        return 0, {}

    matches = {}
    for reg, expected in expected_registers.items():
        actual = values.get(reg)
        if actual is not None and int(actual) == int(expected):
            matches[reg] = actual
    return len(matches), matches


def _score_mapping_samples(samples, expected_registers, written_registers):
    reasons = []
    failed = []
    score = 0
    mapped_registers = {}

    if not samples:
        return {
            "score": 0,
            "mapped_registers": {},
            "reasons": [],
            "failed_checks": ["no samples"],
        }

    final_sample = samples[-1]
    final_values = final_sample.get("values") or {}
    match_count, mapped_registers = _values_match(final_values, expected_registers)
    expected_count = max(1, len(expected_registers))
    value_points = round(45 * match_count / expected_count)
    score += value_points

    if match_count:
        reasons.append(f"{match_count}/{len(expected_registers)} expected register values matched")
    else:
        failed.append("no expected register values matched")

    x0_ok = final_values.get("x0") == expected_registers.get("x0", 0)
    if x0_ok:
        score += 15
        reasons.append("x0 remained zero")
    else:
        failed.append("x0 behavior mismatch")

    persistence_ok = False
    quiescence_samples = samples[-3:]
    if quiescence_samples and mapped_registers:
        persistence_ok = all(
            all((sample.get("values") or {}).get(reg) == value for reg, value in mapped_registers.items())
            for sample in quiescence_samples
        )
    if persistence_ok:
        score += 15
        reasons.append("matched values persisted in loop window")
    else:
        failed.append("matched values did not persist through loop window")

    written_values = [final_values.get(reg) for reg in written_registers if final_values.get(reg) is not None]
    selectivity_ok = len(set(written_values)) > 1 if written_values else False
    if selectivity_ok:
        score += 10
        reasons.append("written registers carry distinct values")
    else:
        failed.append("written registers were not selective")

    first_values = samples[0].get("values") or {}
    update_timing_ok = any(first_values.get(reg) != final_values.get(reg) for reg in written_registers)
    if update_timing_ok:
        score += 15
        reasons.append("values changed after program execution")
    else:
        failed.append("no dynamic update observed")

    if not x0_ok:
        score = min(score, 49)

    return {
        "score": min(score, 100),
        "mapped_registers": mapped_registers,
        "reasons": reasons,
        "failed_checks": failed,
    }


def _status_from_score(score, confirmed=False, x0_failed=False):
    if confirmed and score >= 80:
        return "confirmed_candidate"
    if x0_failed or score < 50:
        return "rejected_candidate"
    if score >= 70:
        return "likely_candidate"
    return "ambiguous_candidate"


def classify_regfile_candidates(trace_result, program_metadata):
    expected_registers = program_metadata.get("expected_registers", {})
    written_registers = program_metadata.get("written_registers", [])
    results = []

    for candidate_trace in trace_result.get("candidate_traces", []):
        if candidate_trace.get("untraced"):
            results.append({
                "candidate_path": candidate_trace.get("candidate_path"),
                "kind": candidate_trace.get("kind"),
                "score": 0,
                "confidence": "none",
                "status": "rejected_candidate",
                "mapped_registers": {},
                "mapping_order": None,
                "reasons": [],
                "failed_checks": [candidate_trace.get("reason", "candidate was not traced")],
            })
            continue

        best = None
        for mapping_order, samples in _candidate_mapping_views(candidate_trace):
            scored = _score_mapping_samples(samples, expected_registers, written_registers)
            scored["mapping_order"] = mapping_order
            if best is None or scored["score"] > best["score"]:
                best = scored

        score = best["score"] if best else 0
        x0_failed = any("x0 behavior" in check for check in (best or {}).get("failed_checks", []))
        if score >= 85:
            confidence = "high"
        elif score >= 70:
            confidence = "medium"
        elif score >= 50:
            confidence = "low"
        else:
            confidence = "none"

        results.append({
            "candidate_path": candidate_trace.get("candidate_path"),
            "kind": candidate_trace.get("kind"),
            "score": score,
            "confidence": confidence,
            "status": _status_from_score(score, x0_failed=x0_failed),
            "mapped_registers": (best or {}).get("mapped_registers", {}),
            "mapping_order": (best or {}).get("mapping_order"),
            "reasons": (best or {}).get("reasons", []),
            "failed_checks": (best or {}).get("failed_checks", ["no classification result"]),
        })

    return sorted(results, key=lambda result: result["score"], reverse=True)


async def _start_clock_once(dut):
    if getattr(dut, "_regfile_finder_clock_started", False):
        return
    cocotb.start_soon(Clock(dut.sys_clk, 10, unit="ns").start())
    try:
        setattr(dut, "_regfile_finder_clock_started", True)
    except Exception:
        pass


async def _reset_for_regfile_program(dut):
    if hasattr(dut, "rst_n"):
        dut.rst_n.value = 0
    if hasattr(dut, "reset_core"):
        dut.reset_core.value = 1
    dut.core_ack.value = 0
    dut.core_data_in.value = NOP_INSTRUCTION
    await Timer(50, unit="ns")
    if hasattr(dut, "rst_n"):
        dut.rst_n.value = 1
    if hasattr(dut, "reset_core"):
        dut.reset_core.value = 0


async def run_regfile_program_and_trace(dut, program_metadata, candidates):
    trace_result = {
        "program_name": program_metadata.get("program_name"),
        "loop_pc": program_metadata.get("loop_pc"),
        "ran": False,
        "reached_loop": False,
        "loop_cycle": None,
        "error": None,
        "candidate_traces": [],
    }

    required = ("sys_clk", "core_addr", "core_data_in", "core_ack")
    missing = [name for name in required if not hasattr(dut, name)]
    if missing:
        trace_result["error"] = f"missing wrapper signal(s): {', '.join(missing)}"
        return trace_result

    trace_by_key = {}
    visible_candidates = []
    for candidate in candidates:
        entry = {
            "candidate_path": _candidate_id(candidate),
            "kind": candidate.get("kind"),
            "samples": [],
        }
        if candidate.get("visibility_status") != "visible":
            entry["untraced"] = True
            entry["reason"] = candidate.get("visibility_status", "not visible")
        else:
            visible_candidates.append(candidate)
        trace_result["candidate_traces"].append(entry)
        trace_by_key[_candidate_id(candidate)] = entry

    driver_task = None
    try:
        await _start_clock_once(dut)
        driver_task = cocotb.start_soon(regfile_write_instr_mem_driver(dut, program_metadata))
        await _reset_for_regfile_program(dut)

        loop_pc = program_metadata["loop_pc"]
        max_cycles = program_metadata["max_cycles"]
        first_loop_cycle = None
        trace_result["ran"] = True

        for cycle in range(max_cycles):
            await RisingEdge(dut.sys_clk)
            await Timer(0.001, unit="ns")

            pc = _safe_value_int(dut.core_addr)
            transaction_ok = True
            if hasattr(dut, "core_stb"):
                transaction_ok = bool(_safe_value_int(dut.core_stb))

            in_loop = pc == loop_pc and transaction_ok
            if in_loop:
                if first_loop_cycle is None:
                    first_loop_cycle = cycle
                    trace_result["loop_cycle"] = cycle

            for candidate in visible_candidates:
                values = sample_candidate_value(dut, candidate)
                trace_by_key[_candidate_id(candidate)]["samples"].append({
                    "cycle": cycle,
                    "pc": pc,
                    "in_loop": in_loop,
                    "values": values or {},
                })

            if first_loop_cycle is not None and cycle - first_loop_cycle >= REGFILE_LOOP_QUIESCENCE_CYCLES:
                trace_result["reached_loop"] = True
                break

        if not trace_result["reached_loop"]:
            trace_result["error"] = f"loop PC 0x{loop_pc:08x} not reached within {max_cycles} cycles"
        return trace_result
    except Exception as exc:
        trace_result["error"] = str(exc)
        return trace_result
    finally:
        if driver_task is not None:
            try:
                if hasattr(driver_task, "cancel"):
                    driver_task.cancel()
                else:
                    driver_task.kill()
            except Exception:
                pass


# -----------------------------------------------------------------------------
# Phase 6: confirmation with a second program
# -----------------------------------------------------------------------------

def build_regfile_confirmation_program(max_cycles=REGFILE_WRITE_MAX_CYCLES):
    metadata = build_regfile_write_program(max_cycles=max_cycles)
    metadata["program_name"] = "regfile_write_confirm_v1"
    metadata["program"] = {
        0x00: _addi(0, 0, 321),       # x0 must remain zero
        0x04: _addi(1, 0, 0x12),
        0x08: _addi(2, 0, 0x24),
        0x0C: _addi(3, 0, 0x36),
        0x10: _addi(4, 0, 0x48),
        0x14: _addi(5, 0, 0x5A),
        0x18: _addi(6, 0, 0x6C),
        0x1C: _addi(7, 0, 0x7E),
        0x20: _lui(8, 0x23456),
        0x24: _ori(8, 8, 0x789),
        0x28: NOP_INSTRUCTION,
        REGFILE_WRITE_LOOP_PC: _jal(0, 0),
    }
    metadata["expected_registers"] = {
        "x0": 0,
        "x1": 0x12,
        "x2": 0x24,
        "x3": 0x36,
        "x4": 0x48,
        "x5": 0x5A,
        "x6": 0x6C,
        "x7": 0x7E,
        "x8": 0x23456789,
    }
    return metadata


def _select_best_regfile(classification_results, confirmation_results=None):
    confirmation_results = confirmation_results or []
    confirmed = [result for result in confirmation_results if result.get("status") == "confirmed_candidate"]
    if confirmed:
        return max(confirmed, key=lambda result: result.get("score", 0))

    likely = [result for result in classification_results if result.get("status") == "likely_candidate"]
    if likely:
        return max(likely, key=lambda result: result.get("score", 0))

    if classification_results:
        return max(classification_results, key=lambda result: result.get("score", 0))
    return None


def _confirm_classification_results(phase5_results, confirmation_classification):
    phase5_by_signature = {
        _candidate_signature(result): result
        for result in phase5_results
        if result.get("score", 0) >= 70
    }
    confirmation_results = []
    for result in confirmation_classification:
        signature = _candidate_signature(result)
        previous = phase5_by_signature.get(signature)
        same_mapping = (
            previous is not None
            and previous.get("mapping_order") == result.get("mapping_order")
            and set(previous.get("mapped_registers", {})) == set(result.get("mapped_registers", {}))
        )
        confirmed = same_mapping and result.get("score", 0) >= 80
        result = dict(result)
        result["status"] = _status_from_score(
            result.get("score", 0),
            confirmed=confirmed,
            x0_failed=any("x0 behavior" in check for check in result.get("failed_checks", [])),
        )
        if confirmed:
            result["reasons"] = list(result.get("reasons", [])) + ["same candidate and mapping confirmed with second program"]
        else:
            result["failed_checks"] = list(result.get("failed_checks", [])) + ["confirmation mapping did not match Phase 5"]
        confirmation_results.append(result)
    return confirmation_results


async def confirm_regfile_candidate(dut, candidates, phase5_results):
    confirmation_program = build_regfile_confirmation_program()
    trace_result = await run_regfile_program_and_trace(dut, confirmation_program, candidates)
    confirmation_classification = classify_regfile_candidates(trace_result, confirmation_program)
    confirmation_results = _confirm_classification_results(phase5_results, confirmation_classification)

    return {
        "program": confirmation_program,
        "trace_result": trace_result,
        "classification_results": confirmation_results,
    }


# -----------------------------------------------------------------------------
# Dynamic register-file write-interface discovery
# -----------------------------------------------------------------------------

WRITE_ENABLE_NAME_HINTS = (
    "rf_wen", "regfile_wen", "gpr_wen", "reg_wen", "regwr_en",
    "write_enable", "write_en", "wen", "wren", "wr_en", "we",
)
WRITE_ADDR_NAME_HINTS = (
    "regwr_sel", "waddr", "write_addr", "wr_addr", "rd_addr", "dest",
    "rd_wb", "rd_w", "rd", "wa", "wsel", "wrsel",
)
WRITE_DATA_NAME_HINTS = (
    "regwr_data", "wdata", "write_data", "wr_data", "wb_data",
    "writeback", "rd_data", "wd", "data_i",
)
INTERFACE_EXCLUDE_HINTS = (
    "clk", "clock", "rst", "reset", "debug", "dbg", "trace", "jtag",
    "csr", "cache", "mem", "memory", "ram", "rom",
)


def _parent_path(path):
    parts = str(path or "").split(".")
    if len(parts) <= 1:
        return ""
    return ".".join(parts[:-1])


def _scope_path_for_signal(path):
    return _parent_path(path)


def _interface_name_score(path, role):
    path_l = str(path or "").lower()
    basename = _leaf_basename(path_l)
    score = 0
    reasons = []
    hints_by_role = {
        "write_enable": WRITE_ENABLE_NAME_HINTS,
        "write_addr": WRITE_ADDR_NAME_HINTS,
        "write_data": WRITE_DATA_NAME_HINTS,
    }

    matched = [hint for hint in hints_by_role.get(role, ()) if hint in basename or hint in path_l]
    if matched:
        score += min(20, 6 * len(matched))
        reasons.append(f"{role} name hint(s): {', '.join(matched[:3])}")

    excluded = [hint for hint in INTERFACE_EXCLUDE_HINTS if hint in basename]
    if excluded:
        score -= min(20, 8 * len(excluded))
        reasons.append(f"excluded name hint(s): {', '.join(excluded[:3])}")

    return score, reasons


def _infer_candidate_word_width(dut, candidate):
    if candidate.get("word_width"):
        return candidate.get("word_width")

    values = sample_candidate_value(dut, candidate) or {}
    for value in values.values():
        try:
            width = int(value).bit_length()
            if width <= 32:
                return 32
            if width <= 64:
                return 64
        except Exception:
            pass
    return 32


def _collect_leaf_signals_in_scope(scope_handle, include_child_scopes=False):
    leaves = []
    child_scopes = []

    for name, child in _iter_sim_children(scope_handle):
        if _is_hierarchy_handle(child):
            if include_child_scopes:
                child_scopes.append(child)
            continue
        child_path = _safe_path(child, fallback=name)
        leaves.append({
            "path": child_path,
            "name": _leaf_basename(child_path),
            "scope": _scope_path_for_signal(child_path),
            "width": _safe_len(child),
            "handle_type": _safe_type(child),
        })

    for child_scope in child_scopes:
        for name, child in _iter_sim_children(child_scope):
            if _is_hierarchy_handle(child):
                continue
            child_path = _safe_path(child, fallback=name)
            leaves.append({
                "path": child_path,
                "name": _leaf_basename(child_path),
                "scope": _scope_path_for_signal(child_path),
                "width": _safe_len(child),
                "handle_type": _safe_type(child),
            })

    return leaves


def collect_nearby_regfile_interface_candidates(dut, selected_regfile):
    regfile_path = selected_regfile.get("path") or selected_regfile.get("candidate_path")
    parent_scope = _parent_path(regfile_path)
    parent_handle = _resolve_path(dut, parent_scope)
    word_width = _infer_candidate_word_width(dut, selected_regfile)
    result = {
        "regfile_path": regfile_path,
        "parent_scope": parent_scope,
        "word_width": word_width,
        "write_enable_candidates": [],
        "write_addr_candidates": [],
        "write_data_candidates": [],
        "unclassified_candidates": [],
    }

    if parent_handle is None:
        result["error"] = f"parent scope not resolvable: {parent_scope}"
        return result

    seen = set()
    for leaf in _collect_leaf_signals_in_scope(parent_handle, include_child_scopes=True):
        path = leaf["path"]
        if path in seen or path == regfile_path:
            continue
        seen.add(path)

        width = leaf.get("width")
        roles = []
        if width == 1:
            roles.append("write_enable")
        if width in (4, 5):
            roles.append("write_addr")
        if width == word_width:
            roles.append("write_data")

        if not roles:
            result["unclassified_candidates"].append(leaf)
            continue

        for role in roles:
            scored = dict(leaf)
            scored["role"] = role
            name_score, reasons = _interface_name_score(path, role)
            scored["name_score"] = name_score
            scored["name_reasons"] = reasons
            result[f"{role}_candidates"].append(scored)

    return result


def build_regfile_interface_probe_program(max_cycles=REGFILE_WRITE_MAX_CYCLES):
    write_sequence = [
        {"pc": 0x08, "reg": "x5", "reg_index": 5, "value": 0x0C, "opclass": "r_alu"},
        {"pc": 0x0C, "reg": "x6", "reg_index": 6, "value": 0x07, "opclass": "i_alu_overlap"},
        {"pc": 0x10, "reg": "x5", "reg_index": 5, "value": 0x00012000, "opclass": "lui"},
        {"pc": 0x14, "reg": "x6", "reg_index": 6, "value": 0x04, "opclass": "i_alu_xor"},
    ]
    return {
        "program_name": "regfile_interface_write_probe_v1",
        "program": {
            0x00: _addi(9, 0, 0x05),
            0x04: _addi(10, 0, 0x07),
            0x08: _add(5, 9, 10),
            0x0C: _ori(6, 9, 0x03),
            0x10: _lui(5, 0x12),
            0x14: _xori(6, 10, 0x03),
            0x18: NOP_INSTRUCTION,
            REGFILE_INTERFACE_LOOP_PC: _jal(0, 0),
        },
        "loop_pc": REGFILE_INTERFACE_LOOP_PC,
        "write_sequence": write_sequence,
        "setup_registers": {"x9": 0x05, "x10": 0x07},
        "expected_registers": {"x5": 0x00012000, "x6": 0x04},
        "overwrite_register": "x5",
        "max_cycles": max_cycles,
        "default_instruction": NOP_INSTRUCTION,
    }


def _watched_regfile_values(dut, selected_regfile):
    values = sample_candidate_value(dut, selected_regfile) or {}
    return {"x5": values.get("x5"), "x6": values.get("x6")}


def _watched_regfile_values_for_program(dut, selected_regfile, program_metadata):
    values = sample_candidate_value(dut, selected_regfile) or {}
    watched = {}
    for entry in program_metadata.get("write_sequence", []):
        reg = entry.get("reg")
        if reg:
            watched[reg] = values.get(reg)
    return watched


def _interface_signal_paths(interface_candidates):
    paths = []
    for key in ("write_enable_candidates", "write_addr_candidates", "write_data_candidates"):
        for candidate in interface_candidates.get(key, []):
            path = candidate.get("path")
            if path and path not in paths:
                paths.append(path)
    return paths


def _sample_interface_signals(dut, signal_paths):
    values = {}
    for path in signal_paths:
        handle = _resolve_path(dut, path)
        values[path] = _safe_value_int(handle) if handle is not None else None
    return values


def detect_regfile_storage_update_events(trace_samples, program_metadata):
    write_sequence = list(program_metadata.get("write_sequence", []))
    events = []
    expected_idx = 0
    previous_values = None

    for sample in trace_samples:
        current_values = sample.get("regfile_values") or {}
        if previous_values is None:
            previous_values = current_values
            continue
        if expected_idx >= len(write_sequence):
            previous_values = current_values
            continue

        expected = write_sequence[expected_idx]
        reg = expected["reg"]
        old_value = previous_values.get(reg)
        new_value = current_values.get(reg)
        if old_value != new_value and new_value == expected["value"]:
            cycle = sample.get("cycle")
            events.append({
                "cycle": cycle,
                "reg_index": expected["reg_index"],
                "old_value": old_value,
                "new_value": new_value,
                "expected_write_index": expected_idx,
                "pc_window": [
                    s.get("pc")
                    for s in trace_samples
                    if cycle is not None and cycle - 2 <= s.get("cycle", -999) <= cycle + 1
                ],
            })
            expected_idx += 1
        previous_values = current_values

    return events


def _samples_by_cycle(trace_samples):
    return {sample.get("cycle"): sample for sample in trace_samples}


def _signal_values(trace_samples, path):
    return [(sample.get("signals") or {}).get(path) for sample in trace_samples]


def _score_write_addr_candidate(candidate, trace_samples, update_events):
    path = candidate.get("path")
    samples = _samples_by_cycle(trace_samples)
    best = {"score": 0, "timing_offset": None, "reasons": [], "failed_checks": ["no aligned write-address matches"]}
    for offset in REGFILE_INTERFACE_TIMING_OFFSETS:
        matched = 0
        observed = []
        for event in update_events:
            sample = samples.get(event["cycle"] + offset)
            value = (sample.get("signals") or {}).get(path) if sample else None
            observed.append(value)
            if value == event["reg_index"]:
                matched += 1
        score = round(70 * matched / max(1, len(update_events))) + max(0, candidate.get("name_score", 0))
        if len(set(v for v in observed if v is not None)) > 1:
            score += 10
        if matched < len(update_events):
            score = min(score, 69)
        result = {
            "score": min(score, 100),
            "timing_offset": offset,
            "reasons": [f"{matched}/{len(update_events)} write-address values matched"] + candidate.get("name_reasons", []),
            "failed_checks": [] if matched == len(update_events) else ["write address did not match every update event"],
        }
        if result["score"] > best["score"]:
            best = result
    return best


def _score_write_data_candidate(candidate, trace_samples, update_events):
    path = candidate.get("path")
    samples = _samples_by_cycle(trace_samples)
    best = {"score": 0, "timing_offset": None, "reasons": [], "failed_checks": ["no aligned write-data matches"]}
    for offset in REGFILE_INTERFACE_TIMING_OFFSETS:
        matched = 0
        observed = []
        for event in update_events:
            sample = samples.get(event["cycle"] + offset)
            value = (sample.get("signals") or {}).get(path) if sample else None
            observed.append(value)
            if value == event["new_value"]:
                matched += 1
        distinct_observed = len(set(v for v in observed if v is not None))
        score = round(70 * matched / max(1, len(update_events))) + max(0, candidate.get("name_score", 0))
        if distinct_observed >= 2:
            score += 10
        else:
            score = min(score, 59)
        if matched < len(update_events):
            score = min(score, 69)
        failed = [] if matched == len(update_events) and distinct_observed >= 2 else ["write data did not distinguish every update event"]
        result = {
            "score": min(score, 100),
            "timing_offset": offset,
            "reasons": [f"{matched}/{len(update_events)} write-data values matched"] + candidate.get("name_reasons", []),
            "failed_checks": failed,
        }
        if result["score"] > best["score"]:
            best = result
    return best


def _score_write_enable_candidate(candidate, trace_samples, update_events):
    path = candidate.get("path")
    samples = _samples_by_cycle(trace_samples)
    all_values = [v for v in _signal_values(trace_samples, path) if v is not None]
    active_total = sum(1 for value in all_values if value != 0)
    active_ratio = active_total / max(1, len(all_values))
    stuck_high = active_ratio > 0.85
    stuck_low = active_total == 0
    best = {"score": 0, "timing_offset": None, "reasons": [], "failed_checks": ["no aligned write-enable activity"]}

    for offset in REGFILE_INTERFACE_TIMING_OFFSETS:
        active_matches = 0
        for event in update_events:
            sample = samples.get(event["cycle"] + offset)
            value = (sample.get("signals") or {}).get(path) if sample else None
            if value not in (None, 0):
                active_matches += 1
        score = round(65 * active_matches / max(1, len(update_events))) + max(0, candidate.get("name_score", 0))
        if not stuck_high and not stuck_low:
            score += 15
        if stuck_high:
            score = min(score, 59)
        if stuck_low or active_matches < len(update_events):
            score = min(score, 69)
        failed = []
        if active_matches < len(update_events):
            failed.append("write enable was not active for every update event")
        if stuck_high:
            failed.append("write enable was active on most cycles")
        if stuck_low:
            failed.append("write enable was never active")
        result = {
            "score": min(score, 100),
            "timing_offset": offset,
            "reasons": [f"{active_matches}/{len(update_events)} write-enable events active"] + candidate.get("name_reasons", []),
            "failed_checks": failed,
        }
        if result["score"] > best["score"]:
            best = result
    return best


def _score_role_candidates(candidates, trace_samples, update_events, role):
    scorer = {
        "write_enable": _score_write_enable_candidate,
        "write_addr": _score_write_addr_candidate,
        "write_data": _score_write_data_candidate,
    }[role]
    results = []
    for candidate in candidates:
        result = dict(candidate)
        result.update(scorer(candidate, trace_samples, update_events))
        results.append(result)
    return sorted(results, key=lambda item: item.get("score", 0), reverse=True)


def _needs_derived_role(role_results, threshold=70):
    return not role_results or role_results[0].get("score", 0) < threshold


def _derived_role_results(role, trace_result):
    path = DERIVED_WRITE_ENABLE_PATH if role == "write_enable" else DERIVED_WRITE_DATA_PATH
    name = "storage_update_event" if role == "write_enable" else "storage_update_value"
    score = 80 if role == "write_enable" else 100
    return [
        {
            "path": path,
            "name": name,
            "scope": trace_result.get("regfile_path"),
            "width": 1 if role == "write_enable" else None,
            "handle_type": "derived_from_regfile_storage",
            "role": role,
            "name_score": 0,
            "name_reasons": [],
            "score": score,
            "timing_offset": offset,
            "reasons": [
                "derived from observed register-file storage update"
                if role == "write_enable"
                else "uses new register-file storage value as effective write data"
            ],
            "failed_checks": [],
            "derived": True,
        }
        for offset in REGFILE_INTERFACE_TIMING_OFFSETS
    ]


def _best_candidate_at_offset(results, offset):
    compatible = [result for result in results if result.get("timing_offset") == offset]
    if not compatible:
        return None
    return max(compatible, key=lambda item: item.get("score", 0))


def _candidates_at_offset(results, offset):
    return [result for result in results if result.get("timing_offset") == offset]


def _interface_status(score, failed_checks):
    if failed_checks or score < 50:
        return "rejected_interface"
    if score >= 85:
        return "confirmed_interface"
    if score >= 70:
        return "likely_interface"
    return "ambiguous_interface"


def classify_regfile_interface(trace_result, interface_candidates):
    trace_samples = trace_result.get("samples", [])
    update_events = trace_result.get("update_events", [])
    if not trace_samples or not update_events:
        selected = {
            "status": "rejected_interface",
            "score": 0,
            "confidence": "none",
            "write_enable": None,
            "write_addr": None,
            "write_data": None,
            "timing_offset": None,
            "reasons": [],
            "failed_checks": ["no trace samples or storage update events"],
        }
        return {"role_scores": {}, "tuples": [], "selected": selected}

    role_scores = {
        "write_enable": _score_role_candidates(interface_candidates.get("write_enable_candidates", []), trace_samples, update_events, "write_enable"),
        "write_addr": _score_role_candidates(interface_candidates.get("write_addr_candidates", []), trace_samples, update_events, "write_addr"),
        "write_data": _score_role_candidates(interface_candidates.get("write_data_candidates", []), trace_samples, update_events, "write_data"),
    }
    derived_roles = []
    for role in ("write_enable", "write_data"):
        if _needs_derived_role(role_scores[role]):
            role_scores[role] = sorted(
                role_scores[role] + _derived_role_results(role, trace_result),
                key=lambda item: item.get("score", 0),
                reverse=True,
            )
            derived_roles.append(role)
    tuples = []

    for offset in REGFILE_INTERFACE_TIMING_OFFSETS:
        we_candidates = _candidates_at_offset(role_scores["write_enable"], offset)
        wa_candidates = _candidates_at_offset(role_scores["write_addr"], offset)
        wd_candidates = _candidates_at_offset(role_scores["write_data"], offset)
        for we in we_candidates:
            for wa in wa_candidates:
                for wd in wd_candidates:
                    failed = []
                    for label, result in (("write_enable", we), ("write_addr", wa), ("write_data", wd)):
                        if result.get("score", 0) < 50:
                            failed.append(f"{label} score below threshold")

                    score = round(0.30 * we["score"] + 0.35 * wa["score"] + 0.35 * wd["score"])
                    reasons = [
                        f"common timing offset {offset}",
                        f"write_enable score {we['score']}",
                        f"write_addr score {wa['score']}",
                        f"write_data score {wd['score']}",
                    ]
                    if len({we.get("scope"), wa.get("scope"), wd.get("scope")}) == 1:
                        score += 5
                        reasons.append("all selected signals are in the same scope")
                    if we.get("derived"):
                        reasons.append("write_enable is derived from storage updates")
                    if wd.get("derived"):
                        reasons.append("write_data is derived from storage updates")
                    if failed:
                        score = min(score, 59)

                    score = min(score, 100)
                    if we.get("derived") or wd.get("derived"):
                        score = min(score, 84)
                    confidence = "high" if score >= 85 else "medium" if score >= 70 else "low" if score >= 50 else "none"
                    tuples.append({
                        "status": _interface_status(score, failed),
                        "score": score,
                        "confidence": confidence,
                        "write_enable": we.get("path"),
                        "write_addr": wa.get("path"),
                        "write_data": wd.get("path"),
                        "timing_offset": offset,
                        "reasons": reasons,
                        "failed_checks": failed,
                    })

    selected = max(tuples, key=lambda item: item.get("score", 0), default={
        "status": "rejected_interface",
        "score": 0,
        "confidence": "none",
        "write_enable": None,
        "write_addr": None,
        "write_data": None,
        "timing_offset": None,
        "reasons": [],
            "failed_checks": ["no complete write interface tuple found"],
    })
    return {
        "role_scores": role_scores,
        "tuples": sorted(tuples, key=lambda item: item["score"], reverse=True),
        "selected": selected,
        "derived_roles": derived_roles,
    }


async def run_regfile_interface_probe_and_trace(dut, selected_regfile, program_metadata):
    interface_candidates = collect_nearby_regfile_interface_candidates(dut, selected_regfile)
    trace_result = {
        "program_name": program_metadata.get("program_name"),
        "regfile_path": selected_regfile.get("path") or selected_regfile.get("candidate_path"),
        "loop_pc": program_metadata.get("loop_pc"),
        "ran": False,
        "reached_loop": False,
        "loop_cycle": None,
        "error": interface_candidates.get("error"),
        "samples": [],
        "update_events": [],
    }
    if trace_result["error"]:
        return {"interface_candidates": interface_candidates, "trace_result": trace_result}

    required = ("sys_clk", "core_addr", "core_data_in", "core_ack")
    missing = [name for name in required if not hasattr(dut, name)]
    if missing:
        trace_result["error"] = f"missing wrapper signal(s): {', '.join(missing)}"
        return {"interface_candidates": interface_candidates, "trace_result": trace_result}

    signal_paths = _interface_signal_paths(interface_candidates)
    driver_task = None
    try:
        await _start_clock_once(dut)
        driver_task = cocotb.start_soon(regfile_write_instr_mem_driver(dut, program_metadata))
        await _reset_for_regfile_program(dut)

        loop_pc = program_metadata["loop_pc"]
        first_loop_cycle = None
        trace_result["ran"] = True
        for cycle in range(program_metadata["max_cycles"]):
            await RisingEdge(dut.sys_clk)
            await Timer(0.001, unit="ns")

            pc = _safe_value_int(dut.core_addr)
            transaction_ok = True
            if hasattr(dut, "core_stb"):
                transaction_ok = bool(_safe_value_int(dut.core_stb))
            in_loop = pc == loop_pc and transaction_ok
            if in_loop and first_loop_cycle is None:
                first_loop_cycle = cycle
                trace_result["loop_cycle"] = cycle

            trace_result["samples"].append({
                "cycle": cycle,
                "pc": pc,
                "in_loop": in_loop,
                "regfile_values": _watched_regfile_values_for_program(dut, selected_regfile, program_metadata),
                "signals": _sample_interface_signals(dut, signal_paths),
            })

            if first_loop_cycle is not None and cycle - first_loop_cycle >= REGFILE_LOOP_QUIESCENCE_CYCLES:
                trace_result["reached_loop"] = True
                break

        if not trace_result["reached_loop"]:
            trace_result["error"] = f"loop PC 0x{loop_pc:08x} not reached within {program_metadata['max_cycles']} cycles"
        trace_result["update_events"] = detect_regfile_storage_update_events(trace_result["samples"], program_metadata)
        return {"interface_candidates": interface_candidates, "trace_result": trace_result}
    except Exception as exc:
        trace_result["error"] = str(exc)
        return {"interface_candidates": interface_candidates, "trace_result": trace_result}
    finally:
        if driver_task is not None:
            try:
                if hasattr(driver_task, "cancel"):
                    driver_task.cancel()
                else:
                    driver_task.kill()
            except Exception:
                pass


def _candidate_for_selected_regfile(selected_regfile, candidates):
    if not selected_regfile:
        return None
    selected_path = selected_regfile.get("candidate_path") or selected_regfile.get("path")
    selected_kind = selected_regfile.get("kind")
    for candidate in candidates:
        if _candidate_id(candidate) == selected_path and candidate.get("kind") == selected_kind:
            return dict(candidate)
    return {
        "path": selected_path,
        "kind": selected_kind or "array_of_words",
        "depth": 32,
        "word_width": 32,
        "visibility_status": "visible",
    }


def _interface_trace_summary(trace_result):
    return {
        "program_name": trace_result.get("program_name"),
        "ran": trace_result.get("ran"),
        "reached_loop": trace_result.get("reached_loop"),
        "loop_cycle": trace_result.get("loop_cycle"),
        "sample_count": len(trace_result.get("samples", [])),
        "update_event_count": len(trace_result.get("update_events", [])),
        "error": trace_result.get("error"),
    }


def _env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on", "debug")


def _compact_selected_regfile(selected_regfile):
    if not selected_regfile:
        return None
    keys = (
        "candidate_path",
        "kind",
        "status",
        "score",
        "confidence",
        "mapping_order",
        "mapped_registers",
    )
    return {key: selected_regfile.get(key) for key in keys if key in selected_regfile}


def _compact_selected_interface(selected_interface, interface_classification=None):
    if not selected_interface:
        return None
    keys = (
        "status",
        "score",
        "confidence",
        "write_enable",
        "write_addr",
        "write_data",
        "timing_offset",
    )
    compact = {key: selected_interface.get(key) for key in keys if key in selected_interface}
    derived_roles = (interface_classification or {}).get("derived_roles")
    if derived_roles:
        compact["derived_roles"] = derived_roles
    return compact


def _compat_regfile_interface(selected_interface):
    selected_interface = selected_interface or {}
    return {
        "write_enable": selected_interface.get("write_enable"),
        "write_addr": selected_interface.get("write_addr"),
        "write_data": selected_interface.get("write_data"),
    }


def _compact_regfile_output(verbose_output):
    selected_regfile = verbose_output.get("selected_regfile")
    selected_interface = verbose_output.get("selected_regfile_interface")
    selected_path = None
    if selected_regfile:
        selected_path = selected_regfile.get("candidate_path") or selected_regfile.get("path")
    regfile_candidates = [selected_path] if selected_path else verbose_output.get("regfile_candidates", [])

    return {
        "regfile_candidates": regfile_candidates,
        "selected_regfile": _compact_selected_regfile(selected_regfile),
        "regfile_interface": _compat_regfile_interface(selected_interface),
        "selected_regfile_interface": _compact_selected_interface(
            selected_interface,
            verbose_output.get("interface_classification"),
        ),
    }


def _write_regfile_json(output_file, verbose_output, debug_enabled=False):
    output_data = verbose_output if debug_enabled else _compact_regfile_output(verbose_output)
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(output_data, json_file, indent=4)


def get_all_leaf_handles(module, leaves=None):
    if leaves is None:
        leaves = []

    new_leaves, submodules = get_current_module_leaf_handles(module)
    leaves.extend(new_leaves)

    for m in submodules:
        try:
            submodule_instance = getattr(module, m)
        except Exception:
            continue
        get_all_leaf_handles(submodule_instance, leaves)

    return leaves


def get_current_module_leaf_handles(module):
    """
    Get all leaf signal handles in the current module.
    Check its type to differentiate between submodules and leaf signals.
    """
    submodules = []
    leaves = []

    for name, obj_handle in _iter_sim_children(module):
        obj_path = _safe_path(obj_handle, fallback=name)

        if _is_hierarchy_handle(obj_handle):
            submodules.append(name)
        else:
            leaves.append(obj_path)

    return leaves, submodules

def guess_register_file_location(module):
    """
    Get all leaf signal handles and filter them by name.
    The selected leaves may be part of the register file
    """
    regfile_guesses = []
    common_names = [
        "reg", # includes register, regfile, reg_file, etc.
        "file",
        "bank", # includes regbank, etc.
        "rf",
        "gpr"
    ]

    all_leaf_handles = get_all_leaf_handles(module)

    # Rank by how early the common name appears
    ranked_entries = []  # (match_idx, leaf)
    for leaf in all_leaf_handles:
        parts = leaf.split('.')
        # Find index of first component containing any common name (case-insensitive)
        match_idx = None
        for idx, comp in enumerate(parts):
            comp_l = comp.lower()
            if any(name in comp_l for name in common_names):
                match_idx = idx
                break
        if match_idx is None:
            # No component contains a common name; skip this leaf
            continue
        ranking_idx = len(parts) - match_idx # How far from the leaf the match is
        ranked_entries.append((ranking_idx, leaf))

    # Sort so higher-level matches (smaller match_idx) come first
    ranked_entries.sort(key=lambda e: e[0], reverse=True)
    regfile_guesses = [leaf for _, leaf in ranked_entries]

    # Filter processor_ci_top.Processor from guesses
    filtered_regfile_guesses = []
    for guess in regfile_guesses:
        split_guess = guess.split(".")
        joined_guess = ".".join(split_guess[2:])
        filtered_regfile_guesses.append(joined_guess)

    return filtered_regfile_guesses


def filter_processor_interface_from_response(response):
    """
    It is expected a response with the following json format:
    {
        "read_addr_1": "signal_path",
        "read_addr_2": "signal_path",
        "read_data_1": "signal_path",
        "read_data_2": "signal_path",
        "write_enable": "signal_path",
        "write_addr": "signal_path",
        "write_data": "signal_path"
    }
    This function extracts and returns only the JSON part of the response.
    """

    # Scan for the last balanced JSON object in the text
    in_string = False
    string_char = ""
    escape = False
    depth = 0
    start_idx = None
    last_obj = None

    for i, ch in enumerate(response):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == string_char:
                in_string = False
        else:
            if ch in ("'", '"'):
                in_string = True
                string_char = ch
            elif ch == "{":
                if depth == 0:
                    start_idx = i
                depth += 1
            elif ch == "}":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start_idx is not None:
                        last_obj = response[start_idx:i+1]

    if not last_obj:
        raise ValueError("No JSON object found in the response")

    try:
        return json.loads(last_obj)
    except json.JSONDecodeError as e:
        raise ValueError(f"Found a JSON-like object but failed to parse: {e}") from e


def find_register_file_interface(dut, regfile_guesses):
    """
    Identify the register file interface signals from the guessed leaves.
    Uses Ollama.
    Put imports and defines here because this function may be moved to another file
    """
    from ollama import Client
    SERVER_URL = 'http://enqii.lsc.ic.unicamp.br:11434'
    client = Client(host=SERVER_URL)

    def send_prompt(prompt: str, model: str = 'qwen2.5:14b') -> tuple[bool, str]:
        """
        Sends a prompt to the specified server and receives the model's response.
        Args:
            prompt (str): The prompt to be sent to the model.
            model (str, optional): The model to use. Default is 'qwen2.5:32b'.
        Returns:
            tuple: A tuple containing a boolean value (indicating success)
                and the model's response as a string.
        """
        response = client.generate(prompt=prompt, model=model)

        if not response or 'response' not in response:
            return 0, ''

        return 1, response['response']

    find_regfile_prompt = """
        You're a Hardware Engineer. You must analyze signals from an RTL simulation and decide which signals are part of the register file interface of a RISC-V processor. Then you must map these signals to a standard interface.
        **Part 1 Filtering signals**
            1. Analyze the given signal paths in the format "module.module.signal".
            2. First look for a module that is most probably the register file. These are common names found in register file modules: ["reg","bank","rf","gpr","integer_file"]
            3. Check if the module's signals correspond to the standard regfile interface signals: [read_addr_1, read_addr_2, read_data_1, read_data_2, write_enable, write_addr, write_data]
            4. List the chosen signals **Part 2 Mapping signals** Map the signal chosen from part 1 to the standard interface signals.
            Provide your reasoning first and then use extactly the following json format, it is crucial for the system.
            {{
            "read_addr_1": "signal_path",
            "read_addr_2": "signal_path",
            "read_data_1": "signal_path",
            "read_data_2": "signal_path",
            "write_enable": "signal_path",
            "write_addr": "signal_path",
            "write_data": "signal_path"
            }}
        - Register File Guessed signals:
        {regfile_guesses}
    """
    find_regfile_prompt = find_regfile_prompt.format(regfile_guesses="\n".join(regfile_guesses))

    success, response = send_prompt(find_regfile_prompt, model='gpt-oss:20b')

    if not success:
        dut._log.error('Error communicating with the server.')
        return None
    
    dut._log.info(f"Ollama response for register file interface extraction: \n{response}\n\n")
    
    regfile_interface = filter_processor_interface_from_response(response)

    return regfile_interface

def find_regfile_write_signals(dut, core_name, regfile=None):
    """
    Search for register file write interface signals.
    
    If regfile handle is provided, searches in the parent module of the register file.
    Otherwise searches from dut root.
    
    Common patterns:
    - write_enable: wen, we, write_en, reg_write, rf_wen, wren
    - write_address: waddr, rd, dest_reg, rd_addr, wa
    - write_data: wdata, rd_data, wd
    
    Args:
        dut: The design under test
        core_name: Name of the core being tested
        regfile: Optional handle to the register file array
    
    Returns:
        dict: {
            "write_enable": "path.to.signal",
            "write_addr": "path.to.signal", 
            "write_data": "path.to.signal"  # optional
        }
        or None if signals not found
    """
    
    # Patterns to search for (in priority order)
    # Exclude CSR-related signals
    write_enable_patterns = [
        "rf_wen", "regfile_wen", "gpr_wen", "reg_wen",
        "regwr_en",  # Kronos uses regwr_en
        "wr_en_i", "wr_en_o", "wr_en",  # Grande-Risco-5 uses wr_en_i
        "wen_wb", "wen_w", "wen",  # Common write enable names
        "we_i", "we_o", "we",  # Tinyriscv uses we_i
        "write_en", "write_enable", "reg_write", "wren"
    ]
    
    write_addr_patterns = [
        "instruction_rd_address",  # rvx uses instruction_rd_address - check first!
        "regwr_sel", "reg_wr_sel",  # Kronos uses regwr_sel
        "rd_address",  # Generic rd_address
        "rd_wb", "rd_w", "rd",  # Destination register
        "waddr_i", "waddr_o", "waddr",  # Tinyriscv uses waddr_i
        "wsel", "wrsel", "wr_sel",  # Write select variations
        "dest_reg", "rd_addr", "wa",
        "write_addr", "dest_addr", "regfile_waddr"
    ]
    
    write_data_patterns = [
        "regwr_data",  # Kronos uses regwr_data
        "writeback_multiplexer_output", "writeback_mux", "wb_data",  # rvx uses writeback_multiplexer_output
        "data_i",  # Grande-Risco-5 uses data_i (input only, not data_o which is output)
        "wdata_wb", "wdata_w", 
        "wdata_i", "wdata_o", "wdata",  # Tinyriscv uses wdata_i
        "rd_data", "wd", "write_data", "regfile_wdata"
    ]
    
    # Patterns to EXCLUDE (CSR, debug, JTAG, read signals, ready signals, load/store, instruction-specific, etc.)
    exclude_patterns = ["csr", "debug", "dbg", "trace", "jtag", "rdata", "raddr", "rdy", "ready", "fetch", "regrd", "read", "load", "store", "prev", "ebreak", "ecall", "mret", "_rs1", "_rs2", "size"]
    
    found_signals = {}
    
    def search_signals(module, path="", depth=0, max_depth=8):
        """Recursively search for signals in the design hierarchy."""
        if depth > max_depth:
            return
        
        # Get all signals/submodules in this module
        try:
            for name in dir(module):
                if name.startswith('_'):
                    continue
                
                try:
                    obj = getattr(module, name)
                    full_path = f"{path}.{name}" if path else name
                    
                    # Check if this signal matches any pattern
                    name_lower = name.lower()
                    
                    # Skip if matches exclude patterns
                    if any(excl in name_lower for excl in exclude_patterns):
                        continue
                    
                    # Check write enable patterns
                    if "write_enable" not in found_signals:
                        for pattern in write_enable_patterns:
                            if pattern in name_lower:
                                # Verify it's actually a signal (has value attribute)
                                if hasattr(obj, 'value'):
                                    found_signals["write_enable"] = full_path
                                    cocotb.log.info(f"Found write_enable: {full_path}")
                                    break
                    
                    # Check write address patterns
                    if "write_addr" not in found_signals:
                        for pattern in write_addr_patterns:
                            if pattern in name_lower:
                                if hasattr(obj, 'value'):
                                    found_signals["write_addr"] = full_path
                                    cocotb.log.info(f"Found write_addr: {full_path}")
                                    break
                    
                    # Check write data patterns
                    if "write_data" not in found_signals:
                        for pattern in write_data_patterns:
                            if pattern in name_lower:
                                if hasattr(obj, 'value'):
                                    found_signals["write_data"] = full_path
                                    cocotb.log.info(f"Found write_data: {full_path}")
                                    break
                    
                    # Recurse into submodules
                    if not hasattr(obj, 'value') and hasattr(obj, '__dict__'):
                        search_signals(obj, full_path, depth + 1, max_depth)
                    
                except (AttributeError, TypeError):
                    continue
                    
        except (AttributeError, TypeError):
            pass
    
    # Start search from the register file module if provided
    cocotb.log.info(f"Searching for register file write signals in {core_name}...")
    
    if regfile is not None:
        # Get the parent module of the register file (e.g., u_regs module)
        # The regfile is typically regfile_module.regs, so we search in regfile_module
        regfile_path = regfile._path
        cocotb.log.info(f"Register file path: {regfile_path}")
        
        # Extract parent path (remove last component which is the array name)
        parent_path_parts = regfile_path.split('.')
        if len(parent_path_parts) > 1:
            parent_path_parts = parent_path_parts[:-1]  # Remove array name (e.g., 'regs')
            parent_path = '.'.join(parent_path_parts)
            
            # Navigate to parent module
            try:
                parent_module = dut
                for part in parent_path_parts:
                    if part and hasattr(parent_module, part):
                        parent_module = getattr(parent_module, part)
                
                cocotb.log.info(f"Searching in register file parent module: {parent_path}")
                search_signals(parent_module, parent_path, depth=0, max_depth=3)
            except Exception as e:
                cocotb.log.warning(f"Failed to navigate to parent module: {e}")
                search_signals(dut, "", depth=0, max_depth=10)
        else:
            search_signals(dut, "", depth=0, max_depth=10)
    else:
        # No regfile provided, search from top
        search_signals(dut, "", depth=0, max_depth=10)
    
    # Validate we found the critical signals
    if "write_enable" in found_signals and "write_addr" in found_signals:
        cocotb.log.info(f"✓ Found register file write interface!")
        
        # Save to JSON for future use
        config_dir = os.path.join(os.getcwd(), "processor_ci", "config", "regfile_interfaces")
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, f"{core_name}_regfile.json")
        
        with open(config_file, 'w') as f:
            json.dump(found_signals, f, indent=2)
        
        cocotb.log.info(f"Saved configuration to {config_file}")
        return found_signals
    else:
        cocotb.log.warning(f"Could not find complete register file write interface")
        cocotb.log.warning(f"Found: {found_signals}")
        return None


def load_regfile_interface(core_name):
    """
    Load previously saved register file interface configuration.
    
    Returns dict with signal paths or None if not found.
    """
    config_file = os.path.join(
        os.getcwd(), 
        "processor_ci", 
        "config", 
        "regfile_interfaces",
        f"{core_name}_regfile.json"
    )
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return None

@cocotb.test()
async def find_register_file(dut):
    output_dir = os.environ.get('OUTPUT_DIR', "default")
    processor_name = os.path.basename(output_dir)
    debug_output = _env_flag("REGFILE_FINDER_DEBUG") or _env_flag("DEBUG_REGFILE_FINDER")
    output_data = {}

    print("""
            ####################################################
            #Looking for the register file - regfile_finder.py #
            ####################################################
          """)
    
    # Static discovery stage: find array-like objects whose shape is compatible
    # with a RISC-V architectural register file.
    regfile_array_candidates = discover_regfile_array_candidates(dut)
    regfile_array_candidates, visibility_summary = check_regfile_candidate_visibility(dut, regfile_array_candidates)
    regfile_candidates = [candidate["path"] for candidate in regfile_array_candidates]
    dynamic_program = build_regfile_write_program()
    trace_result = await run_regfile_program_and_trace(dut, dynamic_program, regfile_array_candidates)
    classification_results = classify_regfile_candidates(trace_result, dynamic_program)
    confirmation = await confirm_regfile_candidate(dut, regfile_array_candidates, classification_results)
    confirmation_results = confirmation["classification_results"]
    selected_regfile = _select_best_regfile(classification_results, confirmation_results)
    selected_regfile_candidate = _candidate_for_selected_regfile(selected_regfile, regfile_array_candidates)
    interface_probe_program = build_regfile_interface_probe_program()
    interface_probe = {
        "interface_candidates": {
            "write_enable_candidates": [],
            "write_addr_candidates": [],
            "write_data_candidates": [],
            "unclassified_candidates": [],
        },
        "trace_result": {
            "ran": False,
            "reached_loop": False,
            "loop_cycle": None,
            "error": "no confirmed register file selected",
            "samples": [],
            "update_events": [],
        },
    }
    interface_classification = {
        "role_scores": {},
        "tuples": [],
        "selected": {
            "status": "rejected_interface",
            "score": 0,
            "confidence": "none",
            "write_enable": None,
            "write_addr": None,
            "write_data": None,
            "timing_offset": None,
            "reasons": [],
            "failed_checks": ["no confirmed register file selected"],
        },
    }
    if selected_regfile_candidate is not None and selected_regfile and selected_regfile.get("status") == "confirmed_candidate":
        interface_probe = await run_regfile_interface_probe_and_trace(dut, selected_regfile_candidate, interface_probe_program)
        interface_classification = classify_regfile_interface(
            interface_probe["trace_result"],
            interface_probe["interface_candidates"],
        )
    dynamic_program_output = dict(dynamic_program)
    dynamic_program_output["run_result"] = {
        "ran": trace_result.get("ran"),
        "reached_loop": trace_result.get("reached_loop"),
        "loop_cycle": trace_result.get("loop_cycle"),
        "error": trace_result.get("error"),
    }

    if regfile_array_candidates:
        dut._log.info("- Static Register File Array Candidates Found:")
        for i, candidate in enumerate(regfile_array_candidates):
            dut._log.info(
                f"  {i + 1}: {candidate['path']} "
                f"kind={candidate['kind']} "
                f"depth={candidate['depth']} "
                f"word_width={candidate['word_width']} "
                f"score={candidate['score']} "
                f"visibility={candidate['visibility_status']}"
            )
            dut._log.info(f"     reasons: {', '.join(candidate['reasons'])}")
            dut._log.info(f"     visibility: {', '.join(candidate['visibility_reasons'][:6])}")
        dut._log.info("\n")

    dut._log.info(f"Visibility summary: {visibility_summary}")
    if trace_result.get("reached_loop"):
        dut._log.info(
            f"Dynamic regfile write program reached loop at cycle "
            f"{trace_result.get('loop_cycle')}"
        )
    else:
        dut._log.warning(f"Dynamic regfile write program did not complete: {trace_result.get('error')}")

    output_data = {
        "regfile_candidates": regfile_candidates,
        "regfile_array_candidates": regfile_array_candidates,
        "visibility_summary": visibility_summary,
        "dynamic_program": dynamic_program_output,
        "trace_runs": {
            "phase4": trace_result,
            "phase6_confirmation": confirmation["trace_result"],
        },
        "classification_results": classification_results,
        "confirmation_results": confirmation_results,
        "selected_regfile": selected_regfile,
        "regfile_interface_discovery": {
            "ran": interface_probe["trace_result"].get("ran"),
            "regfile_path": interface_probe["trace_result"].get("regfile_path"),
            "parent_scope": interface_probe["interface_candidates"].get("parent_scope"),
            "error": interface_probe["trace_result"].get("error"),
        },
        "interface_probe_program": interface_probe_program,
        "interface_trace_summary": _interface_trace_summary(interface_probe["trace_result"]),
        "interface_candidates": interface_probe["interface_candidates"],
        "interface_classification": interface_classification,
        "selected_regfile_interface": interface_classification["selected"],
    }
    
    ollama_flag = os.environ.get('OLLAMA', False)
    ollama_flag = True if str(ollama_flag).lower() == 'true' else False
    if not ollama_flag:
        dut._log.info("Skipping register file interface detection via Ollama.")
        if debug_output:
            dut._log.info("REGFILE_FINDER_DEBUG enabled; writing full regfile discovery JSON.")
        # Save the current data back to the JSON file
        output_file = os.path.join(output_dir, f"{processor_name}_reg_file.json")

        try:
            _write_regfile_json(output_file, output_data, debug_enabled=debug_output)
            logging.info(f'Results saved to {output_file}')
        except OSError as e:
            logging.warning(f'Error writing to {output_file}: %s', e)
        return
    else:
        dut._log.info("Register file interface detection via Ollama enabled.")
        regfile_interface = None
        # In case no candidates were found, look for the interface
        regfile_guesses = guess_register_file_location(dut)

        if regfile_guesses:
            dut._log.info("- Register File Guessed Signals:")
            for i, guess in enumerate(regfile_guesses):
                dut._log.info(f"  {i + 1}: {guess}")
            dut._log.info("\n")

            regfile_interface = find_register_file_interface(dut, regfile_guesses)

            if isinstance(regfile_interface, dict):
                dut._log.info("- Register File Interface:")
                for signal, path in regfile_interface.items():
                    dut._log.info(f"  {signal}: {path}")

                output_data["regfile_interface"] = regfile_interface

        # Save the updated data back to the JSON file
        output_file = os.path.join(output_dir, f"{processor_name}_reg_file.json")

        try:
            _write_regfile_json(output_file, output_data, debug_enabled=debug_output)
            logging.info(f'Results saved to {output_file}')
        except OSError as e:
            logging.warning(f'Error writing to {output_file}: %s', e)

        # Consider the interface invalid if at least one required entry is null or missing
        # Other error condition are harder to detect
        required_keys = {
            "read_addr_1",
            "read_addr_2",
            "read_data_1",
            "read_data_2",
            "write_enable",
            "write_addr",
            "write_data",
        }

        if isinstance(regfile_interface, dict) and required_keys.issubset(regfile_interface.keys()):
            # invalid if any required entry is None
            any_nulls = any(regfile_interface[k] is None for k in required_keys)
            valid_regfile_interface = not any_nulls
        else:
            valid_regfile_interface = False

        if not regfile_candidates and not valid_regfile_interface:
            assert False, f"No register file found for the {processor_name} processor"


# This script is intended to be run as a cocotb testbench.
# If called directly, it will open a subprocess and run the cocotb simulation
# The simulation will run only the 'async def find_register_file(dut)' function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This regfile_finder testbench runs a cocotb simulation and parses the design hierarchy to find the register file.")
    parser.add_argument("--makefile", required=True, help="Specify the cocotb makefile path")
    parser.add_argument("--output", required=True, default="detected_reg_file.json", help="Specify the output file path. Must be an absolute path.")
    args = parser.parse_args()

    if not os.path.isabs(args.output):
        raise ValueError("The --output argument must be an absolute path.")

    
    # These commands:
    # copy this file to the makefile directory
    # run the simulation to find the register file
    # remove the copy
    # TODO: change this to use "PYTHONPATH" and "make -f"

    makefile_dir = os.path.dirname(os.path.abspath(args.makefile))
    subprocess.run(["cp", __file__, makefile_dir])

    module_name = os.path.splitext(os.path.basename(__file__))[0]
    subprocess.run(["make", f"MODULE={module_name}", f"OUTPUT_FILE={args.output}"], cwd=makefile_dir)

    file_copy_path = os.path.join(makefile_dir, os.path.basename(__file__))
    subprocess.run(["rm", "-f", file_copy_path], cwd=makefile_dir)


    
