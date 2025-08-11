from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

from asciimatics.screen import Screen

from ..base import Actor
from ..core import Bubble
from ...util import sprite_size, draw_sprite_masked_with_bg
from ...environment import CHEST_CLOSED, CHEST_OPEN, CHEST_MASK


@dataclass
class TreasureChest(Actor):
    x: int
    y: int
    burst_period: float = 60.0  # seconds between lid bursts
    burst_duration: float = 2.0  # how long the lid stays open
    burst_emit_rate: float = 10.0  # bubbles per second during burst
    small_bubble_min: float = 4.0
    small_bubble_max: float = 9.0

    # internal state
    _time: float = 0.0
    _next_small: float = 0.0
    _burst_timer: float = 0.0
    _bursting: bool = False
    _burst_time_left: float = 0.0
    _burst_emit_accum: float = 0.0

    def __post_init__(self):
        # Randomize initial timers so multiple chests don't sync
        self._next_small = random.uniform(self.small_bubble_min, self.small_bubble_max)
        self._burst_timer = self.burst_period * random.uniform(0.7, 1.3)

    def update(self, dt: float, screen: Screen, app) -> None:  # type: ignore[override]
        self._time += dt
        self._next_small -= dt
        self._burst_timer -= dt
        # Compute current draw origin to place bubbles correctly relative to visual
        def current_origin(opened: bool) -> tuple[int, int, int, int]:
            lines = CHEST_OPEN if opened else CHEST_CLOSED
            w, h = sprite_size(lines)
            _wc, h_closed = sprite_size(CHEST_CLOSED)
            baseline = self.y + h_closed - 1
            baseline = min(screen.height - 2, max(0, baseline))
            y_draw = max(0, min(screen.height - h, baseline - h + 1))
            x_draw = max(0, min(screen.width - w, self.x))
            return x_draw, y_draw, w, h

        # Emit occasional small bubble from the lid area when not bursting
        if self._next_small <= 0 and not self._bursting:
            x_draw, y_draw, w, h = current_origin(False)
            lid_x = x_draw + max(2, min(w - 2, 5 + random.randint(-1, 1)))
            lid_y = y_draw - 1
            app.bubbles.append(Bubble(x=max(0, min(screen.width - 1, lid_x)), y=lid_y))
            self._next_small = random.uniform(self.small_bubble_min, self.small_bubble_max)
        # Handle periodic burst
        if not self._bursting and self._burst_timer <= 0:
            self._bursting = True
            self._burst_time_left = float(self.burst_duration)  # burst animation duration
            self._burst_timer = self.burst_period * random.uniform(0.9, 1.1)
            self._burst_emit_accum = 0.0
        if self._bursting:
            # Emit a stream of bubbles from the lid while open
            x_draw, y_draw, w, h = current_origin(True)
            self._burst_emit_accum += max(0.0, float(self.burst_emit_rate)) * dt
            n = int(self._burst_emit_accum)
            if n > 0:
                self._burst_emit_accum -= n
                for _ in range(n):
                    bx = x_draw + max(2, min(w - 2, 4 + random.randint(0, 3)))
                    by = y_draw - random.randint(1, 2)
                    app.bubbles.append(Bubble(x=max(0, min(screen.width - 1, bx)), y=by))
            self._burst_time_left -= dt
            if self._burst_time_left <= 0:
                self._bursting = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        # Choose current sprite and anchor drawing by a fixed baseline (bottom)
        lines = CHEST_OPEN if self._bursting else CHEST_CLOSED
        w, h = sprite_size(lines)
        # Compute a stable baseline from the original (closed) height so the
        # chest doesn't pop vertically when switching sprites.
        _wc, h_closed = sprite_size(CHEST_CLOSED)
        baseline = self.y + h_closed - 1
        # Keep the baseline within the screen (leave one row margin like spawn)
        baseline = min(screen.height - 2, max(0, baseline))
        # Recompute top-left y so bottom stays on the same baseline
        y = baseline - h + 1
        # Clamp within top edge if needed
        y = max(0, min(screen.height - h, y))
        x = max(0, min(screen.width - w, self.x))
        fg = Screen.COLOUR_WHITE if mono else Screen.COLOUR_YELLOW
        # Opaque mask like castle to avoid see-through artifacts
        draw_sprite_masked_with_bg(screen, lines, CHEST_MASK, x, y, fg, Screen.COLOUR_BLACK)

    @property
    def active(self) -> bool:
        # Chest is persistent decor; always active
        return True


def spawn_treasure_chest(screen: Screen, app) -> List[TreasureChest]:
    # Place near bottom-left-ish, leaving some space from edges
    lines = CHEST_CLOSED
    w, h = sprite_size(lines)
    x = max(0, min(screen.width - w - 2, 2))
    y = max(0, screen.height - h - 1)
    chest = TreasureChest(x=x, y=y, burst_period=getattr(app.settings, "chest_burst_seconds", 60.0))
    return [chest]
