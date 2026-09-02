"""Stateful word memory used by forwarding probes."""


class DataMemory:
    def __init__(self):
        self.words = {}
        self.transactions = []
        self.supported = None
        self.current_cycle = 0
        self.generation = 0
        self.response_delay_cycles = 0
        self.response_delay_address = None
        self.transaction_sequence = 0

    def configure_response_delay(self, cycles=0, address=None):
        self.response_delay_cycles = max(0, int(cycles))
        self.response_delay_address = None if address is None else int(address) & ~3

    def reset(self, initial=None):
        self.generation += 1
        self.words = {int(address): int(value) & 0xFFFFFFFF for address, value in (initial or {}).items()}
        self.transactions = []
        self.transaction_sequence = 0

    def _transaction_metadata(self):
        transaction_id = f"data:{self.generation}:{self.transaction_sequence}"
        self.transaction_sequence += 1
        return {"epoch_id": self.generation, "transaction_id": transaction_id}

    def read_word(self, address, cycle=None):
        address = int(address) & ~3
        value = self.words.get(address, 0)
        if cycle is not None:
            self.transactions.append({
                "cycle": cycle, "kind": "load", "address": address, "value": value,
                **self._transaction_metadata(),
            })
        return value

    def write_word(self, address, value, byte_enable=None, cycle=None):
        address = int(address) & ~3
        old = self.words.get(address, 0)
        mask = 0xF if byte_enable is None else int(byte_enable) & 0xF
        merged = old
        for byte in range(4):
            if mask & (1 << byte):
                merged = (merged & ~(0xFF << (byte * 8))) | (int(value) & (0xFF << (byte * 8)))
        self.words[address] = merged & 0xFFFFFFFF
        if cycle is not None:
            self.transactions.append({
                "cycle": cycle, "kind": "store", "address": address,
                "value": merged & 0xFFFFFFFF, "byte_enable": mask,
                **self._transaction_metadata(),
            })
