from __future__ import annotations

import random
from typing import TYPE_CHECKING
from ...screen_compat import Screen
if TYPE_CHECKING:
    from ...protocols import ScreenProtocol
else:
    from ...screen_compat import Screen as ScreenProtocol

from ...util import parse_sprite, draw_sprite, aabb_overlap
from ..core import Splat
from ..base import Actor
from ...constants import (
    FISHHOOK_SPEED,
    FISHHOOK_IMPACT_PAUSE_DURATION,
    FISHHOOK_DWELL_TIME_DEFAULT,
    FISHHOOK_DEPTH_LIMIT_FRACTION,
    FISHHOOK_TIP_OFFSET_X,
    FISHHOOK_TIP_OFFSET_Y,
    FISHHOOK_LINE_TOP,
    FISHHOOK_LINE_OFFSET_X,
)


class FishHook(Actor):
    def __init__(self, screen: "ScreenProtocol", app, target_x: int | None = None, target_y: int | None = None):
        # Hook ASCII: hook point relative offset is (dx=1, dy=2)
        # World width for horizontal clamping: scene width in scene mode, else screen
        try:
            world_w = int(getattr(app.settings, "scene_width", screen.width))
            if bool(getattr(app.settings, "fish_tank", False)):
                world_w = screen.width
        except Exception:
            world_w = screen.width
        if target_x is not None:
            # target_x is in scene coordinates: align hook point (x+1) to target_x
            self.x = int(target_x) - 1
        else:
            # Choose a random scene X within current view
            try:
                off = int(getattr(app.settings, "scene_offset", 0))
            except Exception:
                off = 0
            lo = max(0, off + 10)
            hi = max(lo + 1, min(off + screen.width - 10, world_w - 1))
            self.x = random.randint(lo, hi) - 1
        # Clamp within world bounds considering hook sprite width (~8)
        self.x = max(0, min(world_w - 8, int(self.x)))
        self.y = -4
        self.state = "lowering"
        self.speed = FISHHOOK_SPEED
        self.caught = None
        self._active = True
        # Optional targeted drop (hook point to reach target_y)
        self._target_top_y = (int(target_y) - 2) if target_y is not None else None
        # Short pause after impact to show splat before retracting
        self.pause_timer = 0.0
        # Dwell timer when reaching bottom (seconds); pulled from app.settings
        self.dwell_timer = float(getattr(app.settings, "fishhook_dwell_seconds", FISHHOOK_DWELL_TIME_DEFAULT))

    def retract_now(self):
        if self.state != "retracting":
            self.state = "retracting"

    @property
    def active(self) -> bool:
        return True if self._active else False

    def update(self, dt: float, screen: "ScreenProtocol", app) -> None:
        if self.state == "lowering":
            limit_reached = False
            # Move down towards target or depth limit
            if self._target_top_y is not None:
                if self.y < self._target_top_y:
                    self.y += self.speed * dt
                else:
                    limit_reached = True
            else:
                if self.y + 6 < int(screen.height * FISHHOOK_DEPTH_LIMIT_FRACTION):
                    self.y += self.speed * dt
                else:
                    limit_reached = True

            # Check for collision with regular fish using the hook tip (hx, hy)
            if not self.caught:
                hx = int(self.x + FISHHOOK_TIP_OFFSET_X)
                hy = int(self.y + FISHHOOK_TIP_OFFSET_Y)
                for f in app.fish:
                    if f.hooked:
                        continue
                    if aabb_overlap(hx, hy, 1, 1, int(f.x), int(f.y), f.width, f.height):
                        # Play splat animation at impact point and attach fish to hook
                        app.splats.append(Splat(x=hx, y=hy, coord_space="scene"))
                        self.caught = f
                        f.attach_to_hook(hx, hy)
                        # Pause briefly so the splat is visible
                        self.state = "impact_pause"
                        self.pause_timer = FISHHOOK_IMPACT_PAUSE_DURATION
                        break
            if not self.caught and limit_reached:
                # Start dwelling at bottom instead of retracting immediately
                self.state = "dwelling"
        elif self.state == "impact_pause":
            # Hold position briefly; keep attached fish aligned with tip
            hx = int(self.x + FISHHOOK_TIP_OFFSET_X)
            hy = int(self.y + FISHHOOK_TIP_OFFSET_Y)
            if self.caught:
                self.caught.follow_hook(hx, hy)
            self.pause_timer -= dt
            if self.pause_timer <= 0:
                self.state = "retracting"
        elif self.state == "dwelling":
            # Stay put at bottom for a while; keep fish (if any) aligned
            hx = int(self.x + FISHHOOK_TIP_OFFSET_X)
            hy = int(self.y + FISHHOOK_TIP_OFFSET_Y)
            if self.caught:
                self.caught.follow_hook(hx, hy)
            else:
                # While dwelling, still check for fish contact at the hook tip
                for f in app.fish:
                    if f.hooked:
                        continue
                    if aabb_overlap(hx, hy, 1, 1, int(f.x), int(f.y), f.width, f.height):
                        app.splats.append(Splat(x=hx, y=hy, coord_space="scene"))
                        self.caught = f
                        f.attach_to_hook(hx, hy)
                        # Brief impact pause before retracting for visibility
                        self.state = "impact_pause"
                        self.pause_timer = FISHHOOK_IMPACT_PAUSE_DURATION
                        break
            self.dwell_timer -= dt
            if self.dwell_timer <= 0:
                self.state = "retracting"
        else:
            self.y -= self.speed * dt
            hx = int(self.x + FISHHOOK_TIP_OFFSET_X)
            hy = int(self.y + FISHHOOK_TIP_OFFSET_Y)
            if self.caught:
                self.caught.follow_hook(hx, hy)
            else:
                # While retracting without a catch, still allow catching a fish
                for f in app.fish:
                    if f.hooked:
                        continue
                    if aabb_overlap(hx, hy, 1, 1, int(f.x), int(f.y), f.width, f.height):
                        app.splats.append(Splat(x=hx, y=hy, coord_space="scene"))
                        self.caught = f
                        f.attach_to_hook(hx, hy)
                        # Brief pause to show the splat, then continue retracting
                        self.state = "impact_pause"
                        self.pause_timer = FISHHOOK_IMPACT_PAUSE_DURATION
                        break
            if self.y <= 0:
                # Remove the caught fish when hook returns to top
                if self.caught and self.caught in app.fish:
                    try:
                        app.fish.remove(self.caught)
                    except ValueError:
                        pass
                self._active = False

    def draw(self, screen: "ScreenProtocol", mono: bool = False) -> None:
        top = FISHHOOK_LINE_TOP
        line_len = int(self.y) - top
        for i in range(line_len):
            ly = top + i
            if 0 <= ly < screen.height:
                screen.print_at("|", self.x + FISHHOOK_LINE_OFFSET_X, ly, colour=Screen.COLOUR_WHITE if mono else Screen.COLOUR_GREEN)
        hook = parse_sprite(
            r"""
       o
      ||
 .    ||
/ \   ||
 \\__//
  `--'
"""
        )
        draw_sprite(screen, hook, self.x, int(self.y), Screen.COLOUR_WHITE if mono else Screen.COLOUR_GREEN)


def spawn_fishhook(screen: "ScreenProtocol", app):
    # Enforce single fishhook: if one is active, do not spawn another
    if any(isinstance(a, FishHook) and a.active for a in app.specials):
        return []
    # Spawn within current view in scene coordinates
    try:
        off = int(getattr(app.settings, "scene_offset", 0))
        world_w = int(getattr(app.settings, "scene_width", screen.width))
        if bool(getattr(app.settings, "fish_tank", False)):
            world_w = screen.width
    except Exception:
        off = 0
        world_w = screen.width
    lo = max(0, off + 5)
    hi = max(lo + 1, min(off + screen.width - 5, world_w - 1))
    x_scene = random.randint(lo, hi)
    return [FishHook(screen, app, target_x=x_scene, target_y=None)]


def spawn_fishhook_to(screen: "ScreenProtocol", app, target_x: int, target_y: int):
    # Enforce single fishhook for targeted spawns as well
    if any(isinstance(a, FishHook) and a.active for a in app.specials):
        return []
    # Convert screen click x to scene x
    try:
        off = int(getattr(app.settings, "scene_offset", 0))
        x_scene = int(target_x) + off
    except Exception:
        x_scene = int(target_x)
    return [FishHook(screen, app, target_x=x_scene, target_y=target_y)]
