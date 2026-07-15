try:
    from ..riscv.encoding import ADDI
except ImportError:
    from riscv.encoding import ADDI
from .model import ExpectedWrite, ProgramSpec

_values = (0x135, 0x246, 0x357, 0x468, 0x579, 0x68A)
CYCLE_SIGNATURE = ProgramSpec(
    name="cycle_signature",
    instructions={index * 4: ADDI(5 + index, 0, value) for index, value in enumerate(_values)},
    expected_writes=tuple(ExpectedWrite(index * 4, 5 + index, value) for index, value in enumerate(_values)),
    loop_offset=0x30,
    loop_base_addresses=(0x80, 0x200),
)
