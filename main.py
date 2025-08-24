from game import Game
import sys, traceback

if __name__ == "__main__":
    try:
        Game().run()
    except Exception:
        print("ERROR: The game crashed. Python:", sys.version)
        try:
            import pygame
            print("Pygame version:", pygame.version.ver)
        except Exception:
            print("Pygame not available or failed to import.")
        traceback.print_exc()
