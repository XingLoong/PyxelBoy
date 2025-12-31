# PyxelBoy

#### Video Demo: --insert video here--

#### Description:

An ambitious Gameboy emulator written entirely in Python — my final project for **CS50x**.
The Game Boy emulator was chosen for my own keen interest into the emulation of a hardware architecture entirely in software language. As for why Game Boy, it seemed the most accessible entry, yet challenging still. The Python language was chosen as a point of learning due to the ease of implementation and testing, and lacking the verbose nature of C.

I first started with the CPU emulation, where opcode is decoded into particular instructions, in which the rest of the systems would follow. Particularly, the flag register (F) was quite the headache in learning how it behaved physically involving bitwise operations, and the carry of the individual flags associated with the F register. Namely the n, h, c, and z flags. Thanks to the many documentations available online, such as pandocs, this was a relatively solvable step. Working out and testing the cycling of the CPU was tricky, as the other subsystems had yet to form, and many iterations as each subsystem was completed was needed.

Memory setup was relatively straight-forward at first, simply a read and write situation. However, as I delved into the finer details of unique opcodes, and structures of the architecture, the interactions the memory system had to be slowly adjusted to account for those. Examples include how certain register values get altered instead of just being read or written.

All in all, the CPU system and the Memory systems were quite stress-free in implementing. The most time consuming was writing the opcode codes instructions and the associated look-up table used to modulate the code. Batch-coding, in the sense that similar opcodes were grouped up, and 'generated' with helper functions to be inserted into the look-up table on initialization, along with the creation of the opcode instructions themselves. Prior experiences in writing a CHIP-8 emulator/simulator helped as a warm-up in understanding the basic structure.

After the construct of the basic CPU system and step-cycle, I ran the cpu_instrs test suite from 'Blarrg', a commonly used selection of tests in the emulation world. However, it's not very well documented in how the test itself works. Certain variables needed to be set to a particular default if the whole architecture isn't complete. Yet, after a day or two of learning, I eventually got to test working, albeit slowly, in which case, I switched to running the indiviual parts of the test suite, in which eventually, they all passed. Validating the correctness of my opcode implementation.

Moving onto the PPU (Picture Processing Unit) system was where progress got stalled. Understanding of the complex structure was relatively simple to learn. However, the implementation was quite challenging. "The Ultimate Game Boy Talk" was particularly helpful (and an interesting insight) in breaking down the PPU problem into more manageable parts. After the preliminary code was written, an output (the display) was wired up to the existing setup for testing. The Pyxel module was first tested, as it was designed for '8-bit' gaming. However, complications arose, and was eventually scrapped for the universally renowned Pygame. Testing of the 'display' was a simpler process than Pyxel. Once the standalone worked, it was then wired up with the existing PPU. Various tests were done next, of which ROMs (legally obtained via backups), and other test suites were used. This was where problems arose, incorrect images, incomplete images, blank screens, and not advancing screens were several of the problems. Eventually most of the bugs and problems were slowly solved, until a 'second' frame of a ROM was displayed successfully. It was at this point, while testing the famous Mooneye Acid2-dmg test, where flaws arose. Many iterations were done within my limits to correct, and try to produce the correct 'face' image. However, in the end, I was forced to move on, and continue with a 'working' emulator, instead of an 'accurate' emulator. I learnt via the Acid2 test, that the accuracy of my code was quite lacking, where the timing of the system had to advance side-by-side, instead of governed by frame. In that the whole emulator needs to account for each subsystem working independently, yet advancing to a certain timing. I resolved myself to address this issue in the next iteration of my emulator.

After the visuals were working, I then progressed onto wiring up the input of commands for the interaction of the emulator. Thanks to the existing Pygame module being used, keyboard input was relatively simple to wire up. After a small hiccup on the design, I eventually ran, and played a few minutes of Tetris on my emulator.

Next was audio, while the github repository doesn't show it, I've tried and tested audio. But due to the implementation of my coding not being cycle-accurate, it surmounts another layer of difficulty. I've resigned my project to be soundless at this stage.

Upon 'completing' this project, I find myself thinking on how to improve and go further on my next iteration of this emulator. I aim to make it cycle-accurate, and I aim to get Acid2 test fully passing, before aiming to implement sounds next.

---

## Table of Contents

1. [Features](#features)
2. [Usage](#usage)
3. [File Overview](#file-overview)
4. [Challenges & Learning](#challenges--learning)
5. [Reflections](#reflections)
6. [Limitations](#limitations)
7. [Disclaimer](#disclaimer)
8. [License](#license)

---

## Features

- [x] Loads Gameboy ROMs (.gb)
- [x] CPU emulation with opcode handling
- [x] Memory management
- [x] Basic graphics rendering
- [x] Plays 32kb sized ROMs

---

## Usage

1. Ensure Python **3.11 or newer** is installed:

```bash
python3 --version
```

2. Clone this repository:

```bash
git clone https://github.com/XingLoong/PyxelBoy
cd PyxelBoy
```

3. Create a virtual environment (optional):

```bash
python3 -m venv venv
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. In the terminal run main with path to ROM (supply own 32kb size game):

```bash
python main.py path/to/ROM.gb
```

e.g.

```bash
python main.py /ROMs/Tetris.gb
```

---

## File Overview

-`main.py`: Entry point of the emulator. Handles ROM loading and initialization of the subsystems. -`cpu.py`: Implements the Game Boy CPU, it includes the fetching, decoding, and execution of the opcodes, and the associated registers and flags. -`memory.py`: Manages the memory mapping and somewhat acts as the BUS between the other modules. -`ppu.py`: Handles the logic rendering of the graphics. -`display.py`: Handles the display/output of the graphics. -`input.py`: Handles the registering/input of keyboard presses. -`pyxelboy.py`: The module that ties the rest of the codes together for use.

---

## Challenges & Learning

Some of the major challenges I faced while building the emulator:

- Implementing the opcode table/dictionary from a preexisting JSON file.
- Learning about the gameboy specific header code validation.
- The architecture of the original Gameboy.
- Learning other ways instead of giant blocks of if/else statements, e.g. getter and setter, lookup tables/dictionaries, and the trade-offs of overhead.
- Flag logic.
- Interrupt logic.
- Rendering of graphics
- Timing, actual versus 'good-enough'

---

## Reflections

### CPU + Memory

Running Blargg’s test suite was challenging but highly educational. Learned the necessary conditions to execute test ROMs, and the importance of adding debugging prints in the testing.
Flag logic proved to be critical, challenging, and tricky to implement.
The toughest hurdle was getting to the printout of failure/passed from the ROMs. After that, it was smooth sailing until the next major update. The next hiccup was the interrupt, to pass cpu_instrs.02 in Blarrg's tests.

### PPU + Display

Wrapping my head around the separate function of the PPU and how the actual architecture worked was difficult. While not 100% accurate to the actual hardware, the emulator works as intended.

### Input

Mapping key inputs was simplest in the scope of the project, seeing as Pygame handles that beautifully.

---

## Limitations

- Timing accuracy is not cycle-perfect
- CPU/PPU behaviour is simplified compared to original hardware
- Does not implement MBC support, therefore games larger than 32kb are unsupported.

---

## Disclaimer

PyxelBoy is intended for **educational purposes only**. I do **not** endorse the trading of copyrighted Game Boy ROMs. This project **does not** include or distribute any copyrighted ROMs.

---

## License

This project is licensed under the MIT License © 2025 XingLoong.
