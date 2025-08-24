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
            pygame.K_q: (-1, -1), pygame.K_w: (0, -1),  pygame.K_e: (1, -1),
            pygame.K_a: (-1,  0), pygame.K_s: None,      pygame.K_d: (1,  0),
            pygame.K_z: (-1,  1), pygame.K_x: (0,  1),  pygame.K_c: (1,  1),
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
        self.human  = HumanPlayer("HUMAN",  self.cfg.colors["human"],  human_p)
        self.hunter = HunterCPU  ("HUNTER", self.cfg.colors["hunter"], hunter_p)
        self.target = TargetCPU  ("TARGET", self.cfg.colors["target"], target_p)

        if self.obstacles_enabled:
            self.obstacles, self.obstacles_styles = generate_obstacles(self.cfg.grid_w, self.cfg.grid_h, self.cfg.obstacle_density,
                                                {human_p, hunter_p, target_p}, self.cfg.tree_ratio)
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
            for dx in range(-r, r+1):
                for dy in range(-r, r+1):
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
        return (self.cfg.grid_w//2, self.cfg.grid_h//2)

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
                trunk_color  = self.cfg.colors.get('tree_trunk', self.cfg.colors['obstacle'])
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

    

    def draw_actor(self, pos: Vec, color: tuple[int,int,int]) -> None:
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
            pygame.quit(); sys.exit()
        if key == pygame.K_o:
            self.obstacles_enabled = not self.obstacles_enabled
            # re-generate to avoid covering actors
            if self.obstacles_enabled:
                self.obstacles, self.obstacles_styles = generate_obstacles(self.cfg.grid_w, self.cfg.grid_h, self.cfg.obstacle_density,
                                                    {self.human.pos, self.hunter.pos, self.target.pos}, self.cfg.tree_ratio)
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
                        self.advance_turn(); self.post_step()
                elif current is self.hunter:
                    if self.hunter.alive:
                        nxt = self.hunter.decide(self.target.pos, self.cfg.grid_w, self.cfg.grid_h, self.obstacles, self.obstacles_enabled)
                        self.hunter.set_pos(nxt)
                        if self.fire and self.fire.cell_in_fire(self.hunter.pos):
                            self.kill_actor(self.hunter)
                    self.advance_turn(); self.check_win_after_move(); self.post_step()
                elif current is self.target:
                    if self.target.alive:
                        nxt = self.target.decide(self.human.pos, self.hunter.pos, self.cfg.grid_w, self.cfg.grid_h, self.obstacles, self.obstacles_enabled)
                        self.target.set_pos(nxt)
                        if self.fire and self.fire.cell_in_fire(self.target.pos):
                            self.kill_actor(self.target)
                    self.advance_turn(); self.check_win_after_move(); self.post_step()

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
                self.draw_actor(self.human.pos,  self.cfg.colors["human"])

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

        pygame.quit(); sys.exit()
