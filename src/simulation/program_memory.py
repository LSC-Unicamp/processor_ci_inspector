try:
    from ..riscv.encoding import NOP
except ImportError:
    from riscv.encoding import NOP


class ProgramMemory:
    def __init__(self, program=None):
        self.program = None
        self.image = {}
        if program is not None:
            self.select(program)

    def select(self, program):
        self.program = program
        self.image = program.image()

    @staticmethod
    def address_aliases(address):
        if address is None:
            return ()
        address = int(address)
        aliases = []
        for candidate in (address, address & 0xFFF, address & 0x3FF, address & 0x7F):
            if candidate not in aliases:
                aliases.append(candidate)
        return tuple(aliases)

    def read(self, address):
        for candidate in self.address_aliases(address):
            if candidate in self.image:
                return self.image[candidate]
        return NOP
