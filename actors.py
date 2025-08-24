from __future__ import annotations
from typing import Optional, Set, List
from utils import Vec, add, cheb, legal_neighbors

class Actor:
    def __init__(self, name: str, color: tuple[int,int,int], pos: Vec):
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
        best_score = -10**9
        best: List[Vec] = []
        for q in options:
            score = min(cheb(q, human), cheb(q, hunter))
            if score > best_score:
                best, best_score = [q], score
            elif score == best_score:
                best.append(q)
        return best[0]
