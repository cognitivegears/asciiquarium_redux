from __future__ import annotations

import random
from typing import TYPE_CHECKING

from ...screen_compat import Screen

if TYPE_CHECKING:
    from ...protocols import ScreenProtocol, AsciiQuariumProtocol

from ...util import parse_sprite, sprite_size
from ..base import Actor


class Crab(Actor):
    def __init__(self, screen: "ScreenProtocol", app: "AsciiQuariumProtocol"):
        self.app = app
        self.dir = random.choice([-1, 1])
        self.speed = 5.0 * self.dir
        self.frames = [
            parse_sprite(
                r"""
 /\
( /   @ @    ()
 \\ __| |__  /
  \/   "   \/
 /-|       |-\
/ /-\     /-\ \
 / /-`---´-\ \
  /         \
"""
            ),
            parse_sprite(
                r"""
            /\
()    @ @   \ )
 \  __| |__ //
  \/   "   \/
 /-|       |-\
/ /-\     /-\ \
 / /-`---´-\ \
  /         \
"""
            )
        ]
        self.mask_frames = [
            parse_sprite(
                r"""
 rr
r r   w w    rr
 rr rrr rrr  r
  rr   r   rr
 rrr       rrr
r rrr     rrr r
 r rrrrrrrrr r
  r         r
"""
            ),
            parse_sprite(
                r"""
            rr
rr    w w   r r
 r  rrr rrr rr
  rr   r   rr
 rrr       rrr
r rrr     rrr r
 r rrrrrrrrr r
  r         r
"""
            )
        ]
        w_list = [sprite_size(f)[0] for f in self.frames]
        h_list = [sprite_size(f)[1] for f in self.frames]
        self.w, self.h = max(w_list), max(h_list)

        try:
            scene_w = int(getattr(getattr(app, "settings", None), "scene_width", screen.width))
        except Exception:
            scene_w = screen.width
        self.x = -self.w if self.dir > 0 else scene_w
        self.y = screen.height - self.h - 1
        
        self._frame_idx = 0
        self._frame_t = 0.0
        self._frame_dt = 1
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: "ScreenProtocol", app: "AsciiQuariumProtocol") -> None:
        self.x += self.speed * dt
        self._frame_t += dt
        if self._frame_t >= self._frame_dt:
            self._frame_t = 0.0
            self._frame_idx = (self._frame_idx + 1) % len(self.frames)
        try:
            scene_w = int(getattr(getattr(app, "settings", None), "scene_width", screen.width))
        except Exception:
            scene_w = screen.width
        if (self.dir > 0 and self.x > scene_w) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: "ScreenProtocol", mono: bool = False) -> None:
        self.draw_sprite(
            self.app,
            screen,
            self.frames[self._frame_idx],
            self.mask_frames[self._frame_idx],
            int(self.x),
            int(self.y),
            Screen.COLOUR_RED
        )


def spawn_crab(screen: "ScreenProtocol", app: "AsciiQuariumProtocol"):
    return [Crab(screen, app)]
