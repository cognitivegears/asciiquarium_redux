from __future__ import annotations

import random
import math
from asciimatics.screen import Screen

from ...util import parse_sprite, draw_sprite, draw_sprite_masked
from ..base import Actor


class Dolphins(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 20.0 * self.dir
        self.x = -13 if self.dir > 0 else screen.width
        self.base_y = 5
        self.t = 0.0
        self.distance = 15 * self.dir
        dolph_lr = [
            parse_sprite(
                r"""
     ,
   _/(__
.-'a    `-._/)
'^^~\)''''~~\)
"""
            ),
            parse_sprite(
                r"""
     ,
   _/(__  __/)
.-'a    ``.~\)
'^^~(/''''
"""
            ),
        ]
        dolph_rl = [
            parse_sprite(
                r"""
        ,
      __)\_
(\_.-'    a`-.
(/~~````(/~^^`
"""
            ),
            parse_sprite(
                r"""
        ,
(\__  __)\_
(/~.''    a`-.
    ````\)~^^`
"""
            ),
        ]
        self.frames = dolph_lr if self.dir > 0 else dolph_rl
        # Masks from Perl: left-to-right has W far right; right-to-left has W near left
        if self.dir > 0:
            self.mask = parse_sprite(
                r"""


          W
"""
            )
        else:
            self.mask = parse_sprite(
                r"""


   W
"""
            )
        self._frame_idx = 0
        self._frame_t = 0.0
        self._frame_dt = 0.25
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app) -> None:
        self.t += dt
        self.x += self.speed * dt
        self._frame_t += dt
        if self._frame_t >= self._frame_dt:
            self._frame_t = 0.0
            self._frame_idx = (self._frame_idx + 1) % len(self.frames)
        if (self.dir > 0 and self.x > screen.width + 30) or (self.dir < 0 and self.x < -30):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        for i in range(3):
            frame = self.frames[(self._frame_idx + i) % len(self.frames)]
            px = int(self.x + i * self.distance)
            py = int(self.base_y + 3 * math.sin((self.t * 2 + i) * 1.2))
            if mono:
                draw_sprite(screen, frame, px, py, Screen.COLOUR_WHITE)
            else:
                draw_sprite_masked(screen, frame, self.mask, px, py, Screen.COLOUR_CYAN)


def spawn_dolphins(screen: Screen, app):
    return [Dolphins(screen, app)]
