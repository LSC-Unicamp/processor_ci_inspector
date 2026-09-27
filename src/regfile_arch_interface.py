"""Trace-driven, fully validated architectural GPR write interface (v2)."""

from collections import Counter
from itertools import combinations, product
from statistics import median

try:
    from .regfile_interface_expression import (
        ARCHITECTURAL_EXPRESSION_VERSION, EXPRESSION_PREFIX,
        evaluate_expression, expression_paths,
    )
    from .riscv.encoding import ADD, ADDI, AUIPC, BNE, JAL, JALR, LUI, LW, NOP, SW
except ImportError:
    from regfile_interface_expression import (
        ARCHITECTURAL_EXPRESSION_VERSION, EXPRESSION_PREFIX,
        evaluate_expression, expression_paths,
    )
    from riscv.encoding import ADD, ADDI, AUIPC, BNE, JAL, JALR, LUI, LW, NOP, SW


WRITE_CLASSES = ("alu_imm", "alu_reg", "lui", "auipc", "jal", "jalr", "load")
OPCODES = {"alu_imm": 0x13, "alu_reg": 0x33, "lui": 0x37,
           "auipc": 0x17, "jal": 0x6F, "jalr": 0x67, "load": 0x03}
OFFSETS = tuple(range(-4, 3))
ROLES = ("write_enable", "write_addr", "write_data")
PARTIAL_REQUIRED_CLASSES = frozenset(("alu_imm", "alu_reg", "lui"))
VIRTUAL_INTERFACE_SEMANTICS = frozenset(
    ("architectural_write", "validated_write_interface")
)


def _signal(path):
    return {"op": "signal", "path": path}


def _constant(value):
    return {"op": "constant", "value": value}


def _binary(op, left, right):
    return {"op": op, "args": [left, right]}


def build_architectural_write_program(held_out=False, max_cycles=2000):
    """Seven RV32I write classes plus architectural non-write controls."""
    (a, b, load_value, imm20, auipc_imm, a_reg, b_reg, anchor,
     alu_rd, lui_rd, auipc_rd, jal_rd, jalr_rd, load_rd) = (
        (0x62, 0x13, 0x27B13, 0x23456, 2, 10, 11, 4, 12, 13, 14, 15, 9, 3)
        if held_out else
        (0x21, 0x34, 0x51A21, 0x12345, 1, 1, 2, 7, 3, 4, 5, 6, 8, 9)
    )
    program = {
        0x00: NOP, 0x04: NOP,
        0x08: ADDI(a_reg, 0, a), 0x0C: NOP,
        0x10: ADDI(b_reg, 0, b), 0x14: NOP,
        0x18: ADD(alu_rd, a_reg, b_reg), 0x1C: NOP,
        0x20: LUI(lui_rd, imm20), 0x24: NOP,
        0x28: AUIPC(auipc_rd, auipc_imm), 0x2C: NOP,
        0x30: JAL(jal_rd, 4), 0x34: NOP,
        0x38: AUIPC(anchor, 0), 0x3C: NOP,
        0x40: JALR(jalr_rd, anchor, 12), 0x44: NOP,
        # Keep semantic instructions on 8-byte boundaries. Some multi-cycle
        # wrappers only accept an instruction request on alternating cycles.
        # Controls required for partial validation also precede memory, since
        # a wrapper with no usable data transport may stall permanently on LW.
        0x48: ADDI(a_reg, a_reg, 0), 0x4C: NOP,
        0x50: ADDI(0, 0, 0x5A), 0x54: NOP,
        0x58: BNE(0, 0, 4), 0x5C: NOP,
        0x60: NOP, 0x64: NOP,
        0x68: LW(load_rd, 0, 0x100), 0x6C: NOP,
        0x70: SW(b_reg, 0, 0x104), 0x74: NOP,
        0x78: JAL(0, 0),
    }
    writes = [
        (0x08, a_reg, a, "alu_imm"),
        (0x10, b_reg, b, "alu_imm"),
        (0x18, alu_rd, a + b, "alu_reg"),
        (0x20, lui_rd, imm20 << 12, "lui"),
        (0x28, auipc_rd, (0x28 + (auipc_imm << 12), "pc_relative"), "auipc"),
        (0x30, jal_rd, (0x34, "pc_relative"), "jal"),
        (0x38, anchor, (0x38, "pc_relative"), "auipc"),
        (0x40, jalr_rd, (0x44, "pc_relative"), "jalr"),
        (0x48, a_reg, a, "alu_imm"),
        (0x68, load_rd, load_value, "load"),
    ]
    negative_controls = [
        {"pc": 0x50, "kind": "x0"},
        {"pc": 0x70, "kind": "store"},
        {"pc": 0x58, "kind": "branch"},
        {"pc": 0x60, "kind": "nop"},
    ]
    loop_pc = 0x78
    if held_out:
        # Shift the control-flow half by a complete request pair, changing
        # AUIPC and link values while preserving alignment and JALR distance.
        program = {pc + (8 if pc >= 0x28 else 0): word for pc, word in program.items()}
        program[0x28] = NOP
        program[0x2C] = NOP
        writes = [
            (pc + (8 if pc >= 0x28 else 0), reg,
             (value[0] + 8, value[1]) if isinstance(value, tuple) and pc >= 0x28 else value,
             opclass)
            for pc, reg, value, opclass in writes
        ]
        negative_controls = [
            {**control, "pc": control["pc"] + 8} for control in negative_controls
        ]
        loop_pc += 8
    sequence = [
        {"pc": pc, "reg": f"x{reg}", "reg_index": reg,
         "value": value, "opclass": opclass,
         "idempotent": pc == (0x50 if held_out else 0x48)}
        for pc, reg, value, opclass in writes
    ]
    return {
        "program_name": "architectural_gpr_write_confirmation_v2" if held_out
                        else "architectural_gpr_write_discovery_v2",
        "architectural_probe": True,
        "program": program,
        "loop_pc": loop_pc,
        "write_sequence": sequence,
        "negative_controls": negative_controls,
        "data_memory_initial": {0x100: load_value},
        "data_access_addresses": [0x100, 0x104],
        "expected_store": {"address": 0x104, "value": b},
        "load_delay_cycles": 2 if held_out else 0,
        "expected_registers": {
            f"x{reg}": value for _, reg, value, _ in writes if isinstance(value, int)
        },
        "default_instruction": NOP,
        "max_cycles": max_cycles,
    }


def _expected(entry, base, mask, pc_bias=0):
    value = entry["value"]
    if isinstance(value, tuple):
        return (base + value[0] + pc_bias) & mask
    return int(value) & mask


def _infer_pc_value_bias(program, fetches, changes, base, mask):
    biases = []
    for entry in program.get("write_sequence", ()):
        if not isinstance(entry.get("value"), tuple):
            continue
        fetch = fetches.get(entry["pc"])
        if fetch is None:
            continue
        nominal = (base + entry["value"][0]) & mask
        matches = [change for change in changes
                   if change["reg"] == entry["reg"]
                   and fetch <= change["cycle"] <= fetch + 64]
        if not matches:
            continue
        raw = (min(matches, key=lambda item: item["cycle"])["value"] - nominal) & mask
        signed = raw if raw <= mask // 2 else raw - (mask + 1)
        if -64 <= signed <= 64:
            biases.append(signed)
    if not biases:
        return 0
    bias, count = Counter(biases).most_common(1)[0]
    return bias if count >= 2 else 0


def analyze_architectural_trace(trace, program, word_width):
    """Associate architectural writes while separating unsupported coverage from failures."""
    samples = trace.get("samples") or []
    by_cycle = {sample["cycle"]: sample for sample in samples}
    hard_failures = []
    unavailable = []
    class_failures = {opclass: [] for opclass in WRITE_CLASSES}
    class_unavailable = set()
    base = program.get("_runtime_base_address")
    if base is None:
        hard_failures.append("instruction runtime base was not observed")
        base = 0
    mask = (1 << int(word_width)) - 1
    memory = trace.get("data_memory") or {}
    load_available = bool(memory.get("supported") and memory.get("load_verified"))
    store_available = bool(memory.get("supported") and memory.get("store_verified"))
    if not load_available:
        class_unavailable.add("load")
        unavailable.append("LW data transaction was not served and verified")
    if not store_available:
        unavailable.append("store control was not acknowledged and verified")

    fetches = {}
    fetch_width = int(trace.get("fetch_width_bytes") or 4)
    for sample in samples:
        pc = sample.get("pc")
        if not sample.get("fetch_valid") or pc is None:
            continue
        for fetched_pc in range(pc, pc + fetch_width, 4):
            fetches.setdefault(fetched_pc, sample["cycle"])

    previous = {}
    changes = []
    for sample in samples:
        current = sample.get("regfile_values") or {}
        for reg, value in current.items():
            old = previous.get(reg)
            if old is not None and value is not None and old != value:
                changes.append({"cycle": sample["cycle"], "reg": reg,
                                "old": old & mask, "value": value & mask})
        previous = current

    pc_value_bias = _infer_pc_value_bias(program, fetches, changes, base, mask)

    records = []
    claimed = set()
    claimed_cycles = set()
    for entry in program["write_sequence"]:
        opclass = entry["opclass"]
        fetch = fetches.get(entry["pc"])
        expected = _expected(entry, base, mask, pc_value_bias)
        record = {"pc": entry["pc"], "reg": entry["reg"],
                  "reg_index": entry["reg_index"], "value": expected,
                  "opclass": opclass, "idempotent": entry["idempotent"]}
        if fetch is None:
            reason = f"instruction fetch not observed at 0x{entry['pc']:x}"
            if opclass == "load" and not load_available:
                class_unavailable.add(opclass)
            else:
                class_failures[opclass].append(reason)
            records.append(record)
            continue
        record["fetch_cycle"] = fetch
        if not entry["idempotent"] and opclass not in class_unavailable:
            matches = [change for change in changes
                       if change["reg"] == entry["reg"]
                       and change["value"] == expected
                       and fetch <= change["cycle"] <= fetch + 64
                       and (change["cycle"], change["reg"], change["value"]) not in claimed]
            if matches:
                match = min(matches, key=lambda item: item["cycle"])
                record["cycle"] = match["cycle"]
                key = (match["cycle"], match["reg"], match["value"])
                claimed.add(key)
                claimed_cycles.add(match["cycle"])
            else:
                class_failures[opclass].append(
                    f"expected x{entry['reg_index']}={expected:#x} storage update missing"
                )
        records.append(record)

    latencies = [record["cycle"] - record["fetch_cycle"] for record in records
                 if record["opclass"] == "alu_imm" and not record["idempotent"]
                 and "cycle" in record and "fetch_cycle" in record]
    latency = round(median(latencies)) if latencies else None
    for record in records:
        if not record["idempotent"] or "fetch_cycle" not in record:
            continue
        if latency is None:
            class_failures[record["opclass"]].append(
                "ALU-immediate fetch-to-commit latency could not be calibrated"
            )
            continue
        held = 0
        for cycle in range(record["fetch_cycle"] + 1, record["fetch_cycle"] + 33):
            sample = by_cycle.get(cycle)
            if sample is None or sample.get("pc") != record["pc"]:
                break
            held += 1
        record["cycle"] = record["fetch_cycle"] + latency + held
        record["fetch_hold_cycles"] = held
        sample = by_cycle.get(record["cycle"])
        if sample is None or (sample.get("regfile_values") or {}).get(record["reg"]) != record["value"]:
            class_failures[record["opclass"]].append(
                "idempotent write could not be checked at calibrated commit cycle"
            )

    active_start = min(fetches.values(), default=0)
    active_end = trace.get("loop_cycle")
    if active_end is None:
        active_end = samples[-1]["cycle"] if samples else 0
    unexpected = [change for change in changes
                  if (change["cycle"], change["reg"], change["value"]) not in claimed
                  and active_start <= change["cycle"] <= active_end]
    if unexpected:
        hard_failures.append(f"{len(unexpected)} unaccounted storage changes during probe")

    simultaneous = {}
    for change in changes:
        if active_start <= change["cycle"] <= active_end:
            simultaneous.setdefault(change["cycle"], set()).add(change["reg"])
    topology = None
    if any(len(regs) > 1 for regs in simultaneous.values()):
        topology = "unsupported_multiport"
        hard_failures.append("simultaneous GPR updates require a multi-port interface")
    elif len(unexpected) >= 4 and all(
        (change["old"] ^ change["value"]).bit_count() <= 2 for change in unexpected
    ):
        topology = "unsupported_serial"
        hard_failures.append("incremental bit-level GPR updates require a serial interface")

    if any((sample.get("regfile_values") or {}).get("x0") not in (None, 0)
           for sample in samples):
        hard_failures.append("x0 storage changed despite an attempted write")

    negatives = []
    for control in program.get("negative_controls", []):
        fetch = fetches.get(control["pc"])
        if fetch is None:
            if control["kind"] == "store" and not store_available:
                continue
            hard_failures.append(
                f"negative control fetch not observed at 0x{control['pc']:x}"
            )
        elif latency is not None:
            negatives.append({"cycle": fetch + latency, "fetch_cycle": fetch,
                              "kind": control["kind"]})

    class_states = {}
    for opclass in WRITE_CLASSES:
        class_records = [record for record in records if record["opclass"] == opclass]
        if opclass in class_unavailable:
            state = "unavailable"
        elif class_failures[opclass] or not class_records or any(
            "cycle" not in record for record in class_records
        ):
            state = "failed"
        else:
            state = "validated"
        class_states[opclass] = {
            "state": state,
            "failed_checks": list(dict.fromkeys(class_failures[opclass])),
            "write_count": sum("cycle" in record for record in class_records),
        }

    validated = sorted(
        opclass for opclass, state in class_states.items() if state["state"] == "validated"
    )
    failed_class_checks = [reason for state in class_states.values()
                           if state["state"] == "failed"
                           for reason in state["failed_checks"]]
    partial_control_kinds = {item["kind"] for item in negatives}
    partial_execution_complete = (
        PARTIAL_REQUIRED_CLASSES.issubset(validated)
        and any(record["idempotent"] and "cycle" in record for record in records)
        and partial_control_kinds.issuperset({"x0", "branch", "nop"})
    )
    if not trace.get("reached_loop"):
        if "load" in class_unavailable and partial_execution_complete:
            unavailable.append(
                "self-loop was not reached after the unavailable memory probe"
            )
        else:
            hard_failures.append("self-loop was not reached")
    partial_passed = (
        not hard_failures
        and PARTIAL_REQUIRED_CLASSES.issubset(validated)
        and len({record["reg_index"] for record in records if "cycle" in record}) >= 2
        and len({record["value"] for record in records if "cycle" in record}) >= 3
        and any(record["idempotent"] and "cycle" in record for record in records)
        and partial_control_kinds.issuperset({"x0", "branch", "nop"})
    )
    full_failures = list(hard_failures) + failed_class_checks
    if set(validated) != set(WRITE_CLASSES):
        full_failures.append("not all seven GPR-writing classes were observed")
    if not load_available:
        full_failures.append("LW data transaction was not served and verified")
    if not store_available:
        full_failures.append("store control was not acknowledged and verified")
    full_failures = list(dict.fromkeys(full_failures))
    return {
        "passed": not full_failures,
        "partial_passed": partial_passed,
        "failed_checks": full_failures,
        "hard_failed_checks": list(dict.fromkeys(hard_failures + failed_class_checks)),
        "unavailable_checks": unavailable,
        "records": records,
        "negative_controls": negatives,
        "classes": validated,
        "class_states": class_states,
        "runtime_base": base,
        "pc_value_bias": pc_value_bias,
        "active_window": [active_start, active_end],
        "expected_registers": {
            entry["reg"]: _expected(entry, base, mask, pc_value_bias)
            for entry in program["write_sequence"]
        },
        "load_verified": load_available,
        "store_verified": store_available,
        "changed_update_count": len(claimed_cycles),
        "topology": topology,
    }


def _sample_at(trace, cycle):
    samples = trace.get("samples") or ()
    if isinstance(cycle, int) and 0 <= cycle < len(samples):
        sample = samples[cycle]
        if sample.get("cycle") == cycle:
            return sample
    return None


def _value_at(expr, trace, cycle):
    sample = _sample_at(trace, cycle)
    return evaluate_expression(expr, sample.get("signals") or {}) if sample else None


def _leaves(candidates):
    storage = candidates.get("regfile_path") or ""
    seen = set()
    for role in ROLES:
        for leaf in candidates.get(f"{role}_candidates", ()):
            path = leaf.get("path")
            if (path and path not in seen and not path.startswith("__storage_")
                    and path != storage and not path.startswith(storage + ".")
                    and not path.startswith(storage + "[")):
                seen.add(path)
                yield leaf
    for leaf in candidates.get("unclassified_candidates", ()):
        path = leaf.get("path")
        if (path and path not in seen and not path.startswith("__storage_")
                and path != storage and not path.startswith(storage + ".")
                and not path.startswith(storage + "[")):
            seen.add(path)
            yield leaf


def _records(evidence, classes=None):
    classes = set(classes or evidence.get("classes") or ())
    return [record for record in evidence.get("records", ())
            if record.get("opclass") in classes and "cycle" in record]


def _expr_key(expr):
    return repr(expr)


def _predicate_options(opclass, trace, evidence, leaves, offset):
    usable_records = _records(evidence)
    positive = [record for record in usable_records if record["opclass"] == opclass]
    other = [record for record in usable_records if record["opclass"] != opclass]
    # NOP is ADDI x0,x0,0, so its ALU-I decoder flag may be correct; the
    # destination-zero guard, not the class predicate, must suppress commit.
    negative = [control for control in evidence["negative_controls"]
                if control["kind"] not in ("x0", "nop")]
    if not positive or not other:
        return []
    expected_cycles = {record["cycle"] + offset for record in positive}
    options = []
    for leaf in leaves:
        path, width = leaf.get("path"), leaf.get("width")
        expressions = []
        if width == 1:
            expressions.append(_signal(path))
            expressions.append({"op": "not", "args": [_signal(path)]})
        if width and 2 <= width <= 8 and leaf.get("role") != "write_addr":
            values = {_value_at(_signal(path), trace, record["cycle"] + offset)
                      for record in positive}
            values.discard(None)
            if len(values) == 1:
                expressions.append(_binary("eq", _signal(path), _constant(values.pop())))
        if width in (7, 16, 32, 64):
            opcode = _signal(path) if width == 7 else {
                "op": "slice", "args": [_signal(path)], "lsb": 0, "width": 7,
            }
            expressions.append(_binary("eq", opcode, _constant(OPCODES[opclass])))
        for expr in expressions:
            if not all(_value_at(expr, trace, record["cycle"] + offset) == 1
                       for record in positive):
                continue
            if any(_value_at(expr, trace, record["cycle"] + offset) != 0
                   for record in other):
                continue
            if any(_value_at(expr, trace, control["cycle"] + offset) != 0
                   for control in negative):
                continue
            extras = sum(
                _value_at(expr, trace, sample["cycle"]) == 1
                for sample in trace.get("samples", ())
                if sample["cycle"] not in expected_cycles
            )
            name = str(leaf.get("name", "")).lower()
            hints = {
                "alu_imm": ("mcc", "alui", "imm"),
                "alu_reg": ("rcc", "alur", "add"),
                "lui": ("lui",), "auipc": ("auipc",),
                "jal": ("jal",), "jalr": ("jalr",),
                "load": ("lcc", "load", "lw"),
            }[opclass]
            hint_score = 1 if any(hint in name for hint in hints) else 0
            options.append((extras, -hint_score, len(str(expr)), expr))
    options.sort(key=lambda item: (item[1], item[0], item[2]))
    unique = []
    seen = set()
    for item in options:
        key = _expr_key(item[3])
        if key not in seen:
            seen.add(key)
            unique.append(item[3])
    return unique[:8]


def _address_sources(leaves):
    for leaf in leaves:
        width = leaf.get("width")
        path = leaf.get("path")
        if width in (4, 5):
            yield _signal(path), leaf
        elif width and 6 <= width <= 40:
            for bit in range(min(width - 4, 32)):
                yield {"op": "slice", "args": [_signal(path)], "lsb": bit, "width": 5}, leaf


def _data_sources(leaves, word_width, opclass):
    for leaf in leaves:
        width = leaf.get("width")
        path = leaf.get("path")
        if width == word_width or (opclass == "load" and word_width == 64 and width == 32):
            yield _signal(path), leaf
        elif width and word_width and width <= 256 and width % word_width == 0:
            for bit in range(0, width, word_width):
                yield {"op": "slice", "args": [_signal(path)],
                       "lsb": bit, "width": word_width}, leaf


def _derived_data_sources(leaves, word_width, opclass):
    word_leaves = [leaf for leaf in leaves if leaf.get("width") == word_width]
    instruction_leaves = [leaf for leaf in leaves if leaf.get("width") in (32, 64)
                          and any(hint in str(leaf.get("name", "")).lower()
                                  for hint in ("instr", "inst", "ir", "opcode", "xidata"))]
    pc_leaves = [leaf for leaf in word_leaves
                 if "pc" in str(leaf.get("name", "")).lower()]
    if opclass == "lui":
        for leaf in instruction_leaves:
            immediate = {"op": "slice", "args": [_signal(leaf["path"])],
                         "lsb": 12, "width": 20}
            yield {"op": "shift_left", "args": [immediate], "amount": 12,
                   "width": word_width}, leaf
    if opclass in ("jal", "jalr"):
        for leaf in pc_leaves[:12]:
            yield {"op": "add", "args": [_signal(leaf["path"]), _constant(4)],
                   "width": word_width}, leaf
    if opclass == "auipc":
        for pc_leaf in pc_leaves[:8]:
            for inst_leaf in instruction_leaves[:8]:
                immediate = {"op": "shift_left", "args": [{
                    "op": "slice", "args": [_signal(inst_leaf["path"])],
                    "lsb": 12, "width": 20,
                }], "amount": 12, "width": word_width}
                yield {"op": "add", "args": [_signal(pc_leaf["path"]), immediate],
                       "width": word_width}, pc_leaf
    if opclass == "load" and word_width == 64:
        for leaf in leaves:
            if leaf.get("width") == 32:
                yield {"op": "sign_extend", "args": [_signal(leaf["path"])],
                       "from_width": 32, "to_width": 64}, leaf
    if opclass in ("alu_imm", "alu_reg"):
        operands = [leaf for leaf in word_leaves if any(
            hint in str(leaf.get("name", "")).lower()
            for hint in ("op", "src", "rs", "data", "value")
        )][:12]
        for left, right in combinations(operands, 2):
            yield {"op": "add", "args": [_signal(left["path"]), _signal(right["path"])],
                   "width": word_width}, left


def _data_source_rank(leaf, opclass):
    name = str(leaf.get("name") or "").lower()
    hints = {
        "alu_imm": ("rmd", "alu", "result"),
        "alu_reg": ("rmd", "alu", "result"),
        "lui": ("simm", "imm", "lui"),
        "auipc": ("pcsimm", "pc", "result"),
        "jal": ("nxpc", "pc", "link"),
        "jalr": ("nxpc", "pc", "link"),
        "load": ("ldata", "load", "datai", "read_data"),
    }[opclass]
    return (max((len(hint) for hint in hints if hint in name), default=0),
            leaf.get("name_score", 0))


def _or_all(expressions):
    if len(expressions) == 1:
        return expressions[0]
    middle = len(expressions) // 2
    return _binary("or", _or_all(expressions[:middle]), _or_all(expressions[middle:]))


def _seed_expression(seed, role):
    if not seed or str(seed.get(role) or "").startswith("__storage_"):
        return None
    expression = (seed.get("role_expressions") or {}).get(role)
    if expression is not None:
        return expression
    path = seed.get(role)
    return _signal(path) if isinstance(path, str) and path and not path.startswith("__") else None


def _matching_address_options(trace, evidence, leaves, seed=None):
    records = _records(evidence)
    ranked = []
    x0 = [control for control in evidence["negative_controls"] if control["kind"] == "x0"]
    sources = list(_address_sources(leaves))
    seeded = _seed_expression(seed, "write_addr")
    if seeded is not None:
        sources.insert(0, (seeded, {"name_score": 100, "name": "seeded_write_addr"}))
    for offset in OFFSETS:
        for expr, leaf in sources:
            if all(_value_at(expr, trace, record["cycle"] + offset) == record["reg_index"]
                   for record in records) and all(
                       _value_at(expr, trace, control["cycle"] + offset) == 0
                       for control in x0
                   ):
                ranked.append((leaf.get("name_score", 0), -abs(offset),
                               -len(str(expr)), expr, offset))
    ranked.sort(key=lambda item: item[:3], reverse=True)
    return [{"expression": item[3], "offset": item[4]} for item in ranked[:8]]


def _matching_data_options(trace, evidence, leaves, word_width, seed=None):
    mask = (1 << int(word_width)) - 1
    classes = list(evidence.get("classes") or ())
    all_records = _records(evidence, classes)
    options = []
    seed_expr = _seed_expression(seed, "write_data")
    for offset in OFFSETS:
        common_sources = list(_data_sources(leaves, word_width, classes[0])) if classes else []
        if seed_expr is not None:
            common_sources.insert(0, (seed_expr, {"name_score": 100, "name": "seeded_write_data"}))
        for expr, leaf in common_sources:
            if all(_value_at(expr, trace, record["cycle"] + offset) is not None
                   and (_value_at(expr, trace, record["cycle"] + offset) & mask) == record["value"]
                   for record in all_records):
                options.append((100 + leaf.get("name_score", 0), -abs(offset),
                                -len(str(expr)), expr, offset))
        predicates = {}
        for opclass in classes:
            choices = _predicate_options(opclass, trace, evidence, leaves, offset)
            if choices:
                predicates[opclass] = choices[0]
        if len(predicates) != len(classes):
            continue
        cases = []
        rank = 0
        complete = True
        for opclass in classes:
            records = _records(evidence, (opclass,))
            matches = []
            sources = list(_data_sources(leaves, word_width, opclass))
            sources.extend(_derived_data_sources(leaves, word_width, opclass))
            for expr, leaf in sources:
                values = [_value_at(expr, trace, record["cycle"] + offset) for record in records]
                if all(value is not None and (value & mask) == record["value"]
                       for value, record in zip(values, records)):
                    matches.append((_data_source_rank(leaf, opclass), -len(str(expr)), expr))
            matches.sort(key=lambda item: item[:2], reverse=True)
            if not matches:
                complete = False
                break
            rank += matches[0][0][0] + matches[0][0][1]
            cases.append({"when": predicates[opclass], "value": matches[0][2]})
        if complete:
            expr = {"op": "priority_mux", "cases": cases, "default": _constant(0)}
            try:
                expression_paths(expr, version=ARCHITECTURAL_EXPRESSION_VERSION)
            except ValueError:
                continue
            options.append((rank, -abs(offset), -len(str(expr)), expr, offset))
    options.sort(key=lambda item: item[:3], reverse=True)
    unique = []
    seen = set()
    for item in options:
        key = (_expr_key(item[3]), item[4])
        if key not in seen:
            seen.add(key)
            unique.append({"expression": item[3], "offset": item[4]})
    return unique[:8]


def _active_false_count(expr, trace, evidence, positive_cycles):
    start, end = evidence.get("active_window") or (0, 0)
    return sum(
        _value_at(expr, trace, cycle) not in (0, None)
        for cycle in range(start, end + 1)
        if cycle not in positive_cycles
    )


def _enable_options(trace, evidence, leaves, seed=None):
    records = _records(evidence)
    options = []
    seed_expr = _seed_expression(seed, "write_enable")
    for offset in OFFSETS:
        positive_cycles = {record["cycle"] + offset for record in records}
        atoms = []
        named_guards = []
        address_guards = []
        if seed_expr is not None:
            atoms.append((seed_expr, 100))
            if (
                all(_value_at(seed_expr, trace, cycle) == 1
                    for cycle in positive_cycles)
                and _active_false_count(
                    seed_expr, trace, evidence, positive_cycles
                ) == 0
            ):
                options.append((200, -abs(offset), -len(str(seed_expr)),
                                seed_expr, offset))
        for leaf in leaves:
            path, width = leaf.get("path"), leaf.get("width")
            if width == 1:
                atoms.extend(((_signal(path), leaf.get("name_score", 0)),
                              ({"op": "not", "args": [_signal(path)]}, 0)))
            elif width and 2 <= width <= 8:
                values = {_value_at(_signal(path), trace, cycle) for cycle in positive_cycles}
                values.discard(None)
                if len(values) == 1:
                    atoms.append((_binary("eq", _signal(path), _constant(values.pop())),
                                  leaf.get("name_score", 0)))
        predicates = []
        for opclass in evidence.get("classes") or ():
            choices = _predicate_options(opclass, trace, evidence, leaves, offset)
            if not choices:
                predicates = []
                break
            predicates.append(choices[0])
        if predicates:
            class_enable = _or_all(predicates)
            atoms.append((class_enable, 20))
            for leaf in leaves:
                name = str(leaf.get("name") or "").lower()
                if leaf.get("width") != 1 or not any(
                    hint in name for hint in ("stall", "hold", "halt", "hlt", "wait", "reset", "rst")
                ):
                    continue
                for guard in (_signal(leaf["path"]),
                              {"op": "not", "args": [_signal(leaf["path"])]}):
                    guarded = _binary("and", class_enable, guard)
                    if all(_value_at(guarded, trace, cycle) == 1
                           for cycle in positive_cycles):
                        atoms.append((guarded, 30))
                        guard_priority = 120 if any(
                            hint in name for hint in ("stall", "hold", "halt", "hlt", "wait")
                        ) else 110
                        named_guards.append((guard_priority, guard))
        for addr, leaf in _address_sources(leaves):
            guard = _binary("ne", addr, _constant(0))
            if all(_value_at(guard, trace, cycle) == 1 for cycle in positive_cycles):
                atoms.append((guard, leaf.get("name_score", 0)))
                address_guards.append(guard)

        if predicates:
            for address_guard in address_guards[:12]:
                base_enable = _binary("and", class_enable, address_guard)
                preferred = [(100, base_enable)]
                preferred.extend(
                    (priority, _binary("and", base_enable, guard))
                    for priority, guard in named_guards[:8]
                )
                for priority, expression in preferred:
                    try:
                        expression_paths(expression, version=ARCHITECTURAL_EXPRESSION_VERSION)
                    except ValueError:
                        continue
                    if _active_false_count(
                        expression, trace, evidence, positive_cycles
                    ) == 0:
                        options.append((priority, -abs(offset), -len(str(expression)),
                                        expression, offset))

        ranked_atoms = []
        seen = set()
        for expr, hint in atoms:
            key = _expr_key(expr)
            if key in seen or not all(_value_at(expr, trace, cycle) == 1
                                      for cycle in positive_cycles):
                continue
            seen.add(key)
            extras = _active_false_count(expr, trace, evidence, positive_cycles)
            ranked_atoms.append((extras, -hint, len(str(expr)), expr, frozenset((key,))))
        ranked_atoms.sort(key=lambda item: item[:3])
        beam = ranked_atoms[:32]
        completed = []
        for depth in range(1, 5):
            for state in beam:
                if state[0] == 0:
                    completed.append(state)
            if depth == 4:
                break
            expanded = []
            for state in beam:
                for atom in ranked_atoms[:32]:
                    if atom[4] & state[4]:
                        continue
                    expr = _binary("and", state[3], atom[3])
                    try:
                        expression_paths(expr, version=ARCHITECTURAL_EXPRESSION_VERSION)
                    except ValueError:
                        continue
                    extras = _active_false_count(expr, trace, evidence, positive_cycles)
                    expanded.append((extras, state[1] + atom[1], len(str(expr)), expr,
                                     state[4] | atom[4]))
            expanded.sort(key=lambda item: item[:3])
            dedup = {}
            for state in expanded:
                dedup.setdefault(state[4], state)
            beam = list(dedup.values())[:64]
        for state in completed:
            options.append((min(-state[1], 80), -abs(offset),
                            -len(str(state[3])), state[3], offset))
    options.sort(key=lambda item: item[:3], reverse=True)
    return [{"expression": item[3], "offset": item[4]} for item in options[:8]]


def validate_architectural_interface(selected, trace, evidence, word_width):
    """Check a frozen tuple against every expected and forbidden commit slot."""
    semantics = selected.get("interface_semantics")
    failures = list(
        evidence.get("failed_checks") if semantics == "architectural_write"
        else evidence.get("hard_failed_checks") or []
    )
    expressions = selected.get("role_expressions") or {}
    if set(expressions) != set(ROLES):
        failures.append("architectural tuple is incomplete")
        return {"passed": False, "failed_checks": failures}
    try:
        for role in ROLES:
            paths = expression_paths(expressions[role], version=ARCHITECTURAL_EXPRESSION_VERSION)
            storage = selected.get("regfile_path") or ""
            if any(path.startswith("__storage_") or path == storage
                   or (storage and (path.startswith(storage + ".")
                                    or path.startswith(storage + "[")))
                   for path in paths):
                failures.append(f"{role} uses register-file storage")
    except (TypeError, ValueError) as exc:
        failures.append(str(exc))
    selected_classes = set(selected.get("validated_instruction_classes") or ())
    evidence_classes = set(evidence.get("classes") or ())
    if not selected_classes or not selected_classes.issubset(evidence_classes):
        failures.append("held-out trace did not validate the frozen instruction classes")
    records = _records(evidence, selected_classes)
    positive_cycles = set()
    mask = (1 << int(word_width)) - 1
    for record in records:
        for role, expected in (("write_enable", 1), ("write_addr", record["reg_index"]),
                               ("write_data", record["value"])):
            offset = selected.get(f"{role}_timing_offset")
            if offset is None:
                failures.append(f"{role} has no timing offset")
                continue
            actual = _value_at(expressions[role], trace, record["cycle"] + offset)
            if role == "write_data" and actual is not None:
                actual &= mask
            if actual != expected:
                failures.append(
                    f"{role} mismatch for {record['opclass']} x{record['reg_index']} at 0x{record['pc']:x}"
                )
        positive_cycles.add(record["cycle"] + selected["write_enable_timing_offset"])
    enable = expressions["write_enable"]
    for control in evidence.get("negative_controls", ()):
        cycle = control["cycle"] + selected["write_enable_timing_offset"]
        if cycle in positive_cycles or _value_at(enable, trace, cycle) != 0:
            failures.append(f"false architectural commit on {control['kind']} control")
    active_start, active_end = evidence.get("active_window") or (0, 0)
    false_cycles = [sample["cycle"] for sample in trace.get("samples", ())
                    if active_start <= sample["cycle"] <= active_end
                    and sample["cycle"] not in positive_cycles
                    and _value_at(enable, trace, sample["cycle"]) not in (0, None)]
    if false_cycles:
        failures.append(f"write_enable asserted on {len(false_cycles)} non-commit cycles")
    if any(_value_at(enable, trace, sample["cycle"]) is None
           for sample in trace.get("samples", ()) if sample["cycle"] in positive_cycles):
        failures.append("unresolved expression leaf at a commit")
    if semantics == "architectural_write" and evidence_classes != set(WRITE_CLASSES):
        failures.append("incomplete RV32I write-class coverage")
    if semantics == "validated_write_interface" and not evidence.get("partial_passed"):
        failures.append("minimum partial write-interface coverage was not met")
    return {"passed": not failures, "failed_checks": list(dict.fromkeys(failures)),
            "validated_instruction_classes": sorted(selected_classes) if not failures else [],
            "checked_writes": len(records)}


def synthesize_architectural_interface(trace, evidence, candidates, word_width, seed=None):
    """Fit independent role expressions without weakening confirmation requirements."""
    if not (evidence.get("passed") or evidence.get("partial_passed")):
        return None, {"passed": False, "failed_checks":
                      evidence.get("hard_failed_checks") or evidence.get("failed_checks", [])}
    leaves = list(_leaves(candidates))
    address_options = _matching_address_options(trace, evidence, leaves, seed=seed)
    data_options = _matching_data_options(trace, evidence, leaves, word_width, seed=seed)
    enable_options = _enable_options(trace, evidence, leaves, seed=seed)
    missing = []
    if not enable_options:
        missing.append("no bounded architectural write-enable expression")
    if not address_options:
        missing.append("no architectural destination signal")
    if not data_options:
        missing.append("no data source for every validated write class")
    if missing:
        return None, {"passed": False, "failure_stage": "synthesis",
                      "failed_checks": missing,
                      "role_option_counts": {"write_enable": len(enable_options),
                                             "write_addr": len(address_options),
                                             "write_data": len(data_options)}}

    semantics = "architectural_write" if evidence.get("passed") else "validated_write_interface"
    validated_classes = list(evidence.get("classes") or ())
    attempts = []
    for enable, address, data in product(enable_options, address_options, data_options):
        expressions = {
            "write_enable": enable["expression"],
            "write_addr": address["expression"],
            "write_data": data["expression"],
        }
        offsets = {
            "write_enable": enable["offset"],
            "write_addr": address["offset"],
            "write_data": data["offset"],
        }
        candidate = {
            "status": "confirmed_interface",
            "score": 96 if semantics == "architectural_write" else 88,
            "confidence": "high" if semantics == "architectural_write" else "medium",
            "interface_semantics": semantics,
            "expression_version": ARCHITECTURAL_EXPRESSION_VERSION,
            "validated_instruction_classes": validated_classes,
            "missing_instruction_classes": sorted(set(WRITE_CLASSES) - set(validated_classes)),
            "role_expressions": expressions,
            "role_sources": {
                role: "signal" if expression.get("op") == "signal" else "expression"
                for role, expression in expressions.items()
            },
            "regfile_path": candidates.get("regfile_path"),
            "write_enable": f"{EXPRESSION_PREFIX}write_enable",
            "write_addr": f"{EXPRESSION_PREFIX}write_addr",
            "write_data": f"{EXPRESSION_PREFIX}write_data",
            "timing_offset": offsets["write_enable"],
            **{f"{role}_timing_offset": offsets[role] for role in ROLES},
            "reasons": [
                "all seven RV32I write classes matched" if semantics == "architectural_write"
                else "minimum write classes and negative controls matched",
                "write-interface roles were aligned independently",
            ],
            "failed_checks": [],
        }
        validation = validate_architectural_interface(candidate, trace, evidence, word_width)
        if validation["passed"]:
            return candidate, validation
        attempts.extend(validation["failed_checks"][:3])
        if len(attempts) >= 24:
            break
    return None, {"passed": False, "failure_stage": "validation",
                  "failed_checks": list(dict.fromkeys(attempts))}
