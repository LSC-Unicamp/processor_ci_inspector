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
class ProgramSpec:
    name: str
    instructions: dict
    expected_writes: tuple = ()
    initial_memory: dict = field(default_factory=dict)
    base_addresses: tuple = (0x40, 0x80, 0x200)
    loop_offset: int = None
    loop_base_addresses: tuple = None
    dependency_kind: str = None
    consumer_offset: int = None
    pair_role: str = None

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
        return image

    def entries(self):
        return tuple({"offset": item.offset, "reg": item.register, "value": item.value, "role": item.role} for item in self.expected_writes)
