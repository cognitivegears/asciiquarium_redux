from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List
from asciimatics.screen import Screen

from ...util import draw_sprite, draw_sprite_masked, randomize_colour_mask
from .fish_assets import (
    FISH_RIGHT,
    FISH_LEFT,
    FISH_RIGHT_MASKS,
    FISH_LEFT_MASKS,
)
from .bubble import Bubble


@dataclass
class Fish:
    frames: List[str]
    x: float
    y: float
    vx: float
    colour: int
    colour_mask: List[str] | None = None
    next_bubble: float = field(default_factory=lambda: random.uniform(1.5, 4.0))
    # Hook interaction state
    hooked: bool = False
    hook_dx: int = 0
    hook_dy: int = 0
    # Configurable movement and bubble behavior
    speed_min: float = 0.6
    speed_max: float = 2.5
    bubble_min: float = 2.0
    bubble_max: float = 5.0
    # Y-band as fractions of screen height, plus waterline context
    band_low_frac: float = 0.0
    band_high_frac: float = 1.0
    waterline_top: int = 5
    water_rows: int = 3

    @property
    def width(self) -> int:
        return max(len(r) for r in self.frames)

    @property
    def height(self) -> int:
        return len(self.frames)

    def update(self, dt: float, screen: Screen, bubbles: List[Bubble]):
        self.x += self.vx * dt * 20.0
        self.next_bubble -= dt
        if self.next_bubble <= 0:
            by = int(self.y + self.height // 2)
            bx = int(self.x + (self.width if self.vx > 0 else -1))
            bubbles.append(Bubble(x=bx, y=by))
            self.next_bubble = random.uniform(self.bubble_min, self.bubble_max)
        if self.vx > 0 and self.x > screen.width:
            self.respawn(screen, direction=1)
        elif self.vx < 0 and self.x + self.width < 0:
            self.respawn(screen, direction=-1)

    def respawn(self, screen: Screen, direction: int):
        # choose new frames and matching mask
        if direction > 0:
            choices = list(zip(FISH_RIGHT, FISH_RIGHT_MASKS))
        else:
            choices = list(zip(FISH_LEFT, FISH_LEFT_MASKS))
        frames, mask = random.choice(choices)
        self.frames = frames
        self.colour_mask = randomize_colour_mask(mask)
        self.vx = random.uniform(self.speed_min, self.speed_max) * direction
        # compute y-band respecting waterline and screen size
        default_low = max(self.waterline_top + self.water_rows + 1, 1)
        low = max(default_low, int(screen.height * self.band_low_frac))
        high = min(screen.height - self.height - 2, int(screen.height * self.band_high_frac) - 1)
        if high < low:
            low = max(1, default_low)
            high = max(low, screen.height - self.height - 2)
        self.y = random.randint(low, max(low, high))
        self.x = -self.width if direction > 0 else screen.width

    def draw(self, screen: Screen):
        if self.colour_mask is not None:
            draw_sprite_masked(screen, self.frames, self.colour_mask, int(self.x), int(self.y), self.colour)
        else:
            draw_sprite(screen, self.frames, int(self.x), int(self.y), self.colour)

    # Hook API used by FishHook special
    def attach_to_hook(self, hook_x: int, hook_y: int):
        self.hooked = True
        self.hook_dx = int(self.x) - hook_x
        self.hook_dy = int(self.y) - hook_y
        self.vx = 0.0

    def follow_hook(self, hook_x: int, hook_y: int):
        if self.hooked:
            self.x = hook_x + self.hook_dx
            self.y = hook_y + self.hook_dy
