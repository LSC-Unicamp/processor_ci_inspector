"""Cocotb data-bus support shared by discovery and execution probes."""

from cocotb.triggers import RisingEdge, Timer

from .data_memory import DataMemory


def _signal_int(handle):
    try:
        value = handle.value
        if hasattr(value, "is_resolvable") and not value.is_resolvable:
            return None
        return int(value)
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None


def _high(handle):
    return bool(_signal_int(handle))


async def data_mem_driver(dut, memory=None):
    """Serve a separate data bus with zero wait states or a configured load delay."""
    memory = memory or DataMemory()
    memory.reset()
    if not hasattr(dut, "data_mem_ack"):
        memory.supported = False
        return
    memory.supported = all(hasattr(dut, name) for name in (
        "data_mem_addr", "data_mem_we", "data_mem_data_out", "data_mem_data_in"
    ))
    dut.data_mem_data_in.value = 0
    dut.data_mem_ack.value = 1
    cycle = 0
    active_transaction = None
    active_generation = memory.generation
    delayed_transaction = None
    delay_remaining = 0
    while True:
        await RisingEdge(dut.sys_clk)
        await Timer(0.001, unit="ns")
        dut.data_mem_ack.value = 1
        cycle += 1
        memory.current_cycle = cycle
        if active_generation != memory.generation:
            active_transaction = None
            delayed_transaction = None
            delay_remaining = 0
            active_generation = memory.generation
        if not memory.supported:
            dut.data_mem_data_in.value = 0
            continue
        requested = (
            (not hasattr(dut, "data_mem_cyc") or _high(dut.data_mem_cyc))
            and (not hasattr(dut, "data_mem_stb") or _high(dut.data_mem_stb))
        )
        if not requested:
            active_transaction = None
            delayed_transaction = None
            delay_remaining = 0
            dut.data_mem_data_in.value = 0
            continue
        address = _signal_int(dut.data_mem_addr)
        is_write = _high(dut.data_mem_we)
        value = _signal_int(dut.data_mem_data_out)
        transaction = (address, is_write, value)
        if address is None:
            continue
        delay_applies = (
            memory.response_delay_cycles > 0 and not is_write
            and (memory.response_delay_address is None
                 or (int(address) & ~3) == memory.response_delay_address)
        )
        if delay_applies:
            if delayed_transaction != transaction:
                delayed_transaction = transaction
                delay_remaining = memory.response_delay_cycles
            if delay_remaining > 0:
                dut.data_mem_ack.value = 0
                delay_remaining -= 1
                dut.data_mem_data_in.value = memory.read_word(address)
                continue
            dut.data_mem_ack.value = 1
        if transaction != active_transaction:
            if is_write:
                byte_enable = None
                for name in ("data_mem_wstrb", "data_mem_sel", "data_mem_be"):
                    if hasattr(dut, name):
                        byte_enable = _signal_int(getattr(dut, name))
                        break
                memory.write_word(address, value or 0, byte_enable, cycle=cycle)
            else:
                memory.read_word(address, cycle=cycle)
            active_transaction = transaction
        dut.data_mem_data_in.value = memory.read_word(address)
