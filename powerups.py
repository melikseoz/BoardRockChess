from __future__ import annotations
from typing import TYPE_CHECKING

import pygame

from utils import Vec

if TYPE_CHECKING:
    from game import Game
    from actors import Actor

class PowerUp:
    """Base power-up with position and sprite rendering"""
    def __init__(self, pos: Vec):
        self.pos = pos
        self.active = True

    def apply(self, actor: 'Actor', game: 'Game') -> None:
        """Apply the effect to the actor; by default simply deactivates."""
        self.active = False

    def draw(self, screen, cfg) -> None:
        """Default drawing: small white circle."""
        cell = cfg.cell
        cx = self.pos[0] * cell + cell // 2
        cy = self.pos[1] * cell + cell // 2
        r = max(3, cell // 3)
        pygame.draw.circle(screen, (250, 250, 250), (cx, cy), r)

class SpeedPowerUp(PowerUp):
    color = (0, 200, 0)

    def apply(self, actor: 'Actor', game: 'Game') -> None:
        super().apply(actor, game)
        actor.speed_turns = max(actor.speed_turns, 2)

    def draw(self, screen, cfg) -> None:
        cell = cfg.cell
        cx = self.pos[0] * cell + cell // 2
        cy = self.pos[1] * cell + cell // 2
        r = max(3, cell // 3)
        points = [(cx - r, cy - r), (cx - r, cy + r), (cx + r, cy)]
        pygame.draw.polygon(screen, self.color, points)

class TimeStopPowerUp(PowerUp):
    color = (200, 0, 0)

    def apply(self, actor: 'Actor', game: 'Game') -> None:
        super().apply(actor, game)
        if actor.name == 'HUMAN' and game.hunter:
            game.hunter.skip_turns = max(game.hunter.skip_turns, 2)
        elif actor.name == 'HUNTER' and game.human:
            game.human.skip_turns = max(game.human.skip_turns, 2)

    def draw(self, screen, cfg) -> None:
        cell = cfg.cell
        cx = self.pos[0] * cell + cell // 2
        cy = self.pos[1] * cell + cell // 2
        r = max(3, cell // 3)
        # shell
        pygame.draw.circle(screen, self.color, (cx, cy), r)
        # head
        head_r = max(2, cell // 8)
        pygame.draw.circle(screen, self.color, (cx + r, cy), head_r)
        # legs
        leg_r = head_r
        pygame.draw.circle(screen, self.color, (cx - r//2, cy - r//2), leg_r)
        pygame.draw.circle(screen, self.color, (cx - r//2, cy + r//2), leg_r)
        pygame.draw.circle(screen, self.color, (cx + r//2, cy - r//2), leg_r)
        pygame.draw.circle(screen, self.color, (cx + r//2, cy + r//2), leg_r)
