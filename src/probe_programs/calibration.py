"""Known-token programs used to calibrate dynamic pipeline observation."""

try:
    from ..riscv.encoding import ADDI, JAL, LW, SW
except ImportError:
    from riscv.encoding import ADDI, JAL, LW, SW

from .model import ExpectedWrite, OperandObservation, ProgramSpec


# The landing preflight chooses the first three bases which the wrapped core
# demonstrably reaches without address aliasing.  The values deliberately
# exercise different low address patterns while remaining JAL-reachable from
# every supported reset-entry trampoline.
CALIBRATION_LANDING_BASES = (
    0x40, 0x98, 0x184, 0x254, 0x34C, 0x4D8,
)
CALIBRATION_EXECUTION_BASES = CALIBRATION_LANDING_BASES[:3]
CALIBRATION_ENTRY_ADDRESSES = (
    0x00, 0x40, 0x60, 0x80, 0x100, 0x200,
)


def pipeline_calibration_flow(variant=0, hold=False, execution_base=None):
    """Return an independent, uniquely encoded stage/operand calibration flow."""
    variant = max(0, int(variant))
    execution_base = int(
        CALIBRATION_EXECUTION_BASES[
            variant % len(CALIBRATION_EXECUTION_BASES)
        ] if execution_base is None else execution_base
    )
    image_base = 0x40
    runway = execution_base - image_base
    memory_base = 64 + 16 * variant
    load_value = 0x241 + variant
    store_value = 0x181 + variant
    immediates = [0x101 + 0x10 * index + variant for index in range(6)]
    instructions = {
        runway + 0: ADDI(8, 0, memory_base),
        runway + 4: ADDI(9, 0, store_value),
        runway + 8: ADDI(10, 0, immediates[0]),
        runway + 12: ADDI(11, 0, immediates[1]),
        runway + 16: ADDI(12, 0, immediates[2]),
        runway + 20: ADDI(13, 0, immediates[3]),
        runway + 24: ADDI(15, 0, immediates[4]),
        runway + 28: LW(14, 8, 0),
        runway + 32: SW(9, 8, 4),
        runway + 36: ADDI(16, 0, immediates[5]),
        runway + 40: JAL(0, 8),
        runway + 44: ADDI(17, 0, 0x6A0 + variant),
        runway + 48: ADDI(18, 0, 0x4A0 + variant),
    }
    writes = (
        ExpectedWrite(runway + 0, 8, memory_base, "calibration_setup"),
        ExpectedWrite(runway + 4, 9, store_value, "calibration_setup"),
        *(ExpectedWrite(runway + 8 + 4 * index, 10 + index, immediates[index], "calibration_flow")
          for index in range(4)),
        ExpectedWrite(runway + 24, 15, immediates[4], "calibration_flow"),
        ExpectedWrite(runway + 28, 14, load_value, "calibration_load"),
        ExpectedWrite(runway + 36, 16, immediates[5], "calibration_flow"),
        ExpectedWrite(runway + 48, 18, 0x4A0 + variant, "completion"),
    )
    observations = (
        OperandObservation(runway + 0, "calibration_setup", 0, 0, "execute", destination_register=8, result_value=memory_base),
        OperandObservation(runway + 4, "calibration_setup", 0, 0, "execute", destination_register=9, result_value=store_value),
        *(OperandObservation(
            runway + 8 + 4 * index, "calibration_flow", 0, 0, "execute",
            destination_register=10 + index, result_value=immediates[index],
        ) for index in range(4)),
        OperandObservation(runway + 24, "calibration_flow", 0, 0, "execute", destination_register=15, result_value=immediates[4]),
        OperandObservation(
            runway + 28, "calibration_load", 8, memory_base, "execute",
            destination_register=14, result_value=load_value,
        ),
        OperandObservation(
            runway + 32, "calibration_store", 8, memory_base, "store_address",
            9, store_value, "store_data",
        ),
        OperandObservation(runway + 36, "calibration_flow", 0, 0, "execute", destination_register=16, result_value=immediates[5]),
        OperandObservation(runway + 40, "calibration_redirect"),
        OperandObservation(runway + 44, "wrong_path_poison", 0, 0, "execute", destination_register=17, result_value=0x6A0 + variant),
        OperandObservation(runway + 48, "completion", 0, 0, "execute", destination_register=18, result_value=0x4A0 + variant),
    )
    return ProgramSpec(
        name=f"pipeline_calibration_{'hold' if hold else 'flow'}_{variant}",
        instructions=instructions,
        expected_writes=writes,
        initial_memory={memory_base: load_value, memory_base + 4: 0xDEADBEEF},
        loop_offset=runway + 52,
        base_addresses=(image_base,),
        entry_addresses=CALIBRATION_ENTRY_ADDRESSES,
        entry_trampoline_target=execution_base,
        expected_store_address=memory_base + 4,
        expected_store_value=store_value,
        operand_observations=observations,
        control_flow={
            "redirect_offset": runway + 40,
            "wrong_path_offsets": (runway + 44,),
            "target_offset": runway + 48,
        },
        calibration_load_address=memory_base,
        calibration_kind="flow",
        calibration_variant=variant,
        calibration_relocation_base=execution_base,
        calibration_relocation_origin=runway,
        calibration_requested_base=execution_base,
        calibration_sections={
            "straight_line": {
                "register_offsets": tuple(runway + 4 * index for index in range(6)),
            },
            "memory": {
                "register_offsets": (
                    runway + 28, runway + 36,
                ),
                "memory_required": True,
            },
            "redirect": {
                "register_offsets": (runway + 48,),
                "poison_required": True,
            },
        },
    )


def pipeline_relocation_landing(requested_base, landing_index=0):
    """Return a short uniquely marked relocation/redirect reachability probe."""
    requested_base = int(requested_base)
    landing_index = max(0, int(landing_index))
    image_base = 0x40
    if requested_base < image_base or requested_base % 4:
        raise ValueError("relocation landing bases must be word aligned >= 0x40")
    runway = requested_base - image_base
    setup_value = 0x640 + landing_index
    completion_value = 0x740 + landing_index
    poison_value = 0x7C0 + landing_index
    return ProgramSpec(
        name=f"pipeline_calibration_landing_{landing_index}",
        instructions={
            runway: ADDI(8, 0, setup_value),
            runway + 4: JAL(0, 8),
            runway + 8: ADDI(17, 0, poison_value),
            runway + 12: ADDI(18, 0, completion_value),
        },
        expected_writes=(
            ExpectedWrite(runway, 8, setup_value, "calibration_setup"),
            ExpectedWrite(
                runway + 12, 18, completion_value, "completion",
            ),
        ),
        loop_offset=runway + 16,
        base_addresses=(image_base,),
        entry_addresses=CALIBRATION_ENTRY_ADDRESSES,
        entry_trampoline_target=requested_base,
        operand_observations=(
            OperandObservation(
                runway, "calibration_setup", 0, 0, "execute",
                destination_register=8, result_value=setup_value,
            ),
            OperandObservation(runway + 4, "calibration_redirect"),
            OperandObservation(
                runway + 8, "wrong_path_poison", 0, 0, "execute",
                destination_register=17, result_value=poison_value,
            ),
            OperandObservation(
                runway + 12, "completion", 0, 0, "execute",
                destination_register=18, result_value=completion_value,
            ),
        ),
        control_flow={
            "redirect_offset": runway + 4,
            "wrong_path_offsets": (runway + 8,),
            "target_offset": runway + 12,
        },
        calibration_kind="relocation_landing",
        calibration_variant=landing_index,
        calibration_relocation_base=requested_base,
        calibration_relocation_origin=runway,
        calibration_requested_base=requested_base,
        calibration_landing_index=landing_index,
        calibration_sections={
            "straight_line": {
                "register_offsets": (runway,),
            },
            "redirect": {
                "register_offsets": (runway + 12,),
                "poison_required": True,
            },
        },
    )


def pipeline_handshake_calibration(variant=0):
    """Short independent-load flow used to prove delayed ACK capability."""
    variant = max(0, int(variant))
    runway = 64
    memory_base = 0x100 + 16 * variant
    load_value = 0x520 + variant
    marker = 0x620 + variant
    return ProgramSpec(
        name=f"pipeline_calibration_handshake_{variant}",
        instructions={
            runway: ADDI(8, 0, memory_base),
            runway + 4: LW(14, 8, 0),
            runway + 8: ADDI(18, 0, marker),
        },
        expected_writes=(
            ExpectedWrite(runway, 8, memory_base, "calibration_setup"),
            ExpectedWrite(runway + 4, 14, load_value, "calibration_load"),
            ExpectedWrite(runway + 8, 18, marker, "completion"),
        ),
        initial_memory={memory_base: load_value},
        loop_offset=runway + 12,
        base_addresses=(0x40,),
        entry_addresses=CALIBRATION_ENTRY_ADDRESSES,
        operand_observations=(
            OperandObservation(runway, "calibration_setup", 0, 0, "execute", destination_register=8, result_value=memory_base),
            OperandObservation(runway + 4, "calibration_load", 8, memory_base, "execute", destination_register=14, result_value=load_value),
            OperandObservation(runway + 8, "completion", 0, 0, "execute", destination_register=18, result_value=marker),
        ),
        calibration_load_address=memory_base,
        calibration_kind="handshake",
        calibration_variant=variant,
        calibration_sections={
            "memory": {
                "register_offsets": (runway, runway + 4, runway + 8),
            },
        },
        handshake_role="baseline" if variant == 0 else "delayed",
        response_delay_cycles=0 if variant == 0 else 1,
    )
