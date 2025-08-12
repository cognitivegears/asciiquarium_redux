from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any
from ...screen_compat import Screen

# Maximum bubble lifetime to prevent memory leaks
MAX_BUBBLE_LIFETIME = 10.0


@dataclass
class Bubble:
    x: int
    y: int
    lifetime: float = 0

    @property
    def active(self) -> bool:
        """Check if bubble is still active (hasn't exceeded max lifetime)"""
        return self.lifetime < MAX_BUBBLE_LIFETIME

    def update(self, dt: float, screen: Screen, app: Any):
        self.lifetime += dt
        self.y -= max(1, int(10 * dt))

    def draw(self, screen: Screen):
        if 0 <= self.y < screen.height:
            ch = random.choice([".", "o", "O"])
            screen.print_at(ch, self.x, self.y, colour=Screen.COLOUR_CYAN)
