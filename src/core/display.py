import pygame
import numpy 

class Display:
    def __init__(self, scale=4):
        self.width = 160
        self.height = 144
        self.scale = scale

        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.width * self.scale, self.height * self.scale)
        )
        pygame.display.set_caption("PyxelBoy")

        self.surface = pygame.Surface((self.width, self.height))
        self.running = True

        # GB palette
        self.gb_palette = [
            (255, 255, 255),    # colour 0
            (192, 192, 192),    # colour 1
            (96, 96 , 96),      # colour 2
            (0, 0, 0),          # colour 3
        ]

    def update_frame(self, framebuffer):
        # call each VBlank
        if framebuffer is None or len(framebuffer) != self.width * self.height:
            return

        try:
            self._blit_framebuffer(framebuffer)
            # draw scaled to screen
            scaled = pygame.transform.scale(
                self.surface,
                (self.width * self.scale, self.height * self.scale)
            )
            self.screen.blit(scaled, (0, 0))
            pygame.display.flip()
        except Exception as e:
            print("Display.update_frame error:", e)

        self._handle_events()

    def _blit_framebuffer(self, fb):
        # convert fb[] into rgb
        palette = numpy.array(self.gb_palette, dtype=numpy.uint8)
        indices = numpy.array(fb, dtype=numpy.uint8).reshape((self.height, self.width))
        rgb = palette[indices]
        rgb_blit = rgb.swapaxes(0, 1)
        # blit_array width first
        pygame.surfarray.blit_array(self.surface, rgb_blit)

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def running_ok(self):
        self._handle_events()
        return self.running