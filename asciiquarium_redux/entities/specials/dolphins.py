from __future__ import annotations

import random
import math
from ...screen_compat import Screen

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
        # Match Perl orientation: use the opposite set we previously had
        # so that left-to-right faces right and right-to-left faces left.
        self.frames = dolph_rl if self.dir > 0 else dolph_lr
        # Masks from Perl: align the 'W' with the eye on the facing side
        # Perl uses mask[0] (far right 'W') for left-to-right and mask[1] (near left 'W') for right-to-left.
        if self.dir > 0:
            # Left-to-right: eye highlight far right
            self.mask = parse_sprite(
                r"""


          W
"""
            )
        else:
            # Right-to-left: eye highlight near left
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
        # Match Perl: body coloured mostly blue, with one cyan highlight dolphin
        colours = [Screen.COLOUR_BLUE, Screen.COLOUR_BLUE, Screen.COLOUR_CYAN]
        for i in range(3):
            frame = self.frames[(self._frame_idx + i) % len(self.frames)]
            px = int(self.x + i * self.distance)
            py = int(self.base_y + 3 * math.sin((self.t * 2 + i) * 1.2))
            if mono:
                draw_sprite(screen, frame, px, py, Screen.COLOUR_WHITE)
            else:
                draw_sprite_masked(screen, frame, self.mask, px, py, colours[i])


def spawn_dolphins(screen: Screen, app):
    return [Dolphins(screen, app)]
