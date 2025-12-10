from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from cpu import CPU
    from ppu import PPU


class Memory:
    def __init__(self):
        # =Registers=
        self.rom_bank0 = [0] * 0x4000   # 0x0000 - 0x3FFF: 16kb ROM bank 0
        self.rom_bank1 = [0] * 0x4000   # 0x4000 - 0x7FFF: 16kb ROM bank 1 (switchable via mapper)
        self.vram = [0] * 0x2000        # 0x8000 - 0x9FFF: 8kb VRAM
        self.eram = [0] * 0x2000        # 0xA000 - 0xBFFF: 8kb ext cart RAM
        self.wram = [0] * 0x2000        # 0xC000 - 0xDFFF: 8kb work RAM
        # Echo RAM mirrors C000-DDFF (optional, handled as alias later)
        self.eram_echo = [0] * 0x2000   # 0xE000 - 0xFDFF: forbidden, can point to same array
        self.oam = [0] * 0xA0           # 0xFE00 - 0xFE9F: Sprite Attribute Table (OAM) 160
                                        # 0xFEA0 - 0xFEFF: forbidden
        self.io_regs = [0] * 0x80       # 0xFF00 - 0xFF7F: IO Registers
        self.hram = [0] * 0x7F          # 0xFF80 - 0xFFFE: HRAM
        self.interrupt_enable = 0       # 0xFFFF: IE Interrupt Enable
        self.interrupt_flag = 0         # 0xFF0F: IF

        # =Timers=
        self.DIV = 0
        self.TIMA = 0
        self.TMA = 0
        self.TAC = 0
        self.timer_periods = {
            0: 1024,
            1: 16,
            2: 64,
            3: 256,
        }
        self.div_counter = 0
        self.tima_counter = 0

        self.cpu: Optional["CPU"] = None
        self.ppu: Optional["PPU"] = None
        # field to store serial data (FF01)
        self.serial_data = 0
        # blarrrg
        self.test_output = []

    def __getitem__(self, addr):
        addr &= 0xFFFF

        if 0x0000 <= addr <= 0x3FFF:
            return self.rom_bank0[addr]
        elif 0x4000 <= addr <= 0x7FFF:
            return self.rom_bank1[addr - 0x4000]
        elif 0x8000 <= addr <= 0x9FFF:
            return self.vram[addr - 0x8000]
        elif 0xA000 <= addr <= 0xBFFF:
            return self.eram[addr - 0xA000]
        elif 0xC000 <= addr <= 0xDFFF:
            return self.wram[addr - 0xC000]
        elif 0xE000 <= addr <= 0xFDFF:
            return self.wram[addr - 0xE000]
        elif 0xFEA0 <= addr <= 0xFEFF:
            return 0
        elif 0xFE00 <= addr <= 0xFE9F:
            return self.oam[addr - 0xFE00]
        elif 0xFF00 <= addr <= 0xFF7F:
            if addr == 0xFF00: return 0xFF     
            elif addr == 0xFF04: return self.DIV   
            elif addr == 0xFF05: return self.TIMA   
            elif addr == 0xFF06: return self.TMA               
            elif addr == 0xFF07: return self.TAC                
            elif addr == 0xFF0F: return 0xE0 | (self.interrupt_flag & 0x1F)                
            elif 0xFF40 <= addr <= 0xFF4B and self.ppu is not None:
                ppu = self.ppu
                if addr == 0xFF40: return ppu.LCDC
                elif addr == 0xFF41: return ppu.STAT
                elif addr == 0xFF42: return ppu.SCY
                elif addr == 0xFF43: return ppu.SCX
                elif addr == 0xFF44: return ppu.LY
                elif addr == 0xFF45: return ppu.LYC
                elif addr == 0xFF46: return ppu.DMA
                elif addr == 0xFF47: return ppu.BGP
                elif addr == 0xFF48: return ppu.OBP0
                elif addr == 0xFF49: return ppu.OBP1
                elif addr == 0xFF4A: return ppu.WY
                elif addr == 0xFF4B: return ppu.WX               
            elif addr == 0xFF4D: return 0xFF               

            return self.io_regs[addr - 0xFF00]
        elif 0xFF80 <= addr <= 0xFFFE:
            return self.hram[addr - 0xFF80]
        elif addr == 0xFFFF:
            return self.interrupt_enable
        else:
            # Echo RAM and unused areas
            return 0xFF

    def __setitem__(self, addr, value):
        addr &= 0xFFFF
        value &= 0xFF
        """# Detect potential MBC writes (future) TODO
        if 0x2000 <= addr <= 0x3FFF:
        # This is where MBC1/2/3/5 handle ROM bank switching
            self.rom_bank0[addr] = value
        elif 0x4000 <= addr <= 0x7FFF:
            self.rom_bank1[addr - 0x4000] = value"""
        if 0x0000 <= addr <= 0x7FFF:
            return
        elif 0x8000 <= addr <= 0x9FFF:
            self.vram[addr - 0x8000] = value
        elif 0xA000 <= addr <= 0xBFFF:
            self.eram[addr - 0xA000] = value
        elif 0xC000 <= addr <= 0xDFFF:
            self.wram[addr - 0xC000] = value
        elif 0xE000 <= addr <= 0xFDFF:
            self.wram[addr - 0xE000] = value
        elif 0xFE00 <= addr <= 0xFE9F:
            self.oam[addr - 0xFE00] = value
        elif 0xFF00 <= addr <= 0xFF7F:
            self.io_regs[addr - 0xFF00] = value
            if addr == 0xFF01:
                self.serial_data = value
            elif addr == 0xFF02:
                if value == 0x81:
                    # CPU test expects the last value written to FF01 to be "printed"
                    char = chr(self.serial_data)
                    print(char, end='', flush=True)      # or append to a test_output list
                    self.test_output.append(char)
                    self.serial_data = 0     # clear after printing
            elif addr == 0xFF04:
                self.DIV = 0
                self.DIV_counter = 0
            elif addr == 0xFF05: self.TIMA = value
            elif addr == 0xFF06: self.TMA = value
            elif addr == 0xFF07: self.TAC = value & 0x07   # lower 3 bits used
            elif addr == 0xFF0F:
                self.interrupt_flag = value & 0x1F  # 0001 1111
                # once cpu attached, wake from HALT
                if self.cpu is not None:
                    self.cpu.on_interrupt_flag_changed()
            elif 0xFF40 <= addr <= 0xFF4B and self.ppu is not None:
                ppu = self.ppu
                if addr == 0xFF40:  # LCDC
                    ppu.LCDC = value
                elif addr == 0xFF41:  # STAT
                    # preserve bits 0,1,2:
                    read_bits = self.ppu.STAT & 0x07
                    write = value & 0xF8
                    ppu.STAT = read_bits | write
                elif addr == 0xFF42:  # SCY
                    ppu.SCY = value
                elif addr == 0xFF43:  # SCX
                    ppu.SCX = value
                elif addr == 0xFF44:  # LY — writing resets it to 0
                    ppu.LY = 0
                elif addr == 0xFF45:  # LYC
                    ppu.LYC = value
                elif addr == 0xFF46:  # DMA
                    ppu.start_dma(value)
                elif addr == 0xFF47:  # BGP
                    ppu.BGP = value
                elif addr == 0xFF48:  # OBP0
                    ppu.OBP0 = value
                elif addr == 0xFF49:  # OBP1
                    ppu.OBP1 = value
                elif addr == 0xFF4A:  # WY
                    ppu.WY = value
                elif addr == 0xFF4B:  # WX
                    ppu.WX = value
        elif 0xFF80 <= addr <= 0xFFFE:
            self.hram[addr - 0xFF80] = value
        elif addr == 0xFFFF:
            self.interrupt_enable = value 
        # ROM is read-only, so writes are ignored

    def load_rom(self, rom_data):
        # load 32kb for now, figure rest later TODO banking
        for i in range(min(len(rom_data), 0x4000)):
            self.rom_bank0[i] = rom_data[i]
        if len(rom_data) > 0x4000:
            for i in range(min(len(rom_data) - 0x4000, 0x4000)):
                self.rom_bank1[i] = rom_data[i + 0x4000]

    def update_timers(self, cycles):
        # DIV++ ever 256 cycles
        self.div_counter = (self.div_counter + cycles) & 0xFFFF
        while self.div_counter >= 256:
            self.div_counter -= 256
            self.DIV = (self.DIV + 1) & 0xFF
        # timer enabled
        if self.TAC & 0x04:
            period = self.timer_periods[self.TAC & 0x03]
            self.tima_counter += cycles

            while self.tima_counter >= period:
                self.tima_counter -= period

                if self.TIMA == 0xFF:
                    self.TIMA = self.TMA
                    # interrupt
                    self.interrupt_flag |= 0x04
                else:
                    self.TIMA = (self.TIMA + 1) & 0xFF