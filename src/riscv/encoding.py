"""Small RV32I encoder used by architectural simulation probes."""

NOP = 0x00000013


def ADDI(rd, rs1, imm):
    return ((imm & 0xFFF) << 20) | ((rs1 & 0x1F) << 15) | ((rd & 0x1F) << 7) | 0x13


def ORI(rd, rs1, imm):
    return ADDI(rd, rs1, imm) | (6 << 12)


def XORI(rd, rs1, imm):
    return ADDI(rd, rs1, imm) | (4 << 12)


def ANDI(rd, rs1, imm):
    return ADDI(rd, rs1, imm) | (7 << 12)


def SLLI(rd, rs1, shamt):
    return ((shamt & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (1 << 12) | ((rd & 0x1F) << 7) | 0x13


def LUI(rd, imm20):
    return ((imm20 & 0xFFFFF) << 12) | ((rd & 0x1F) << 7) | 0x37


def AUIPC(rd, imm20):
    return ((imm20 & 0xFFFFF) << 12) | ((rd & 0x1F) << 7) | 0x17


def ADD(rd, rs1, rs2):
    return ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | ((rd & 0x1F) << 7) | 0x33


def SUB(rd, rs1, rs2):
    return ADD(rd, rs1, rs2) | 0x40000000


def LW(rd, rs1, imm):
    return ((imm & 0xFFF) << 20) | ((rs1 & 0x1F) << 15) | (2 << 12) | ((rd & 0x1F) << 7) | 0x03


def SW(rs2, rs1, imm):
    return (((imm >> 5) & 0x7F) << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (2 << 12) | ((imm & 0x1F) << 7) | 0x23


def JAL(rd, offset):
    return (((offset >> 20) & 1) << 31) | (((offset >> 1) & 0x3FF) << 21) | (((offset >> 11) & 1) << 20) | (((offset >> 12) & 0xFF) << 12) | ((rd & 0x1F) << 7) | 0x6F

def JALR(rd, rs1, offset):
    return ((offset & 0xFFF) << 20) | ((rs1 & 0x1F) << 15) | (0 << 12) | ((rd & 0x1F) << 7) | 0x67

def BEQ(rs1, rs2, offset):
    return (((offset >> 12) & 1) << 31) | (((offset >> 5) & 0x3F) << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (0 << 12) | (((offset >> 1) & 0xF) << 8) | (((offset >> 11) & 1) << 7) | 0x63

def BNE(rs1, rs2, offset):
    return (((offset >> 12) & 1) << 31) | (((offset >> 5) & 0x3F) << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (1 << 12) | (((offset >> 1) & 0xF) << 8) | (((offset >> 11) & 1) << 7) | 0x63

def BLT(rs1, rs2, offset):
    return (((offset >> 12) & 1) << 31) | (((offset >> 5) & 0x3F) << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (4 << 12) | (((offset >> 1) & 0xF) << 8) | (((offset >> 11) & 1) << 7) | 0x63

def BGE(rs1, rs2, offset):
    return (((offset >> 12) & 1) << 31) | (((offset >> 5) & 0x3F) << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (5 << 12) | (((offset >> 1) & 0xF) << 8) | (((offset >> 11) & 1) << 7) | 0x63

def BGEU(rs1, rs2, offset):
    return (((offset >> 12) & 1) << 31) | (((offset >> 5) & 0x3F) << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (7 << 12) | (((offset >> 1) & 0xF) << 8) | (((offset >> 11) & 1) << 7) | 0x63

def BLTU(rs1, rs2, offset):
    return (((offset >> 12) & 1) << 31) | (((offset >> 5) & 0x3F) << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (6 << 12) | (((offset >> 1) & 0xF) << 8) | (((offset >> 11) & 1) << 7) | 0x63

def AUIPC(rd, imm20):
    return ((imm20 & 0xFFFFF) << 12) | ((rd & 0x1F) << 7) | 0x17
