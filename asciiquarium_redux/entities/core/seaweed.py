from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Tuple
from asciimatics.screen import Screen


@dataclass
class Seaweed:
    x: int
    base_y: int
    height: int
    phase: int
    # Per-entity sway speed (seconds per sway toggle roughly)
    sway_speed: float = field(default_factory=lambda: random.uniform(0.18, 0.5))
    sway_t: float = 0.0
    # Lifecycle
    state: str = "alive"  # alive | growing | dying | dormant
    visible_height: float = -1.0  # -1 means init to full height in __post_init__
    lifetime_t: float = 0.0
    lifetime_max: float = field(default_factory=lambda: random.uniform(25.0, 60.0))
    regrow_delay_t: float = 0.0
    regrow_delay_max: float = field(default_factory=lambda: random.uniform(4.0, 12.0))
    growth_rate: float = field(default_factory=lambda: random.uniform(6.0, 12.0))  # rows/sec
    shrink_rate: float = field(default_factory=lambda: random.uniform(8.0, 16.0))  # rows/sec
    # Configurable ranges (used on regrowth). Set by app when constructing.
    sway_min: float = 0.18
    sway_max: float = 0.5
    lifetime_min_cfg: float = 25.0
    lifetime_max_cfg: float = 60.0
    regrow_delay_min_cfg: float = 4.0
    regrow_delay_max_cfg: float = 12.0
    growth_rate_min_cfg: float = 6.0
    growth_rate_max_cfg: float = 12.0
    shrink_rate_min_cfg: float = 8.0
    shrink_rate_max_cfg: float = 16.0

    def __post_init__(self):
        # Initialize visible height
        if self.visible_height < 0:
            self.visible_height = float(max(1, self.height))
        # Stagger lifetime so not all die together
        self.lifetime_t = random.uniform(0.0, self.lifetime_max * 0.4)

    def frames(self) -> Tuple[List[str], List[str]]:
        a = ["(" if i % 2 == 0 else "" for i in range(self.height)]
        b = [" )" if i % 2 == 0 else "" for i in range(self.height)]
        frame1 = [s.ljust(2) for s in a]
        frame2 = [s.ljust(2) for s in b]
        return frame1, frame2

    def update(self, dt: float, screen: Screen):
        # advance sway timer
        self.sway_t += dt
        # lifecycle
        if self.state == "alive":
            self.lifetime_t += dt
            if self.lifetime_t >= self.lifetime_max:
                self.state = "dying"
        elif self.state == "growing":
            self.visible_height = min(self.height, self.visible_height + self.growth_rate * dt)
            if int(self.visible_height + 0.001) >= self.height:
                self.visible_height = float(self.height)
                self.state = "alive"
                self.lifetime_t = 0.0
                self.lifetime_max = random.uniform(self.lifetime_min_cfg, self.lifetime_max_cfg)
        elif self.state == "dying":
            self.visible_height = max(0.0, self.visible_height - self.shrink_rate * dt)
            if self.visible_height <= 0.0:
                self.state = "dormant"
                self.regrow_delay_t = 0.0
        elif self.state == "dormant":
            self.regrow_delay_t += dt
            if self.regrow_delay_t >= self.regrow_delay_max:
                # Regrow with some variation
                self.height = random.randint(3, 6)
                self.phase = random.randint(0, 1)
                self.sway_speed = random.uniform(self.sway_min, self.sway_max)
                self.growth_rate = random.uniform(self.growth_rate_min_cfg, self.growth_rate_max_cfg)
                self.shrink_rate = random.uniform(self.shrink_rate_min_cfg, self.shrink_rate_max_cfg)
                self.visible_height = 0.0
                self.state = "growing"
                self.regrow_delay_max = random.uniform(self.regrow_delay_min_cfg, self.regrow_delay_max_cfg)

    def draw(self, screen: Screen, tick: int, mono: bool = False):
        f1, f2 = self.frames()
        # compute sway toggle based on per-entity timer and speed
        step = int(self.sway_t / max(0.05, self.sway_speed))
        sway = (step + self.phase) % 2
        rows = f1 if sway == 0 else f2
        # How many rows to draw from the bottom
        vis = max(0, min(self.height, int(self.visible_height)))
        start_idx = self.height - vis
        for i in range(start_idx, self.height):
            row = rows[i]
            y = self.base_y - (self.height - 1 - i)
            if 0 <= y < screen.height:
                screen.print_at(row, self.x, y, colour=Screen.COLOUR_WHITE if mono else Screen.COLOUR_GREEN)
