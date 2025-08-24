# ===============================
# Project: Hunter-Human-Target Proto (Pygame)
# Files below are split by headers like:  ### FILE: <name>
# Save each block into its own file in the same folder.
# Then run:  python main.py
# ===============================

### FILE: config.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple, Dict
import json, os

Color = Tuple[int, int, int]


@dataclass
class Config:
    # Grid & render
    grid_w: int = 40
    grid_h: int = 40
    cell: int = 18
    margin: int = 1
    fps: int = 60

    # Gameplay
    min_start_dist: int = 12  # min Chebyshev distance human↔hunter
    obstacles_enabled_default: bool = True
    obstacle_density: float = 0.10  # 0.0–0.4 reasonable
    tree_ratio: float = 0.5  # fraction of obstacles drawn as trees vs boulders
    # Fire system
    fire_max: int = 5
    fire_lifetime: int = 8  # measured in sub-turns
    fire_spawn_chance: float = 0.25  # attempt per sub-turn, at most 1 fire spawned
    respawn_delay: int = 5  # sub-turns until an actor respawns

    # Colors
    colors: Dict[str, Color] = field(default_factory=lambda: {
        "bg": (18, 18, 20),
        "grid": (35, 35, 40),
        "human": (255, 100, 90),
        "hunter": (71, 130, 55),
        "target": (51, 168, 222),
        "obstacle": (80, 80, 88),
        "text": (230, 230, 235),
        "tree_leaf": (46, 160, 67),
        "tree_trunk": (110, 78, 48),
        "rock": (120, 120, 130),
        "fire_core": (255, 120, 40),
        "fire_glow": (255, 200, 60),
    })

    @staticmethod
    def load(path: str = "config.json") -> "Config":
        cfg = Config()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # known simple fields
                for k in ("grid_w", "grid_h", "cell", "margin", "fps", "min_start_dist",
                          "obstacles_enabled_default", "obstacle_density", "tree_ratio",
                          "fire_max", "fire_lifetime", "fire_spawn_chance", "respawn_delay"):
                    if k in data:
                        setattr(cfg, k, data[k])
                # colors
                if isinstance(data.get("colors"), dict):
                    for name, rgb in data["colors"].items():
                        if (isinstance(rgb, (list, tuple)) and len(rgb) == 3 and
                                all(isinstance(c, int) for c in rgb)):
                            cfg.colors[name] = tuple(rgb)  # type: ignore
            except Exception as e:
                print(f"[Config] Failed to read {path}: {e}. Using defaults.")
        return cfg


### FILE: utils.py
from __future__ import annotations
from typing import Tuple, Set, List, Dict
import random

Vec = Tuple[int, int]
DIRS_8: List[Vec] = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1)
]


def add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1])


def in_bounds(p: Vec, w: int, h: int) -> bool:
    return 0 <= p[0] < w and 0 <= p[1] < h


def cheb(a: Vec, b: Vec) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def legal_neighbors(p: Vec, w: int, h: int, obstacles: Set[Vec], obstacles_enabled: bool) -> List[Vec]:
    opts: List[Vec] = []
    for d in DIRS_8:
        q = add(p, d)
        if in_bounds(q, w, h) and (not obstacles_enabled or q not in obstacles):
            opts.append(q)
    return opts


# --- Starts & obstacles ---

def random_in_quadrant(q: int, w: int, h: int) -> Vec:
    # Quadrants: 0=TL, 1=TR, 2=BL, 3=BR
    wq, hq = w // 2, h // 2
    x0 = 0 if q in (0, 2) else wq
    y0 = 0 if q in (0, 1) else hq
    margin = 3
    x = random.randint(x0 + margin, x0 + wq - 1 - margin)
    y = random.randint(y0 + margin, y0 + hq - 1 - margin)
    return (x, y)


def pick_start_positions(w: int, h: int, min_start_dist: int) -> Tuple[Vec, Vec, Vec]:
    # human & hunter opposite quadrants
    opposite = {0: 3, 1: 2, 2: 1, 3: 0}
    while True:
        qh = random.choice([0, 1, 2, 3])
        qH = opposite[qh]
        human = random_in_quadrant(qh, w, h)
        hunter = random_in_quadrant(qH, w, h)
        if cheb(human, hunter) >= min_start_dist:
            break

    # target near center, far from both
    cx, cy = w // 2, h // 2
    min_dist = max(6, min_start_dist // 2)
    target = None
    for radius in range(4, min(w, h) // 2):
        candidates: List[Vec] = []
        for x in range(cx - radius, cx + radius + 1):
            for y in range(cy - radius, cy + radius + 1):
                p = (x, y)
                if not in_bounds(p, w, h):
                    continue
                if p == human or p == hunter:
                    continue
                if cheb(p, (cx, cy)) <= radius and cheb(p, human) >= min_dist and cheb(p, hunter) >= min_dist:
                    candidates.append(p)
        if candidates:
            target = random.choice(candidates)
            break
    if target is None:
        # fallback to center or nearest ring
        center = (cx, cy)
        if center != human and center != hunter and in_bounds(center, w, h):
            target = center
        else:
            for r in range(1, max(w, h)):
                ring: List[Vec] = []
                for x in range(cx - r, cx + r + 1):
                    for y in range(cy - r, cy + r + 1):
                        p = (x, y)
                        if not in_bounds(p, w, h):
                            continue
                        if p == human or p == hunter:
                            continue
                        if cheb(p, (cx, cy)) == r:
                            ring.append(p)
                if ring:
                    target = random.choice(ring)
                    break
    return human, hunter, target  # type: ignore


def generate_obstacles(w: int, h: int, density: float, exclude: Set[Vec], tree_ratio: float = 0.5) -> Tuple[
    Set[Vec], Dict[Vec, str]]:
    obstacles: Set[Vec] = set()
    styles: Dict[Vec, str] = {}
    for y in range(h):
        for x in range(w):
            p = (x, y)
            if p in exclude:
                continue
            if random.random() < density:
                obstacles.add(p)
                styles[p] = 'tree' if random.random() < tree_ratio else 'rock'
    # keep a 1-cell ring around excluded positions clear
    ring_clear: Set[Vec] = set()
    for e in exclude:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (e[0] + dx, e[1] + dy)
                if in_bounds(q, w, h):
                    ring_clear.add(q)
    filtered = {p for p in obstacles if p not in ring_clear}
    styles = {p: styles[p] for p in filtered if p in styles}
    return filtered, styles


### FILE: actors.py
from __future__ import annotations
from typing import Optional, Set, List
from utils import Vec, add, cheb, legal_neighbors


class Actor:
    def __init__(self, name: str, color: tuple[int, int, int], pos: Vec):
        self.name = name
        self.color = color
        self.pos: Vec = pos
        # life/death tracking
        self.deaths: int = 0
        self.dead: bool = False
        self.respawn_ticks: int = 0
        self.last_death_pos: Optional[Vec] = None

    @property
    def alive(self) -> bool:
        return not self.dead

    def set_pos(self, p: Vec) -> None:
        self.pos = p

    def set_pos(self, p: Vec) -> None:
        self.pos = p


class HumanPlayer(Actor):
    """Human-controlled via key mapping handled by Game; this class validates moves."""

    def try_move(self, delta: Optional[Vec], w: int, h: int, obstacles: Set[Vec], obstacles_enabled: bool) -> bool:
        if delta is None:
            return True  # skip turn
        nxt = add(self.pos, delta)
        # Bounds + obstacle check
        if 0 <= nxt[0] < w and 0 <= nxt[1] < h and (not obstacles_enabled or nxt not in obstacles):
            self.pos = nxt
            return True
        return False


class HunterCPU(Actor):
    def decide(self, target: Vec, w: int, h: int, obstacles: Set[Vec], obstacles_enabled: bool) -> Vec:
        options = legal_neighbors(self.pos, w, h, obstacles, obstacles_enabled)
        options.append(self.pos)  # stay if blocked
        best_dist = min(cheb(q, target) for q in options)
        # all best moves toward target
        best = [q for q in options if cheb(q, target) == best_dist]
        return best[0]


class TargetCPU(Actor):
    def decide(self, human: Vec, hunter: Vec, w: int, h: int, obstacles: Set[Vec], obstacles_enabled: bool) -> Vec:
        options = legal_neighbors(self.pos, w, h, obstacles, obstacles_enabled)
        if not options:
            return self.pos
        # maximize distance to the nearer chaser
        best_score = -10 ** 9
        best: List[Vec] = []
        for q in options:
            score = min(cheb(q, human), cheb(q, hunter))
            if score > best_score:
                best, best_score = [q], score
            elif score == best_score:
                best.append(q)
        return best[0]


### FILE: fire.py
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
        return [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]

    def cell_in_fire(self, p: Vec) -> bool:
        for f in self.fires:
            if p in f.cells:
                return True
        return False

    def can_place_fire(self, top_left: Vec, obstacles_styles: Dict[Vec, str]) -> bool:
        x, y = top_left
        if x < 0 or y < 0 or x + 1 >= self.w or y + 1 >= self.h:
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
            x = random.randrange(0, self.w - 1)
            y = random.randrange(0, self.h - 1)
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
                pygame.draw.rect(screen, core, (rx + 1, ry + 1, cell - 2, cell - 2), border_radius=3)
                gpad = max(2, cell // 6)
                pygame.draw.rect(screen, glow, (rx + gpad, ry + gpad, cell - 2 * gpad, cell - 2 * gpad),
                                 border_radius=3)


### FILE: game.py
from __future__ import annotations
import sys
from typing import Optional, Set, Dict

import pygame

from config import Config
from utils import Vec, add, cheb, DIRS_8, pick_start_positions, generate_obstacles
from fire import FireSystem
from actors import HumanPlayer, HunterCPU, TargetCPU


class Game:
    def __init__(self, cfg: Optional[Config] = None) -> None:
        self.cfg = cfg or Config.load()
        self.screen = None
        self.font = None
        self.clock = None

        # actors & state
        self.human: HumanPlayer | None = None
        self.hunter: HunterCPU | None = None
        self.target: TargetCPU | None = None

        self.turn_order: list = []
        self.turn_idx: int = 0
        self.winner: Optional[str] = None
        self.step_counter: int = 0

        # obstacles
        self.obstacles_enabled: bool = self.cfg.obstacles_enabled_default
        self.obstacles: Set[Vec] = set()
        self.obstacles_styles: Dict[Vec, str] = {}
        # fires
        self.fire: FireSystem | None = None

        # Controls: qwe/ asd / zxc ; S=skip
        self.key_to_dir: Dict[int, Optional[Vec]] = {
            pygame.K_q: (-1, -1), pygame.K_w: (0, -1), pygame.K_e: (1, -1),
            pygame.K_a: (-1, 0), pygame.K_s: None, pygame.K_d: (1, 0),
            pygame.K_z: (-1, 1), pygame.K_x: (0, 1), pygame.K_c: (1, 1),
        }

    # ------------ lifecycle ------------
    def init_pygame(self) -> None:
        pygame.init()
        pygame.key.set_repeat(0)  # KEYDOWN only (no held-key repeat)
        self.screen = pygame.display.set_mode((self.cfg.grid_w * self.cfg.cell,
                                               self.cfg.grid_h * self.cfg.cell))
        pygame.display.set_caption("Hunter-Human-Target • QWE/ASD/ZXC • S=Skip • O=Obstacles • R=Restart • ESC=Quit")
        self.font = pygame.font.SysFont("consolas", 18)
        self.clock = pygame.time.Clock()

    def init_world(self) -> None:
        human_p, hunter_p, target_p = pick_start_positions(self.cfg.grid_w, self.cfg.grid_h, self.cfg.min_start_dist)
        self.human = HumanPlayer("HUMAN", self.cfg.colors["human"], human_p)
        self.hunter = HunterCPU("HUNTER", self.cfg.colors["hunter"], hunter_p)
        self.target = TargetCPU("TARGET", self.cfg.colors["target"], target_p)

        if self.obstacles_enabled:
            self.obstacles, self.obstacles_styles = generate_obstacles(self.cfg.grid_w, self.cfg.grid_h,
                                                                       self.cfg.obstacle_density,
                                                                       {human_p, hunter_p, target_p},
                                                                       self.cfg.tree_ratio)
        else:
            self.obstacles.clear()
            self.obstacles_styles = {}

        # init fires (clears any prior fires)
        self.fire = FireSystem(self.cfg, self.cfg.grid_w, self.cfg.grid_h)
        self.fire.clear()

        # Human → Hunter → Human → Hunter → Target
        self.turn_order = [self.human, self.hunter, self.human, self.hunter, self.target]
        self.turn_idx = 0
        self.winner = None
        self.step_counter = 0

    # ------------ helpers ------------
    def in_bounds(self, p: Vec) -> bool:
        return 0 <= p[0] < self.cfg.grid_w and 0 <= p[1] < self.cfg.grid_h

    def occupied_same(self, a: Vec, b: Vec) -> bool:
        return a == b

    def kill_actor(self, actor) -> None:
        if actor.dead:
            return
        actor.deaths += 1
        actor.dead = True
        actor.respawn_ticks = self.cfg.respawn_delay
        actor.last_death_pos = actor.pos

    def find_safe_spawn(self, around: Vec) -> Vec:
        # expanding Chebyshev ring search
        live_positions = set()
        for a in [self.human, self.hunter, self.target]:
            if a and a.alive:
                live_positions.add(a.pos)
        for r in range(0, max(self.cfg.grid_w, self.cfg.grid_h)):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    q = (around[0] + dx, around[1] + dy)
                    if not self.in_bounds(q):
                        continue
                    if self.obstacles_enabled and q in self.obstacles:
                        continue
                    if self.fire and self.fire.cell_in_fire(q):
                        continue
                    if q in live_positions:
                        continue
                    return q
        # fallback center
        return (self.cfg.grid_w // 2, self.cfg.grid_h // 2)

    def decrement_respawns(self) -> None:
        for a in [self.human, self.hunter, self.target]:
            if a and a.dead and a.respawn_ticks > 0:
                a.respawn_ticks -= 1
                if a.respawn_ticks <= 0:
                    where = a.last_death_pos or a.pos
                    a.set_pos(self.find_safe_spawn(where))
                    a.dead = False
                    a.respawn_ticks = 0

    def check_fire_kills(self) -> None:
        if not self.fire:
            return
        for a in [self.human, self.hunter, self.target]:
            if a and a.alive and self.fire.cell_in_fire(a.pos):
                self.kill_actor(a)

    def post_step(self) -> None:
        # Fires expire, perhaps spawn one, then check for any immediate kills
        if self.fire:
            self.fire.update(self.step_counter)
            self.fire.maybe_spawn(self.step_counter, self.obstacles, self.obstacles_styles)
            self.check_fire_kills()
        # handle respawn countdowns
        self.decrement_respawns()

    # ------------ drawing ------------
    def draw_grid(self) -> None:
        assert self.screen
        self.screen.fill(self.cfg.colors["bg"])
        # subtle grid
        for y in range(self.cfg.grid_h):
            for x in range(self.cfg.grid_w):
                rx = x * self.cfg.cell
                ry = y * self.cfg.cell
                pygame.draw.rect(self.screen, self.cfg.colors["grid"],
                                 (rx, ry, self.cfg.cell - self.cfg.margin, self.cfg.cell - self.cfg.margin), 1)

    def draw_obstacles(self) -> None:
        if not self.obstacles_enabled or not self.obstacles:
            return
        assert self.screen
        cell = self.cfg.cell
        for (x, y) in self.obstacles:
            rx = x * cell
            ry = y * cell
            style = self.obstacles_styles.get((x, y), 'rock')
            if style == 'tree':
                canopy_color = self.cfg.colors.get('tree_leaf', self.cfg.colors['obstacle'])
                trunk_color = self.cfg.colors.get('tree_trunk', self.cfg.colors['obstacle'])
                cx = rx + cell // 2
                # Canopy: triangle
                top = (cx, ry + 2)
                left = (rx + 3, ry + cell // 2)
                right = (rx + cell - 3, ry + cell // 2)
                pygame.draw.polygon(self.screen, canopy_color, [top, left, right])
                # Trunk
                tw = max(3, cell // 6)
                th = max(3, cell // 3)
                tx = cx - tw // 2
                ty = ry + cell // 2
                pygame.draw.rect(self.screen, trunk_color, (tx, ty, tw, th), border_radius=2)
            else:
                # Boulder: circle
                rock_color = self.cfg.colors.get('rock', self.cfg.colors['obstacle'])
                cx = rx + cell // 2
                cy = ry + cell // 2
                r = max(3, cell // 3)
                pygame.draw.circle(self.screen, rock_color, (cx, cy), r)

    def draw_actor(self, pos: Vec, color: tuple[int, int, int]) -> None:
        assert self.screen
        rx = pos[0] * self.cfg.cell + 2
        ry = pos[1] * self.cfg.cell + 2
        size = self.cfg.cell - 4
        pygame.draw.rect(self.screen, color, (rx, ry, size, size), border_radius=4)

    def draw_text(self, text: str, y: int) -> None:
        assert self.screen and self.font
        surf = self.font.render(text, True, self.cfg.colors["text"])
        self.screen.blit(surf, (10, y))

    # ------------ turn logic ------------
    def advance_turn(self) -> None:
        self.turn_idx = (self.turn_idx + 1) % len(self.turn_order)
        self.step_counter += 1

    def check_win_after_move(self) -> None:
        assert self.human and self.hunter and self.target
        if self.human.alive and self.occupied_same(self.human.pos, self.target.pos):
            self.winner = "HUMAN"
        elif self.hunter.alive and self.occupied_same(self.hunter.pos, self.target.pos):
            self.winner = "HUNTER"

    # ------------ event handling ------------
    def handle_keydown(self, key: int) -> None:
        assert self.human and self.hunter and self.target
        # global controls
        if key == pygame.K_ESCAPE:
            pygame.quit();
            sys.exit()
        if key == pygame.K_o:
            self.obstacles_enabled = not self.obstacles_enabled
            # re-generate to avoid covering actors
            if self.obstacles_enabled:
                self.obstacles, self.obstacles_styles = generate_obstacles(self.cfg.grid_w, self.cfg.grid_h,
                                                                           self.cfg.obstacle_density,
                                                                           {self.human.pos, self.hunter.pos,
                                                                            self.target.pos}, self.cfg.tree_ratio)
            else:
                self.obstacles.clear()
                self.obstacles_styles = {}
            return
        if key == pygame.K_r:
            # Restart a fresh world (actors, obstacles, turn order)
            self.init_world()
            return

        # turn-based controls: only on human’s sub-turn
        current = self.turn_order[self.turn_idx]
        if self.winner is None and current is self.human and self.human.alive:
            if key in self.key_to_dir:
                delta = self.key_to_dir[key]
                if self.human.try_move(delta, self.cfg.grid_w, self.cfg.grid_h, self.obstacles, self.obstacles_enabled):
                    if self.fire and self.fire.cell_in_fire(self.human.pos):
                        self.kill_actor(self.human)
                    self.advance_turn()
                    self.check_win_after_move()
                    self.post_step()

    # ------------ main loop ------------
    def run(self) -> None:
        self.init_pygame()
        self.init_world()

        running = True
        while running:
            assert self.clock
            self.clock.tick(self.cfg.fps)

            # events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)

            # AI sub-turns resolve automatically
            if self.winner is None:
                current = self.turn_order[self.turn_idx]
                if current is self.human:
                    if self.human.alive:
                        pass  # wait for keydown (one move per press)
                    else:
                        # human is dead; turns auto-advance while respawning
                        self.advance_turn();
                        self.post_step()
                elif current is self.hunter:
                    if self.hunter.alive:
                        nxt = self.hunter.decide(self.target.pos, self.cfg.grid_w, self.cfg.grid_h, self.obstacles,
                                                 self.obstacles_enabled)
                        self.hunter.set_pos(nxt)
                        if self.fire and self.fire.cell_in_fire(self.hunter.pos):
                            self.kill_actor(self.hunter)
                    self.advance_turn();
                    self.check_win_after_move();
                    self.post_step()
                elif current is self.target:
                    if self.target.alive:
                        nxt = self.target.decide(self.human.pos, self.hunter.pos, self.cfg.grid_w, self.cfg.grid_h,
                                                 self.obstacles, self.obstacles_enabled)
                        self.target.set_pos(nxt)
                        if self.fire and self.fire.cell_in_fire(self.target.pos):
                            self.kill_actor(self.target)
                    self.advance_turn();
                    self.check_win_after_move();
                    self.post_step()

            # draw
            self.draw_grid()
            self.draw_obstacles()
            if self.fire:
                self.fire.draw(self.screen, self.cfg, self.step_counter)
            assert self.human and self.hunter and self.target
            if self.target.alive:
                self.draw_actor(self.target.pos, self.cfg.colors["target"])  # draw target first so chasers on top
            if self.hunter.alive:
                self.draw_actor(self.hunter.pos, self.cfg.colors["hunter"])
            if self.human.alive:
                self.draw_actor(self.human.pos, self.cfg.colors["human"])

            self.draw_text(f"Turn: {self.turn_order[self.turn_idx].name}   Steps: {self.step_counter}", 8)
            self.draw_text("Move: QWE/ASD/ZXC • S=Skip • O=Toggle Obstacles • R=Restart • ESC=Quit", 30)
            self.draw_text(f"Deaths – H:{self.human.deaths}  Hun:{self.hunter.deaths}  T:{self.target.deaths}", 52)
            if self.human.dead:
                self.draw_text(f"H respawns in {self.human.respawn_ticks}", 72)
            if self.hunter.dead:
                self.draw_text(f"Hun respawns in {self.hunter.respawn_ticks}", 92)
            if self.target.dead:
                self.draw_text(f"T respawns in {self.target.respawn_ticks}", 112)
            if self.winner:
                self.draw_text(f"WINNER: {self.winner}", 132)

            pygame.display.flip()

        pygame.quit();
        sys.exit()


### FILE: main.py
from game import Game

if __name__ == "__main__":
    Game().run()

### FILE: config.json  (example)
# Save this JSON (without the leading #) as config.json to override defaults.
# {
#   "grid_w": 40,
#   "grid_h": 40,
#   "cell": 18,
#   "margin": 1,
#   "fps": 60,
#   "min_start_dist": 12,
#   "obstacles_enabled_default": true,
#   "obstacle_density": 0.1,
#   "colors": {
#     "bg": [18,18,20],
#     "grid": [35,35,40],
#     "human": [255,100,90],
#     "hunter": [71,130,55],
#     "target": [51,168,222],
#     "obstacle": [80,80,88],
#     "text": [230,230,235]
#   }
# }
