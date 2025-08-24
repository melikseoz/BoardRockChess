import sys
import random
import pygame
from typing import Tuple, List, Optional, Set

# -------------------------
# CONFIG
# -------------------------
GRID_W, GRID_H = 40, 40
CELL = 18                   # pixel size per cell
MARGIN = 1                  # grid line / cell padding
FPS = 60

BG_COLOR       = (18, 18, 20)
GRID_COLOR     = (35, 35, 40)
HUMAN_COLOR    = (255, 100, 90)   # red
HUNTER_COLOR   = (71, 130, 55)    # green
TARGET_COLOR   = (51, 168, 222)   # blue
OBST_COLOR     = (80, 80, 88)
TEXT_COLOR     = (230, 230, 235)

MIN_START_DIST = 12  # min Chebyshev distance between human & hunter

# Obstacles (can be toggled at runtime with the 'O' key)
OBSTACLES_ENABLED_DEFAULT = True
OBSTACLE_DENSITY = 0.10  # 0.0–0.4 is sensible for playability

# If you want to let an AI drive the "human" for simulation/testing, set False -> True
HUMAN_IS_PLAYER = True

# -------------------------
# UTILS / CORE ENGINE
# -------------------------
Vec = Tuple[int, int]

DIRS_8: list[Vec] = [
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1)
]

def add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1])

def in_bounds(p: Vec) -> bool:
    return 0 <= p[0] < GRID_W and 0 <= p[1] < GRID_H

def cheb(a: Vec, b: Vec) -> int:
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]))

def legal_neighbors(p: Vec, obstacles: Set[Vec], obstacles_enabled: bool) -> list[Vec]:
    opts: list[Vec] = []
    for d in DIRS_8:
        q = add(p, d)
        if in_bounds(q) and (not obstacles_enabled or q not in obstacles):
            opts.append(q)
    return opts

# -------------------------
# STARTING POSITIONS
# -------------------------
def random_in_quadrant(q: int) -> Vec:
    # Quadrants: 0=TL, 1=TR, 2=BL, 3=BR
    wq, hq = GRID_W // 2, GRID_H // 2
    x0 = 0 if q in (0,2) else wq
    y0 = 0 if q in (0,1) else hq
    margin = 3
    x = random.randint(x0 + margin, x0 + wq - 1 - margin)
    y = random.randint(y0 + margin, y0 + hq - 1 - margin)
    return (x, y)

def pick_start_positions() -> Tuple[Vec, Vec, Vec]:
    # Pick human & hunter in opposite quadrants for "far apart" bias.
    opposite = {0:3, 1:2, 2:1, 3:0}
    while True:
        qh = random.choice([0,1,2,3])
        qH = opposite[qh]
        human  = random_in_quadrant(qh)
        hunter = random_in_quadrant(qH)
        if cheb(human, hunter) >= MIN_START_DIST:
            break

    # Place target near the center (semi-random), and not too close to either
    cx, cy = GRID_W // 2, GRID_H // 2
    min_dist = max(6, MIN_START_DIST // 2)
    target: Optional[Vec] = None

    for radius in range(4, min(GRID_W, GRID_H) // 2):
        candidates: list[Vec] = []
        for x in range(cx - radius, cx + radius + 1):
            for y in range(cy - radius, cy + radius + 1):
                p = (x, y)
                if not in_bounds(p):
                    continue
                if p == human or p == hunter:
                    continue
                if cheb(p, (cx, cy)) <= radius and cheb(p, human) >= min_dist and cheb(p, hunter) >= min_dist:
                    candidates.append(p)
        if candidates:
            target = random.choice(candidates)
            break

    if target is None:
        center = (cx, cy)
        if center != human and center != hunter and in_bounds(center):
            target = center
        else:
            for r in range(1, max(GRID_W, GRID_H)):
                ring: list[Vec] = []
                for x in range(cx - r, cx + r + 1):
                    for y in range(cy - r, cy + r + 1):
                        p = (x, y)
                        if not in_bounds(p):
                            continue
                        if p == human or p == hunter:
                            continue
                        if cheb(p, (cx, cy)) == r:
                            ring.append(p)
                if ring:
                    target = random.choice(ring)
                    break

    return human, hunter, target

# -------------------------
# OBSTACLES
# -------------------------
def generate_obstacles(exclude: Set[Vec]) -> Set[Vec]:
    obstacles: Set[Vec] = set()
    for y in range(GRID_H):
        for x in range(GRID_W):
            p = (x, y)
            if p in exclude:
                continue
            if random.random() < OBSTACLE_DENSITY:
                obstacles.add(p)
    # keep a 1-cell ring around each excluded pos clear
    ring_clear: Set[Vec] = set()
    for e in exclude:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (e[0] + dx, e[1] + dy)
                if in_bounds(q):
                    ring_clear.add(q)
    return {p for p in obstacles if p not in ring_clear}

# -------------------------
# AI
# -------------------------
def hunter_ai(hunter: Vec, target: Vec, obstacles: Set[Vec], obstacles_enabled: bool) -> Vec:
    """Greedy Chebyshev pursuit with obstacle awareness."""
    options = legal_neighbors(hunter, obstacles, obstacles_enabled)
    options.append(hunter)  # allow staying if blocked
    best_dist = min(cheb(q, target) for q in options)
    best = [q for q in options if cheb(q, target) == best_dist]
    nxt = random.choice(best)
    return nxt

def target_ai(target: Vec, human: Vec, hunter: Vec, obstacles: Set[Vec], obstacles_enabled: bool) -> Vec:
    """Move to maximize distance to the nearer chaser (obstacle-aware)."""
    options = legal_neighbors(target, obstacles, obstacles_enabled)
    # options.append(target)  # uncomment to allow the target to wait
    if not options:
        return target
    best_score = -10**9
    best: list[Vec] = []
    for q in options:
        score = min(cheb(q, human), cheb(q, hunter))
        if score > best_score:
            best, best_score = [q], score
        elif score == best_score:
            best.append(q)
    return random.choice(best)

# Optional AI for auto-human testing

def human_ai(human: Vec, target: Vec, obstacles: Set[Vec], obstacles_enabled: bool) -> Vec:
    options = legal_neighbors(human, obstacles, obstacles_enabled)
    if not options:
        return human
    # naïve: step toward target
    best_dist = min(cheb(q, target) for q in options)
    best = [q for q in options if cheb(q, target) == best_dist]
    return random.choice(best)

# -------------------------
# RENDERING
# -------------------------
def draw_grid(screen):
    screen.fill(BG_COLOR)
    for y in range(GRID_H):
        for x in range(GRID_W):
            rx = x * CELL
            ry = y * CELL
            pygame.draw.rect(screen, GRID_COLOR, (rx, ry, CELL - MARGIN, CELL - MARGIN), 1)

def draw_obstacles(screen, obstacles: Set[Vec], obstacles_enabled: bool):
    if not obstacles_enabled:
        return
    size = CELL - 2
    for (x, y) in obstacles:
        rx = x * CELL + 1
        ry = y * CELL + 1
        pygame.draw.rect(screen, OBST_COLOR, (rx, ry, size, size), border_radius=2)

def draw_actor(screen, pos: Vec, color: Tuple[int,int,int]):
    rx = pos[0] * CELL + 2
    ry = pos[1] * CELL + 2
    size = CELL - 4
    pygame.draw.rect(screen, color, (rx, ry, size, size), border_radius=4)

def draw_text(screen, font, text, y):
    surf = font.render(text, True, TEXT_COLOR)
    screen.blit(surf, (10, y))

# -------------------------
# GAME LOOP
# -------------------------
def main():
    pygame.init()
    pygame.key.set_repeat(0)  # process only KEYDOWN events; avoid held-key repeats

    screen = pygame.display.set_mode((GRID_W * CELL, GRID_H * CELL))
    pygame.display.set_caption("Board Rock Chess: Movement QWEADZXC | S skip | O toggle obstacles")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    human, hunter, target = pick_start_positions()

    obstacles_enabled = OBSTACLES_ENABLED_DEFAULT
    obstacles: Set[Vec] = generate_obstacles({human, hunter, target}) if obstacles_enabled else set()

    # Turn schedule: Human → Hunter → Human → Hunter → Target (repeat)
    TURN_ORDER = ["HUMAN", "HUNTER", "HUMAN", "HUNTER", "TARGET"]
    turn_idx = 0
    winner: Optional[str] = None
    step_counter = 0

    # Mapping for human moves (qweadzxc) + S to skip
    KEY_TO_DIR: dict[int, Optional[Vec]] = {
        pygame.K_q: (-1, -1), pygame.K_w: (0, -1),  pygame.K_e: (1, -1),
        pygame.K_a: (-1,  0), pygame.K_s: None,      pygame.K_d: (1,  0),
        pygame.K_z: (-1,  1), pygame.K_x: (0,  1),  pygame.K_c: (1,  1),
    }

    def occupied_same(a: Vec, b: Vec) -> bool:
        return a == b

    running = True
    while running:
        clock.tick(FPS)

        # ---------------- Events ----------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_o:
                    # toggle obstacles; re-generate to avoid covering actors
                    obstacles_enabled = not obstacles_enabled
                    obstacles = generate_obstacles({human, hunter, target}) if obstacles_enabled else set()
                elif winner is None and TURN_ORDER[turn_idx] == "HUMAN" and HUMAN_IS_PLAYER:
                    # process exactly one key press per human sub-turn
                    if event.key in KEY_TO_DIR:
                        v = KEY_TO_DIR[event.key]
                        if v is None:
                            # skip turn
                            turn_idx = (turn_idx + 1) % len(TURN_ORDER)
                            step_counter += 1
                        else:
                            nxt = add(human, v)
                            if in_bounds(nxt) and (not obstacles_enabled or nxt not in obstacles):
                                human = nxt
                                turn_idx = (turn_idx + 1) % len(TURN_ORDER)
                                step_counter += 1
                                if occupied_same(human, target):
                                    winner = "HUMAN"
                        # consume only one human action per press
                        # (do not allow multiple moves from a held key because we rely on KEYDOWN only)

        # ------------- Sub-turn updates (AI) -------------
        if winner is None:
            actor = TURN_ORDER[turn_idx]
            if actor == "HUMAN":
                if not HUMAN_IS_PLAYER:
                    # AI-driven human for simulation
                    nxt = human_ai(human, target, obstacles, obstacles_enabled)
                    if in_bounds(nxt) and (not obstacles_enabled or nxt not in obstacles):
                        human = nxt
                    turn_idx = (turn_idx + 1) % len(TURN_ORDER)
                    step_counter += 1
                    if occupied_same(human, target):
                        winner = "HUMAN"
            elif actor == "HUNTER":
                hunter = hunter_ai(hunter, target, obstacles, obstacles_enabled)
                turn_idx = (turn_idx + 1) % len(TURN_ORDER)
                step_counter += 1
                if occupied_same(hunter, target):
                    winner = "HUNTER"
            elif actor == "TARGET":
                target = target_ai(target, human, hunter, obstacles, obstacles_enabled)
                turn_idx = (turn_idx + 1) % len(TURN_ORDER)
                step_counter += 1
                if occupied_same(target, human):
                    winner = "HUMAN"
                elif occupied_same(target, hunter):
                    winner = "HUNTER"

        # ---------------- Render ----------------
        draw_grid(screen)
        draw_obstacles(screen, obstacles, obstacles_enabled)
        draw_actor(screen, target, TARGET_COLOR)
        draw_actor(screen, hunter, HUNTER_COLOR)
        draw_actor(screen, human, HUMAN_COLOR)

        # HUD
        draw_text(screen, font, f"Turn: {TURN_ORDER[turn_idx]}   Steps: {step_counter}", 8)
        draw_text(screen, font, "Move: QWE/ASD/ZXC  •  S=Skip  •  O=Toggle Obstacles  •  ESC=Quit", 30)
        if winner:
            draw_text(screen, font, f"WINNER: {winner}", 52)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
