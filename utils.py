
from __future__ import annotations
from typing import Tuple, Set, List
import random

Vec = Tuple[int, int]
DIRS_8: List[Vec] = [
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1)
]

def add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1])

def in_bounds(p: Vec, w: int, h: int) -> bool:
    return 0 <= p[0] < w and 0 <= p[1] < h

def cheb(a: Vec, b: Vec) -> int:
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]))

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
    x0 = 0 if q in (0,2) else wq
    y0 = 0 if q in (0,1) else hq
    margin = 3
    x = random.randint(x0 + margin, x0 + wq - 1 - margin)
    y = random.randint(y0 + margin, y0 + hq - 1 - margin)
    return (x, y)

def pick_start_positions(w: int, h: int, min_start_dist: int):
    # human & hunter opposite quadrants
    opposite = {0:3, 1:2, 2:1, 3:0}
    while True:
        qh = random.choice([0,1,2,3])
        qH = opposite[qh]
        human  = random_in_quadrant(qh, w, h)
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

def generate_obstacles(w: int, h: int, density: float, exclude: Set[Vec]) -> Set[Vec]:
    obstacles: Set[Vec] = set()
    import random as _r
    for y in range(h):
        for x in range(w):
            p = (x, y)
            if p in exclude:
                continue
            if _r.random() < density:
                obstacles.add(p)
    # keep a 1-cell ring around excluded positions clear
    ring_clear: Set[Vec] = set()
    for e in exclude:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (e[0] + dx, e[1] + dy)
                if in_bounds(q, w, h):
                    ring_clear.add(q)
    return {p for p in obstacles if p not in ring_clear}
