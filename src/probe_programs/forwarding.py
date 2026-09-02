from dataclasses import replace

try:
    from ..riscv.encoding import ADD, ADDI, LW, NOP, SUB, SW
except ImportError:
    from riscv.encoding import ADD, ADDI, LW, NOP, SUB, SW
from .model import ExpectedWrite, OperandObservation, ProgramSpec


FORWARDING_PROBES = {
    "alu_to_alu": ProgramSpec(
        "alu_to_alu",
        {0: ADDI(1, 0, 10), 4: ADDI(2, 0, 20), 8: ADD(3, 1, 2), 12: SUB(4, 3, 1), 16: ADD(5, 4, 3), 20: ADDI(6, 5, 1)},
        tuple(ExpectedWrite(o, r, v, "producer" if o < 8 else "dependent") for o, r, v in ((0,1,10),(4,2,20),(8,3,30),(12,4,20),(16,5,50),(20,6,51))),
        loop_offset=0x20,
        dependency_kind="register_raw",
    ),
    "alu_to_store_data": ProgramSpec(
        "alu_to_store_data",
        {0: ADDI(1, 0, 51), 4: SW(1, 0, 0), 8: LW(2, 0, 0)},
        (ExpectedWrite(0, 1, 51, "producer"), ExpectedWrite(8, 2, 51, "verification")),
        dependency_kind="store_data_raw",
    ),
    "alu_to_store_address": ProgramSpec(
        "alu_to_store_address",
        {0: ADDI(1, 0, 64), 4: ADDI(2, 0, 85), 8: SW(2, 1, 0), 12: LW(3, 1, 0)},
        (ExpectedWrite(0, 1, 64, "address_producer"), ExpectedWrite(4, 2, 85, "data_setup"), ExpectedWrite(12, 3, 85, "verification")),
        dependency_kind="store_address_raw",
    ),
    "load_to_alu": ProgramSpec(
        "load_to_alu",
        {0: LW(1, 0, 0), 4: ADD(2, 1, 1)},
        (ExpectedWrite(0, 1, 37, "producer"), ExpectedWrite(4, 2, 74, "dependent")),
        initial_memory={0: 37},
        dependency_kind="load_use_raw",
    ),
    "load_to_store_data": ProgramSpec(
        "load_to_store_data",
        {0: LW(3, 0, 0), 4: SW(3, 0, 64)},
        (ExpectedWrite(0, 3, 61, "producer"),),
        initial_memory={0: 61},
        dependency_kind="load_store_data_raw",
        consumer_offset=4,
        expected_store_address=64,
        expected_store_value=61,
    ),
    "load_to_store_address": ProgramSpec(
        "load_to_store_address",
        {0: LW(3, 0, 0), 4: SW(0, 3, 0)},
        (ExpectedWrite(0, 3, 64, "producer"),),
        initial_memory={0: 64},
        dependency_kind="load_store_address_raw",
        consumer_offset=4,
        expected_store_address=64,
        expected_store_value=0,
    ),
}


def forwarding_distance_variant(name, gap):
    """Build the legacy focused view from the discriminated dependent probe."""
    gap = max(0, int(gap))
    if name in (
        "alu_to_alu", "alu_to_store_data", "alu_to_store_address",
        "load_to_alu", "load_to_store_data", "load_to_store_address",
    ):
        dependent, _ = forwarding_probe_pair(name, gap=gap, variant=gap % 5)
        return replace(
            dependent,
            name=f"{name}_gap_{gap}",
            pair_role=None,
        )
    # Kept as a defensive compatibility path for callers that expect KeyError
    # below rather than during pair construction.
    nops = {4 * (index + 1): NOP for index in range(gap)}
    consumer = 4 * (gap + 1)
    if name == "alu_to_alu":
        producer_value = 10 + gap
        instructions = {0: ADDI(1, 0, producer_value), **nops, consumer: ADDI(2, 1, 1)}
        writes = (ExpectedWrite(0, 1, producer_value, "producer"), ExpectedWrite(consumer, 2, producer_value + 1, "dependent"))
        memory = {}
    elif name == "load_to_alu":
        load_value = 37 + gap
        instructions = {0: LW(1, 0, 0), **nops, consumer: ADD(2, 1, 1)}
        writes = (ExpectedWrite(0, 1, load_value, "producer"), ExpectedWrite(consumer, 2, load_value * 2, "dependent"))
        memory = {0: load_value}
    elif name == "alu_to_store_data":
        store_value = 51 + gap
        instructions = {0: ADDI(1, 0, store_value), **nops, consumer: SW(1, 0, 0), consumer + 4: LW(2, 0, 0)}
        writes = (ExpectedWrite(0, 1, store_value, "producer"), ExpectedWrite(consumer + 4, 2, store_value, "verification"))
        memory = {}
    elif name == "alu_to_store_address":
        address = 64 + gap * 4
        store_value = 85 + gap
        instructions = {0: ADDI(2, 0, store_value), 4: ADDI(1, 0, address)}
        instructions.update({8 + 4 * index: NOP for index in range(gap)})
        consumer = 8 + 4 * gap
        instructions.update({consumer: SW(2, 1, 0), consumer + 4: LW(3, 1, 0)})
        writes = (ExpectedWrite(0, 2, store_value, "data_setup"), ExpectedWrite(4, 1, address, "address_producer"), ExpectedWrite(consumer + 4, 3, store_value, "verification"))
        memory = {}
    else:
        raise KeyError(name)
    return ProgramSpec(
        name=f"{name}_gap_{gap}",
        instructions=instructions,
        expected_writes=writes,
        initial_memory=memory,
        dependency_kind=FORWARDING_PROBES[name].dependency_kind,
        consumer_offset=consumer,
    )


def forwarding_probe_pair(name, gap=0, variant=0, spacer_kind="nop"):
    """Return a semantically discriminated dependent/control probe pair."""
    gap = max(0, int(gap))
    variant = max(0, int(variant)) % 5
    spacer_kind = str(spacer_kind).lower()
    if spacer_kind not in {"nop", "independent"}:
        raise ValueError(f"unsupported forwarding spacer kind: {spacer_kind}")
    if spacer_kind == "independent" and gap > 8:
        raise ValueError("independent forwarding gaps are limited to eight")
    if name not in (
        "alu_to_alu", "alu_to_store_data", "alu_to_store_address",
        "load_to_alu", "load_to_store_data", "load_to_store_address",
    ):
        raise KeyError(name)

    producer_register = (1, 4, 7, 10, 13)[variant]
    control_register = producer_register + 1
    result_register = producer_register + 2
    register_ids = {
        producer_register, control_register, result_register,
    }
    filler_registers = (
        tuple(
            register for register in range(1, 16)
            if register not in register_ids
        )[:gap]
        if spacer_kind == "independent" else ()
    )
    if spacer_kind == "independent" and len(filler_registers) != gap:
        raise AssertionError("insufficient x1-x15 independent filler registers")
    all_register_ids = register_ids | set(filler_registers)

    def semantic_value(seed, used=()):
        used = set(used)
        for value in range(int(seed), 0x7FF):
            if (value & 0x1F) not in all_register_ids and value not in used:
                return value
        raise AssertionError("unable to construct a discriminated immediate")

    producer = 12
    consumer = 16 + gap * 4
    middle = {16 + 4 * index: NOP for index in range(gap)}
    producer_value = semantic_value(0x120 + 7 * variant)
    control_value = semantic_value(
        0x220 + 7 * variant, {producer_value},
    )
    poison_value = semantic_value(
        0x320 + 7 * variant, {producer_value, control_value},
    )
    alu_immediate = next(
        immediate
        for immediate in range(0x20 + 3 * variant, 0x7FF)
        if (immediate & 0x1F) not in all_register_ids
        and ((producer_value + immediate) & 0x1F) not in all_register_ids
        and ((control_value + immediate) & 0x1F) not in all_register_ids
        and immediate not in {producer_value, control_value, poison_value}
    )
    marker_value = semantic_value(
        0x420 + 7 * variant,
        {producer_value, control_value, poison_value, alu_immediate},
    )
    filler_values = []
    used_semantic_values = {
        producer_value, control_value, poison_value,
        alu_immediate, marker_value,
    }
    for index, _ in enumerate(filler_registers):
        value = semantic_value(
            0x520 + 17 * variant + 7 * index,
            used_semantic_values,
        )
        filler_values.append(value)
        used_semantic_values.add(value)
    filler_values = tuple(filler_values)
    common = {
        0: ADDI(producer_register, 0, poison_value),
        4: ADDI(control_register, 0, control_value),
        8: NOP,
    }
    common.update(
        {
            16 + 4 * index: ADDI(register, 0, value)
            for index, (register, value) in enumerate(zip(
                filler_registers, filler_values,
            ))
        }
        if spacer_kind == "independent" else middle
    )
    if name.startswith("alu_to_"):
        common[producer] = ADDI(producer_register, 0, producer_value)
        memory = {}
    else:
        common[producer] = LW(producer_register, 0, 0)
        memory = {0: producer_value}

    dependent_store = control_store = None
    immediate_value = None
    effective_address = None
    if name.endswith("_to_alu"):
        immediate_value = alu_immediate
        dependent_instructions = {
            **common,
            consumer: ADDI(
                result_register, producer_register, immediate_value,
            ),
        }
        control_instructions = {
            **common,
            consumer: ADDI(
                result_register, control_register, immediate_value,
            ),
        }
        dependent_result = producer_value + immediate_value
        control_result = control_value + immediate_value
        dependent_writes = (
            ExpectedWrite(
                producer, producer_register, producer_value, "producer",
            ),
            ExpectedWrite(
                consumer, result_register, dependent_result, "consumer",
            ),
        )
        control_writes = (
            ExpectedWrite(
                producer, producer_register, producer_value, "producer",
            ),
            ExpectedWrite(
                consumer, result_register, control_result, "consumer",
            ),
        )
    elif name.endswith("store_data"):
        immediate_value = next(
            value for value in range(0x80 + 0x10 * variant, 0x7FC, 4)
            if (value & 0x1F) not in all_register_ids
        )
        effective_address = immediate_value
        marker = consumer + 4
        dependent_instructions = {
            **common,
            consumer: SW(producer_register, 0, immediate_value),
            marker: ADDI(result_register, 0, marker_value),
        }
        control_instructions = {
            **common,
            consumer: SW(control_register, 0, immediate_value),
            marker: ADDI(result_register, 0, marker_value),
        }
        dependent_writes = (
            ExpectedWrite(
                producer, producer_register, producer_value, "producer",
            ),
            ExpectedWrite(
                marker, result_register, marker_value, "completion",
            ),
        )
        control_writes = tuple(dependent_writes)
        dependent_store = (effective_address, producer_value)
        control_store = (effective_address, control_value)
        memory = {**memory, effective_address: 0xDEADBEEF}
    else:
        effective_address = 0x180 + 0x20 * variant
        allowed_offsets = [
            offset for offset in range(4, 64, 4)
            if (offset & 0x1F) not in all_register_ids
            and ((effective_address - offset) & 0x1F)
            not in all_register_ids
        ]
        if len(allowed_offsets) < 2:
            raise AssertionError("unable to discriminate store base/offset")
        dependent_offset, control_offset = allowed_offsets[:2]
        dependent_base = effective_address - dependent_offset
        control_base = effective_address - control_offset
        producer_value = dependent_base
        control_value = control_base
        # Rebuild the common setup after choosing the address operands.
        common[0] = ADDI(producer_register, 0, poison_value)
        common[4] = ADDI(control_register, 0, control_value)
        if name.startswith("alu_to_"):
            common[producer] = ADDI(
                producer_register, 0, producer_value,
            )
        else:
            common[producer] = LW(producer_register, 0, 0)
            memory = {0: producer_value}
        marker = consumer + 4
        dependent_instructions = {
            **common,
            consumer: SW(0, producer_register, dependent_offset),
            marker: ADDI(result_register, 0, marker_value),
        }
        control_instructions = {
            **common,
            consumer: SW(0, control_register, control_offset),
            marker: ADDI(result_register, 0, marker_value),
        }
        dependent_writes = (
            ExpectedWrite(
                producer, producer_register, producer_value, "producer",
            ),
            ExpectedWrite(
                marker, result_register, marker_value, "completion",
            ),
        )
        control_writes = tuple(dependent_writes)
        dependent_store = (effective_address, 0)
        control_store = (effective_address, 0)
        memory = {**memory, effective_address: 0xDEADBEEF}

    def build(role, instructions, writes):
        store = None
        if name in (
            "alu_to_store_data", "alu_to_store_address",
            "load_to_store_data", "load_to_store_address",
        ):
            store = dependent_store if role == "dependent" else control_store
        producer_write = next(item for item in writes if item.offset == producer)
        producer_instruction = instructions[producer]
        producer_rs1 = (producer_instruction >> 15) & 0x1F
        consumer_instruction = instructions[consumer]
        opcode = consumer_instruction & 0x7F
        consumer_rs1 = (consumer_instruction >> 15) & 0x1F
        consumer_rs2 = (consumer_instruction >> 20) & 0x1F
        filler_writes = tuple(
            ExpectedWrite(
                16 + 4 * index, register, value,
                "independent_filler",
            )
            for index, (register, value) in enumerate(zip(
                filler_registers, filler_values,
            ))
        )
        writes = tuple(sorted(
            (*writes, *filler_writes),
            key=lambda item: item.offset,
        ))
        observations = [OperandObservation(
            producer, "producer", producer_rs1, 0, "execute",
            destination_register=producer_write.register,
            result_value=producer_write.value,
            poison_value=poison_value,
            immediate_value=(
                producer_value if opcode != 0x03 else 0
            ),
            non_source_registers=(
                control_register, result_register, *filler_registers,
            ),
            forbidden_operand_values=(
                poison_value, control_value, marker_value, *filler_values,
            ),
        )]
        if opcode == 0x23:
            store_immediate = (
                ((consumer_instruction >> 25) & 0x7F) << 5
                | ((consumer_instruction >> 7) & 0x1F)
            )
            if store_immediate & 0x800:
                store_immediate -= 0x1000
            store_base_value = (store[0] - store_immediate) & 0xFFFFFFFF
            correct_operands = {store_base_value, store[1]}
            observations.append(OperandObservation(
                consumer, "consumer",
                consumer_rs1, store_base_value, "store_address",
                consumer_rs2, store[1], "store_data",
                poison_value=poison_value,
                immediate_value=store_immediate,
                effective_address=store[0],
                non_source_registers=tuple(
                    register for register in all_register_ids
                    if register not in {consumer_rs1, consumer_rs2}
                ),
                forbidden_operand_values=tuple(
                    value for value in dict.fromkeys((
                    poison_value, producer_value, marker_value,
                    store[0],
                    control_value if role == "dependent"
                    else producer_value,
                    *filler_values,
                    )) if value not in correct_operands
                ),
            ))
        elif opcode == 0x13:
            result = next(
                item.value for item in writes if item.offset == consumer
            )
            immediate = (consumer_instruction >> 20) & 0xFFF
            if immediate & 0x800:
                immediate -= 0x1000
            source_value = result - immediate
            observations.append(OperandObservation(
                consumer, "consumer", consumer_rs1,
                source_value, "execute",
                destination_register=result_register,
                result_value=result,
                poison_value=poison_value,
                immediate_value=immediate,
                non_source_registers=tuple(
                    register for register in all_register_ids
                    if register != consumer_rs1
                ),
                forbidden_operand_values=tuple(
                    value for value in dict.fromkeys((
                    poison_value, result, immediate,
                    control_value if role == "dependent"
                    else producer_value,
                    *filler_values,
                    )) if value != source_value
                ),
            ))
        else:
            result = next(item.value for item in writes if item.offset == consumer)
            source_value = result // 2
            observations.append(OperandObservation(
                consumer, "consumer", consumer_rs1, source_value, "execute",
                consumer_rs2, source_value, "execute", poison_value=poison_value,
            ))
        spec = ProgramSpec(
            name=(
                f"{name}_{role}_gap_{gap}_independent"
                if spacer_kind == "independent"
                else f"{name}_{role}_gap_{gap}"
            ),
            instructions=instructions,
            expected_writes=writes,
            initial_memory=memory,
            dependency_kind=FORWARDING_PROBES[name].dependency_kind,
            producer_offset=producer,
            consumer_offset=consumer,
            pair_role=role,
            forwarding_variant=variant,
            forwarding_gap=gap,
            spacer_kind=spacer_kind,
            filler_registers=filler_registers,
            filler_values=filler_values,
            expected_store_address=None if store is None else store[0],
            expected_store_value=None if store is None else store[1],
            operand_observations=tuple(observations),
        )
        semantic_values = {
            poison_value, producer_value, control_value, marker_value,
            *filler_values,
        }
        semantic_values.update(
            value for observation in observations
            for value in (
                observation.rs1_value, observation.rs2_value,
                observation.result_value, observation.immediate_value,
            )
            if value is not None
        )
        assert all(
            (int(value) & 0x1F) not in all_register_ids
            for value in semantic_values
        ), "semantic value aliases a variant register ID"
        return spec

    return build("dependent", dependent_instructions, dependent_writes), build("control", control_instructions, control_writes)
