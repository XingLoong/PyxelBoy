from .instructions import Operand, Instruction
from pathlib import Path


class CPU:
    def __init__(self, memory):
        self.memory = memory
        self.halted = False
        self.halt_bug = False
        self.stopped = False
        self.IME = 0
        self.enable_IME_after = False
        self.cycles = 0
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
        self.opcodes = 0
        # TODO cleanup dsi?
        self.opcode_table = { 
            0x00: lambda d=None,s=None,i=None: self.NOP(),
            0x10: lambda d=None,s=None,i=None: self.STOP(),
            0x02: lambda d=None,s=None,i=None: self.LD_mem_A('BC'),
            0x12: lambda d=None,s=None,i=None: self.LD_mem_A('DE'),
            0x22: lambda d=None,s=None,i=None: self.LD_mem_A('HL+'),
            0x32: lambda d=None,s=None,i=None: self.LD_mem_A('HL-'),
            0x0A: lambda d=None,s=None,i=None: self.LD_A_mem('BC'),
            0x1A: lambda d=None,s=None,i=None: self.LD_A_mem('DE'),
            0x2A: lambda d=None,s=None,i=None: self.LD_A_mem('HL+'),
            0x3A: lambda d=None,s=None,i=None: self.LD_A_mem('HL-'),
            0x03: lambda d=None,s=None,i=None: self.INC_rr('BC'),
            0x13: lambda d=None,s=None,i=None: self.INC_rr('DE'),
            0x23: lambda d=None,s=None,i=None: self.INC_rr('HL'),
            0x33: lambda d=None,s=None,i=None: self.INC_rr('SP'),
            0x0B: lambda d=None,s=None,i=None: self.DEC_rr('BC'),
            0x1B: lambda d=None,s=None,i=None: self.DEC_rr('DE'),
            0x2B: lambda d=None,s=None,i=None: self.DEC_rr('HL'),
            0x3B: lambda d=None,s=None,i=None: self.DEC_rr('SP'),
            0x01: lambda d=None,s=None,i=None: self.LD_rr_nn('BC'),
            0x11: lambda d=None,s=None,i=None: self.LD_rr_nn('DE'),
            0x21: lambda d=None,s=None,i=None: self.LD_rr_nn('HL'),
            0x31: lambda d=None,s=None,i=None: self.LD_rr_nn('SP'),
            0x09: lambda d=None,s=None,i=None: self.ADD_HL_rr('BC'),
            0x19: lambda d=None,s=None,i=None: self.ADD_HL_rr('DE'),
            0x29: lambda d=None,s=None,i=None: self.ADD_HL_rr('HL'),
            0x39: lambda d=None,s=None,i=None: self.ADD_HL_rr('SP'),
            0x08: lambda d=None,s=None,i=None: self.LD_nn_SP(),

            0x07: lambda d=None,s=None,i=None: self.RLCA(), 
            0x17: lambda d=None,s=None,i=None: self.RLA(),
            0x0F: lambda d=None,s=None,i=None: self.RRCA(),
            0x1F: lambda d=None,s=None,i=None: self.RRA(),

            0x27: lambda d=None,s=None,i=None: self.DAA(),  
            0x37: lambda d=None,s=None,i=None: self.SCF(),
            0x2F: lambda d=None,s=None,i=None: self.CPL(),
            0x3F: lambda d=None,s=None,i=None: self.CCF(),

            0x18: lambda d=None,s=None,i=None: self.JR(True),
            0x20: lambda d=None,s=None,i=None: self.JR((self.F & 0x80) == 0),
            0x28: lambda d=None,s=None,i=None: self.JR((self.F & 0x80) != 0),
            0x30: lambda d=None,s=None,i=None: self.JR((self.F & 0x10) == 0),
            0x38: lambda d=None,s=None,i=None: self.JR((self.F & 0x10) != 0),

            0xC0: lambda d=None,s=None,i=None: self.RET_cc((self.F & 0x80) == 0),
            0xC8: lambda d=None,s=None,i=None: self.RET_cc((self.F & 0x80) != 0),
            0xD0: lambda d=None,s=None,i=None: self.RET_cc((self.F & 0x10) == 0),
            0xD8: lambda d=None,s=None,i=None: self.RET_cc((self.F & 0x10) != 0),
            0xC9: lambda d=None,s=None,i=None: self.RET(),
            0xD9: lambda d=None,s=None,i=None: self.RETI(),
            # POP
            0xC1: lambda d=None,s=None,i=None: self.POP_rr('BC'),
            0xD1: lambda d=None,s=None,i=None: self.POP_rr('DE'),
            0xE1: lambda d=None,s=None,i=None: self.POP_rr('HL'),
            0xF1: lambda d=None,s=None,i=None: self.POP_rr('AF'),
            #PUSH
            0xC5: lambda d=None,s=None,i=None: self.PUSH_rr('BC'),
            0xD5: lambda d=None,s=None,i=None: self.PUSH_rr('DE'),
            0xE5: lambda d=None,s=None,i=None: self.PUSH_rr('HL'),
            0xF5: lambda d=None,s=None,i=None: self.PUSH_rr('AF'),

            0xE0: lambda d=None,s=None,i=None: self.LDH_n_A(),
            0xF0: lambda d=None,s=None,i=None: self.LDH_A_n(),
            0xE2: lambda d=None,s=None,i=None: self.LD_C_A(),
            0xF2: lambda d=None,s=None,i=None: self.LD_A_C(),
            0xEA: lambda d=None,s=None,i=None: self.LD_nn_A(),
            0xFA: lambda d=None,s=None,i=None: self.LD_A_nn(),
            # unconditional
            0xC3: lambda d=None,s=None,i=None: self.JP_nn(),    
            # conditional
            0xC2: lambda d=None,s=None,i=None: self.JP_cc_nn((self.F & 0x80) == 0), #nz
            0xCA: lambda d=None,s=None,i=None: self.JP_cc_nn((self.F & 0x80) != 0), #z
            0xD2: lambda d=None,s=None,i=None: self.JP_cc_nn((self.F & 0x10) == 0), #nc
            0xDA: lambda d=None,s=None,i=None: self.JP_cc_nn((self.F & 0x10) != 0), #c
            #HL indirect
            0xE9: lambda d=None,s=None,i=None: self.JP_HL(),
            # CALL: unconditional
            0xCD: lambda d=None,s=None,i=None: self.CALL_nn(),
            # conditional
            0xC4: lambda d=None,s=None,i=None: self.CALL_cc_nn((self.F & 0x80) == 0),
            0xCC: lambda d=None,s=None,i=None: self.CALL_cc_nn((self.F & 0x80) != 0),
            0xD4: lambda d=None,s=None,i=None: self.CALL_cc_nn((self.F & 0x10) == 0),
            0xDC: lambda d=None,s=None,i=None: self.CALL_cc_nn((self.F & 0x10) != 0),
            # RST
            # ALU mix
            0xC6: lambda d=None,s=None,i=None: self.ADD_A_n(),
            0xD6: lambda d=None,s=None,i=None: self.SUB_A_n(),
            0xE6: lambda d=None,s=None,i=None: self.AND_n(),
            0xF6: lambda d=None,s=None,i=None: self.OR_n(),
            0xCE: lambda d=None,s=None,i=None: self.ADC_A_n(),
            0xDE: lambda d=None,s=None,i=None: self.SBC_A_n(),
            0xEE: lambda d=None,s=None,i=None: self.XOR_n(),
            0xFE: lambda d=None,s=None,i=None: self.CP_n(),
            # DI
            0xF3: lambda d=None,s=None,i=None: self.DI(),
            # EI
            0xFB: lambda d=None,s=None,i=None: self.EI(),
            # ADD SP, LDHL LDSP
            0xE8: lambda d=None,s=None,i=None: self.ADD_SP_n(),
            0xF8: lambda d=None,s=None,i=None: self.LD_HL_SP_n(),
            0xF9: lambda d=None,s=None,i=None: self.LD_SP_HL(),
        }
        self.prefixed_table = {}
        
        self._init_LD_r_r()
        self._init_ADD_A_r()
        self._init_ADC_A_r()
        self._init_SUB_A_r()
        self._init_SBC_A_r()
        self._init_AND_A_r()
        self._init_OR_A_r()
        self._init_XOR_A_r()
        self._init_CP_A_r()
        self._init_INC_r()
        self._init_DEC_r()
        self._init_LD_r_n()
        self._init_RST_n()

        self._init_00_3F()
        self._init_BIT_n_r()
        self._init_RES_n_r()
        self._init_SET_n_r()

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
                if opcode == 0x76:
                    self.opcode_table[opcode] = (lambda d=None,s=None,i=None: self.HALT())
                    continue
                self.opcode_table[opcode] = (lambda d=dest,s=src,i=None: self.LD_r_r(d, s))

    def LD_r_r(self, dest, src):
        if dest == '(HL)' and src == '(HL)':
            raise Exception(f"LD (HL),(HL) is invalid {self.opcode}")
        
        if dest == '(HL)':
            self.memory[self.HL] = getattr(self, src)
        elif src == '(HL)':
            setattr(self, dest, self.memory[self.HL])
        else:
            setattr(self, dest, getattr(self, src))
        
        return 8 if (dest == '(HL)' or src == '(HL)') else 4

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
        return 8 if src == '(HL)' else 4
        
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
        if ((self.A & 0xF) + (r_value & 0xF) + carry) > 0xF:
            self.F |= 0x20  # h
        if result > 0xFF:
            self.F |= 0x10  # c
        self.A = result & 0xFF
        return 8 if src == '(HL)' else 4

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
        if (self.A & 0xF) < (r_value & 0xF):
            self.F |= 0x20
        if self.A < r_value:
            self.F |= 0x10
        
        self.A = result & 0xFF
        return 8 if src == '(HL)' else 4
    
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
        return 8 if src == '(HL)' else 4

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
        return 8 if src == '(HL)' else 4
    
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
        return 8 if src == '(HL)' else 4

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
        return 8 if src == '(HL)' else 4

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

        return 8 if src == '(HL)' else 4

    def _init_INC_r(self):      # 0-3x4 + 0-3xC
        for col, src in enumerate(self.registers):
            # 4 12 20 28
            opcode = 0x04 + (col * 0x08)
            self.opcode_table[opcode] = lambda d=None,s=src,i=None: self.INC_r(s)
    
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
        
        return 12 if src == '(HL)' else 4

    def _init_DEC_r(self):      # 0-3x5 + 0-3xD
        for col, src in enumerate(self.registers):
            opcode = 0x05 + (col * 0x08)
            self.opcode_table[opcode] = lambda d=None,s=src,i=None: self.DEC_r(s)      

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
        if (r_value & 0x0F) == 0:
            self.F |= 0x20

        return 12 if src == '(HL)' else 4

    def _init_LD_r_n(self):     # 0-3x6 + 0-3xE
        for col, src in enumerate(self.registers):
            opcode = 0x06 + (col * 0x08)
            self.opcode_table[opcode] = lambda d=None,s=src,i=None: self.LD_r_n(s)
    
    def LD_r_n(self, src):
        if src == '(HL)':
            self.memory[self.HL] = (self.memory[self.PC] & 0xFF)
        else:
            setattr(self, src, self.memory[self.PC] & 0xFF)
        self.PC += 1
        return 12 if src == '(HL)' else 8

    def LD_mem_A(self, src):    
        if src == 'BC':
            self.memory[self.BC] = self.A
        elif src == 'DE':
            self.memory[self.DE] = self.A
        elif src == 'HL+':
            self.memory[self.HL] = self.A
            self.HL = (self.HL + 1) & 0xFFFF
        elif src == 'HL-':
            self.memory[self.HL] = self.A
            self.HL = (self.HL - 1) & 0xFFFF
        return 8
    
    def LD_A_mem(self, src):
        if src == 'BC':
            self.A = self.memory[self.BC]
        elif src == 'DE':
            self.A = self.memory[self.DE]
        elif src == 'HL+':
            self.A = self.memory[self.HL]
            self.HL = (self.HL + 1) & 0xFFFF
        elif src == 'HL-':
            self.A = self.memory[self.HL]
            self.HL = (self.HL - 1) & 0xFFFF    
        return 8
    
    def INC_rr(self, src):
        if src == 'BC':
            self.BC = (self.BC + 1) & 0xFFFF
        elif src == 'DE':
            self.DE = (self.DE + 1) & 0xFFFF
        elif src == 'HL':
            self.HL = (self.HL + 1) & 0xFFFF
        elif src == 'SP':
            self.SP = (self.SP + 1) & 0xFFFF
        return 8
    
    def DEC_rr(self, src):
        if src == 'BC':
            self.BC = (self.BC - 1) & 0xFFFF
        elif src == 'DE':
            self.DE = (self.DE - 1) & 0xFFFF
        elif src == 'HL':
            self.HL = (self.HL - 1) & 0xFFFF
        elif src == 'SP':
            self.SP = (self.SP - 1) & 0xFFFF
        return 8
    
    def LD_rr_nn(self, src): 
        r_value = self.memory[self.PC] | (self.memory[self.PC + 1] << 8)  # endianess
        setattr(self, src, r_value)
        self.PC += 2
        return 12
        
    def ADD_HL_rr(self, src):
        r_value = getattr(self, src)
        result = self.HL + r_value

        # z remains, n reset, h c set
        self.F &= 0x80
        
        if ((self.HL & 0x0FFF) + (r_value & 0x0FFF)) > 0x0FFF:
            self.F |= 0x20
        if result > 0xFFFF:
            self.F |= 0x10
        self.HL = result & 0xFFFF
        return 8
    
    def NOP(self):
        # NOP: do nothing (4 cycles)
        return 4
    
    def STOP(self):
        self.PC += 1
        # TODO self.stopped = True
        return 4
    
    def HALT(self):
        pending = self.memory.interrupt_flag & self.memory.interrupt_enable
        if pending == 0:
            # no pending interrupts -> enter true HALT: CPU stops until IF has a matching bit
            self.halted = True
        else:
            # An interrupt is pending but IME == 0 -> HALT bug occurs:
            # the next instruction fetch will not increment PC (i.e. same PC used twice).
            self.halt_bug = True
        return 4  
    
    def LD_nn_SP(self):
        # read immediate 16-bit address (little endian)
        low = self.memory[self.PC]
        high = self.memory[self.PC + 1]
        addr = (high << 8) | low

        self.memory[addr] = self.SP & 0xFF
        self.memory[addr + 1] = (self.SP >> 8) & 0xFF

        self.PC += 2
        return 20

    def RLCA(self):
        # shift bit7 -> bit0 and carry
        carry = (self.A >> 7) & 1
        self.A = ((self.A << 1) | carry) & 0xFF
        self.F = 0
        if carry:
            self.F |= 0x10
        return 4
    
    def RLA(self):
        # shift through carry
        carry_in = (self.F >> 4) & 1    # c
        carry_out = (self.A >> 7) & 1   # bit7
        self.A = ((self.A << 1) | carry_in) & 0xFF
        self.F = 0
        if carry_out:
            self.F |= 0x10
        return 4
    
    def RRCA(self):
        # shifht right
        carry = self.A & 1
        self.A = ((carry << 7) | (self.A >> 1)) & 0xFF
        self.F = 0
        if carry:
            self.F |= 0x10
        return 4
    
    def RRA(self):
        # through carry
        carry_in = (self.F >> 4) & 1
        carry_out = self.A & 1
        self.A = ((carry_in << 7) | (self.A >> 1)) & 0xFF
        self.F = 0
        if carry_out:
            self.F |= 0x10
        return 4
    
    def DAA(self):
        # Binary Coded Decimal - funky maths, relies on the n flag (sub)
        a = self.A

        n = self.F & 0x40
        h = self.F & 0x20
        c = self.F & 0x10

        correction = 0
        new_carry = False
        # addition
        if not n:
            if c or a > 0x99:
                correction |= 0x60
                new_carry = True
            if h or (a & 0x0F) > 0x09:
                correction |= 0x06
        # sub
        else:
            if c:
                correction |= 0x60
                new_carry = True
            if h:
                correction |= 0x06
        if n:
            a = (a - correction) & 0xFF
        else:
            a = (a + correction) & 0xFF
        # update flags n remains, h cleared
        self.A = a
        self.F = 0

        if n:
            self.F |= 0x40
        # z
        if a == 0:
            self.F |= 0x80
        # c
        if new_carry:
            self.F |= 0x10

        return 4

    def CPL(self):
        # invert A bits
        self.A ^= 0xFF
        self.F |= 0x60
        return 4
    
    def SCF(self):
        # preserve z, reset nh, set c
        self.F &= 0x80
        self.F |= 0x10
        return 4
    
    def CCF(self):
        # preserve z, reset nh, switch c
        carry = (self.F >> 4) & 1
        self.F &= 0x80
        if not carry:
            self.F |= 0x10
        return 4

    def JR(self, condition=True):
        offset = self.memory[self.PC]
        self.PC += 1
        if offset & 0x80:
            offset = offset - 0x100
        if condition:
            self.PC = (self.PC + offset) & 0xFFFF
        return 12 if condition else 8

    def RET_cc(self, condition):
        if condition:
            self.PC = self.memory[self.SP] | (self.memory[self.SP + 1] << 8)
            self.SP += 2
            return 20
        return 8

    def RET(self):
        self.PC = self.memory[self.SP] | (self.memory[self.SP + 1] << 8)
        self.SP += 2
        return 16

    def RETI(self):     #TODO interrupts
        result= self.RET()
        self.IME = 1
        return result

    def POP_rr(self, src):
        low = self.memory[self.SP]
        high = self.memory[self.SP + 1]
        self.SP += 2

        r_value = (high << 8) | low
        if src == 'AF':
            # lower nibble of F is always 0
            self.A = (r_value >> 8) & 0xFF
            self.F = r_value & 0xF0
        else:
            setattr(self, src, r_value)
        return 12
    
    def PUSH_rr(self, src):
        if src == 'AF':
            r_value = (self.A << 8) | (self.F & 0xF0)
        else:
            r_value = getattr(self, src)
        self.SP -= 2
        self.memory[self.SP] = r_value & 0xFF
        self.memory[self.SP + 1] = (r_value >> 8)
        return 16
    
    def LDH_n_A(self):
        offset = self.memory[self.PC]
        self.memory[0xFF00 + offset] = self.A
        self.PC += 1
        return 12
    
    def LDH_A_n(self):
        offset = self.memory[self.PC]
        self.A = self.memory[0xFF00 + offset]
        self.PC += 1
        return 12
    
    def LD_C_A(self):
        self.memory[0xFF00 + self.C] = self.A
        return 8
    
    def LD_A_C(self):
        self.A = self.memory[0xFF00 + self.C]
        return 8
    
    def LD_nn_A(self):
        low = self.memory[self.PC]
        high = self.memory[self.PC + 1]
        addr = (high << 8) | low
        self.memory[addr] = self.A
        self.PC +=2
        return 16

    def LD_A_nn(self):
        low = self.memory[self.PC]
        high = self.memory[self.PC + 1]
        addr = (high << 8) | low
        self.A = self.memory[addr]
        self.PC += 2
        return 16

    def JP_nn(self):
        low = self.memory[self.PC]
        high = self.memory[self.PC + 1]
        self.PC = (high << 8) | low
        return 16
    
    def JP_cc_nn(self, condition):
        low = self.memory[self.PC]
        high = self.memory[self.PC + 1]
        self.PC +=2
        if condition:
            self.PC = (high << 8) | low
            return 16
        return 12
           
    def JP_HL(self):
        self.PC = self.HL
        return 4
    
    def CALL_nn(self):
        low = self.memory[self.PC]
        high = self.memory[self.PC + 1]
        addr = (high << 8) | low
        
        # push PC after nn
        ret_addr = self.PC + 2
        self.SP -= 2
        self.memory[self.SP] = ret_addr & 0xFF
        self.memory[self.SP + 1] = (ret_addr >> 8) & 0xFF

        self.PC = addr
        return 24

    def CALL_cc_nn(self, condition):
        low = self.memory[self.PC]
        high = self.memory[self.PC + 1]
        addr = (high << 8) | low

        if condition:
            ret_addr = self.PC + 2
            self.SP -= 2
            self.memory[self.SP] = ret_addr & 0xFF
            self.memory[self.SP + 1] = (ret_addr >> 8) & 0xFF

            self.PC = addr
            return 24
        else:
            self.PC += 2    #skip nn
            return 12

    def _init_RST_n(self):      #RST
        for col in range(8):
            opcode = 0xC7 + (col * 0x08)
            value = col * 0x08

            def make_RST(v):
                def handler(d=None, s=None, i=None):
                    return self.RST_n(v)
                return handler
            
            self.opcode_table[opcode] = make_RST(value)
            
    def RST_n(self, value):
        self.SP -= 2
        self.memory[self.SP] = self.PC & 0xFF
        self.memory[self.SP + 1] = (self.PC >> 8)
        self.PC = value
        return 32
    # ALU n
    def ADD_A_n(self):
        n = self.memory[self.PC]
        self.PC += 1
        result = self.A + n
        # Flags
        self.F = 0
        if (result & 0xFF) == 0:
            self.F |= 0x80  # z
        if ((self.A & 0xF) + (n & 0xF)) > 0xF:
            self.F |= 0x20  # h
        if result > 0xFF:
            self.F |= 0x10  # c
        self.A = result & 0xFF
        return 8

    def ADC_A_n(self):
        n = self.memory[self.PC]
        self.PC += 1
        carry = 1 if (self.F & 0x10) else 0
        result = self.A + n + carry
        self.F = 0
        if (result & 0xFF) == 0:
            self.F |= 0x80
        if ((self.A & 0xF) + (n & 0xF) + carry) > 0xF:
            self.F |= 0x20
        if result > 0xFF:
            self.F |= 0x10
        self.A = result & 0xFF
        return 8

    def SUB_A_n(self):
        n = self.memory[self.PC]
        self.PC += 1
        result = self.A - n
        self.F = 0x40  # n
        if (result & 0xFF) == 0:
            self.F |= 0x80
        if (self.A & 0xF) < (n & 0xF):
            self.F |= 0x20
        if self.A < n:
            self.F |= 0x10
        self.A = result & 0xFF
        return 8

    def SBC_A_n(self):
        n = self.memory[self.PC]
        self.PC += 1
        carry = 1 if (self.F & 0x10) else 0
        result = self.A - n - carry
        self.F = 0x40  # n
        if (result & 0xFF) == 0:
            self.F |= 0x80
        if (self.A & 0xF) < ((n & 0xF) + carry):
            self.F |= 0x20
        if result < 0:
            self.F |= 0x10
        self.A = result & 0xFF
        return 8

    def AND_n(self):
        n = self.memory[self.PC]
        self.PC += 1
        self.A &= n
        self.F = 0x20  # h
        if self.A == 0:
            self.F |= 0x80
        return 8

    def OR_n(self):
        n = self.memory[self.PC]
        self.PC += 1
        self.A |= n
        self.F = 0
        if self.A == 0:
            self.F |= 0x80
        return 8

    def XOR_n(self):
        n = self.memory[self.PC]
        self.PC += 1
        self.A ^= n
        self.F = 0
        if self.A == 0:
            self.F |= 0x80
        return 8

    def CP_n(self):
        n = self.memory[self.PC]
        self.PC += 1
        result = self.A - n
        self.F = 0x40  # n
        if (result & 0xFF) == 0:
            self.F |= 0x80
        if (self.A & 0xF) < (n & 0xF):
            self.F |= 0x20
        if result < 0:
            self.F |= 0x10
        return 8

    def DI(self):
        self.IME = 0
        return 4
    
    def EI(self):       
        self.enable_IME_after = True
        return 4

    def ADD_SP_n(self):
        n = self.memory[self.PC]
        self.PC += 1
        signed = n if n < 0x80 else n - 0x100   # convert to signed
        result = (self.SP + signed) & 0xFFFF
        
        self.F = 0
        if ((self.SP & 0xF) + (signed & 0xF)) > 0xF:
            self.F |= 0x20  # h
        if ((self.SP & 0xFF) + (signed & 0xFF)) > 0xFF:
            self.F |= 0x10  # c
        
        self.SP = result
        return 16

    def LD_HL_SP_n(self):
        n = self.memory[self.PC]
        self.PC += 1
        signed = n if n < 0x80 else n - 0x100   
        result = (self.SP + signed) & 0xFFFF

        self.F = 0
        if ((self.SP & 0xF) + (signed & 0xF)) > 0xF:
            self.F |= 0x20  # h
        if ((self.SP & 0xFF) + (signed & 0xFF)) > 0xFF:
            self.F |= 0x10  # c
        
        self.HL = result
        return 12

    def LD_SP_HL(self):
        self.SP = self.HL
        return 8
    
    def _init_00_3F(self):
        instr_list = ["RLC","RRC","RL","RR","SLA","SRA","SWAP","SRL"]
        for i, instr in enumerate(instr_list):
            for r_index, src in enumerate(self.registers):
                opcode = i*8 + r_index
                # Create a lambda pointing to the handler with reg
                self.prefixed_table[opcode] = lambda d=None, s=src, i=instr: getattr(self, i)(s)

    def RLC(self, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
            carry = (r_value & 0x80) >> 7
            result = ((r_value << 1) | carry) & 0xFF
            self.memory[self.HL] = result
        else:
            r_value = getattr(self, src)
            carry = (r_value & 0x80) >> 7
            result = ((r_value << 1) | carry) & 0xFF
            setattr(self, src, result)
        
        self.F = 0
        if result == 0:
            self.F |= 0x80
        self.F |= carry << 4
        
        return 16 if src == '(HL)' else 8

    def RRC(self, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
            carry = r_value & 1
            result = ((r_value >> 1) | (carry << 7)) & 0xFF
            self.memory[self.HL] = result
        else:
            r_value = getattr(self, src)
            carry = r_value & 1
            result = ((r_value >> 1) | (carry << 7)) & 0xFF
            setattr(self, src, result)
        
        self.F = 0
        if result == 0:
            self.F |= 0x80
        self.F |= carry << 4
        
        return 16 if src == '(HL)' else 8        
    
    def RL(self, src):
        carry_in = (self.F & 0x10) >> 4
        if src == '(HL)':
            r_value = self.memory[self.HL]
            carry_out = (r_value & 0x80) >> 7
            result = ((r_value << 1) | carry_in) & 0xFF
            self.memory[self.HL] = result
        else:
            r_value = getattr(self, src)
            carry_out = (r_value & 0x80) >> 7
            result = ((r_value << 1) | carry_in) & 0xFF
            setattr(self, src, result)
        
        self.F = 0
        if result == 0:
            self.F |= 0x80
        self.F |= carry_out << 4
        
        return 16 if src == '(HL)' else 8
    
    def RR(self, src):
        carry_in = (self.F & 0x10) >> 4
        if src == '(HL)':
            r_value = self.memory[self.HL]
            carry_out = r_value & 1
            result = ((r_value >> 1) | (carry_in << 7)) & 0xFF
            self.memory[self.HL] = result
        else:
            r_value = getattr(self, src)
            carry_out = r_value & 1
            result = ((r_value >> 1) | (carry_in << 7)) & 0xFF
            setattr(self, src, result)

        self.F = 0
        if result == 0:
            self.F |= 0x80
        self.F |= carry_out << 4

        return 16 if src == '(HL)' else 8 

    def SLA(self, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
            carry = (r_value & 0x80) >> 7
            result = (r_value << 1) & 0xFF
            self.memory[self.HL] = result
        else:
            r_value = getattr(self, src)
            carry = (r_value & 0x80) >> 7
            result = (r_value << 1) & 0xFF
            setattr(self, src, result)
        self.F = 0
        if result == 0:
            self.F |= 0x80
        self.F |= carry << 4
        
        return 16 if src == '(HL)' else 8
            
    def SRA(self, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
            carry = r_value & 1
            result = ((r_value >> 1) | (r_value & 0x80)) & 0xFF    # preserve bit 7
            self.memory[self.HL] = result
        else:
            r_value = getattr(self, src)
            carry = r_value & 1
            result = ((r_value >> 1) | (r_value & 0x80)) & 0xFF 
            setattr(self, src, result)
        
        self.F = 0
        if result == 0:
            self.F |= 0x80
        if carry:
            self.F |= 0x10
        
        return 16 if src == '(HL)' else 8

    def SWAP(self, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
            result = ((r_value >> 4) | (r_value << 4)) & 0xFF
            self.memory[self.HL] = result
        else:
            r_value = getattr(self, src)
            result = ((r_value >> 4) | (r_value << 4)) & 0xFF
            setattr(self, src, result)
        
        self.F = 0
        if result == 0:
            self. F |= 0x80
            
        return 16 if src == '(HL)' else 8
    
    def SRL(self, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
            carry = r_value & 0x1
            result = (r_value >> 1) & 0xFF
            self.memory[self.HL] = result
        else:
            r_value = getattr(self, src)
            carry = r_value & 0x1
            result = (r_value >> 1) & 0xFF
            setattr(self, src, result)

        self.F = 0
        if result == 0:
            self.F |= 0x80
        if carry:
            self.F |= 0x10
        
        return 16 if src == '(HL)' else 8

    def _init_BIT_n_r(self):    # TODO check dsi
        for row in range(8):
            for col, src in enumerate(self.registers):
                opcode = 0x40 + row*8 + col
                self.prefixed_table[opcode] = (lambda n=row,s=src,i=None: self.BIT_n_r(n, s))
                
    def BIT_n_r(self, dest, src):
        if src == '(HL)':
            r_value = self.memory[self.HL]
        else:
            r_value = getattr(self, src)

        mask = 1 << dest
        bit_is_zero = (r_value & mask) == 0
        
        c = self.F & 0x10
        
        self.F = c          # keep c, refresh others
        self.F |= 0x20      # h = 1
        if bit_is_zero:
            self.F |= 0x80
        
        return 12 if src == '(HL)' else 8
    
    def _init_RES_n_r(self):
        for row in range(8):
            for col, src in enumerate(self.registers):
                opcode = 0x80 + row*8 + col
                self.prefixed_table[opcode] = (lambda n=row,s=src,i=None: self.RES_n_r(n, s))

    def RES_n_r(self, dest, src):
        # bit is set to 0, ~ to flip
        mask = ~(1 << dest) & 0xFF
        
        if src == '(HL)':
            r_value = self.memory[self.HL]
            self.memory[self.HL] = r_value & mask
            return 16
        else:
            r_value = getattr(self, src)
            setattr(self, src, r_value & mask)
            return 8

    def _init_SET_n_r(self):
        for row in range(8):
            for col, src in enumerate(self.registers):
                opcode = 0xC0 + row*8 + col
                self.prefixed_table[opcode] = (lambda n=row,s=src,i=None: self.SET_n_r(n, s))

    def SET_n_r(self, dest, src):
        # force bit to 1
        mask = 1 << dest
        
        if src == '(HL)':
            r_value = self.memory[self.HL]
            self.memory[self.HL] = r_value | mask
            return 16
        else:
            r_value = getattr(self, src)
            setattr(self, src, r_value | mask)
            return 8

    def handle_interrupt(self):
        IF = self.memory.interrupt_flag
        IE = self.memory.interrupt_enable
        pending = IF & IE

        if pending == 0:
            return False

        # Find highest-priority interrupt (0-4): VBlank, LCD STAT, Timer, Serial, Joypad
        vectors = [0x40, 0x48, 0x50, 0x58, 0x60]

        for i in range(5):
            if pending & (1 << i):

                # Clear the IF bit
                self.memory.interrupt_flag &= ~(1 << i)

                # Disable IME
                self.IME = 0

                # Push PC on stack
                self.SP -= 1
                self.memory[self.SP] = (self.PC >> 8) & 0xFF
                self.SP -= 1
                self.memory[self.SP] = self.PC & 0xFF

                # Jump to interrupt vector
                
                self.PC = vectors[i]

                # Interrupts takes 20 cycles
                self.cycles += 20
                return True
        
        return False

    def on_interrupt_flag_changed(self):
        # Called when memory writes IF. *Important* to wake from HALT.
        # If halted and matching interrupt becomes pending, un-halt.
        pending = self.memory.interrupt_flag & self.memory.interrupt_enable
        if self.halted and pending != 0:
            # Wake from HALT — the HALT will end and next cycle proceeds normally.
            self.halted = False

    # =CYCLE=
    def cycle(self):
        # =Halt/Stop=
        IF = self.memory.interrupt_flag
        IE = self.memory.interrupt_enable
        pending = IF & IE
        ppu = getattr(self.memory, "ppu", None)
        cycles_used = 0

        # IME + pending interrupt:
        if self.IME and pending:             
            if self.handle_interrupt():
                cycles_used = 20
                self.memory.update_timers(cycles_used)
                
                if ppu is not None:
                    ppu.step(cycles_used)
                return
        # in Halt and no pending interrupt:
        if self.halted:
            if pending == 0:
                # keep halted
                self.cycles += 4
                self.memory.update_timers(4)

                if ppu is not None:
                    ppu.step(4)
                return
            else:
                # wake from halt, and continue
                self.halted = False

        # =Fetch=
        # HALT-bug: suppress PC
        if self.halt_bug:
            self.opcode = self.memory[self.PC]
            self.halt_bug = False
            increment_pc = False
        else:
            self.opcode = self.memory[self.PC]
            increment_pc = True

        if increment_pc:
            self.PC = (self.PC + 1) & 0xFFFF

        # =Decode=
        if self.opcode == 0xCB:
            pref = self.memory[self.PC]
            self.PC = (self.PC + 1) & 0xFFFF
            handler = self.prefixed_table.get(pref)
        else:
            handler = self.opcode_table.get(self.opcode)

        # =Execute=
        s = self.registers[self.opcode & 0x07]
        d = self.registers[(self.opcode >> 3) & 0x07]
        i = None #immediate value TODO

        if handler:
            cycles_used = handler()
            if cycles_used is None:
                cycles_used = 4
        else:
            cycles_used = 4

        self.cycles += cycles_used
        self.memory.update_timers(cycles_used)

        if ppu is not None:
            ppu.step(cycles_used)

        if self.enable_IME_after:
            self.IME = 1
            self.enable_IME_after = False



        # ppu.step(cycles)
        

    