
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
    min_start_dist: int = 12                  # min Chebyshev distance human↔hunter
    obstacles_enabled_default: bool = True
    obstacle_density: float = 0.10            # 0.0–0.4 reasonable

    # Colors
    colors: Dict[str, Color] = field(default_factory=lambda: {
        "bg":        (18, 18, 20),
        "grid":      (35, 35, 40),
        "human":     (255, 100, 90),
        "hunter":    (71, 130, 55),
        "target":    (51, 168, 222),
        "obstacle":  (80, 80, 88),
        "text":      (230, 230, 235),
    })

    @staticmethod
    def load(path: str = "config.json") -> "Config":
        cfg = Config()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # known simple fields
                for k in ("grid_w","grid_h","cell","margin","fps","min_start_dist",
                          "obstacles_enabled_default","obstacle_density"):
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
