from __future__ import annotations

import random
from asciimatics.screen import Screen

from ...util import parse_sprite, draw_sprite, aabb_overlap
from ..core import Fish
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
        self.caught: Fish | None = None
        self._active = True
        # Optional targeted drop (hook point to reach target_y)
        self._target_top_y: int | None = (int(target_y) - 2) if target_y is not None else None

    @property
    def active(self) -> bool:
        return True if self._active else False

    def update(self, dt: float, screen: Screen, app) -> None:
        if self.state == "lowering":
            limit_reached = False
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
                hx = int(self.x + 1)
                hy = int(self.y + 2)
                for f in app.fish:
                    if f.hooked:
                        continue
                    if aabb_overlap(hx, hy, 1, 1, int(f.x), int(f.y), f.width, f.height):
                        self.caught = f
                        f.attach_to_hook(hx, hy)
                        self.state = "retracting"
                        break
            if not self.caught and limit_reached:
                self.state = "retracting"
        else:
            self.y -= self.speed * dt
            hx = int(self.x + 1)
            hy = int(self.y + 2)
            if self.caught:
                self.caught.follow_hook(hx, hy)
            if self.y <= 0:
                if self.caught and self.caught in app.fish:
                    self.x = screen.width - 1
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
    return [FishHook(screen, app)]


def spawn_fishhook_to(screen: Screen, app, target_x: int, target_y: int):
    return [FishHook(screen, app, target_x=target_x, target_y=target_y)]
