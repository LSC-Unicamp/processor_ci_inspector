"""Programs that test correct hazard handling without claiming forwarding."""

try:
    from ..riscv.encoding import ADDI, LW, NOP, SW
except ImportError:
    from riscv.encoding import ADDI, LW, NOP, SW

from .model import ExpectedWrite, ProgramSpec


def store_to_load_hazard_probe(gap=0):
    """Check that a younger load observes an older same-address store."""
    gap = max(0, int(gap))
    value = 90 + gap
    instructions = {0: ADDI(1, 0, value), 4: SW(1, 0, 0)}
    instructions.update({8 + 4 * index: NOP for index in range(gap)})
    consumer = 8 + 4 * gap
    instructions[consumer] = LW(2, 0, 0)
    return ProgramSpec(
        name=f"store_to_load_hazard_gap_{gap}",
        instructions=instructions,
        expected_writes=(
            ExpectedWrite(0, 1, value, "producer"),
            ExpectedWrite(consumer, 2, value, "verification"),
        ),
        dependency_kind="memory_ordering_hazard",
        consumer_offset=consumer,
    )
