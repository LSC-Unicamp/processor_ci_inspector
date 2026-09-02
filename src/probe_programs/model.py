from dataclasses import dataclass, field

try:
    from ..riscv.encoding import JAL, NOP
except ImportError:
    from riscv.encoding import JAL, NOP


@dataclass(frozen=True)
class ExpectedWrite:
    offset: int
    register: int
    value: int
    role: str = "result"


@dataclass(frozen=True)
class OperandObservation:
    """Expected operand/result values used to validate internal probe signals."""

    offset: int
    role: str
    rs1_register: int = None
    rs1_value: int = None
    rs1_use: str = None
    rs2_register: int = None
    rs2_value: int = None
    rs2_use: str = None
    destination_register: int = None
    result_value: int = None
    poison_value: int = None
    immediate_value: int = None
    effective_address: int = None
    non_source_registers: tuple = ()
    forbidden_operand_values: tuple = ()


@dataclass(frozen=True)
class ProgramSpec:
    name: str
    instructions: dict
    expected_writes: tuple = ()
    initial_memory: dict = field(default_factory=dict)
    base_addresses: tuple = (0x40, 0x80, 0x200)
    entry_addresses: tuple = (0x40, 0x80, 0x200)
    entry_trampoline_target: int = None
    loop_offset: int = None
    loop_base_addresses: tuple = None
    dependency_kind: str = None
    producer_offset: int = None
    consumer_offset: int = None
    pair_role: str = None
    forwarding_variant: int = None
    forwarding_gap: int = 0
    spacer_kind: str = "nop"
    filler_registers: tuple = ()
    filler_values: tuple = ()
    expected_store_address: int = None
    expected_store_value: int = None
    control_flow: dict = field(default_factory=dict)
    operand_observations: tuple = ()
    calibration_load_address: int = None
    calibration_kind: str = None
    calibration_variant: int = None
    calibration_relocation_base: int = None
    calibration_relocation_origin: int = None
    calibration_requested_base: int = None
    calibration_landing_index: int = None
    calibration_sections: dict = field(default_factory=dict)
    handshake_role: str = None
    response_delay_cycles: int = 0

    def image(self):
        image = {address: NOP for address in range(0, 0x80, 4)}
        end = self.loop_offset
        if end is None:
            end = max(self.instructions, default=-4) + 4
        for base in self.base_addresses:
            for offset, instruction in self.instructions.items():
                image[base + offset] = instruction
            if self.loop_base_addresses is None or base in self.loop_base_addresses:
                image[base + end] = JAL(0, 0)
        explicit_trampoline = self.entry_trampoline_target is not None
        primary_base = (
            int(self.entry_trampoline_target)
            if explicit_trampoline
            else int(self.base_addresses[0])
            if self.base_addresses else None
        )
        if primary_base is not None:
            executable_addresses = {
                int(base) + int(offset)
                for base in self.base_addresses
                for offset in self.instructions
            }
            covered = tuple(
                (int(base), int(base) + int(end))
                for base in self.base_addresses
            )
            for entry in self.entry_addresses:
                entry = int(entry)
                if (
                    entry == primary_base
                    or entry in executable_addresses
                    or (
                        not explicit_trampoline
                        and any(
                            start <= entry <= finish
                            for start, finish in covered
                        )
                    )
                ):
                    continue
                image[entry] = JAL(0, primary_base - entry)
        return image

    def entries(self):
        return tuple({"offset": item.offset, "reg": item.register, "value": item.value, "role": item.role} for item in self.expected_writes)

    def operand_entries(self):
        return {item.offset: item for item in self.operand_observations}
