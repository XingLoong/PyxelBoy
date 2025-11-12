from .instructions import Operand, Instruction
from pathlib import Path


class CPU:
    def __init__(self, prefixed, regular, memory):
        self.memory = memory
        # =Registers=
        """ A | F = AF 
            B | C = BC
            D | E = DE
            H | L = HL """
        # 0-7
        self.registers = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A'] #(HL) means to mem[HL]
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

        # =Opcode tables=
        self.regular = regular or {}
        self.prefixed = prefixed or {}
        self.cycles = 0
        self.opcodes = 0
        self.opcode_table = {
            0x00: lambda d=None,s=None,i=None: self.NOP()
        }
    # combined values
    @property
    def AF(self):
        return (self.A << 8) | self.F
    @AF.setter
    def AF(self, value):
        self.A = (value >> 8) & 0xFF
        self.F = value & 0xF0   # lower 4 bits of F (flags), 0
    
    @property
    def BC(self):
        return (self.B << 8) | self.C
    @BC.setter
    def BC(self, value):
        self.B = (value >> 8) & 0xFF
        self.C = value & 0xFF
    
    @property
    def DE(self):
        return (self.D << 8) | self.E
    @DE.setter
    def DE(self, value):
        self.D = (value >> 8) & 0xFF
        self.E = value & 0xFF
    
    @property
    def HL(self):
        return (self.H << 8) | self.L
    @HL.setter
    def HL(self, value):
        self.H = (value >> 8) & 0xFF
        self.L = value & 0xFF
    # populate optable with family groups
    def _init_LD_r_r(self):     # 0x40 - 0x7F
        # 8 bits = 01|DES|SRC || 01 111 101 Des = 111 in binary, aka 7/A
        for row, dest in enumerate(self.registers):
            for col, src in enumerate(self.registers):
                opcode = 0x40 + row*8 + col
                self.opcode_table[opcode] = (lambda d=dest, s=src, i=None: self.LD_r_r(d, s))
    
    def LD_r_r(self, dest, src):
        if dest == '(HL)' and src == '(HL)':
            raise Exception(f"LD (HL),(HL) is invalid {self.opcode}")
        
        if dest == '(HL)':
            self.memory[self.HL] = getattr(self, src)
        elif src == '(HL)':
            setattr(self, dest, self.memory[self.HL])
        else:
            setattr(self, dest, getattr(self, src))
        
        return True

    def _init_ADD_A_r(self):    # 0x80 - 0x87
        for col, src in enumerate(self.registers):
            opcode = 0x80 + col 
            self.opcode_table[opcode] = (lambda d=None,s=src,i=None: self.ADD_A_r(s))
 
    def ADD_A_r(self, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
        else:
            r_value = getattr(self, src)
        result = self.A + r_value
        # Flags
        self.F = 0
        if (result & 0xFF) == 0:
            self.F |= 0x80  # z
        if ((self.A & 0xF) + (r_value & 0xF)) > 0xF:
            self.F |= 0x20  # h
        if result > 0xFF:
            self.F |= 0x10  # c

        self.A = result & 0xFF
        return True
        
    def _init_ADC_A_r(self):    # 0x88 - 0x8F
        for col, src in enumerate(self.registers):
            opcode = 0x88 + col 
            self.opcode_table[opcode] = (lambda d=None,s=src,i=None: self.ADC_A_r(s))

    def ADC_A_r(self, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
        else:
            r_value = getattr(self, src)
        carry = 1 if (self.F & 0x10) else 0

        result = self.A + r_value + carry
        self.F = 0

        if (result & 0xFF) == 0:
            self.F |= 0x80  # z
        if ((self.A & 0xF) + (r_value & 0xF)) > 0xF:
            self.F |= 0x20  # h
        if result > 0xFF:
            self.F |= 0x10  # c
        self.A = result & 0xFF
        return True

    def _init_SUB_A_r(self):    # 0x90 - 0x97
        for col, src in enumerate(self.registers):
            opcode = 0x90 + col 
            self.opcode_table[opcode] = (lambda d=None,s=src,i=None: self.SUB_A_r(s))

    def SUB_A_r(self, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
        else:
            r_value = getattr(self, src)
        result = self.A - r_value

        self.F = 0x40
        if (result & 0xFF) == 0:
            self.F |= 0x80  
        if ((self.A & 0xF) < (r_value & 0xF)):
            self.F |= 0x20
        if self.A < result:
            self.F |= 0x10
        
        self.A = result & 0xFF
        return True
    
    def _init_SBC_A_r(self):    # 0x98 - 0x9F
        for col, src in enumerate(self.registers):
            opcode = 0x98 + col 
            self.opcode_table[opcode] = (lambda d=None,s=src,i=None: self.SBC_A_r(s))
    
    def SBC_A_r(self, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
        else:
            r_value = getattr(self, src)
        carry = 1 if (self.F & 0x10) else 0

        result = self.A - r_value - carry
        self.F = 0x40

        if (result & 0xFF) == 0:
            self.F |= 0x80  # z
        if (self.A & 0xF) < ((r_value & 0xF) + carry):
            self.F |= 0x20  # h
        if self.A < (r_value + carry):
            self.F |= 0x10  # c
        self.A = result & 0xFF
        return True

    def _init_AND_A_r(self):    # 0xA0 - 0xA7
        for col, src in enumerate(self.registers):
            opcode = 0xA0 + col 
            self.opcode_table[opcode] = (lambda d=None,s=src,i=None: self.AND_A_r(s))

    def AND_A_r(self, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
        else:
            r_value = getattr(self, src)
        result = self.A & r_value

        self.F = 0
        if (result & 0xFF) == 0:
            self.F |= 0x80
        self.F |= 0x20

        self.A = result & 0xFF
        return True
    
    def _init_OR_A_r(self):     # 0xB0 - 0xB7
        for col, src in enumerate(self.registers):
            opcode = 0xB0 + col 
            self.opcode_table[opcode] = (lambda d=None,s=src,i=None: self.OR_A_r(s))

    def OR_A_r(self, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
        else:
            r_value = getattr(self, src)
        result = self.A | r_value

        self.F = 0
        if (result & 0xFF) == 0:
            self.F |= 0x80
        
        self.A = result & 0xFF
        return True

    def _init_XOR_A_r(self):    # 0xA8 - 0xAF
        for col, src in enumerate(self.registers):
            opcode = 0xA8 + col 
            self.opcode_table[opcode] = (lambda d=None,s=src,i=None: self.XOR_A_r(s))

    def XOR_A_r(self, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
        else:
            r_value = getattr(self, src)
        result = self.A ^ r_value

        self.F = 0
        if (result & 0xFF) == 0:
            self.F |= 0x80

        self.A = result & 0xFF
        return True

    def _init_CP_A_r(self):     # 0xB8 - 0xBF
        for col, src in enumerate(self.registers):
            opcode = 0xB8 + col 
            self.opcode_table[opcode] = (lambda d=None,s=src,i=None: self.CP_A_r(s))

    def CP_A_r(self, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
        else:
            r_value = getattr(self, src)
        result = self.A - r_value

        self.F = 0
        self.F |= 0x40
        if (result & 0xFF) == 0:
            self.F |= 0x80
        if (self.A & 0xF) < (r_value & 0xF):
            self.F |= 0x20
        if self.A < r_value:
            self.F |= 0x10

        return True

    def _init_INC_r(self):      # 1-3x4 + 1-3xC
        for col, src in enumerate(self.registers):
            # 4 12 20 28
            opcode = 0x04 + (col * 0x08)
            self.opcode_table[opcode] = (lambda d=None,s=src,i=None: self.INC_r(s))
    
    def INC_r(self, src):
        # self.register += 1, change flags
        if src == '(HL)':
            r_value = self.memory[self.HL]
            result = (r_value + 1) & 0xFF
            self.memory[self.HL] = result
        else:
            r_value = getattr(self, src) 
            result = (r_value + 1) & 0xFF
            setattr(self, src, result)
        # set c and n respectively 00010000
        self.F &= 0x10  
        if result == 0:             
            self.F |= 0x80  # z
        if (r_value & 0x0F) + 1 > 0x0F:
            self.F |= 0x20  # h
        
        return True

    def _init_DEC_r(self):      # 1-3x5 + 1-3xD
        for col, src in enumerate(self.registers):
            opcode = 0x05 + (col * 0x08)
            self.opcode_table[opcode] = (lambda d=None,s=src,i=None: self.DEC_r(s))        

    def DEC_r(self, src):
        # opposite of INC
        if src == '(HL)':
            r_value = self.memory[self.HL]
            result = (r_value - 1) & 0xFF
            self.memory[self.HL] = result
        else:
            r_value = getattr(self, src)
            result = (r_value - 1) & 0xFF
            setattr(self, src, result)
        # keep c
        self.F &= 0x10
        # set n
        self.F |= 0x40
        if result == 0:
            self.F |= 0x80
        if r_value & 0x0F == 0:
            self.F |= 0x20

        return True

    def _init_LD_r_n(self):     # 1-3x6 + 1-3xE
        for col, src in enumerate(self.registers):
            opcode = 0x06 + (col * 0x08)
            self.opcode_table[opcode] = (lambda d=None,s=src,i=None: self.LD_r_n(s))
    
    def LD_r_n(self, src):
        if src == '(HL)':
            self.memory[self.HL] = (self.memory[self.PC + 1] & 0xFF)
        else:
            setattr(self, src, self.memory[self.PC + 1] & 0xFF)
        self.PC += 1
        return True


    def NOP(self):
        # NOP: do nothing (4 cycles)
        return True
    


    def cycle(self):
        # =Fetch=
        self.opcode = self.memory[self.PC]  # instructions from gb rom        
        self.PC += 1
        # =Decode=
        if self.opcode == 0xCB:
            #operands = self.prefixed[self.opcode].operands
            # TODO: fix cycles
            self.opcode = self.memory[self.PC]
            self.PC += 1
            handler = self.opcode_table.get(self.opcode)
            self.cycles += self.prefixed[self.opcode].cycles
        else:
            handler = self.opcode_table.get(self.opcode)
            self.cycles += self.regular[self.opcode].cycles
        # =Execute=
        s = self.registers[self.opcode & 0x07]
        d = self.registers[(self.opcode >> 3) & 0x07]
        i = None #immediate value TODO
        if handler:

            result = handler(s, d, i)
            if result is False:
                increment_PC = False
        



    