from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

from ...screen_compat import Screen
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ...protocols import ScreenProtocol, AsciiQuariumProtocol

from ..base import Actor
from ..core import Bubble
from ...util import sprite_size, draw_sprite_masked_with_bg
from ..environment import CHEST_CLOSED, CHEST_OPEN, CHEST_MASK


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
        # Validate burst_emit_rate to prevent negative values that could cause issues
        self.burst_emit_rate = max(0.0, float(self.burst_emit_rate))
        # Randomize initial timers so multiple chests don't sync
        self._next_small = random.uniform(self.small_bubble_min, self.small_bubble_max)
        self._burst_timer = self.burst_period * random.uniform(0.7, 1.3)

    def update(self, dt: float, screen: "ScreenProtocol", app: "AsciiQuariumProtocol") -> None:  # type: ignore[override]
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
            # Map scene -> screen using current view offset for correct bubble positions
            try:
                off = int(getattr(app.settings, "scene_offset", 0))
            except Exception:
                off = 0
            x_draw = int(self.x) - off
            # Cull/clamp to on-screen bounds for bubble emission logic
            x_draw = max(0, min(screen.width - w, x_draw))
            return x_draw, y_draw, w, h

        # Determine visibility for emission culling (scene mode)
        try:
            off = int(getattr(app.settings, "scene_offset", 0))
        except Exception:
            off = 0
        w_vis, _h_vis = sprite_size(CHEST_CLOSED)
        chest_x_view = int(self.x) - off
        visible = (chest_x_view + w_vis > 0) and (chest_x_view < screen.width)

        # Emit occasional small bubble from the lid area when not bursting
        if self._next_small <= 0 and not self._bursting and visible:
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
        if self._bursting and visible:
            # Emit a stream of bubbles from the lid while open
            x_draw, y_draw, w, h = current_origin(True)
            # Ensure burst_emit_rate is always non-negative
            safe_emit_rate = max(0.0, float(self.burst_emit_rate))
            self._burst_emit_accum += safe_emit_rate * dt
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

    def draw(self, screen: "ScreenProtocol", mono: bool = False) -> None:
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
        # Use scene-mapped x directly; clipping is handled by drawing utilities
        x = int(self.x)
        fg = Screen.COLOUR_WHITE if mono else Screen.COLOUR_YELLOW
        # Opaque mask like castle to avoid see-through artifacts
        draw_sprite_masked_with_bg(screen, lines, CHEST_MASK, x, y, fg, Screen.COLOUR_BLACK)

    @property
    def active(self) -> bool:
        # Chest is persistent decor; always active
        return True


def spawn_treasure_chest(screen: Screen, app) -> List[TreasureChest]:
    # Enforce single pirate chest overall, similar to the castle.
    lines = CHEST_CLOSED
    w, h = sprite_size(lines)
    y = max(0, screen.height - h - 1)
    try:
        scene_w = int(getattr(app.settings, "scene_width", screen.width))
        tank_mode = bool(getattr(app.settings, "fish_tank", True))
        off = int(getattr(app.settings, "scene_offset", 0))
    except Exception:
        scene_w = screen.width
        tank_mode = True
        off = 0
    # Tank mode: single chest near left
    if tank_mode:
        x = max(0, min(screen.width - w - 2, 2))
        return [TreasureChest(x=x, y=y, burst_period=getattr(app.settings, "chest_burst_seconds", 60.0))]
    # Scene mode: place the single chest within the initial centered view
    view_lo, view_hi = off, off + screen.width
    margin = 2
    x = max(view_lo + margin, min(view_hi - w - margin, off + screen.width // 3))
    # Clamp within scene bounds
    x = max(0, min(scene_w - w - 1, x))
    return [TreasureChest(x=int(x), y=y, burst_period=getattr(app.settings, "chest_burst_seconds", 60.0))]
