from __future__ import annotations
from dataclasses import dataclass
from typing import List, Set, Dict
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
        # Palette with sensible fallbacks
        col_orange = cfg.colors.get('fire_orange', cfg.colors.get('fire_core', (255, 120, 40)))
        col_yellow = cfg.colors.get('fire_yellow', cfg.colors.get('fire_glow', (255, 200, 60)))
        col_red    = cfg.colors.get('fire_red',    (220, 70, 50))
        col_white  = cfg.colors.get('fire_white',  (255, 245, 220))

        def flame_surface(cell: int, x: int, y: int, t: int) -> pygame.Surface:
            # Off-screen surface with alpha so flames layer nicely over obstacles/actors
            surf = pygame.Surface((cell, cell), pygame.SRCALPHA)
            # Deterministic per-cell flicker (no global RNG use → reproducible frames)
            h = (x*73856093 ^ y*19349663 ^ t*83492791) & 0xffffffff
            def rand01():
                nonlocal h
                h ^= (h << 13) & 0xffffffff
                h ^= (h >> 17) & 0xffffffff
                h ^= (h << 5)  & 0xffffffff
                return (h & 0xffff) / 65535.0

            # Flicker wobble
            wobble = int(rand01() * (cell * 0.15))
            base_w = max(3, int(cell * 0.70) - wobble)
            base_h = max(3, int(cell * 0.50) - wobble // 2)

            # 1) Soft radial glow
            glow_r = int(max(cell * 0.55, base_w * 0.6))
            pygame.draw.circle(surf, (*col_yellow, 120), (cell // 2, cell // 2), glow_r)

            # 2) Ember base (red ellipse at bottom)
            pygame.draw.ellipse(
                surf, (*col_red, 220),
                (cell // 2 - base_w // 2, cell - base_h - 2, base_w, base_h)
            )

            # 3) Outer flame body (teardrop-ish polygon)
            tip_x = cell // 2 + int((rand01() - 0.5) * (cell * 0.15))
            tip_y = 2 + int(rand01() * 2)
            left   = (cell // 2 - base_w // 2, cell - base_h - 2)
            right  = (cell // 2 + base_w // 2, cell - base_h - 2)
            midL   = (left[0]  + int(base_w * 0.15), cell - int(base_h * 0.55))
            midR   = (right[0] - int(base_w * 0.15), cell - int(base_h * 0.55))
            body   = [ (tip_x, tip_y), midR, right, (cell // 2, cell - 2), left, midL ]
            pygame.draw.polygon(surf, (*col_orange, 255), body)

            # 4) Inner bright flame (smaller teardrop)
            inner_w = int(base_w * 0.45)
            inner_h = int(base_h * 0.65)
            inner_tip   = (tip_x, tip_y + 2)
            inner_left  = (cell // 2 - inner_w // 2, cell - inner_h - 4)
            inner_right = (cell // 2 + inner_w // 2, cell - inner_h - 4)
            inner_midL  = (inner_left[0]  + int(inner_w * 0.18), cell - int(inner_h * 0.55))
            inner_midR  = (inner_right[0] - int(inner_w * 0.18), cell - int(inner_h * 0.55))
            inner       = [ inner_tip, inner_midR, inner_right, (cell // 2, cell - 4), inner_left, inner_midL ]
            pygame.draw.polygon(surf, (*col_yellow, 255), inner)

            # 5) White-hot core
            core_w = max(2, int(inner_w * 0.35))
            core_h = max(2, int(inner_h * 0.35))
            pygame.draw.ellipse(
                surf, (*col_white, 230),
                (cell // 2 - core_w // 2, cell - inner_h - core_h, core_w, core_h)
            )
            return surf

        for f in self.fires:
            for (x, y) in f.cells:
                rx, ry = x * cell, y * cell
                screen.blit(flame_surface(cell, x, y, step_counter), (rx, ry))
