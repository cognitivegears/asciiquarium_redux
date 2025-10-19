from __future__ import annotations

import random
from typing import TYPE_CHECKING
from ...screen_compat import Screen

from ...util import parse_sprite, sprite_size, draw_sprite, draw_sprite_masked, draw_sprite_masked_with_bg, randomize_colour_mask
from ..base import Actor
from ..environment import WATER_SEGMENTS

if TYPE_CHECKING:
    from ...protocols import ScreenProtocol, AsciiQuariumProtocol


"""Giant fish special.

Includes a guard in the spawner to avoid spawning on screens where it cannot
fit entirely between the water surface and the bottom margin.
"""


# Define sprite templates so we can measure height without instantiating
SPRITE_RIGHT = r"""
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

SPRITE_LEFT = r"""
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

# Pre-compute visible sprite height (both variants have same height)
_BF_W, _BF_H = sprite_size(parse_sprite(SPRITE_RIGHT))


class BigFish(Actor):
  def __init__(self, screen: "ScreenProtocol", app: "AsciiQuariumProtocol"):
    self.app = app
    self.dir = random.choice([-1, 1])
    self.speed = 30.0 * (self.dir / abs(self.dir))

    if self.dir > 0:
      self.img = parse_sprite(SPRITE_RIGHT)
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
      self.img = parse_sprite(SPRITE_LEFT)
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
      try:
        scene_w = int(getattr(getattr(app, "settings", None), "scene_width", screen.width))
      except Exception:
        scene_w = screen.width
      self.x = scene_w

    self.w, self.h = sprite_size(self.img)

    # Choose a vertical spawn range that guarantees full on-screen visibility
    water_top = getattr(getattr(app, "settings", None), "waterline_top", 5)
    below_water = water_top + len(WATER_SEGMENTS) + 1
    min_y = max(1, below_water)
    max_y = max(min_y, screen.height - self.h - 2)
    if max_y < min_y:
      max_y = min_y
    self.y = random.randint(min_y, max_y)

    # Randomize mask colours once to avoid per-frame flicker
    self._rand_mask = randomize_colour_mask(self.mask)
    self._active = True

  @property
  def active(self) -> bool:
    return self._active

  def update(self, dt: float, screen: "ScreenProtocol", app: "AsciiQuariumProtocol") -> None:
    self.x += self.speed * dt
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
          self.img,
          self._rand_mask,
          int(self.x),
          int(self.y),
          Screen.COLOUR_YELLOW
      )

def spawn_big_fish(screen: "ScreenProtocol", app: "AsciiQuariumProtocol"):
  # Ensure there is enough vertical space to fit the big fish entirely
  water_top = getattr(getattr(app, "settings", None), "waterline_top", 5)
  below_water = water_top + len(WATER_SEGMENTS) + 1
  required_rows = below_water + _BF_H + 2
  if screen.height < required_rows:
    return []
  return [BigFish(screen, app)]
