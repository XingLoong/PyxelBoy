from src.core.pyxelboy import PyxelBoy
from pathlib import Path
import time
import sys

def main():
    # Path to ROM (change as needed)
    project_root = Path(__file__).parent
    rom_path = project_root / "ROMs" / "dmg-acid2.gb"

    pb = PyxelBoy(str(rom_path))

    # When PPU finishes a frame, update the display
    pb.ppu.on_frame = lambda fb: pb.display.update_frame(fb)

    # Main run loop
    while pb.display.running_ok():
        pb.cpu.cycle()


if __name__ == "__main__":
    main()
