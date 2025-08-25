from __future__ import annotations
from typing import TYPE_CHECKING

import pygame

from utils import Vec

if TYPE_CHECKING:
    from game import Game
    from actors import Actor


class PowerUp:
    """Base power-up with position, lifetime, and sprite rendering"""

    def __init__(self, pos: Vec, lifetime: int):
        self.pos = pos
        self.active = True
        self.lifetime = lifetime

    def apply(self, actor: 'Actor', game: 'Game') -> None:
        """Apply the effect to the actor; by default simply deactivates."""
        self.active = False

    def tick(self) -> None:
        """Advance lifetime and deactivate when expired."""
        self.lifetime -= 1
        if self.lifetime <= 0:
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
        actor.speed_turns = game.cfg.powerup_length

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
        dur = game.cfg.powerup_length
        if actor is game.human and game.hunter:
            game.hunter.skip_turns = max(game.hunter.skip_turns, dur)
        elif actor is game.hunter and game.human:
            game.human.skip_turns = max(game.human.skip_turns, dur)
        else:
            # if target picks it, slow both chasers
            if game.human:
                game.human.skip_turns = max(game.human.skip_turns, dur)
            if game.hunter:
                game.hunter.skip_turns = max(game.hunter.skip_turns, dur)

    def draw(self, screen, cfg) -> None:
        cell = cfg.cell
        cx = self.pos[0] * cell + cell // 2
        cy = self.pos[1] * cell + cell // 2
        r = max(3, cell // 3)
        # body
        pygame.draw.circle(screen, self.color, (cx, cy), r)
        # head
        pygame.draw.circle(screen, self.color, (cx + r, cy), r // 2)
        # legs
        leg_r = max(2, r // 3)
        pygame.draw.circle(screen, self.color, (cx - r, cy - r), leg_r)
        pygame.draw.circle(screen, self.color, (cx - r, cy + r), leg_r)
        pygame.draw.circle(screen, self.color, (cx + r // 2, cy - r), leg_r)
        pygame.draw.circle(screen, self.color, (cx + r // 2, cy + r), leg_r)
