from __future__ import annotations

import random
from ...screen_compat import Screen

from ...util import parse_sprite, draw_sprite, aabb_overlap
from ..core import Fish, Splat
from ..base import Actor


class FishHook(Actor):
    def __init__(self, screen: Screen, app, target_x: int | None = None, target_y: int | None = None):
        # Hook ASCII: hook point relative offset is (dx=1, dy=2)
        if target_x is not None:
            # Align hook point (x+1) to target_x
            self.x = max(0, min(screen.width - 8, int(target_x) - 1))
        else:
            self.x = random.randint(10, max(11, screen.width - 10))
        self.y = -4
        self.state = "lowering"
        self.speed = 15.0
        self.caught = None
        self._active = True
        # Optional targeted drop (hook point to reach target_y)
        self._target_top_y = (int(target_y) - 2) if target_y is not None else None
        # Short pause after impact to show splat before retracting
        self.pause_timer = 0.0
        # Dwell timer when reaching bottom (seconds); pulled from app.settings
        self.dwell_timer = float(getattr(app.settings, "fishhook_dwell_seconds", 20.0))

    def retract_now(self):
        if self.state != "retracting":
            self.state = "retracting"

    @property
    def active(self) -> bool:
        return True if self._active else False

    def update(self, dt: float, screen: Screen, app) -> None:
        if self.state == "lowering":
            limit_reached = False
            # Move down towards target or depth limit
            if self._target_top_y is not None:
                if self.y < self._target_top_y:
                    self.y += self.speed * dt
                else:
                    limit_reached = True
            else:
                if self.y + 6 < int(screen.height * 0.75):
                    self.y += self.speed * dt
                else:
                    limit_reached = True

            # Check for collision with regular fish using the hook tip (hx, hy)
            if not self.caught:
                hx = int(self.x + 1)
                hy = int(self.y + 2)
                for f in app.fish:
                    if f.hooked:
                        continue
                    if aabb_overlap(hx, hy, 1, 1, int(f.x), int(f.y), f.width, f.height):
                        # Play splat animation at impact point and attach fish to hook
                        app.splats.append(Splat(x=hx, y=hy))
                        self.caught = f
                        f.attach_to_hook(hx, hy)
                        # Pause briefly so the splat is visible
                        self.state = "impact_pause"
                        self.pause_timer = 0.35
                        break
            if not self.caught and limit_reached:
                # Start dwelling at bottom instead of retracting immediately
                self.state = "dwelling"
        elif self.state == "impact_pause":
            # Hold position briefly; keep attached fish aligned with tip
            hx = int(self.x + 1)
            hy = int(self.y + 2)
            if self.caught:
                self.caught.follow_hook(hx, hy)
            self.pause_timer -= dt
            if self.pause_timer <= 0:
                self.state = "retracting"
        elif self.state == "dwelling":
            # Stay put at bottom for a while; keep fish (if any) aligned
            hx = int(self.x + 1)
            hy = int(self.y + 2)
            if self.caught:
                self.caught.follow_hook(hx, hy)
            else:
                # While dwelling, still check for fish contact at the hook tip
                for f in app.fish:
                    if f.hooked:
                        continue
                    if aabb_overlap(hx, hy, 1, 1, int(f.x), int(f.y), f.width, f.height):
                        app.splats.append(Splat(x=hx, y=hy))
                        self.caught = f
                        f.attach_to_hook(hx, hy)
                        # Brief impact pause before retracting for visibility
                        self.state = "impact_pause"
                        self.pause_timer = 0.35
                        break
            self.dwell_timer -= dt
            if self.dwell_timer <= 0:
                self.state = "retracting"
        else:
            self.y -= self.speed * dt
            hx = int(self.x + 1)
            hy = int(self.y + 2)
            if self.caught:
                self.caught.follow_hook(hx, hy)
            else:
                # While retracting without a catch, still allow catching a fish
                for f in app.fish:
                    if f.hooked:
                        continue
                    if aabb_overlap(hx, hy, 1, 1, int(f.x), int(f.y), f.width, f.height):
                        app.splats.append(Splat(x=hx, y=hy))
                        self.caught = f
                        f.attach_to_hook(hx, hy)
                        # Brief pause to show the splat, then continue retracting
                        self.state = "impact_pause"
                        self.pause_timer = 0.35
                        break
            if self.y <= 0:
                # Remove the caught fish when hook returns to top
                if self.caught and self.caught in app.fish:
                    try:
                        app.fish.remove(self.caught)
                    except ValueError:
                        pass
                self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        top = -50
        line_len = int(self.y) - top
        for i in range(line_len):
            ly = top + i
            if 0 <= ly < screen.height:
                screen.print_at("|", self.x + 7, ly, colour=Screen.COLOUR_WHITE if mono else Screen.COLOUR_GREEN)
        hook = parse_sprite(
            r"""
       o
      ||
      ||
/ \   ||
  \__//
  `--'
"""
        )
        draw_sprite(screen, hook, self.x, int(self.y), Screen.COLOUR_WHITE if mono else Screen.COLOUR_GREEN)


def spawn_fishhook(screen: Screen, app):
    # Enforce single fishhook: if one is active, do not spawn another
    if any(isinstance(a, FishHook) and a.active for a in app.specials):
        return []
    return [FishHook(screen, app)]


def spawn_fishhook_to(screen: Screen, app, target_x: int, target_y: int):
    # Enforce single fishhook for targeted spawns as well
    if any(isinstance(a, FishHook) and a.active for a in app.specials):
        return []
    return [FishHook(screen, app, target_x=target_x, target_y=target_y)]
