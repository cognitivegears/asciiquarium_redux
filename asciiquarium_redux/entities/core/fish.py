from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List
from ...screen_compat import Screen

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
    # Z-depth for layering between fish (higher draws on top)
    z: int = field(default_factory=lambda: random.randint(3, 20))
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
    # Turning state
    turning: bool = False
    turn_phase: str = "idle"  # shrink | flip | expand | idle
    turn_t: float = 0.0
    turn_shrink_seconds: float = 0.35
    turn_expand_seconds: float = 0.35
    base_speed: float = 0.0
    next_turn_ok_in: float = field(default_factory=lambda: random.uniform(4.0, 10.0))
    # Global fish settings references (populated by app)
    turn_enabled: bool = True
    turn_chance_per_second: float = 0.01
    turn_min_interval: float = 6.0

    @property
    def width(self) -> int:
        return max(len(r) for r in self.frames)

    @property
    def height(self) -> int:
        return len(self.frames)

    def update(self, dt: float, screen: Screen, bubbles: List[Bubble]):
        # Handle turn timer/chance
        if not self.hooked and self.turn_enabled:
            self.next_turn_ok_in = max(0.0, self.next_turn_ok_in - dt)
            if not self.turning and self.next_turn_ok_in <= 0.0:
                # Poisson process: chance per second scaled by dt
                if random.random() < max(0.0, self.turn_chance_per_second) * dt:
                    self.start_turn()

        # Movement with speed ramp depending on turning phase
        speed_scale = 1.0
        if self.turning:
            if self.turn_phase == "shrink":
                # slow down towards stop
                speed_scale = max(0.0, 1.0 - (self.turn_t / max(0.001, self.turn_shrink_seconds)))
            elif self.turn_phase == "expand":
                # speed up from stop
                speed_scale = min(1.0, (self.turn_t / max(0.001, self.turn_expand_seconds)))
            else:
                speed_scale = 0.0
        self.x += self.vx * dt * 20.0 * speed_scale
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
        # Advance turn animation
        if self.turning:
            self.turn_t += dt
            if self.turn_phase == "shrink" and self.turn_t >= self.turn_shrink_seconds:
                # Reached middle: flip frames and direction, stop movement
                self.finish_shrink_and_flip()
            elif self.turn_phase == "expand" and self.turn_t >= self.turn_expand_seconds:
                # Done expanding
                self.turning = False
                self.turn_phase = "idle"
                self.turn_t = 0.0
                self.next_turn_ok_in = max(self.turn_min_interval, random.uniform(self.turn_min_interval, self.turn_min_interval + 8.0))

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
        # Reset turning animation state on respawn, but keep cooldown timer so turns still happen across respawns
        self.turning = False
        self.turn_phase = "idle"
        self.turn_t = 0.0

    def draw(self, screen: Screen):
        lines = self.frames
        mask = self.colour_mask
        x_off = 0
        # During turning, render a sliced/narrowed view to simulate columns disappearing/appearing
        if self.turning:
            w = self.width
            # Compute current visible width based on phase
            if self.turn_phase == "shrink":
                frac = max(0.0, 1.0 - (self.turn_t / max(0.001, self.turn_shrink_seconds)))
                vis = max(1, int(round(w * frac)))
                if vis % 2 == 0 and vis > 1:
                    vis -= 1
            elif self.turn_phase == "expand":
                frac = min(1.0, (self.turn_t / max(0.001, self.turn_expand_seconds)))
                vis = max(1, int(round(w * frac)))
                if vis % 2 == 0 and vis > 1:
                    vis -= 1
            else:
                vis = 1
            # Centered slice: remove inside columns one from each side means converge to center
            left = (w - vis) // 2
            right = left + vis
            def slice_cols(rows: List[str], l: int, r: int) -> List[str]:
                out: List[str] = []
                for row in rows:
                    seg = row[l:r] if 0 <= l < len(row) else row
                    # Ensure at least 1 char width; pad if empty
                    if seg == "":
                        seg = " "
                    out.append(seg)
                return out
            lines = slice_cols(lines, left, right)
            if mask is not None:
                mask = slice_cols(mask, left, right)
            # Shift draw position so the center stays stable during shrink/expand
            x_off = left
        if mask is not None:
            draw_sprite_masked(screen, lines, mask, int(self.x) + x_off, int(self.y), self.colour)
        else:
            draw_sprite(screen, lines, int(self.x) + x_off, int(self.y), self.colour)

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

    # Turning control
    def start_turn(self):
        if self.turning or self.hooked:
            return
        self.turning = True
        self.turn_phase = "shrink"
        self.turn_t = 0.0
        self.base_speed = self.vx

    def finish_shrink_and_flip(self):
        # At the narrowest point: flip direction and frames, stop, then expand and ramp speed
        direction = -1 if self.vx > 0 else 1
        # Swap to opposite direction frames but choose the same size index if possible
        from .fish_assets import FISH_RIGHT, FISH_LEFT, FISH_RIGHT_MASKS, FISH_LEFT_MASKS
        src = FISH_RIGHT if direction > 0 else FISH_LEFT
        src_masks = FISH_RIGHT_MASKS if direction > 0 else FISH_LEFT_MASKS
        # Try to match width to current lines
        curr_w = self.width
        candidate = list(zip(src, src_masks))
        frames, mask = min(candidate, key=lambda fm: abs(max(len(r) for r in fm[0]) - curr_w))
        self.frames = frames
        self.colour_mask = randomize_colour_mask(mask) if self.colour_mask is not None else None
        # Reverse velocity sign, magnitude picked from base_speed magnitude
        speed_mag = abs(self.base_speed) if self.base_speed != 0 else random.uniform(self.speed_min, self.speed_max)
        self.vx = speed_mag * direction
        # Continue to expand phase
        self.turn_phase = "expand"
        self.turn_t = 0.0
