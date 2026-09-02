"""Instruction programs used to characterize branch-prediction hardware.

The probes are intentionally behavioral.  A testbench should combine the
architectural checks in ``expected_writes`` with the instruction-fetch trace.
The fetch trace, rather than final register values, reveals prediction,
wrong-path fetches, redirects, and predictor warm-up.

All branch and jump immediates are byte offsets relative to the instruction PC,
matching the encoding helpers used by the rest of the test ecosystem.
"""

from dataclasses import dataclass
from typing import Callable, Iterable

try:
    from ..riscv.encoding import (
        ADD,
        ADDI,
        ANDI,
        AUIPC,
        BEQ,
        BGE,
        BGEU,
        BLT,
        BLTU,
        BNE,
        JAL,
        JALR,
        LW,
        NOP,
        SLLI,
        XORI,
    )
except ImportError:
    from riscv.encoding import (
        ADD,
        ADDI,
        ANDI,
        AUIPC,
        BEQ,
        BGE,
        BGEU,
        BLT,
        BLTU,
        BNE,
        JAL,
        JALR,
        LW,
        NOP,
        SLLI,
        XORI,
    )

from .model import ExpectedWrite, ProgramSpec


BranchEncoder = Callable[[int, int, int], int]

@dataclass(frozen=True)
class _Fixup:
    kind: str
    pc: int
    label: str
    encoder: Callable | None = None
    operands: tuple = ()
    base_pc: int | None = None


class _Assembler:
    """Very small label-aware assembler for the probe generators."""

    def __init__(self):
        self.pc = 0
        self.instructions = {}
        self.labels = {}
        self.fixups = []

    def label(self, name):
        if name in self.labels:
            raise ValueError(f"duplicate label: {name}")
        self.labels[name] = self.pc

    def emit(self, instruction):
        offset = self.pc
        self.instructions[offset] = instruction
        self.pc += 4
        return offset

    def branch(self, encoder, rs1, rs2, label):
        offset = self.emit(None)
        self.fixups.append(_Fixup("branch", offset, label, encoder, (rs1, rs2)))
        return offset

    def jal(self, rd, label):
        offset = self.emit(None)
        self.fixups.append(_Fixup("jal", offset, label, JAL, (rd,)))
        return offset

    def load_address(self, rd, label):
        """Load a nearby code label with AUIPC+ADDI.

        Probe images are small enough that the label displacement fits the
        signed 12-bit ADDI immediate.  This remains position-independent when
        ProgramSpec replicates the image at several base addresses.
        """
        auipc_pc = self.emit(AUIPC(rd, 0))
        addi_pc = self.emit(None)
        self.fixups.append(
            _Fixup("pc_relative_addi", addi_pc, label, ADDI, (rd, rd), auipc_pc)
        )
        return auipc_pc

    def resolve(self):
        result = dict(self.instructions)
        for fixup in self.fixups:
            if fixup.label not in self.labels:
                raise ValueError(f"unknown label: {fixup.label}")
            target = self.labels[fixup.label]
            if fixup.kind == "branch":
                result[fixup.pc] = fixup.encoder(
                    *fixup.operands, target - fixup.pc
                )
            elif fixup.kind == "jal":
                result[fixup.pc] = JAL(*fixup.operands, target - fixup.pc)
            elif fixup.kind == "pc_relative_addi":
                displacement = target - fixup.base_pc
                if not -2048 <= displacement <= 2047:
                    raise ValueError(
                        f"label {fixup.label} is too far for AUIPC(0)+ADDI: "
                        f"{displacement} bytes"
                    )
                result[fixup.pc] = ADDI(*fixup.operands, displacement)
            else:
                raise ValueError(f"unknown fixup kind: {fixup.kind}")
        if any(instruction is None for instruction in result.values()):
            raise ValueError("unresolved instruction fixup")
        return result


def _lfsr_bits(length, seed=0xACE1):
    """Generate a deterministic, approximately balanced nontrivial sequence."""
    length = max(1, int(length))
    state = int(seed) & 0xFFFF or 1
    result = []
    for _ in range(length):
        result.append(bool(state & 1))
        feedback = ((state >> 0) ^ (state >> 2) ^ (state >> 3) ^ (state >> 5)) & 1
        state = (state >> 1) | (feedback << 15)
    return tuple(result)


def _outcome_memory(outcomes, base=0):
    """Encode True=taken as zero, because probes use BEQ(sample, x0)."""
    return {base + 4 * index: 0 if taken else 1 for index, taken in enumerate(outcomes)}


def _emit_balanced_branch(builder, encoder, rs1, rs2, prefix, padding_words=8):
    """Emit equal-length paths with the target outside sequential prefetch.

    A target at PC+8 is fetched by ordinary frontend lookahead even when the
    branch is predicted not taken.  Keeping several inert words between the
    fall-through jump and the target makes an early target fetch meaningful
    behavioral evidence while both architectural paths still execute one JAL.
    """
    branch_pc = builder.branch(encoder, rs1, rs2, f"{prefix}_taken")
    builder.jal(0, f"{prefix}_join")
    for _ in range(max(1, int(padding_words))):
        builder.emit(NOP)
    builder.label(f"{prefix}_taken")
    builder.jal(0, f"{prefix}_join")
    builder.label(f"{prefix}_join")
    return branch_pc


def _emit_load_settle(builder, count=4):
    """Separate probe-control loads from dependent branches.

    Branch-predictor probes must not silently become load-use forwarding
    tests. Four inert instructions cover the deepest pipelines in the current
    integration set while preserving identical control-flow layouts.
    """
    for _ in range(max(0, int(count))):
        builder.emit(NOP)


def _finish(builder, marker, marker_register=31):
    marker_pc = builder.emit(ADDI(marker_register, 0, marker))
    return marker_pc, builder.pc


def _base_addresses(loop_offset):
    """Choose code bases whose replicated images cannot overlap.

    Preserve the ecosystem's original (0x40, 0x80, 0x200) bases for probes
    that fit in one 64-byte slot. Larger probes use one canonical image at
    0x400; ProgramSpec.image installs boot-address trampolines so processors
    cannot enter the middle of an overlapping replica.
    """
    image_size = int(loop_offset) + 4
    if image_size <= 0x40:
        return (0x40, 0x80, 0x200)
    return (0x400,)


def _conditional_contract(instructions, offset, outcomes, warmup=0):
    instruction = instructions[offset]
    immediate = (
        (((instruction >> 31) & 1) << 12)
        | (((instruction >> 7) & 1) << 11)
        | (((instruction >> 25) & 0x3F) << 5)
        | (((instruction >> 8) & 0xF) << 1)
    )
    if immediate & 0x1000:
        immediate -= 0x2000
    target = offset + immediate
    return {
        "kind": "conditional", "offset": offset, "target": target,
        "fallthrough": offset + 4,
        "actual_outcomes": tuple(outcomes),
        "actual_targets": tuple(target if value else offset + 4 for value in outcomes),
        "warmup": warmup,
    }


def _emit_taken_branch_chain(builder, prefix, depth):
    """Emit ``depth`` always-taken conditional branches at distinct PCs."""
    for index in range(depth):
        next_label = f"{prefix}_{index}_next"
        builder.branch(BEQ, 0, 0, next_label)
        builder.emit(NOP)  # wrong-path instruction when the branch is predicted NT
        builder.label(next_label)


def long_history_sweep(distances=(0, 2, 4, 8, 16, 32, 64)):
    return tuple(long_history_probe(distance) for distance in distances)


def path_history_sweep(depths=(2, 4, 8, 12, 16, 24)):
    return tuple(path_history_probe(depth) for depth in depths)


def loop_trip_count_pair(stable_trip_count=37, changed_trip_count=41):
    """Return fixed-trip probes used to compare learned and changed counts."""
    return (
        loop_predictor_probe(stable_trip_count),
        loop_predictor_probe(changed_trip_count),
    )


def ras_pair(samples=64):
    """Return layout-equivalent standard-link and nonstandard-link probes."""
    return ras_probe(1, samples), ras_probe(10, samples)


def branch_resolution_pair():
    return (
        branch_resolution_probe(True, "branch_resolution_taken", 0x190),
        branch_resolution_probe(False, "branch_resolution_not_taken", 0x191),
    )


def power_of_two_alias_sweep(spacings=(64, 128, 256, 512), samples=32):
    return tuple(two_pc_alias_probe(spacing, samples) for spacing in spacings)


def ras_depth_sweep(depths=(1, 2, 4, 8), repetitions=8):
    return tuple(
        (nested_ras_probe(depth, 1, repetitions), nested_ras_probe(depth, 10, repetitions))
        for depth in depths
    )


def static_direction_probe(name, direction, taken):
    """Build one cold conditional branch for the static-policy matrix.

    ``direction`` is ``"forward"`` or ``"backward"``.  Run all four
    direction/outcome combinations before inferring always-taken,
    always-not-taken, or backward-taken/forward-not-taken behavior.
    """
    if direction not in ("forward", "backward"):
        raise ValueError("direction must be 'forward' or 'backward'")

    builder = _Assembler()
    builder.emit(ADDI(1, 0, 1))
    builder.emit(ADDI(2, 0, 1 if taken else 0))

    if direction == "forward":
        branch_pc = builder.branch(BEQ, 1, 2, "taken_path")
        not_taken_pc = builder.emit(ADDI(20, 0, 0x11))
        builder.jal(0, "join")
        builder.label("taken_path")
        taken_pc = builder.emit(ADDI(20, 0, 0x22))
        builder.label("join")
    else:
        # Jump over the backward target so that the conditional branch is cold
        # the first time it is encountered.
        builder.jal(0, "branch_site")
        builder.label("taken_path")
        taken_pc = builder.emit(ADDI(20, 0, 0x22))
        builder.jal(0, "join")
        builder.label("branch_site")
        branch_pc = builder.branch(BEQ, 1, 2, "taken_path")
        not_taken_pc = builder.emit(ADDI(20, 0, 0x11))
        builder.label("join")

    marker_pc, loop_offset = _finish(builder, 0x101)
    path_pc = taken_pc if taken else not_taken_pc
    path_value = 0x22 if taken else 0x11
    return ProgramSpec(
        name=name,
        instructions=builder.resolve(),
        expected_writes=(
            ExpectedWrite(path_pc, 20, path_value, "resolved_path"),
            ExpectedWrite(marker_pc, 31, 0x101, "completion"),
        ),
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_static_policy",
        consumer_offset=branch_pc,
        pair_role=f"{direction}_{'taken' if taken else 'not_taken'}",
    )


def direction_sequence_probe(
    name, outcomes, marker=0x110, warmup=0, settle_nops=0,
    load_settle_nops=4,
    path_padding_words=8,
):
    """Exercise one conditional branch PC with an explicit outcome sequence."""
    outcomes = tuple(bool(value) for value in outcomes)
    if not outcomes:
        raise ValueError("outcomes must not be empty")
    byte_length = 4 * len(outcomes)
    if byte_length > 2047:
        raise ValueError("outcome sequence is too long for the ADDI end pointer")

    builder = _Assembler()
    builder.emit(ADDI(1, 0, 0))            # sample pointer
    builder.emit(ADDI(2, 0, byte_length))  # end pointer
    builder.label("iteration")
    builder.emit(LW(3, 1, 0))
    _emit_load_settle(builder, load_settle_nops)
    builder.emit(ADDI(1, 1, 4))
    branch_pc = _emit_balanced_branch(
        builder, BEQ, 3, 0, "tested", padding_words=path_padding_words
    )
    for _ in range(max(0, int(settle_nops))):
        builder.emit(NOP)
    builder.branch(BNE, 1, 2, "iteration")
    marker_pc, loop_offset = _finish(builder, marker)
    instructions = builder.resolve()

    return ProgramSpec(
        name=name,
        instructions=instructions,
        expected_writes=(ExpectedWrite(marker_pc, 31, marker, "completion"),),
        initial_memory=_outcome_memory(outcomes),
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_direction_sequence",
        consumer_offset=branch_pc,
        control_flow={
            "family": "branch_direction_sequence",
            "settle_nops": max(0, int(settle_nops)),
            "load_settle_nops": max(0, int(load_settle_nops)),
            "path_padding_words": max(1, int(path_padding_words)),
            "primary_site": "primary",
            "sites": {"primary": _conditional_contract(instructions, branch_pc, outcomes, warmup=warmup)},
        },
    )


def branch_resolution_probe(taken, name=None, marker=None):
    """Cold branch whose decision depends immediately on a memory response.

    Any accepted path fetch before the load response is necessarily
    pre-resolution. Taken and not-taken variants preserve identical code
    layout and differ only in the initialized word and completion marker.
    """
    taken = bool(taken)
    marker = int(marker if marker is not None else (0x190 if taken else 0x191))
    builder = _Assembler()
    builder.emit(ADDI(1, 0, 0))
    load_pc = builder.emit(LW(3, 1, 0))
    branch_pc = _emit_balanced_branch(builder, BEQ, 3, 0, "resolution")
    marker_pc, loop_offset = _finish(builder, marker)
    instructions = builder.resolve()
    site = _conditional_contract(instructions, branch_pc, (taken,), warmup=0)
    return ProgramSpec(
        name=name or f"branch_resolution_{'taken' if taken else 'not_taken'}",
        instructions=instructions,
        expected_writes=(ExpectedWrite(marker_pc, 31, marker, "completion"),),
        initial_memory={0: 0 if taken else 1},
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_resolution_calibration",
        consumer_offset=branch_pc,
        pair_role="taken" if taken else "not_taken",
        control_flow={
            "family": "branch_resolution_calibration",
            "primary_site": "primary",
            "minimum_occurrence_coverage": 1.0,
            "resolution_barrier": {
                "kind": "dependency_load_response",
                "address": 0,
                "load_offset": load_pc,
                "branch_offset": branch_pc,
            },
            "sites": {"primary": site},
        },
    )


def two_pc_alias_probe(spacing=64, samples=32, name=None):
    """Alternate oppositely biased branches separated by a chosen PC distance.

    Both sites execute in one reset epoch.  If they alias in a direction table,
    training one site taken and the other not-taken causes measurable
    interference.  Power-of-two spacing variants expose index-bit boundaries.
    """
    spacing = max(64, int(spacing))
    spacing = ((spacing + 3) // 4) * 4
    samples = max(8, int(samples))
    byte_length = samples * 4
    builder = _Assembler()
    builder.emit(ADDI(1, 0, 0))
    builder.emit(ADDI(2, 0, byte_length))
    builder.label("iteration")
    builder.emit(LW(3, 1, 0))
    builder.emit(ADDI(1, 1, 4))
    site_a = _emit_balanced_branch(builder, BEQ, 0, 0, "alias_a")
    while builder.pc < site_a + spacing:
        builder.emit(NOP)
    site_b = _emit_balanced_branch(builder, BNE, 0, 0, "alias_b")
    builder.branch(BNE, 1, 2, "iteration")
    marker_pc, loop_offset = _finish(builder, 0x160 + (spacing.bit_length() & 0x1F))
    taken = (True,) * samples
    not_taken = (False,) * samples
    sites = {
        "site_a": _conditional_contract(builder.resolve(), site_a, taken, warmup=4),
        "site_b": _conditional_contract(builder.resolve(), site_b, not_taken, warmup=4),
    }
    return ProgramSpec(
        name=name or f"two_pc_alias_spacing_{spacing}",
        instructions=builder.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, 0x160 + (spacing.bit_length() & 0x1F), "completion"),),
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_pc_aliasing",
        consumer_offset=site_a,
        control_flow={
            "family": "branch_pc_aliasing",
            "primary_site": "site_a",
            "spacing": spacing,
            "sites": sites,
        },
    )


def paired_timing_probes(samples=64):
    """Equal-layout/equal-bias learnable and shuffled direction sequences."""
    samples = max(16, int(samples))
    samples += (-samples) % 4
    predictable = (True,) * (samples // 2) + (False,) * (samples // 2)
    shuffled = list(_lfsr_bits(samples, seed=0x9E37))
    # Preserve exactly the same taken/not-taken population as the predictable
    # member so static policies and resolved-branch costs cancel in the pair.
    order = sorted(range(samples), key=lambda index: (shuffled[index], index))
    balanced = [False] * samples
    for index in order[-(samples // 2):]:
        balanced[index] = True
    return (
        direction_sequence_probe("timing_learnable", predictable, marker=0x171, warmup=8),
        direction_sequence_probe("timing_shuffled_control", tuple(balanced), marker=0x172, warmup=8),
    )


def counter_hysteresis_probe(opposite_outcomes, train_length=4, name=None):
    """Train strongly taken, inject N outcomes, then probe taken again.

    Compare ``opposite_outcomes=1`` and ``opposite_outcomes=2``:
      * one-bit last-outcome predictors miss the final T after one N;
      * conventional two-bit counters retain T after one N, but switch after
        two consecutive N outcomes.
    """
    opposite_outcomes = max(1, int(opposite_outcomes))
    # Use enough taken outcomes to cover a cold strong-not-taken counter plus
    # a one-update read/write delay.  Two outcomes are theoretically enough
    # for an ideal synchronous counter, but real table RAMs can expose the old
    # value for an additional occurrence (ZC is one such implementation).
    train_length = max(4, int(train_length))
    outcomes = (True,) * train_length + (False,) * opposite_outcomes + (True,)
    spec = direction_sequence_probe(
        name or f"counter_hysteresis_{opposite_outcomes}",
        outcomes,
        marker=0x110 + opposite_outcomes,
        settle_nops=0,
        path_padding_words=1,
    )
    spec.control_flow.update({"train_length": train_length, "opposite_outcomes": opposite_outcomes})
    return spec


def local_history_probe(repetitions=24):
    """TTNN local pattern with a pseudorandom intervening distractor branch."""
    repetitions = max(4, int(repetitions))
    local_outcomes = (True, True, False, False) * repetitions
    distractor_outcomes = _lfsr_bits(len(local_outcomes), seed=0xBEEF)
    byte_length = 4 * len(local_outcomes)
    distractor_base = 0x400
    if byte_length > 1024:
        raise ValueError("local-history probe is too large for its memory layout")

    builder = _Assembler()
    builder.emit(ADDI(1, 0, 0))                 # local pointer
    builder.emit(ADDI(2, 0, distractor_base))   # distractor pointer
    builder.emit(ADDI(6, 0, byte_length))       # local end pointer
    builder.label("iteration")
    builder.emit(LW(3, 1, 0))
    builder.emit(LW(4, 2, 0))
    _emit_load_settle(builder)
    builder.emit(ADDI(1, 1, 4))
    builder.emit(ADDI(2, 2, 4))
    _emit_balanced_branch(builder, BEQ, 4, 0, "distractor")
    local_branch_pc = _emit_balanced_branch(builder, BEQ, 3, 0, "local")
    builder.branch(BNE, 1, 6, "iteration")
    marker_pc, loop_offset = _finish(builder, 0x121)

    memory = _outcome_memory(local_outcomes)
    memory.update(_outcome_memory(distractor_outcomes, distractor_base))
    return ProgramSpec(
        name="local_history",
        instructions=builder.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, 0x121, "completion"),),
        initial_memory=memory,
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_local_history",
        consumer_offset=local_branch_pc,
    )


def global_history_probe(samples=96):
    """Producer branch A reveals the otherwise pseudorandom outcome of B."""
    outcomes = _lfsr_bits(max(16, int(samples)), seed=0xD00D)
    byte_length = 4 * len(outcomes)

    builder = _Assembler()
    builder.emit(ADDI(1, 0, 0))
    builder.emit(ADDI(2, 0, byte_length))
    builder.label("iteration")
    builder.emit(LW(3, 1, 0))
    _emit_load_settle(builder)
    builder.emit(ADDI(1, 1, 4))
    _emit_balanced_branch(builder, BEQ, 3, 0, "producer")
    consumer_pc = _emit_balanced_branch(builder, BEQ, 3, 0, "consumer")
    builder.branch(BNE, 1, 2, "iteration")
    marker_pc, loop_offset = _finish(builder, 0x122)

    return ProgramSpec(
        name="global_history",
        instructions=builder.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, 0x122, "completion"),),
        initial_memory=_outcome_memory(outcomes),
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_global_history",
        consumer_offset=consumer_pc,
    )


def path_history_probe(flush_depth=12, samples=64, name=None):
    """Same direction history, different branch-PC paths, common consumer.

    The selector chooses one of two chains.  Both chains execute exactly
    ``flush_depth`` taken conditional branches, so their direction histories
    are identical while their branch-PC histories differ.  The common
    consumer outcome is the selector bit.
    """
    flush_depth = max(1, int(flush_depth))
    outcomes = _lfsr_bits(max(16, int(samples)), seed=0x1234)
    byte_length = 4 * len(outcomes)

    builder = _Assembler()
    builder.emit(ADDI(1, 0, 0))
    builder.emit(ADDI(2, 0, byte_length))
    builder.label("iteration")
    builder.emit(LW(3, 1, 0))
    _emit_load_settle(builder)
    builder.emit(ADDI(1, 1, 4))
    builder.branch(BEQ, 3, 0, "path_a_entry")
    builder.jal(0, "path_b")
    builder.label("path_a_entry")
    builder.jal(0, "path_a")

    builder.label("path_a")
    _emit_taken_branch_chain(builder, "path_a", flush_depth)
    builder.jal(0, "consumer")

    builder.label("path_b")
    _emit_taken_branch_chain(builder, "path_b", flush_depth)
    builder.jal(0, "consumer")

    builder.label("consumer")
    consumer_pc = _emit_balanced_branch(builder, BEQ, 3, 0, "path_consumer")
    builder.branch(BNE, 1, 2, "iteration")
    marker_pc, loop_offset = _finish(builder, 0x123)

    return ProgramSpec(
        name=name or f"path_history_depth_{flush_depth}",
        instructions=builder.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, 0x123, "completion"),),
        initial_memory=_outcome_memory(outcomes),
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_path_history",
        consumer_offset=consumer_pc,
    )


def combined_history_probe(samples=96):
    """Interleave a globally correlated branch and a locally periodic branch."""
    samples = max(16, int(samples))
    global_outcomes = _lfsr_bits(samples, seed=0xCAFE)
    local_pattern = (True, True, False, False)
    local_outcomes = tuple(local_pattern[index % len(local_pattern)] for index in range(samples))
    byte_length = 4 * samples
    local_base = 0x400

    builder = _Assembler()
    builder.emit(ADDI(1, 0, 0))
    builder.emit(ADDI(2, 0, local_base))
    builder.emit(ADDI(6, 0, byte_length))
    builder.label("iteration")
    builder.emit(LW(3, 1, 0))
    builder.emit(LW(4, 2, 0))
    _emit_load_settle(builder)
    builder.emit(ADDI(1, 1, 4))
    builder.emit(ADDI(2, 2, 4))
    _emit_balanced_branch(builder, BEQ, 3, 0, "global_producer")
    global_consumer_pc = _emit_balanced_branch(builder, BEQ, 3, 0, "global_consumer")
    _emit_balanced_branch(builder, BEQ, 4, 0, "local_consumer")
    builder.branch(BNE, 1, 6, "iteration")
    marker_pc, loop_offset = _finish(builder, 0x124)

    memory = _outcome_memory(global_outcomes)
    memory.update(_outcome_memory(local_outcomes, local_base))
    return ProgramSpec(
        name="combined_history",
        instructions=builder.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, 0x124, "completion"),),
        initial_memory=memory,
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_combined_history",
        consumer_offset=global_consumer_pc,
    )


def long_history_probe(distance=16, samples=96, name=None):
    """Correlate a consumer with a producer ``distance`` branches earlier."""
    distance = max(0, int(distance))
    outcomes = _lfsr_bits(max(16, int(samples)), seed=0x0F0F)
    byte_length = 4 * len(outcomes)

    builder = _Assembler()
    builder.emit(ADDI(1, 0, 0))
    builder.emit(ADDI(2, 0, byte_length))
    builder.label("iteration")
    builder.emit(LW(3, 1, 0))
    _emit_load_settle(builder)
    builder.emit(ADDI(1, 1, 4))
    _emit_balanced_branch(builder, BEQ, 3, 0, "long_producer")
    _emit_taken_branch_chain(builder, "history_filler", distance)
    consumer_pc = _emit_balanced_branch(builder, BEQ, 3, 0, "long_consumer")
    builder.branch(BNE, 1, 2, "iteration")
    marker_pc, loop_offset = _finish(builder, 0x125)

    return ProgramSpec(
        name=name or f"long_history_distance_{distance}",
        instructions=builder.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, 0x125, "completion"),),
        initial_memory=_outcome_memory(outcomes),
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_long_history",
        consumer_offset=consumer_pc,
    )


def loop_predictor_probe(trip_count=37, repetitions=24, name=None):
    """Repeat a fixed-trip-count loop to expose loop-exit prediction."""
    trip_count = max(2, int(trip_count))
    repetitions = max(2, int(repetitions))
    if trip_count > 2047 or repetitions > 2047:
        raise ValueError("trip_count and repetitions must fit ADDI immediates")

    builder = _Assembler()
    builder.emit(ADDI(1, 0, repetitions))
    builder.emit(ADDI(3, 0, trip_count))
    builder.label("outer")
    builder.emit(ADDI(2, 0, 0))
    builder.label("inner")
    builder.emit(ADDI(2, 2, 1))
    loop_branch_pc = builder.branch(BLT, 2, 3, "inner")
    builder.emit(ADDI(1, 1, -1))
    builder.branch(BNE, 1, 0, "outer")
    marker_pc, loop_offset = _finish(builder, 0x131)

    return ProgramSpec(
        name=name or f"loop_predictor_trip_{trip_count}",
        instructions=builder.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, 0x131, "completion"),),
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_loop_predictor",
        consumer_offset=loop_branch_pc,
    )


def direct_btb_probe(iterations=32):
    """Execute the same direct JAL repeatedly and compare cold/warm fetches."""
    iterations = max(2, int(iterations))
    builder = _Assembler()
    builder.emit(ADDI(1, 0, iterations))
    builder.label("jump_site")
    jump_pc = builder.jal(0, "target")
    builder.emit(NOP)
    builder.emit(NOP)
    builder.label("target")
    builder.emit(ADDI(1, 1, -1))
    builder.branch(BNE, 1, 0, "jump_site")
    marker_pc, loop_offset = _finish(builder, 0x132)

    return ProgramSpec(
        name="direct_btb",
        instructions=builder.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, 0x132, "completion"),),
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_target_buffer",
        consumer_offset=jump_pc,
    )


def indirect_constant_target_probe(iterations=32):
    """Repeated JALR to one target: detects at least a last-target mechanism."""
    iterations = max(2, int(iterations))
    builder = _Assembler()
    builder.emit(ADDI(1, 0, iterations))
    builder.load_address(5, "target")
    builder.label("jump_site")
    jump_pc = builder.emit(JALR(0, 5, 0))
    builder.emit(NOP)
    builder.emit(NOP)
    builder.label("target")
    builder.emit(ADDI(1, 1, -1))
    builder.branch(BNE, 1, 0, "jump_site")
    marker_pc, loop_offset = _finish(builder, 0x133)

    return ProgramSpec(
        name="indirect_constant_target",
        instructions=builder.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, 0x133, "completion"),),
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_indirect_target",
        consumer_offset=jump_pc,
        pair_role="constant_target",
    )


def indirect_alternating_target_probe(iterations=48):
    """Alternate two JALR targets without a target-selecting branch."""
    iterations = max(2, int(iterations))
    builder = _Assembler()
    builder.emit(ADDI(1, 0, iterations))
    builder.emit(ADDI(2, 0, 0))
    builder.load_address(5, "target_a")
    builder.label("jump_site")
    builder.emit(SLLI(6, 2, 4))  # target_b is 16 bytes after target_a
    builder.emit(ADD(7, 5, 6))
    builder.emit(XORI(2, 2, 1))
    jump_pc = builder.emit(JALR(0, 7, 0))
    builder.emit(NOP)
    builder.emit(NOP)

    builder.label("target_a")
    builder.jal(0, "after_target")
    builder.emit(NOP)
    builder.emit(NOP)
    builder.emit(NOP)
    builder.label("target_b")
    builder.jal(0, "after_target")

    # Keep the arithmetic assumption above explicit and checked.
    if builder.labels["target_b"] - builder.labels["target_a"] != 16:
        raise AssertionError("indirect target spacing must remain 16 bytes")

    builder.label("after_target")
    builder.emit(ADDI(1, 1, -1))
    builder.branch(BNE, 1, 0, "jump_site")
    marker_pc, loop_offset = _finish(builder, 0x134)

    return ProgramSpec(
        name="indirect_alternating_target",
        instructions=builder.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, 0x134, "completion"),),
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_indirect_target",
        consumer_offset=jump_pc,
        pair_role="alternating_targets",
    )


def ras_probe(link_register=1, samples=64, name=None):
    """Call one function from two sites and return through one JALR PC.

    Compare link_register=1 (or 5) with a non-hinted register such as x10.
    A RAS should strongly favor the standard RISC-V link registers.
    """
    link_register = int(link_register)
    if link_register in (0, 20, 21, 22, 31):
        raise ValueError("link register conflicts with probe bookkeeping")
    outcomes = _lfsr_bits(max(16, int(samples)), seed=0x5151)
    byte_length = 4 * len(outcomes)

    builder = _Assembler()
    builder.emit(ADDI(20, 0, 0))
    builder.emit(ADDI(22, 0, byte_length))
    builder.label("iteration")
    builder.emit(LW(21, 20, 0))
    _emit_load_settle(builder)
    builder.emit(ADDI(20, 20, 4))
    builder.branch(BEQ, 21, 0, "call_a")

    builder.label("call_b")
    builder.jal(link_register, "function")
    builder.label("return_b")
    builder.jal(0, "after_return")

    builder.label("call_a")
    builder.jal(link_register, "function")
    builder.label("return_a")
    builder.jal(0, "after_return")

    builder.label("function")
    return_pc = builder.emit(JALR(0, link_register, 0))

    builder.label("after_return")
    builder.branch(BNE, 20, 22, "iteration")
    marker = 0x135 if link_register in (1, 5) else 0x136
    marker_pc, loop_offset = _finish(builder, marker)

    return ProgramSpec(
        name=name or f"ras_link_x{link_register}",
        instructions=builder.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, marker, "completion"),),
        initial_memory=_outcome_memory(outcomes),
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_return_address_stack",
        consumer_offset=return_pc,
        pair_role="ras_hint" if link_register in (1, 5) else "non_ras_control",
    )


def nested_ras_probe(depth=4, link_register=1, repetitions=8, name=None):
    """Generate layout-matched nested calls for behavioral RAS depth sweeps."""
    depth = int(depth)
    repetitions = int(repetitions)
    link_register = int(link_register)
    if not 1 <= depth <= 8:
        raise ValueError("RAS depth must be between 1 and 8")
    if link_register in (0, 20, 31) or 12 <= link_register < 12 + depth:
        raise ValueError("link register conflicts with nested-call bookkeeping")

    builder = _Assembler()
    builder.emit(ADDI(20, 0, repetitions))
    builder.label("iteration")
    main_call = builder.jal(link_register, "function_0")
    builder.emit(ADDI(20, 20, -1))
    builder.branch(BNE, 20, 0, "iteration")
    builder.jal(0, "complete")

    sites = {}
    call_returns = {0: main_call + 4}
    for level in range(depth):
        builder.label(f"function_{level}")
        saved_link = 12 + level
        builder.emit(ADD(saved_link, link_register, 0))
        if level + 1 < depth:
            nested_call = builder.jal(link_register, f"function_{level + 1}")
            call_returns[level + 1] = nested_call + 4
        builder.emit(ADD(link_register, saved_link, 0))
        return_pc = builder.emit(JALR(0, link_register, 0))
        sites[f"return_{level}"] = {
            "kind": "return", "offset": return_pc, "fallthrough": return_pc + 4,
            "targets": (call_returns[level],),
            "actual_targets": (call_returns[level],) * repetitions,
            "warmup": min(2, repetitions // 2),
        }

    builder.label("complete")
    marker = 0x170 + depth if link_register in (1, 5) else 0x180 + depth
    marker_pc, loop_offset = _finish(builder, marker)
    return ProgramSpec(
        name=name or f"nested_ras_d{depth}_x{link_register}",
        instructions=builder.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, marker, "completion"),),
        loop_offset=loop_offset,
        base_addresses=_base_addresses(loop_offset),
        dependency_kind="branch_return_address_stack_depth",
        pair_role="ras_hint" if link_register in (1, 5) else "non_ras_control",
        control_flow={
            "family": "nested_ras_depth", "primary_site": "return_0",
            "depth": depth, "link_register": link_register, "sites": sites,
        },
    )


# Construct the probe catalog only after all probe factories are defined.
STATIC_POLICY_PROBES = {
    "static_forward_taken": static_direction_probe("static_forward_taken", "forward", True),
    "static_forward_not_taken": static_direction_probe("static_forward_not_taken", "forward", False),
    "static_backward_taken": static_direction_probe("static_backward_taken", "backward", True),
    "static_backward_not_taken": static_direction_probe("static_backward_not_taken", "backward", False),
}

BRANCH_PREDICTION_PROBES = {
    **STATIC_POLICY_PROBES,
    "dynamic_one_bit": counter_hysteresis_probe(opposite_outcomes=1, name="dynamic_one_bit"),
    "dynamic_two_bit": counter_hysteresis_probe(opposite_outcomes=2, name="dynamic_two_bit"),
    "local_alternating": direction_sequence_probe(
        "local_alternating", (True, False) * 48, marker=0x120, warmup=16
    ),
    "local_history": local_history_probe(),
    "global_history": global_history_probe(),
    "path_history": path_history_probe(name="path_history"),
    "combined_history": combined_history_probe(),
    "long_history": long_history_probe(distance=16, name="long_history"),
    "loop_predictor": loop_predictor_probe(name="loop_predictor"),
    "direct_btb": direct_btb_probe(),
    "indirect_constant_target": indirect_constant_target_probe(),
    "indirect_alternating_target": indirect_alternating_target_probe(),
    "ras_standard_link": ras_probe(link_register=1, samples=16, name="ras_standard_link"),
    "ras_nonstandard_link_control": ras_probe(
        link_register=10, samples=16, name="ras_nonstandard_link_control"
    ),
}

BRANCH_RESOLUTION_PROBES = branch_resolution_pair()
