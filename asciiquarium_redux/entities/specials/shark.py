from __future__ import annotations

import random
from asciimatics.screen import Screen

from ...util import parse_sprite, sprite_size, draw_sprite, draw_sprite_masked, aabb_overlap
from ..core import Splat, Fish
from ..base import Actor


class Shark(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 2.0 * self.dir
        self.y = random.randint(max(9, 1), max(9, screen.height - 10))
        self.frame = parse_sprite(
            r"""
  __     __
 (  `-._/  )
  \   o  _/
  /  __  \
 /__/  \__\
"""
        )
        self.w, self.h = sprite_size(self.frame)
        self.x = -self.w if self.dir > 0 else screen.width
        # Mask: default white
        self.mask = ["W" * len(row) for row in self.frame]
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app) -> None:
        self.x += self.speed * dt * 20.0
        for f in list(app.fish):
            if f.hooked:
                continue
            if aabb_overlap(int(self.x), int(self.y), self.w, self.h, int(f.x), int(f.y), f.width, f.height):
                app.splats.append(Splat(x=int(f.x + f.width // 2), y=int(f.y + f.height // 2)))
                app.fish.remove(f)
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.frame if self.dir > 0 else [line[::-1] for line in self.frame]
        msk = self.mask if self.dir > 0 else [line[::-1] for line in self.mask]
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            draw_sprite_masked(screen, img, msk, int(self.x), int(self.y), Screen.COLOUR_WHITE)


def spawn_shark(screen: Screen, app):
    return [Shark(screen, app)]
