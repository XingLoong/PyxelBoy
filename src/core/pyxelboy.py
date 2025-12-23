from .cpu import CPU
from .ppu import PPU
from .memory import Memory
from .display import Display
from .input import Input
from pathlib import Path
import pygame

class PyxelBoy:
    def __init__(self, rom_path: str | None = None):
        # Get the path relative to this file's location
        core_dir = Path(__file__).parent  # src/core/
        project_root = core_dir.parent.parent  # PyxelBoy/

        
        self.memory = Memory()
        self.cpu = CPU(self.memory)
        self.display = Display(scale=4)
        self.ppu = PPU(self.memory, self.handle_frame)
        self.input = Input()
        self.memory.cpu = self.cpu
        self.memory.ppu = self.ppu
        
        self.ppu.on_frame = self.display.update_frame

        if rom_path:
            self.load_rom(rom_path)

        self.running = False
    
    def handle_frame(self, framebuffer):
        self.display.update_frame(framebuffer)
    
    def load_rom(self, rom_path: str):
        # load rom
        with open(rom_path, "rb") as f:
            rom_data = f.read()
        self.memory.load_rom(rom_data)

    def run(self, cycles_per_step=10000):
        while self.display.running_ok():
            # Get input state and update joypad
            self.memory.update_joypad(self.input.get_state())
            
            # Keep window responsive
            pygame.event.pump()
            
            # Execute CPU cycles
            for _ in range(cycles_per_step):
                self.cpu.cycle()