from __future__ import annotations

import random
from ...screen_compat import Screen

from ...util import parse_sprite, draw_sprite, draw_sprite_masked
from ..base import Actor


class Swan(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 10.0 * self.dir
        self.x = -10 if self.dir > 0 else screen.width
        self.y = 1
        swan_lr = [
            parse_sprite(
                r"""
       ___
,_    / _,\
| \   \( \|
|  \_  \\
(_   \_) \
(\_   `   \
 \   -=~  /
"""
            ),
            parse_sprite(
                r"""
       ___
,_    / _,\
| \   \( \|
|  \_  \\
(_   \_) \
(\_   `   \
 \   -=~  /
"""
            ),
        ]
        swan_rl = [
            parse_sprite(
                r"""
 ___
/,_ \    _,
|/ )/   / |
  //  _/  |
 / ( /   _)
/   `   _/)
\  ~=-   /
"""
            ),
            parse_sprite(
                r"""
 ___
/,_ \    _,
|/ )/   / |
  //  _/  |
 / ( /   _)
/   `   _/)
\   -=~  /
"""
            ),
        ]
        self.frames = swan_lr if self.dir > 0 else swan_rl
        # Build masks with full sprite height to preserve vertical alignment
        h = len(self.frames[0])
        ltr_mask = [''] * h
        rtl_mask = [''] * h
        # Match Perl: one blank line, then head 'g' and beak 'yy' alignment
        ltr_mask[1] = '         g'
        ltr_mask[2] = '         yy'
        rtl_mask[1] = ' g'
        rtl_mask[2] = 'yy'
        self.mask = ltr_mask if self.dir > 0 else rtl_mask
        self._frame_idx = 0
        self._frame_t = 0.0
        self._frame_dt = 0.25
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app) -> None:
        self.x += self.speed * dt
        self._frame_t += dt
        if self._frame_t >= self._frame_dt:
            self._frame_t = 0.0
            self._frame_idx = (self._frame_idx + 1) % len(self.frames)
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + 10 < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.frames[self._frame_idx]
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            draw_sprite_masked(screen, img, self.mask, int(self.x), int(self.y), Screen.COLOUR_WHITE)


def spawn_swan(screen: Screen, app):
    return [Swan(screen, app)]
