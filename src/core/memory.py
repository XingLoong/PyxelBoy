class Memory:
    def __init__(self):
        self.rom_bank0 = [0] * 0x4000   # 0x0000 - 0x3FFF: 16kb ROM bank 0
        self.rom_bank1 = [0] * 0x4000   # 0x4000 - 0x7FFF: 16kb ROM bank 1 (switchable via mapper)
        self.vram = [0] * 0x2000        # 0x8000 - 0x9FFF: 8kb VRAM
        self.eram = [0] * 0x2000        # 0xA000 - 0xBFFF: 8kb ext cart RAM
        self.wram = [0] * 0x2000        # 0xC000 - 0xDFFF: 8kb work RAM
        # Echo RAM mirrors C000-DDFF (optional, handled as alias later)
        # self.eram_echo = self.wram    # 0xE000 - 0xFDFF: forbidden, can point to same array
        self.oam = [0] * 0xA0           # 0xFE00 - 0xFE9F: Sprite Attribute Table (OAM) 160
                                        # 0xFEA0 - 0xFEFF: forbidden
        self.io_regs = [0] * 0x80       # 0xFF00 - 0xFF7F: IO Registers
        self.hram = [0] * 0x7F          # 0xFF80 - 0xFFFE: HRAM
        self.interrupt_enable = 0       # 0xFFFF: IE Interrup Enable

    def __getitem__(self, addr):
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
        elif 0xFE00 <= addr <= 0xFE9F:
            return self.oam[addr - 0xFE00]
        elif 0xFF00 <= addr <= 0xFF7F:
            return self.io_regs[addr - 0xFF00]
        elif 0xFF80 <= addr <= 0xFFFE:
            return self.hram[addr - 0xFF80]
        elif addr == 0xFFFF:
            return self.interrupt_enable
        else:
            # Echo RAM and unused areas
            return 0

    def __setitem__(self, addr, value):
        # Detect potential MBC writes (future) TODO
        if 0x2000 <= addr <= 0x3FFF:
        # This is where MBC1/2/3/5 handle ROM bank switching
            self.rom_bank0[addr] = value
        elif 0x4000 <= addr <= 0x7FFF:
            self.rom_bank1[addr - 0x4000] = value
        elif 0x8000 <= addr <= 0x9FFF:
            self.vram[addr - 0x8000] = value
        elif 0xA000 <= addr <= 0xBFFF:
            self.eram[addr - 0xA000] = value
        elif 0xC000 <= addr <= 0xDFFF:
            self.wram[addr - 0xC000] = value
        elif 0xFE00 <= addr <= 0xFE9F:
            self.oam[addr - 0xFE00] = value
        elif 0xFF00 <= addr <= 0xFF7F:
            self.io_regs[addr - 0xFF00] = value
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

    