from __future__ import annotations
from dataclasses import dataclass
from typing import List, Set, Dict
import random
from utils import Vec, cheb

@dataclass
class Fire:
    top_left: Vec           # anchor of the 2×2 block
    cells: List[Vec]        # the four cells this fire occupies
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
        # destroy trees inside the fire area (rocks survive)
        for c in cells:
            if c in obstacles and obstacles_styles.get(c) == 'tree':
                obstacles.remove(c)
                obstacles_styles.pop(c, None)
        # store as ONE fire instance
        self.fires.append(Fire(top_left=top_left, cells=cells, expires_at=step_counter + self.cfg.fire_lifetime))
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
        """
        Draw ONE large flame per 2×2 fire, with a soft dark drop-shadow.
        """
        import pygame
        cell = cfg.cell
        # Palette with sensible fallbacks
        col_orange = cfg.colors.get('fire_orange', cfg.colors.get('fire_core', (255, 120, 40)))
        col_yellow = cfg.colors.get('fire_yellow', cfg.colors.get('fire_glow', (255, 200, 60)))
        col_red    = cfg.colors.get('fire_red',    (220, 70, 50))
        col_white  = cfg.colors.get('fire_white',  (255, 245, 220))
        col_shadow = cfg.colors.get('fire_shadow', (0, 0, 0))

        def flame_surface(size: int, seedx: int, seedy: int, t: int) -> pygame.Surface:
            # Off-screen surface sized to cover the full 2×2 area
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            # Deterministic flicker so each fire has a stable, lively motion
            h = (seedx*73856093 ^ seedy*19349663 ^ t*83492791) & 0xffffffff
            def rand01():
                nonlocal h
                h ^= (h << 13) & 0xffffffff
                h ^= (h >> 17) & 0xffffffff
                h ^= (h << 5)  & 0xffffffff
                return (h & 0xffff) / 65535.0

            # Base geometry scaled to the 2x2 size
            wobble = int(rand01() * (size * 0.06))
            base_w = max(4, int(size * 0.55) - wobble)
            base_h = max(4, int(size * 0.35) - wobble // 2)

            # 1) Soft radial glow
            glow_r = int(max(size * 0.45, base_w * 0.55))
            pygame.draw.circle(surf, (*col_yellow, 120), (size // 2, size // 2), glow_r)

            # 2) Ember base (red ellipse at bottom)
            pygame.draw.ellipse(
                surf, (*col_red, 220),
                (size // 2 - base_w // 2, size - base_h - 4, base_w, base_h)
            )

            # 3) Outer flame body (teardrop-ish polygon)
            tip_x = size // 2 + int((rand01() - 0.5) * (size * 0.06))
            tip_y = 4 + int(rand01() * 4)
            left   = (size // 2 - base_w // 2, size - base_h - 4)
            right  = (size // 2 + base_w // 2, size - base_h - 4)
            midL   = (left[0]  + int(base_w * 0.16), size - int(base_h * 0.60))
            midR   = (right[0] - int(base_w * 0.16), size - int(base_h * 0.60))
            body   = [ (tip_x, tip_y), midR, right, (size // 2, size - 4), left, midL ]
            pygame.draw.polygon(surf, (*col_orange, 255), body)

            # 4) Inner bright flame (smaller teardrop)
            inner_w = int(base_w * 0.50)
            inner_h = int(base_h * 0.70)
            inner_tip   = (tip_x, tip_y + 3)
            inner_left  = (size // 2 - inner_w // 2, size - inner_h - 6)
            inner_right = (size // 2 + inner_w // 2, size - inner_h - 6)
            inner_midL  = (inner_left[0]  + int(inner_w * 0.18), size - int(inner_h * 0.58))
            inner_midR  = (inner_right[0] - int(inner_w * 0.18), size - int(inner_h * 0.58))
            inner       = [ inner_tip, inner_midR, inner_right, (size // 2, size - 6), inner_left, inner_midL ]
            pygame.draw.polygon(surf, (*col_yellow, 255), inner)

            # 5) White-hot core
            core_w = max(3, int(inner_w * 0.35))
            core_h = max(3, int(inner_h * 0.35))
            pygame.draw.ellipse(
                surf, (*col_white, 230),
                (size // 2 - core_w // 2, size - inner_h - core_h, core_w, core_h)
            )
            return surf

        def shadow_surface(size: int, seedx: int, seedy: int, t: int) -> pygame.Surface:
            """
            Soft drop-shadow roughly matching the flame silhouette.
            Slightly larger and lower, drawn with high transparency.
            """
            import pygame
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            # light “breathing” jitter tied to time
            h = (seedx*2654435761 ^ seedy*974634777 ^ t*19349663) & 0xffffffff
            def rand01():
                nonlocal h
                h ^= (h << 13) & 0xffffffff; h ^= (h >> 17) & 0xffffffff; h ^= (h << 5) & 0xffffffff
                return (h & 0xffff) / 65535.0

            base_w = max(4, int(size * 0.62))
            base_h = max(4, int(size * 0.40))
            glow_r = int(max(size * 0.48, base_w * 0.58))
            pygame.draw.circle(surf, (*col_shadow, 90), (size // 2, size // 2 + 2), glow_r)
            pygame.draw.ellipse(surf, (*col_shadow, 110),
                (size // 2 - base_w // 2, size - base_h, base_w, base_h))
            tip_x = size // 2 + int((rand01() - 0.5) * (size * 0.04)); tip_y = 6
            left  = (size // 2 - base_w // 2, size - base_h)
            right = (size // 2 + base_w // 2, size - base_h)
            midL  = (left[0]  + int(base_w * 0.16), size - int(base_h * 0.65))
            midR  = (right[0] - int(base_w * 0.16), size - int(base_h * 0.65))
            body  = [ (tip_x, tip_y), midR, right, (size // 2, size - 2), left, midL ]
            pygame.draw.polygon(surf, (*col_shadow, 80), body)
            return surf

        for f in self.fires:
            # Draw a single, large flame covering the whole 2×2 area
            size = cell * 2
            rx, ry = f.top_left[0] * cell, f.top_left[1] * cell
            # Shadow first (slight offset), then flame
            screen.blit(shadow_surface(size, f.top_left[0], f.top_left[1], step_counter),
                        (rx + max(1, cell // 6), ry + max(1, cell // 5)))
            screen.blit(flame_surface(size, f.top_left[0], f.top_left[1], step_counter), (rx, ry))
