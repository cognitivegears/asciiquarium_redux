from __future__ import annotations

import random
from asciimatics.screen import Screen

from ...util import parse_sprite, sprite_size, draw_sprite, draw_sprite_masked
from ..base import Actor


class Whale(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 10.0 * self.dir
        self.x = -18 if self.dir > 0 else screen.width
        self.y = 0
        self.base = parse_sprite(
            r"""
                .-----:
            .'       `.
 / (o)       \
(__,          \_.'
"""
        )
        self.w, self.h = sprite_size(self.base)
        self.mask = parse_sprite(
            r"""
                         C C
                     CCCCCCC
                     C  C  C
                BBBBBBB
            BB       BB
B    B       BWB B
BBBBB          BBBB
"""
        )
        self.spout_frame = 0
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app) -> None:
        self.x += self.speed * dt / 2
        self.spout_frame = (self.spout_frame + 1) % 20
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        if self.spout_frame < 10:
            sp = ["   :", "   :", "  . .", " .-:-."]
            for i, row in enumerate(sp[: max(0, self.spout_frame // 3)]):
                colour = Screen.COLOUR_WHITE if mono else Screen.COLOUR_CYAN
                screen.print_at(row, int(self.x) + (1 if self.dir > 0 else 11), i, colour=colour)
        img = self.base if self.dir > 0 else [line[::-1] for line in self.base]
        msk = self.mask if self.dir > 0 else [line[::-1] for line in self.mask]
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            draw_sprite_masked(screen, img, msk, int(self.x), int(self.y), Screen.COLOUR_WHITE)


def spawn_whale(screen: Screen, app):
    return [Whale(screen, app)]
