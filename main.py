from src.core.pyxelboy import PyxelBoy
from pathlib import Path
import time


def main():
    project_root = Path(__file__).parent
    rom_path = project_root / "ROMs" / "dmg-acid2.gb"

    if not rom_path.exists():
        print("ROM file not found:", rom_path)
        return

    pb = PyxelBoy(str(rom_path))
    
    # Wait for LCD
    print("Waiting for LCD...")
    while (pb.ppu.LCDC & 0x80) == 0:
        pb.cpu.cycle()
    
    print("LCD on! Running...")
    
    # Frame counter
    frame_count = [0]
    def count_frame(fb):
        frame_count[0] += 1
        non_zero = sum(1 for p in fb if p != 0)
        print(f"Frame {frame_count[0]}: {non_zero} non-zero pixels")
        pb.display.update_frame(fb)
    
    pb.ppu.on_frame = count_frame
    
    # Run for a bit
    import time
    while pb.display.running_ok():
        start = time.time()
        
        # Run one frame worth
        for _ in range(10000):
            pb.cpu.cycle()
        
        # Limit speed
        elapsed = time.time() - start
        if elapsed < 1/60:
            time.sleep(1/60 - elapsed)


if __name__ == "__main__":
    main()