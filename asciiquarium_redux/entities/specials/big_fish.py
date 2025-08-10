from __future__ import annotations

import random
from asciimatics.screen import Screen

from ...util import parse_sprite, sprite_size, draw_sprite, draw_sprite_masked, randomize_colour_mask
from ..base import Actor


class BigFish(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 30.0 * (self.dir / abs(self.dir))
        if self.dir > 0:
            self.img = parse_sprite(
                r"""
 ______
`""-.  `````-----.....__
     `.  .      .       `-.
       :     .     .       `.
 ,     :   .    .          _ :
: `.   :                  (@) `._
 `. `..'     .     =`-.       .__)
   ;     .        =  ~  :     .-"
 .' .'`.   .    .  =.-'  `._ .'
: .'   :               .   .'
 '   .'  .    .     .   .-'
   .'____....----''.'='.
   ""             .'.'
               ''"'`
"""
            )
            self.mask = parse_sprite(
                r"""
  111111
 11111  11111111111111111
      11  2      2       111
        1     2     2       11
  1     1   2    2          1 1
 1 11   1                  1W1 111
  11 1111     2     1111       1111
    1     2        1  1  1     111
  11 1111   2    2  1111  111 11
 1 11   1               2   11
  1   11  2    2     2   111
    111111111111111111111
    11             1111
                11111
"""
            )
            self.x = -34
        else:
            self.img = parse_sprite(
                r"""
                           ______
          __.....-----'''''  .-""'
       .-'       .      .  .'
     .'       .     .     :
    : _          .    .   :     ,
 _.' (@)                  :   .' :
(__.       .-'=     .     `..' .'
 "-.     :  ~  =        .     ;
   `. _.'  `-.=  .    .   .'`. `.
     `.   .               :   `. :
       `-.   .     .    .  `.   `
          `.=`.``----....____`.
            `.`.             ""
              '`"``
"""
            )
            self.mask = parse_sprite(
                r"""
                           111111
          11111111111111111  11111
       111       2      2  11
     11       2     2     1
    1 1          2    2   1     1
 111 1W1                  1   11 1
1111       1111     2     1111 11
 111     1  1  1        2     1
   11 111  1111  2    2   1111 11
     11   2               1   11 1
       111   2     2    2  11   1
          111111111111111111111
            1111             11
              11111
"""
            )
            self.x = screen.width
        self.w, self.h = sprite_size(self.img)
        max_height = 9
        min_height = max_height if screen.height - 15 <= max_height else (screen.height - 15)
        self.y = random.randint(max_height, max(min_height, max_height))
        # Randomize mask colours once to avoid per-frame flicker
        self._rand_mask = randomize_colour_mask(self.mask)
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app) -> None:
        self.x += self.speed * dt
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.img
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            mask = self._rand_mask
            draw_sprite_masked(screen, img, mask, int(self.x), int(self.y), Screen.COLOUR_YELLOW)


def spawn_big_fish(screen: Screen, app):
    return [BigFish(screen, app)]
