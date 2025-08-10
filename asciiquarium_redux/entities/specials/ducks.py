from __future__ import annotations

import random
from asciimatics.screen import Screen

from ...util import parse_sprite, sprite_size, draw_sprite, draw_sprite_masked
from ..base import Actor


class Ducks(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 10.0 * self.dir
        self.x = -30 if self.dir > 0 else screen.width
        self.y = 5
        ducks_lr = [
            parse_sprite(
                r"""
      _  _  _
,____(')=,____(')=,____(')<
 \~~= ')  \~~= ')  \~~= ')
"""
            ),
            parse_sprite(
                r"""
      _  _  _
,____(')=,____(')<,____(')=
 \~~= ')  \~~= ')  \~~= ')
"""
            ),
            parse_sprite(
                r"""
      _  _  _
,____(')<,____(')=,____(')=
 \~~= ')  \~~= ')  \~~= ')
"""
            ),
        ]
        ducks_rl = [
            parse_sprite(
                r"""
  _  _  _
>(')____,=(')____,=(')____,
 (` =~~/  (` =~~/  (` =~~/
"""
            ),
            parse_sprite(
                r"""
  _  _  _
=(')____,>(')____,=(')____,
 (` =~~/  (` =~~/  (` =~~/
"""
            ),
            parse_sprite(
                r"""
  _  _  _
=(')____,=(')____,>(')____,
 (` =~~/  (` =~~/  (` =~~/
"""
            ),
        ]
        self.frames = ducks_lr if self.dir > 0 else ducks_rl
        duck_mask_lr = parse_sprite(
            r"""
      g          g          g
wwwwwgcgy  wwwwwgcgy  wwwwwgcgy
 wwww Ww    wwww Ww    wwww Ww
"""
        )
        duck_mask_rl = parse_sprite(
            r"""
  g          g          g
ygcgwwwww  ygcgwwwww  ygcgwwwww
 wW wwww    wW wwww    wW wwww
"""
        )
        self.mask = duck_mask_lr if self.dir > 0 else duck_mask_rl
        w_list = [sprite_size(f)[0] for f in self.frames]
        h_list = [sprite_size(f)[1] for f in self.frames]
        self.w, self.h = max(w_list), max(h_list)
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
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.frames[self._frame_idx]
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            draw_sprite_masked(screen, img, self.mask, int(self.x), int(self.y), Screen.COLOUR_YELLOW)


def spawn_ducks(screen: Screen, app):
    return [Ducks(screen, app)]
