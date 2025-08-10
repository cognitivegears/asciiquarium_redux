from __future__ import annotations

import random
from asciimatics.screen import Screen

from ...util import parse_sprite, sprite_size, draw_sprite, draw_sprite_masked
from ..base import Actor


class Monster(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 15.0 * self.dir
        self.x = -64 if self.dir > 0 else screen.width
        self.y = 2
        self.frames = [
            parse_sprite(
                r"""
   ____
 _/ o  \____
/  __       \
\_/  \_______)
"""
            ),
            parse_sprite(
                r"""
   ____
 _/ O  \____
/  __       \
\_/  \______)
"""
            ),
            parse_sprite(
                r"""
   ____
 _/ o  \____
/  __       \
\_/  \_______)
"""
            ),
            parse_sprite(
                r"""
   ____
 _/ .  \____
/  __       \
\_/  \______)
"""
            ),
        ]
        w_list = [sprite_size(f)[0] for f in self.frames]
        h_list = [sprite_size(f)[1] for f in self.frames]
        self.w, self.h = max(w_list), max(h_list)
        # Build a simple mask indicating a white eye (W); body picks up default green
        self.mask_frames = []
        for fr in self.frames:
            m = []
            for row in fr:
                # mark the eye character 'o' / 'O' / '.' as white; else space to use default
                m.append(''.join('W' if ch in ('o','O','.') else ' ' for ch in row))
            self.mask_frames.append(m)
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
        if self.dir < 0:
            img = [line[::-1] for line in img]
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            mask = self.mask_frames[self._frame_idx]
            if self.dir < 0:
                mask = [line[::-1] for line in mask]
            draw_sprite_masked(screen, img, mask, int(self.x), int(self.y), Screen.COLOUR_GREEN)


def spawn_monster(screen: Screen, app):
    return [Monster(screen, app)]
