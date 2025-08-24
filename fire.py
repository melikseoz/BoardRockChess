from __future__ import annotations
from dataclasses import dataclass
from typing import List, Set, Dict, Tuple
import random
from utils import Vec, in_bounds, cheb

@dataclass
class Fire:
    cells: List[Vec]
    expires_at: int

class FireSystem:
    def __init__(self, cfg, w: int, h: int):
        self.cfg = cfg
        self.w = w
        self.h = h
        self.fires: List[Fire] = []

    def clear(self) -> None:
        self.fires.clear()

    def update(self, step_counter: int) -> None:
        self.fires = [f for f in self.fires if step_counter < f.expires_at]

    def rect_cells(self, top_left: Vec) -> List[Vec]:
        x, y = top_left
        return [(x, y), (x+1, y), (x, y+1), (x+1, y+1)]

    def cell_in_fire(self, p: Vec) -> bool:
        for f in self.fires:
            if p in f.cells:
                return True
        return False

    def can_place_fire(self, top_left: Vec, obstacles_styles: Dict[Vec, str]) -> bool:
        x, y = top_left
        if x < 0 or y < 0 or x+1 >= self.w or y+1 >= self.h:
            return False
        cells = self.rect_cells(top_left)
        # avoid overlapping existing fires
        for f in self.fires:
            if any(c in f.cells for c in cells):
                return False
        # must be within 8 cells (Chebyshev) of at least one tree
        tree_cells = [p for p, sty in obstacles_styles.items() if sty == 'tree']
        if not tree_cells:
            return False
        for c in cells:
            if any(cheb(c, t) <= 8 for t in tree_cells):
                return True
        return False

    def spawn_at(self, top_left: Vec, step_counter: int, obstacles: Set[Vec], obstacles_styles: Dict[Vec, str]) -> bool:
        if not self.can_place_fire(top_left, obstacles_styles):
            return False
        cells = self.rect_cells(top_left)
        # destroy trees inside the fire area
        for c in cells:
            if c in obstacles and obstacles_styles.get(c) == 'tree':
                obstacles.remove(c)
                obstacles_styles.pop(c, None)
        self.fires.append(Fire(cells=cells, expires_at=step_counter + self.cfg.fire_lifetime))
        return True

    def maybe_spawn(self, step_counter: int, obstacles: Set[Vec], obstacles_styles: Dict[Vec, str]) -> bool:
        if len(self.fires) >= self.cfg.fire_max:
            return False
        if random.random() > self.cfg.fire_spawn_chance:
            return False
        # try a handful of random locations
        for _ in range(30):
            x = random.randrange(0, self.w-1)
            y = random.randrange(0, self.h-1)
            if self.spawn_at((x, y), step_counter, obstacles, obstacles_styles):
                return True
        return False

    def draw(self, screen, cfg, step_counter: int) -> None:
        import pygame
        cell = cfg.cell
        core = cfg.colors.get('fire_core', (255, 120, 40))
        glow = cfg.colors.get('fire_glow', (255, 200, 60))
        for f in self.fires:
            for (x, y) in f.cells:
                rx = x * cell
                ry = y * cell
                pygame.draw.rect(screen, core, (rx+1, ry+1, cell-2, cell-2), border_radius=3)
                gpad = max(2, cell // 6)
                pygame.draw.rect(screen, glow, (rx+gpad, ry+gpad, cell-2*gpad, cell-2*gpad), border_radius=3)
