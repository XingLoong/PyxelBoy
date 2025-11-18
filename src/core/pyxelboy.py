from .cpu import CPU
from .memory import Memory
from .opcodes_loader import load_opcodes
from pathlib import Path

class PyxelBoy:
    def __init__(self, rom_path: str | None = None):
        # load Opcode tables
        # Get the path relative to this file's location
        core_dir = Path(__file__).parent  # src/core/
        project_root = core_dir.parent.parent  # PyxelBoy/
        opcode_file = project_root / "data" / "Opcodes.json"
        
        prefixed, regular = load_opcodes(opcode_file)
        
        self.memory = Memory()
        self.cpu = CPU(prefixed, regular, self.memory)
        
        if rom_path:
            self.load_rom(rom_path)

        self.running = False


    def load_rom(self, rom_path: str):
        # load rom
        with open(rom_path, "rb") as f:
            rom_data = f.read()
        self.memory.load_rom(rom_data)

    def run(self, cycles: int = 1000):
        # temp value
        for _ in range(cycles):
            self.cpu.cycle()
