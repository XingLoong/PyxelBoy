# PyxelBoy

An ambitious Gameboy emulator written in Python — my final project for **CS50x**.

---

## Table of Contents

1. [Features](#features)
2. [Usage](#usage)
3. [Project Overview](#project-overview)
4. [Challenges & Learning](#challenges--learning)
5. [Reflections](#reflections)
6. [Disclaimer](#disclaimer)
7. [License](#license)

---

## Features

- [x] Loads Gameboy ROMs (.gb)
- [x] CPU emulation with opcode handling
- [x] Memory management
- [x] Basic graphics rendering
- [ ] Sound support (future work)
- [ ] Save/load game states (future work)
- [ ] TBD

---

## Usage

TBD

---

## Project Overview

PyxelBoy is built entirely in Python, and is designed as a learning exercise for CS50x. The project covers:

- Parsing Gameboy CPU instructions
- Memory
- Graphics
- Input

---

## Challenges & Learning

Some of the major challenges I faced while building the emulator:

- Implementing the opcode table/dictionary from a preexisting json file.
- Learning about the gameboy specific header code validation.
- The architecture of the original Gameboy.
- Learning other ways instead of giant blocks of if/else statements, e.g. gettr and settr, lookup tables/dictionaries, and the trade-offs of overhead.
- Flag logics.
- Interrupt logics.

---

## Reflections

### CPU + Memory

Head and heart ache during the test running of blarrg's test suite; challenging, but educational. Learned the necessary conditions to execute test ROMs, and the importance of adding debugging prints in the testing.
Flag logic proved to be critical, challenging, and tricky to implement.
The toughest hurdle was getting to the printout of failure/passed from the ROMS. After that, it was smooth sailing untili the next major update. The next hiccup was the interrupt, to pass cpu_instrs.02 in blarrg's tests.

### PPU + Display

Wrapping my head around the separate function of the PPU and how the actual architecture worked was difficult. While not 100% accurate to the actual hardware, the emulator works as intended.

### Input

Mapping key inputs was simplest in the scope of the project, seeing as Pygames handles that beautifully.

---

## Disclaimer

PyxelBoy is intended for **educational purposes only**. I do **not** endorse the trading of copyrighted Gameboy ROMs.

---

## License

This project is licensed under the MIT License © 2025 XingLoong.
