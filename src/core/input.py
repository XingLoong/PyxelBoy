import pygame


class Input:

    def __init__(self):
        self.keymap = {
            pygame.K_j: "A",
            pygame.K_h: "B",
            pygame.K_g: "START",
            pygame.K_f: "SELECT",
            pygame.K_w: "UP",
            pygame.K_s: "DOWN",
            pygame.K_a: "LEFT",
            pygame.K_d: "RIGHT",
        }

    def get_state(self):
        keys = pygame.key.get_pressed()

        # T = pressed, F = released/unpressed
        state = {
            "A": False,
            "B": False,
            "START": False,
            "SELECT": False,
            "UP": False,
            "DOWN": False,
            "LEFT": False,
            "RIGHT": False,
        }

        for key, button in self.keymap.items():
            if keys[key]:
                state[button] = True
        
        return state