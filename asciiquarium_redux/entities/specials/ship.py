from __future__ import annotations

import random
from typing import TYPE_CHECKING
from ...screen_compat import Screen

from ...util import parse_sprite, sprite_size, draw_sprite, draw_sprite_masked
from ..base import Actor


class Ship(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 10.0 * self.dir
        # Spawn relative to full scene width so ship traverses entire scene
        scene_w = int(getattr(app.settings, "scene_width", screen.width))
        self.x = -24 if self.dir > 0 else scene_w
        self.y = 0
        ship_lr = [
            parse_sprite(
                r"""
     |    |    |
    )_)  )_)  )_)
   )___))___))___)\
  )____)____)_____)\\\
_____|____|____|____\\\\\__
\                   /
"""
            ),
            parse_sprite(
                r"""
     |    |    |
    )__) )__) )__)
   )___))___))___)\\
  )____)____)_____)\\\\
_____|____|____|____\\\\\\___
\                   /
"""
            ),
        ]
        ship_rl = [
            parse_sprite(
                r"""
         |    |    |
        (_(  (_(  (_(
      /(___((___((___(
    //(_____(____(____(
__///____|____|____|_____
    \                   /
"""
            ),
            parse_sprite(
                r"""
         |    |    |
        (__  (__  (__)
      /(___((___((___(\
    //(_____(____(____(\\
__///____|____|____|______
    \                   /
"""
            ),
        ]
        self.frames = ship_lr if self.dir > 0 else ship_rl
        # Use Perl masks for both animation frames to mirror exact color choices
        ship_mask_lr = [
            parse_sprite(
                r"""
     y    y    y

                  w
                   ww
yyyyyyyyyyyyyyyyyyyywwwyy
y                   y
"""
            ),
            parse_sprite(
                r"""
     y    y    y

                  w
                   ww
yyyyyyyyyyyyyyyyyyyywwwyy
y                   y
"""
            ),
        ]
        ship_mask_rl = [
            parse_sprite(
                r"""
         y    y    y

      w
    ww
yywwwyyyyyyyyyyyyyyyyyyyy
    y                   y
"""
            ),
            parse_sprite(
                r"""
         y    y    y

      w
    ww
yywwwyyyyyyyyyyyyyyyyyyyy
    y                   y
"""
            ),
        ]
        self.mask_frames = ship_mask_lr if self.dir > 0 else ship_mask_rl
        w_list = [sprite_size(f)[0] for f in self.frames]
        h_list = [sprite_size(f)[1] for f in self.frames]
        self.w, self.h = max(w_list), max(h_list)
        self._frame_idx = 0
        self._frame_t = 0.0
        self._frame_dt = 0.5
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen, app) -> None:
        self.x += self.speed * dt
        self._frame_t += dt
        if self._frame_t >= self._frame_dt:
            self._frame_t = 0.0
            self._frame_idx = (self._frame_idx + 1) % len(self.frames)
        scene_w = int(getattr(app.settings, "scene_width", screen.width))
        if (self.dir > 0 and self.x > scene_w) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen, mono: bool = False) -> None:
        img = self.frames[self._frame_idx]
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            mask = self.mask_frames[self._frame_idx % len(self.mask_frames)]
            draw_sprite_masked(screen, img, mask, int(self.x), int(self.y), Screen.COLOUR_WHITE)


def spawn_ship(screen: Screen, app):
    return [Ship(screen, app)]
