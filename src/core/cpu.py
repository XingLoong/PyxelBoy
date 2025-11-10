from .instructions import Operand, Instruction
from pathlib import Path
import json

class CPU:
    def __init__(self, prefixed, regular):
        # =Registers=
        """ A | F = AF 8 8 16 eight 8-bit
            B | C = BC
            D | E = DE
            H | L = HL """
        # 8-bit registers
        # Hi:
        self.A = 0  
        self.B = 0
        self.D = 0
        self.E = 0
        # Lo:
        self.C = 0
        self.H = 0
        self.L = 0
        self.F = 0

        # 16-bit registers
        self.PC = 0x0100    # Program Counter (pointer) starts here for GB
        self.SP = 0xFFFE    # Stack pointer default

        # Flags (stored in F, upper 4: znhc lower: ----)
        self.z = 0 # bit 7: zero flag
        self.n = 0 # bit 6: sub flag (BCD)
        self.h = 0 # bit 5: half carry flag (BCD)
        self.c = 0 # bit 4: carry flag

        # =Opcode talbes=
        self.regular = regular or {}
        self.prefixed = prefixed or {}

    def cycle(self, memory):
        # fetch -> decode -> execute -> update PC
        opcode = memory[self.PC]  # instructions from gb rom
        
        incremen_PC = True
        handler = self.fetch_opcode

    def fetch_opcode(self):
        pass

    def execute_opcode(self, opcode, memory):
        pass

    