from src.core.pyxelboy import PyxelBoy
from pathlib import Path


def main():
    project_root = Path(__file__).parent
    rom_path = project_root / "ROMs" / "Tetris.gb"
    
    pb = PyxelBoy(str(rom_path))
    pb.run()


if __name__ == "__main__":
    main()