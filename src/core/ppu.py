class PPU:


    def __init__(self, memory, handle_frame):
        # 8x8 pixel tiles, 20x18 tiles
        # 40 sprites, 10 per line
        # 8kb VRAM

        self.memory = memory
        # =Registers=
        self.mode = 2       # LCD mode: HBlank (0), VBlank (1), OAM (2), VRAM(3)
        self.dot = 0        # cycle counter
        # LDCD 
        self.LCDC = 0       # 0xFF40
        self.STAT = 0       # 0xFF41  bit 0-1: mode, read only, 2: LY==LYC coincidence flag, 3: Hblank IE, 4: Vblank IE, 5: OAM IE, 6: LY==LYC IE, 7: 0 unused
        # Scrolling
        self.SCY = 0        # 0xFF42
        self.SCX = 0        # 0xFF43
        # LY counters
        self.LY = 0         # 0xFF44: scanline 0-143 + 10 vblank
        self.LYC = 0        # 0xFF45
        # DMA + OAM
        self.DMA = 0        # 0xFF46
        self.dma_active = False
        self.dma_cycles = 0
        self.DMA_bytes_done = 0
        # Palettes
        self.BGP = 0        # 0xFF47
        self.OBP0 = 0       # 0xFF48
        self.OBP1 = 0       # 0xFF49
        # Window 
        self.WY = 0         # 0xFF4A
        self.WX = 0         # 0xFF4B 

        # Clock constants (in cycles)
        self.MODE2_OAM = 80
        self.MODE3_DRAW = 172
        self.MODE0_HBLANK = 204   # (456 - previous two)
        self.LINE_CYCLES = 456

        # Screen 160 x 144 pixels (but 256x256 exists)
        self.SCREEN_WIDTH = 160
        self.SCREEN_HEIGHT = 144
        # 1D list (flat array) access: self.frame_buffer[y * 160 + x]
        self.frame_buffer = [0] * (160 * 144)
        self.on_frame = handle_frame

        self.coincidence_flag = False
        self.last_rendered_line = -1
        self.frame_id = 0

    """PPU.step(cycles):
    - Add cycles to mode counter
    - Check current scanline and mode
    - Transition between modes based on timing
    - When appropriate, render the current scanline
    - Update LY register (0xFF44)
    - Trigger interrupts when needed"""


    # 144-153 1 4560cycles

    def render_scanline(self):
        #TODO VRAM/OAM lock during mode 2/3
        LY = self.LY
        LCDC = self.cached_LCDC
        BG_enable = LCDC & 0x01 != 0         # bit 0 (0: off)
        BG_map_select = LCDC & 0x08 != 0     # bit 3 (0: 0x9800-0x9BFF, 1: 0x9C00-0x9FFF)
        BG_tile_data = LCDC & 0x10 != 0      # bit 4 (0: 0x8800-0x9BFF signed, 1: 0x8000-0x8FFF unsigned)
        OBJ_enable = LCDC & 0x02 != 0        # bit 1 (0: off)
        OBJ_size = LCDC & 0x04 != 0          # bit 2 (0: 8x8, 1: 8x16)
        window_enable = LCDC & 0x20 != 0     # bit 5 (0: off)
        window_map_select = LCDC & 0x40 != 0 # bit 6 (0: 0x9800-0xBFF, 1: 0x9C00-0x9FFF)
        LCD_enable = LCDC & 0x80 != 0        # bit 7 (0: off, ppu frozen)

        # BG enable check (bit 0)
        if BG_enable:
            self._render_background_line(LY, BG_map_select, BG_tile_data, window_enable)
        
        # window check (bit 5)
        if window_enable:
            self._render_window_line(LY, window_map_select, BG_tile_data)

        # sprites check (bit 1)
        if OBJ_enable:
            self._render_sprites_line(LY, OBJ_size)
    
    def _render_background_line(self, LY, BG_map_select, BG_tile_data, window_enable):
        SCX = self.cached_SCX
        SCY = self.cached_SCY

        # determin tile map 
        bg_tile_map_base = 0x9C00 if BG_map_select else 0x9800

        # determine tile data
        tile_data_signed = not BG_tile_data     # True = signed
        BGP = self.BGP                          # palette register

        for x in range(160):
            # skip drawing where window overwrites
            if window_enable and LY >= self.WY and x >= (self.WX - 7):
                continue

            # 1: calc scrolled coords
            map_x = (SCX + x) & 0xFF
            map_y = (SCY + LY) & 0xFF

            # 2: read tile index from bg map
            tile_col = map_x // 8
            tile_row = map_y // 8
            offset = (tile_row * 32) + tile_col
            tile_index = self.memory[bg_tile_map_base + offset]

            # 3: resolve memory address
            if tile_data_signed:
                index = tile_index if tile_index < 128 else (tile_index - 256)
                tile_addr = 0x9000 + (index * 16)
            else:
                tile_addr = 0x8000 + (tile_index * 16)
            
            # 4: fetch row of tile data for this scanline
            y_tile = map_y & 0x07
            row_addr = tile_addr + (y_tile * 2)
            low = self.memory[row_addr]
            high = self.memory[row_addr + 1]
            x_tile = 7 - (map_x & 0x07)

            colour_id = ((high >> x_tile) & 1) << 1 | ((low >> x_tile) & 1)

            # 5: palette -> actual colour (0–3)
            shift = colour_id * 2
            palette_colour = (BGP >> shift) & 0x03

            # Step 6: Store in framebuffer
            self.frame_buffer[(LY * self.SCREEN_WIDTH) + x] = palette_colour


    def _render_window_line(self, LY, window_map_select, BG_tile_data):
        WX = self.WX - 7   # Window X position on screen
        WY = self.WY       # Window Y position on screen
        BGP = self.BGP

        # draw if LY >= WY 
        if LY < WY:
            return

        # Determine window tile map base (LCDC bit 6)
        window_map_base = 0x9C00 if window_map_select else 0x9800

        # Determine tile data addressing mode (same as BG, bit 4)
        tile_data_signed = not BG_tile_data

        # Loop over screen pixels 
        for x in range(160):
            # Only draw window pixels when x >= WX
            if x < WX:
                continue
            # find pixel coords to window
            win_x = x - WX
            win_y = LY - WY

            # find tile like BG
            tile_col = win_x // 8
            tile_row = win_y // 8
            offset = tile_row * 32 + tile_col
            tile_index = self.memory[window_map_base + offset]

            # tile data address
            if tile_data_signed:
                index = (tile_index - 256) if tile_index >= 128 else tile_index
                tile_addr = 0x9000 + index * 16
            else:
                tile_addr = 0x8000 + tile_index * 16

            # tile coords
            y_tile = win_y & 0x07
            x_tile = 7 - (win_x & 0x7)
            row_addr = tile_addr + y_tile * 2
            low = self.memory[row_addr]
            high = self.memory[row_addr + 1]
            colour_id = ((high >> x_tile) & 1) << 1 | ((low >> x_tile) & 1)

            # BGP palette
            shift = colour_id * 2
            palette_colour = (BGP >> shift) & 0x03

            # Write to framebuffer (overwrite BG)
            self.frame_buffer[(LY * self.SCREEN_WIDTH) + x] = palette_colour

    def _render_sprites_line(self, LY, OBJ_size):
        size = 16 if OBJ_size else 8
        sprite_count = 0

        # iterate 40 sprites in OAM: 4 bytes (y, x, tile index, value)
        for i in range(40):
            if sprite_count >= 10:
                return
            base = i * 4
            sprite_y = self.memory[0xFE00 + base] - 16
            sprite_x = self.memory[0xFE00 + base + 1] - 8
            tile_index = self.memory[0xFE00 + base + 2]
            if size == 16:
                tile_index &= 0xFE      # 8x16 sprites use even tile number
            attr = self.memory[0xFE00 + base + 3]

            if LY < sprite_y or LY >= (sprite_y + size):
                continue
            # check vert flip (attr bit 6)
            y_tile = LY - sprite_y
            if attr & 0x40:
                y_tile = size - 1 - y_tile
            row_addr = 0x8000 + (tile_index * 16) + (y_tile * 2)
            low = self.memory[row_addr]
            high = self.memory[row_addr + 1]

            # loop overs pixels in sprite (0-7)
            for x in range(8):
                draw_x = sprite_x + x
                if draw_x < 0 or draw_x >= 160:
                    continue
                x_tile = 7 - x
                # bit 3 for hori flip
                if attr & 0x20:
                    x_tile = x
                colour_id = ((high >> x_tile) & 1) << 1 | ((low >> x_tile) & 1)
                if colour_id == 0:
                    continue    # transparent
                palette = self.OBP1 if (attr & 0x10) else self.OBP0
                shift = colour_id * 2
                pixel_colour = (palette >> shift) & 0x03

                # BG overlap/ priority  attr bit 7, 0: sprite in front, 1: BG in front
                BG_colour = self.frame_buffer[LY * self.SCREEN_WIDTH + draw_x]
                if (attr & 0x80) and BG_colour !=0:
                    continue
                self.frame_buffer[LY * self.SCREEN_WIDTH + draw_x] = pixel_colour
            sprite_count += 1

    def start_dma(self, value):
        self.DMA = value         # high byte of source
        self.dma_cycles = 0      # track cycle progress
        self.DMA_bytes_done = 0  # track bytes transferred
        self.dma_active = True   # flag the DMA as active

    def step(self, cycles):
        # If LCD is off, PPU is frozen
        lcd_enabled = (self.LCDC & 0x80) != 0
        if not lcd_enabled:
            self.LY = 0
            self.mode = 0
            self.dot = 0
            return

        DRAW_END = self.MODE2_OAM + self.MODE3_DRAW

        for _ in range(cycles):
            prev_mode = self.mode
            prev_coin = self.coincidence_flag

            # advance dot
            self.dot += 1

            # DMA (every 4 cycles)
            if self.dma_active:
                self.dma_cycles += 1
                if self.dma_cycles >= 4:
                    self.dma_cycles = 0
                    if self.DMA_bytes_done < 160:
                        index = self.DMA_bytes_done
                        source_addr = (self.DMA << 8) + index
                        self.memory[0xFE00 + index] = self.memory[source_addr]
                        self.DMA_bytes_done += 1
                        if self.DMA_bytes_done >= 160:
                            self.dma_active = False

            # Determine current mode
            if self.LY < 144:
                if self.dot < self.MODE2_OAM:
                    new_mode = 2  # OAM
                elif self.dot < DRAW_END:
                    new_mode = 3  # VRAM/pixel transfer
                else:
                    new_mode = 0  # HBlank

                #TODO
                if prev_mode == 2 and new_mode == 3:
                    self.cached_LCDC = self.LCDC
                    self.cached_SCX = self.SCX
                    self.cached_SCY = self.SCY
                    self.cached_BGP = self.BGP
                    self.cached_WX = self.WX
                    self.cached_WY = self.WY

                # Render scanline on exiting Mode 3 -> 0
                if prev_mode == 3 and new_mode == 0:
                    if self.last_rendered_line != self.LY:
                        self.render_scanline()
                        self.last_rendered_line = self.LY
            else:
                new_mode = 1

            # Update mode bits in STAT and fire mode-change STAT interrupts (only on transition)
            if new_mode != prev_mode:
                # write mode bits
                self.mode = new_mode
                self.STAT = (self.STAT & ~0x03) | self.mode

                # Fire STAT interrupts only on transitions and only if the corresponding IE is set
                if self.mode == 0 and (self.STAT & 0x08):   # HBlank IE (bit 3)
                    self.memory.interrupt_flag |= 0x02
                elif self.mode == 1 and (self.STAT & 0x10): # VBlank IE (bit 4)
                    self.memory.interrupt_flag |= 0x02
                elif self.mode == 2 and (self.STAT & 0x20): # OAM IE (bit 5)
                    self.memory.interrupt_flag |= 0x02

            # End of line: increment LY (may wrap)
            if self.dot >= self.LINE_CYCLES:
                self.dot = 0
                # Advance LY
                self.LY += 1

                # VBlank start
                if self.LY == 144:
                    self.frame_id += 1
                    # mode will be set later, but set to VBlank logically now
                    self.mode = 1
                    self.memory.interrupt_flag |= 0x01  # VBlank interrupt
                    if self.on_frame:
                        self.on_frame(self.frame_buffer)

                # End of frame -> wrap LY and set initial mode (OAM)
                if self.LY > 153:
                    self.LY = 0
                    self.mode = 2
                    self.last_rendered_line = -1

                # Recompute coincidence AFTER LY change (single place)
                new_coin = (self.LY == self.LYC)
                self.coincidence_flag = new_coin
                
                # Update STAT bit 2
                if new_coin:
                    self.STAT |= 0x04
                else:
                    self.STAT &= ~0x04


                # Fire LYC interrupt on rising edge only
                if (not prev_coin) and new_coin and (self.STAT & 0x40):
                    self.memory.interrupt_flag |= 0x02

