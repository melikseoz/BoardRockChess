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

class TeleportPowerUp(PowerUp):
    color = (200, 60, 200)

    def apply(self, actor: 'Actor', game: 'Game') -> None:
        super().apply(actor, game)
        actor.set_pos(game.find_safe_spawn(actor.pos))

    def draw(self, screen, cfg) -> None:
        cell = cfg.cell
        cx = self.pos[0] * cell + cell // 2
        cy = self.pos[1] * cell + cell // 2
        r = max(3, cell // 3)
        points = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(screen, self.color, points)

class HealPowerUp(PowerUp):
    color = (255, 200, 40)

    def apply(self, actor: 'Actor', game: 'Game') -> None:
        super().apply(actor, game)
        actor.deaths = max(0, actor.deaths - 1)

    def draw(self, screen, cfg) -> None:
        cell = cfg.cell
        cx = self.pos[0] * cell + cell // 2
        cy = self.pos[1] * cell + cell // 2
        r = max(3, cell // 3)
        pygame.draw.circle(screen, self.color, (cx, cy), r)
