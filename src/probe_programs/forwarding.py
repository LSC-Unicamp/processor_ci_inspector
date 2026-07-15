try:
    from ..riscv.encoding import ADD, ADDI, LW, NOP, SUB, SW
except ImportError:
    from riscv.encoding import ADD, ADDI, LW, NOP, SUB, SW
from .model import ExpectedWrite, ProgramSpec


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
    "store_to_load": ProgramSpec(
        "store_to_load",
        {0: ADDI(1, 0, 90), 4: SW(1, 0, 0), 8: LW(2, 0, 0)},
        (ExpectedWrite(0, 1, 90, "producer"), ExpectedWrite(8, 2, 90, "verification")),
        dependency_kind="memory_raw",
    ),
}


def forwarding_distance_variant(name, gap):
    """Build a focused producer/consumer probe with ``gap`` intervening NOPs."""
    gap = max(0, int(gap))
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
    elif name == "store_to_load":
        store_value = 90 + gap
        instructions = {0: ADDI(1, 0, store_value), 4: SW(1, 0, 0)}
        instructions.update({8 + 4 * index: NOP for index in range(gap)})
        consumer = 8 + 4 * gap
        instructions[consumer] = LW(2, 0, 0)
        writes = (ExpectedWrite(0, 1, store_value, "producer"), ExpectedWrite(consumer, 2, store_value, "verification"))
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


def forwarding_probe_pair(name, gap=0, variant=0):
    """Return layout-matched dependent and dependency-free control programs."""
    gap = max(0, int(gap))
    variant = max(0, int(variant))
    if name not in ("alu_to_alu", "alu_to_store_data", "alu_to_store_address", "load_to_alu"):
        raise KeyError(name)

    if name == "alu_to_alu":
        value = 10 + variant
        producer = 0
        consumer = 4 * (gap + 1)
        middle = {4 * (index + 1): NOP for index in range(gap)}
        dependent_instructions = {producer: ADDI(1, 0, value), **middle, consumer: ADDI(2, 1, 1)}
        control_instructions = {producer: ADDI(1, 0, value + 100), **middle, consumer: ADDI(2, 0, 1 + variant)}
        dependent_writes = (ExpectedWrite(producer, 1, value, "producer"), ExpectedWrite(consumer, 2, value + 1, "consumer"))
        control_writes = (ExpectedWrite(producer, 1, value + 100, "producer"), ExpectedWrite(consumer, 2, 1 + variant, "consumer"))
        memory = {}
    elif name == "load_to_alu":
        value = 37 + variant
        producer = 4
        consumer = 8 + gap * 4
        middle = {8 + 4 * index: NOP for index in range(gap)}
        dependent_common = {0: ADDI(3, 0, value), producer: LW(1, 0, 0), **middle}
        control_common = {0: ADDI(3, 0, value + 50), producer: LW(1, 0, 4), **middle}
        dependent_instructions = {**dependent_common, consumer: ADD(2, 1, 1)}
        control_instructions = {**control_common, consumer: ADD(2, 3, 3)}
        dependent_writes = (ExpectedWrite(producer, 1, value, "producer"), ExpectedWrite(consumer, 2, value * 2, "consumer"))
        control_writes = (ExpectedWrite(producer, 1, value + 100, "producer"), ExpectedWrite(consumer, 2, (value + 50) * 2, "consumer"))
        memory = {0: value, 4: value + 100}
    elif name == "alu_to_store_data":
        value = 51 + variant
        producer = 4
        consumer = 8 + gap * 4
        middle = {8 + 4 * index: NOP for index in range(gap)}
        dependent_common = {0: ADDI(3, 0, value), producer: ADDI(1, 0, value), **middle}
        control_common = {0: ADDI(3, 0, value + 100), producer: ADDI(1, 0, value + 200), **middle}
        dependent_instructions = {**dependent_common, consumer: SW(1, 0, 0), consumer + 4: LW(2, 0, 0)}
        control_instructions = {**control_common, consumer: SW(3, 0, 0), consumer + 4: LW(2, 0, 0)}
        dependent_writes = (ExpectedWrite(producer, 1, value, "producer"), ExpectedWrite(consumer + 4, 2, value, "verification"))
        control_writes = (ExpectedWrite(producer, 1, value + 200, "producer"), ExpectedWrite(consumer + 4, 2, value + 100, "verification"))
        memory = {}
    else:
        address = 64 + variant * 4
        value = 85 + variant
        producer = 4
        consumer = 12 + gap * 4
        middle = {12 + 4 * index: NOP for index in range(gap)}
        dependent_common = {0: ADDI(3, 0, address), producer: ADDI(1, 0, address), 8: ADDI(2, 0, value), **middle}
        control_common = {0: ADDI(3, 0, address + 128), producer: ADDI(1, 0, address + 256), 8: ADDI(2, 0, value + 100), **middle}
        dependent_instructions = {**dependent_common, consumer: SW(2, 1, 0), consumer + 4: LW(4, 1, 0)}
        control_instructions = {**control_common, consumer: SW(2, 3, 0), consumer + 4: LW(4, 3, 0)}
        dependent_writes = (ExpectedWrite(producer, 1, address, "producer"), ExpectedWrite(consumer + 4, 4, value, "verification"))
        control_writes = (ExpectedWrite(producer, 1, address + 256, "producer"), ExpectedWrite(consumer + 4, 4, value + 100, "verification"))
        memory = {}

    def build(role, instructions, writes):
        return ProgramSpec(
            name=f"{name}_{role}_gap_{gap}",
            instructions=instructions,
            expected_writes=writes,
            initial_memory=memory,
            dependency_kind=FORWARDING_PROBES[name].dependency_kind,
            consumer_offset=consumer,
            pair_role=role,
        )

    return build("dependent", dependent_instructions, dependent_writes), build("control", control_instructions, control_writes)
