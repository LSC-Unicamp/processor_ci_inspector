"""Behavioral cache probes and a draft Cocotb-oriented characterization flow.

The programs use ProgramSpec so the existing instruction-injection runner can
load them exactly like the branch probes.  The flow deliberately infers cache
properties from accepted external-memory transactions, not from final values.

Stages:
  1. Presence / repeated-access retention
  2. Cache-line size
  3. Capacity
  4. Associativity and set count

The draft focuses on a data cache because dependent loads give the cleanest
black-box evidence.  I-cache presence and line-size probes are included as
well; the same one-pass/two-pass idea can later be extended to sparse jump
chains for I-cache capacity and associativity.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import importlib
import json
import os
from typing import Awaitable, Callable, Iterable, Mapping, Sequence

try:
    from ..riscv.encoding import ADD, ADDI, AUIPC, BNE, JAL, LUI, LW, NOP
except ImportError:
    from riscv.encoding import ADD, ADDI, AUIPC, BNE, JAL, LUI, LW, NOP

from .model import ExpectedWrite, ProgramSpec


# ---------------------------------------------------------------------------
# Probe construction
# ---------------------------------------------------------------------------


class _Assembler:
    def __init__(self):
        self.pc = 0
        self.instructions: dict[int, int | None] = {}
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[str, int, str, tuple]] = []

    def seek(self, offset: int):
        offset = int(offset)
        if offset < self.pc or offset & 3:
            raise ValueError("seek target must be aligned and not move backwards")
        while self.pc < offset:
            self.emit(NOP)

    def label(self, name: str):
        if name in self.labels:
            raise ValueError(f"duplicate label: {name}")
        self.labels[name] = self.pc

    def emit(self, instruction: int | None) -> int:
        offset = self.pc
        self.instructions[offset] = instruction
        self.pc += 4
        return offset

    def branch(self, encoder, rs1: int, rs2: int, label: str) -> int:
        pc = self.emit(None)
        self.fixups.append(("branch", pc, label, (encoder, rs1, rs2)))
        return pc

    def jal(self, rd: int, label: str) -> int:
        pc = self.emit(None)
        self.fixups.append(("jal", pc, label, (rd,)))
        return pc

    def resolve(self) -> dict[int, int]:
        result = dict(self.instructions)
        for kind, pc, label, operands in self.fixups:
            if label not in self.labels:
                raise ValueError(f"unknown label: {label}")
            displacement = self.labels[label] - pc
            if kind == "branch":
                encoder, rs1, rs2 = operands
                result[pc] = encoder(rs1, rs2, displacement)
            elif kind == "jal":
                (rd,) = operands
                result[pc] = JAL(rd, displacement)
            else:
                raise ValueError(f"unknown fixup: {kind}")
        if any(value is None for value in result.values()):
            raise ValueError("unresolved instruction")
        return result  # type: ignore[return-value]


def _emit_li(builder: _Assembler, rd: int, value: int) -> tuple[int, ...]:
    """Emit a standard LUI/ADDI constant load for a 32-bit address/value."""
    value = int(value) & 0xFFFFFFFF
    signed = value if value < 0x80000000 else value - 0x100000000
    if -2048 <= signed <= 2047:
        return (builder.emit(ADDI(rd, 0, signed)),)
    upper = (value + 0x800) >> 12
    lower = value - (upper << 12)
    return (builder.emit(LUI(rd, upper & 0xFFFFF)), builder.emit(ADDI(rd, rd, lower)))


def _finish(builder: _Assembler, marker: int) -> tuple[int, int]:
    marker_pc = builder.emit(ADDI(31, 0, int(marker)))
    return marker_pc, builder.pc


def _bases(loop_offset: int, preferred: int = 0x4000) -> tuple[int, ...]:
    # Cache probes must not replicate large/sparse images into overlapping slots.
    return (preferred,)


def _memory_words(addresses: Iterable[int]) -> dict[int, int]:
    return {int(address): (0x5A000000 ^ int(address)) & 0xFFFFFFFF for address in addresses}


def data_repeat_probe(
    address: int = 0x10000,
    repeats: int = 4,
    settle_nops: int = 8,
    name: str = "dcache_presence_repeat",
) -> ProgramSpec:
    """Stage 1: repeatedly load one word; only the first load should miss."""
    repeats = max(1, int(repeats))
    b = _Assembler()
    _emit_li(b, 1, address)
    load_offsets = []
    for index in range(repeats):
        load_offsets.append(b.emit(LW(10 + (index % 8), 1, 0)))
        for _ in range(max(0, settle_nops)):
            b.emit(NOP)
    marker_pc, end = _finish(b, 0x201)
    return ProgramSpec(
        name=name,
        instructions=b.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, 0x201, "completion"),),
        initial_memory=_memory_words((address,)),
        loop_offset=end,
        base_addresses=_bases(end),
        dependency_kind="cache_presence",
        control_flow={"cache": {"stage": 1, "side": "data", "address": address,
                                 "repeats": repeats, "load_offsets": tuple(load_offsets)}},
    )


def data_single_load_probe(address: int = 0x10000) -> ProgramSpec:
    return data_repeat_probe(address, repeats=1, settle_nops=0,
                             name="dcache_presence_single_control")


def data_line_probe(
    offset: int,
    address: int = 0x10000,
    include_second: bool = True,
) -> ProgramSpec:
    """Stage 2 pair member: load A, then optionally A+offset after fill settles."""
    offset = int(offset)
    if offset <= 0:
        raise ValueError("offset must be positive")
    b = _Assembler()
    _emit_li(b, 1, address)
    first_pc = b.emit(LW(10, 1, 0))
    for _ in range(12):
        b.emit(NOP)
    second_pc = None
    addresses = [address]
    if include_second:
        second_pc = b.emit(LW(11, 1, offset)) if -2048 <= offset <= 2047 else None
        if second_pc is None:
            _emit_li(b, 2, address + offset)
            second_pc = b.emit(LW(11, 2, 0))
        addresses.append(address + offset)
    marker = 0x210 if include_second else 0x211
    marker_pc, end = _finish(b, marker)
    return ProgramSpec(
        name=f"dcache_line_{'candidate' if include_second else 'baseline'}_{offset}",
        instructions=b.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, marker, "completion"),),
        initial_memory=_memory_words(addresses),
        loop_offset=end,
        base_addresses=_bases(end),
        dependency_kind="cache_line_size",
        pair_role="candidate" if include_second else "baseline",
        control_flow={"cache": {"stage": 2, "side": "data", "base": address,
                                 "offset": offset, "first_load": first_pc,
                                 "second_load": second_pc}},
    )


def data_line_probe_pair(offset: int, address: int = 0x10000) -> tuple[ProgramSpec, ProgramSpec]:
    return data_line_probe(offset, address, False), data_line_probe(offset, address, True)


def _permutation(count: int, seed: int = 0xCACE) -> list[int]:
    values = list(range(count))
    state = seed & 0xFFFFFFFF
    for i in range(count - 1, 0, -1):
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        j = state % (i + 1)
        values[i], values[j] = values[j], values[i]
    return values


def _pointer_cycle(base: int, working_set: int, line_size: int) -> tuple[int, dict[int, int], tuple[int, ...]]:
    count = max(1, working_set // line_size)
    order = _permutation(count)
    addresses = tuple(base + index * line_size for index in order)
    memory = {addresses[i]: addresses[(i + 1) % count] for i in range(count)}
    return count, memory, addresses


def data_capacity_probe(
    working_set: int,
    line_size: int,
    passes: int,
    base: int = 0x10000,
) -> ProgramSpec:
    """Stage 3: dependent pointer chase over one or two identical passes."""
    working_set, line_size, passes = map(int, (working_set, line_size, passes))
    if working_set < line_size or working_set % line_size:
        raise ValueError("working_set must be a positive multiple of line_size")
    if passes not in (1, 2):
        raise ValueError("passes must be 1 or 2")
    count, memory, addresses = _pointer_cycle(base, working_set, line_size)
    b = _Assembler()
    _emit_li(b, 1, addresses[0])
    _emit_li(b, 2, count * passes)
    b.label("chase")
    load_pc = b.emit(LW(1, 1, 0))
    b.emit(ADDI(2, 2, -1))
    b.branch(BNE, 2, 0, "chase")
    marker = 0x220 + passes
    marker_pc, end = _finish(b, marker)
    return ProgramSpec(
        name=f"dcache_capacity_{working_set}_p{passes}",
        instructions=b.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, marker, "completion"),),
        initial_memory=memory,
        loop_offset=end,
        base_addresses=_bases(end),
        dependency_kind="cache_capacity",
        pair_role=f"{passes}_pass",
        consumer_offset=load_pc,
        control_flow={"cache": {"stage": 3, "side": "data", "working_set": working_set,
                                 "line_size": line_size, "passes": passes,
                                 "access_count": count * passes,
                                 "addresses": addresses}},
    )


def data_capacity_probe_pair(working_set: int, line_size: int, base: int = 0x10000):
    return (data_capacity_probe(working_set, line_size, 1, base),
            data_capacity_probe(working_set, line_size, 2, base))


def data_conflict_probe(
    stride: int,
    line_count: int,
    reprobe: bool,
    base: int = 0x10000,
) -> ProgramSpec:
    """Stage 4 pair member: fill N stride-separated lines, optionally reload A0."""
    stride, line_count = int(stride), int(line_count)
    if stride <= 0 or line_count < 1:
        raise ValueError("stride and line_count must be positive")
    addresses = tuple(base + i * stride for i in range(line_count))
    b = _Assembler()
    for reg_index, address in enumerate(addresses):
        _emit_li(b, 1, address)
        b.emit(LW(10 + (reg_index % 8), 1, 0))
        for _ in range(4):
            b.emit(NOP)
    if reprobe:
        _emit_li(b, 1, addresses[0])
        b.emit(LW(20, 1, 0))
    marker = 0x230 if reprobe else 0x231
    marker_pc, end = _finish(b, marker)
    return ProgramSpec(
        name=f"dcache_conflict_s{stride}_n{line_count}_{'reprobe' if reprobe else 'baseline'}",
        instructions=b.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, marker, "completion"),),
        initial_memory=_memory_words(addresses),
        loop_offset=end,
        base_addresses=_bases(end),
        dependency_kind="cache_associativity",
        pair_role="reprobe" if reprobe else "baseline",
        control_flow={"cache": {"stage": 4, "side": "data", "stride": stride,
                                 "line_count": line_count, "reprobe": reprobe,
                                 "addresses": addresses}},
    )


def data_conflict_probe_pair(stride: int, line_count: int, base: int = 0x10000):
    return (data_conflict_probe(stride, line_count, False, base),
            data_conflict_probe(stride, line_count, True, base))


def icache_repeat_probe(iterations: int = 8) -> ProgramSpec:
    """Stage-1 I-cache probe: execute one small loop repeatedly."""
    b = _Assembler()
    _emit_li(b, 1, max(2, int(iterations)))
    b.label("loop")
    loop_pc = b.emit(ADDI(10, 10, 1))
    for _ in range(8):
        b.emit(NOP)
    b.emit(ADDI(1, 1, -1))
    b.branch(BNE, 1, 0, "loop")
    marker_pc, end = _finish(b, 0x241)
    return ProgramSpec(
        name=f"icache_repeat_{iterations}", instructions=b.resolve(),
        expected_writes=(ExpectedWrite(marker_pc, 31, 0x241, "completion"),),
        loop_offset=end, base_addresses=_bases(end), dependency_kind="cache_presence",
        control_flow={"cache": {"stage": 1, "side": "instruction",
                                 "iterations": iterations, "loop_offset": loop_pc}},
    )


def icache_line_probe(offset: int, code_base: int = 0x4000) -> ProgramSpec:
    """Stage-2 I-cache draft: jump from offset 0 to an aligned candidate target."""
    offset = max(8, int(offset))
    offset = (offset + 3) & ~3
    b = _Assembler()
    b.jal(0, "target")
    b.seek(offset)
    b.label("target")
    target_pc = b.emit(ADDI(10, 0, 1))
    marker_pc, end = _finish(b, 0x242)
    return ProgramSpec(
        name=f"icache_line_offset_{offset}", instructions=b.resolve(),
        expected_writes=(ExpectedWrite(target_pc, 10, 1, "target"),
                         ExpectedWrite(marker_pc, 31, 0x242, "completion")),
        loop_offset=end, base_addresses=(code_base,), dependency_kind="cache_line_size",
        control_flow={"cache": {"stage": 2, "side": "instruction", "offset": offset,
                                 "target_offset": target_pc}},
    )


# ---------------------------------------------------------------------------
# Trace/result contract expected from the existing probe runner
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MemoryEvent:
    cycle: int
    address: int
    side: str                 # "instruction" or "data"
    operation: str = "read"  # "read" or "write"
    accepted: bool = True


@dataclass
class ProbeRun:
    spec: ProgramSpec
    events: Sequence[MemoryEvent]
    completed: bool = True
    metadata: dict = field(default_factory=dict)

    def reads(self, side: str) -> tuple[MemoryEvent, ...]:
        return tuple(event for event in self.events
                     if event.accepted and event.side == side and event.operation == "read")


RunProbe = Callable[[ProgramSpec], Awaitable[ProbeRun]]


@dataclass
class CacheFlowConfig:
    data_base: int = 0x10000
    line_offsets: tuple[int, ...] = (4, 8, 16, 32, 64, 128, 256)
    capacity_sizes: tuple[int, ...] = (
        256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536,
    )
    associativity_candidates: tuple[int, ...] = (1, 2, 4, 8, 16)
    miss_delta_threshold: int = 1
    capacity_hit_ratio_threshold: float = 0.10


@dataclass
class CacheCharacterization:
    data_cache_present: bool | None = None
    instruction_cache_present: bool | None = None
    line_size: int | None = None
    capacity: int | None = None
    associativity: int | None = None
    sets: int | None = None
    evidence: dict = field(default_factory=dict)


def _read_count(run: ProbeRun, side: str) -> int:
    return len(run.reads(side))


def classify_data_presence(
    single_run: ProbeRun, repeated_run: ProbeRun
) -> tuple[bool | None, dict]:
    repeats = max(2, int(repeated_run.spec.control_flow.get("cache", {}).get("repeats", 2)))
    single_reads = _read_count(single_run, "data")
    repeated_reads = _read_count(repeated_run, "data")
    if single_reads == 0:
        return None, {"reason": "no observable external data reads"}
    amplification = repeated_reads / single_reads
    # Cache: roughly one line fill in both runs. Cacheless memory: traffic grows
    # approximately with the number of architectural loads.
    present = amplification < max(1.5, repeats * 0.5)
    return present, {"single_load_reads": single_reads,
                     "repeated_load_reads": repeated_reads,
                     "loads_in_repeated_probe": repeats,
                     "traffic_amplification": amplification}


def infer_line_size(pair_runs: Mapping[int, tuple[ProbeRun, ProbeRun]], threshold: int = 1):
    evidence = {}
    first_miss_offset = None
    for offset in sorted(pair_runs):
        baseline, candidate = pair_runs[offset]
        delta = _read_count(candidate, "data") - _read_count(baseline, "data")
        evidence[offset] = {"baseline_reads": _read_count(baseline, "data"),
                            "candidate_reads": _read_count(candidate, "data"),
                            "extra_reads": delta}
        if first_miss_offset is None and delta >= threshold:
            first_miss_offset = offset
    return first_miss_offset, evidence


def infer_capacity(pair_runs: Mapping[int, tuple[ProbeRun, ProbeRun]], hit_ratio_threshold: float = 0.10):
    evidence = {}
    largest_fitting = None
    for size in sorted(pair_runs):
        one_pass, two_pass = pair_runs[size]
        cold = max(1, _read_count(one_pass, "data"))
        second_pass_reads = max(0, _read_count(two_pass, "data") - cold)
        ratio = second_pass_reads / cold
        fits = ratio <= hit_ratio_threshold
        evidence[size] = {"one_pass_reads": cold,
                          "two_pass_reads": _read_count(two_pass, "data"),
                          "second_pass_ratio": ratio, "fits": fits}
        if fits:
            largest_fitting = size
    return largest_fitting, evidence


def infer_associativity(
    pair_runs: Mapping[tuple[int, int], tuple[ProbeRun, ProbeRun]],
    line_size: int,
    capacity: int,
    threshold: int = 1,
):
    """Find the minimum observed eviction count across power-of-two strides.

    For each stride, the paired baseline omits the final A0 reload. Therefore
    an extra external read in the reprobe member means A0 was evicted. The
    minimum line_count causing eviction is ways+1. The smallest stride that
    reaches that minimum is the estimated set span.
    """
    evidence = {}
    first_eviction_by_stride: dict[int, int] = {}
    for (stride, line_count), (baseline, reprobe) in sorted(pair_runs.items()):
        delta = _read_count(reprobe, "data") - _read_count(baseline, "data")
        evicted = delta >= threshold
        evidence[(stride, line_count)] = {"extra_reads": delta, "evicted": evicted}
        if evicted and stride not in first_eviction_by_stride:
            first_eviction_by_stride[stride] = line_count
    if not first_eviction_by_stride:
        return None, None, None, evidence
    minimum_count = min(first_eviction_by_stride.values())
    associativity = minimum_count - 1
    set_span = min(stride for stride, count in first_eviction_by_stride.items()
                   if count == minimum_count)
    sets = set_span // line_size if set_span % line_size == 0 else None
    if sets is not None and sets * associativity * line_size != capacity:
        # Keep the behavioral result but flag an internally inconsistent model.
        evidence["geometry_warning"] = {
            "derived_capacity": sets * associativity * line_size,
            "measured_capacity": capacity,
        }
    return associativity, sets, set_span, evidence


async def run_cache_flow(run_probe: RunProbe, config: CacheFlowConfig | None = None) -> CacheCharacterization:
    """Run stages 1-4 using the infrastructure's asynchronous probe runner."""
    cfg = config or CacheFlowConfig()
    result = CacheCharacterization()

    # Stage 1: repeated data access.
    presence_single = await run_probe(data_single_load_probe(cfg.data_base))
    presence_repeat = await run_probe(data_repeat_probe(cfg.data_base))
    result.data_cache_present, result.evidence["stage1_data"] = classify_data_presence(
        presence_single, presence_repeat
    )

    # Optional I-cache stage-1 evidence. A runner can ignore this by raising
    # NotImplementedError when it does not expose a separate instruction trace.
    try:
        i_short = await run_probe(icache_repeat_probe(2))
        i_long = await run_probe(icache_repeat_probe(8))
        short_reads = _read_count(i_short, "instruction")
        long_reads = _read_count(i_long, "instruction")
        result.instruction_cache_present = long_reads < short_reads * 4
        result.evidence["stage1_instruction"] = {
            "two_iteration_reads": short_reads, "eight_iteration_reads": long_reads,
        }
    except NotImplementedError:
        result.instruction_cache_present = None

    # Stage 2: paired A-only versus A/A+offset runs.
    line_runs = {}
    for offset in cfg.line_offsets:
        baseline_spec, candidate_spec = data_line_probe_pair(offset, cfg.data_base)
        line_runs[offset] = (await run_probe(baseline_spec), await run_probe(candidate_spec))
    result.line_size, result.evidence["stage2_line"] = infer_line_size(
        line_runs, cfg.miss_delta_threshold
    )
    if result.line_size is None:
        return result

    # Stage 3: one-pass versus two-pass dependent working-set sweeps.
    capacity_runs = {}
    for size in cfg.capacity_sizes:
        if size < result.line_size or size % result.line_size:
            continue
        one, two = data_capacity_probe_pair(size, result.line_size, cfg.data_base)
        capacity_runs[size] = (await run_probe(one), await run_probe(two))
    result.capacity, result.evidence["stage3_capacity"] = infer_capacity(
        capacity_runs, cfg.capacity_hit_ratio_threshold
    )
    if result.capacity is None:
        return result

    # Stage 4: stride/count conflict matrix. Counts go one beyond the largest
    # candidate so the first eviction threshold can be observed.
    conflict_runs = {}
    strides = sorted({result.capacity // ways for ways in cfg.associativity_candidates
                      if result.capacity % ways == 0})
    max_count = max(cfg.associativity_candidates) + 1
    for stride in strides:
        for line_count in range(2, max_count + 1):
            baseline_spec, reprobe_spec = data_conflict_probe_pair(
                stride, line_count, cfg.data_base
            )
            conflict_runs[(stride, line_count)] = (
                await run_probe(baseline_spec), await run_probe(reprobe_spec)
            )
    (result.associativity, result.sets, set_span,
     result.evidence["stage4_associativity"]) = infer_associativity(
        conflict_runs, result.line_size, result.capacity, cfg.miss_delta_threshold
    )
    result.evidence["stage4_associativity"]["set_span"] = set_span
    return result


# Convenient static collections for infrastructure discovery. Capacity and
# associativity probes are factories because they depend on earlier results.
CACHE_STAGE1_PROBES = {
    "dcache_presence_single": data_single_load_probe(),
    "dcache_presence_repeat": data_repeat_probe(),
    "icache_presence_short": icache_repeat_probe(2),
    "icache_presence_long": icache_repeat_probe(8),
}

CACHE_STAGE2_PROBES = {
    f"dcache_line_{offset}": data_line_probe_pair(offset)
    for offset in (4, 8, 16, 32, 64, 128, 256)
}


def cache_stage3_sweep(line_size: int, sizes: Sequence[int] | None = None):
    sizes = sizes or CacheFlowConfig().capacity_sizes
    return tuple(data_capacity_probe_pair(size, line_size) for size in sizes
                 if size >= line_size and size % line_size == 0)


def cache_stage4_sweep(capacity: int, ways=(1, 2, 4, 8, 16)):
    result = []
    for candidate in ways:
        if capacity % candidate:
            continue
        stride = capacity // candidate
        for line_count in range(2, max(ways) + 2):
            result.append(data_conflict_probe_pair(stride, line_count))
    return tuple(result)


# ---------------------------------------------------------------------------
# Optional Cocotb entry point
# ---------------------------------------------------------------------------


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


async def cocotb_cache_characterization(dut):
    """Cocotb body using an infrastructure adapter selected by environment.

    Set PROCESSORCI_CACHE_RUNNER to ``package.module:function``. The function
    must be async and have signature ``await function(dut, spec) -> ProbeRun``.
    This keeps reset, memory driving, register observation, and DUT-specific bus
    names in the existing runner instead of duplicating them in this probe file.
    """
    adapter_path = os.getenv("PROCESSORCI_CACHE_RUNNER")
    if not adapter_path or ":" not in adapter_path:
        raise RuntimeError(
            "Set PROCESSORCI_CACHE_RUNNER=package.module:function to the existing "
            "async ProgramSpec runner adapter"
        )
    module_name, function_name = adapter_path.split(":", 1)
    adapter = getattr(importlib.import_module(module_name), function_name)

    async def run_probe(spec: ProgramSpec) -> ProbeRun:
        run = await adapter(dut, spec)
        if not isinstance(run, ProbeRun):
            raise TypeError("cache runner adapter must return cache.ProbeRun")
        return run

    result = await run_cache_flow(run_probe)
    dut._log.info("CACHE_CHARACTERIZATION=%s", json.dumps(_jsonable(asdict(result)), sort_keys=True))
    return result


try:
    import cocotb
except ImportError:  # Allows probe generation/unit tests without Cocotb installed.
    cocotb = None

if cocotb is not None:
    @cocotb.test()
    async def characterize_cache(dut):
        await cocotb_cache_characterization(dut)