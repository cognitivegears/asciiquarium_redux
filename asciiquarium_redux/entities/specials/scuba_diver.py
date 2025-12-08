from __future__ import annotations

import random
from typing import TYPE_CHECKING

from ...screen_compat import Screen

if TYPE_CHECKING:
    from ...protocols import ScreenProtocol, AsciiQuariumProtocol

from ...util import parse_sprite, sprite_size
from ..base import Actor
from ..core import Bubble


class ScubaDiver(Actor):
    def __init__(self, screen: "ScreenProtocol", app: "AsciiQuariumProtocol"):
        self.app = app
        self.dir = random.choice([-1, 1])
        self.speed = random.uniform(7.5, 11.0) * self.dir
        frames_left = [
            parse_sprite(
                r"""
?
          ______          ______
     _ *o(_||___)________/_____
   O(_)(       o  _______/
  > ^  `/------o-'
D|_|___/
"""
            ),
            parse_sprite(
                r"""
?
          ______          ______
     _ *o(_||___)________/___
   O(_)(       o  ______/    \
  > ^  `/------o-'            \
D|_|___/
"""
            ),
            parse_sprite(
                r"""
?
          ______          ______
     _ *o(_||___)________/_____
   O(_)(       o  _______/
  > ^  `/------o-'
D|_|___/
"""
            ),
            parse_sprite(
                r"""
                           ___
          ______          /
     _ *o(_||___)________/_____
   O(_)(       o  _______/
  > ^  `/------o-'
D|_|___/
"""
            ),
        ]
        frames_right = [
            parse_sprite(
                r"""
?
______          ______
 _____\________(___||_)o* _
      \_______  o       )(_)O
              '-o------\´  ^ <
                        \___|_|ᗡ
"""
            ),
            parse_sprite(
                r"""
?
______          ______
   ___\________(___||_)o* _
  /    \______  o       )(_)O
 /            '-o------\´  ^ <
                        \___|_|ᗡ
"""
            ),
            parse_sprite(
                r"""
?
______          ______
 _____\________(___||_)o* _
      \_______  o       )(_)O
              '-o------\´  ^ <
                        \___|_|ᗡ
"""
            ),
            parse_sprite(
                r"""
  ___
     \          ______
 _____\________(___||_)o* _
      \_______  o       )(_)O
              '-o------\´  ^ <
                        \___|_|ᗡ
"""
            ),
        ]

        masks_left = [
            parse_sprite(
                r"""
?
          bbbbbb          bbbbbb
     b bbbbbbbbbbbbbbbbbbbbbbbb
   wbbbbbbbbbbbbbbbbbbbbbb
  b b  bbbbbbbbbbb
wbbbbbbb
"""
            ),
            parse_sprite(
                r"""
?
          bbbbbb          bbbbbb
     b bbbbbbbbbbbbbbbbbbbbbb
   wbbbbbbbbbbbbbbbbbbbbb    b
  b b  bbbbbbbbbbb            b
wbbbbbbb
"""
            ),
            parse_sprite(
                r"""
?
          bbbbbb          bbbbbb
     b bbbbbbbbbbbbbbbbbbbbbbbb
   wbbbbbbbbbbbbbbbbbbbbbb
  b b  bbbbbbbbbbb
wbbbbbbb
"""
            ),
            parse_sprite(
                r"""
                           bbb
          bbbbbb          b
     b bbbbbbbbbbbbbbbbbbbbbbbb
   wbbbbbbbbbbbbbbbbbbbbbb
  b b  bbbbbbbbbbb
wbbbbbbb
"""
            ),
        ]
        masks_right = [
            parse_sprite(
                r"""
?
bbbbbb          bbbbbb
 bbbbbbbbbbbbbbbbbbbbbbbb b
      bbbbbbbbbbbbbbbbbbbbbbw
              bbbbbbbbbbb  b b
                        bbbbbbbw
"""
            ),
            parse_sprite(
                r"""
?
bbbbbb          bbbbbb
   bbbbbbbbbbbbbbbbbbbbbb b
  b    bbbbbbbbbbbbbbbbbbbbbw
 b            bbbbbbbbbbb  b b
                        bbbbbbbw
"""
            ),
            parse_sprite(
                r"""
?
bbbbbb          bbbbbb
 bbbbbbbbbbbbbbbbbbbbbbbb b
      bbbbbbbbbbbbbbbbbbbbbbw
              bbbbbbbbbbb  b b
                        bbbbbbbw
"""
            ),
            parse_sprite(
                r"""
  bbb
     b          bbbbbb
 bbbbbbbbbbbbbbbbbbbbbbbb b
      bbbbbbbbbbbbbbbbbbbbbbw
              bbbbbbbbbbb  b b
                        bbbbbbbw
"""
            ),
        ]

        self.frames = frames_right if self.dir > 0 else frames_left
        self.masks = masks_right if self.dir > 0 else masks_left

        self.bubble_offset = (26, 2) if self.dir > 0 else (6, 2)

        w_list = [sprite_size(f)[0] for f in self.frames]
        h_list = [sprite_size(f)[1] for f in self.frames]
        self.w, self.h = max(w_list), max(h_list)

        try:
            scene_w = int(getattr(getattr(app, "settings", None), "scene_width", screen.width))
        except Exception:
            scene_w = screen.width
        self.x = -self.w if self.dir > 0 else scene_w

        waterline_top = getattr(getattr(app, "settings", None), "waterline_top", 5)
        self.min_y = max(1, int(waterline_top) + 1)
        self.max_y = max(self.min_y, screen.height - self.h - 2)
        self.y = float(random.randint(self.min_y, self.max_y))

        self._frame_idx = 0
        self._frame_t = 0.0
        self._frame_dt = 0.35
        self._bubble_timer = self._next_burst_delay()
        self._burst_remaining = 0
        self._active = True

    def _next_burst_delay(self) -> float:
        """Delay between bubble bursts (simulates breathing cadence)."""
        return random.uniform(1.2, 2.6)

    def _next_bubble_gap(self) -> float:
        """Delay between bubbles within a burst."""
        return random.uniform(0.05, 0.12)

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: "ScreenProtocol", app: "AsciiQuariumProtocol") -> None:
        self.x += self.speed * dt
        self._frame_t += dt
        if self._frame_t >= self._frame_dt:
            self._frame_t = 0.0
            self._frame_idx = (self._frame_idx + 1) % len(self.frames)

        self._bubble_timer -= dt
        if self._bubble_timer <= 0:
            if self._burst_remaining == 0:
                self._burst_remaining = random.randint(3, 5)
            ox, oy = self.bubble_offset
            view_off = int(getattr(getattr(app, "settings", None), "scene_offset", 0))
            bubble_x = int(self.x + ox) - view_off
            bubble_y = int(self.y + oy)
            if 0 <= bubble_x < screen.width and 0 <= bubble_y < screen.height:
                app.bubbles.append(Bubble(x=bubble_x, y=bubble_y))
            self._burst_remaining -= 1
            if self._burst_remaining > 0:
                self._bubble_timer = self._next_bubble_gap()
            else:
                self._bubble_timer = self._next_burst_delay()

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
            self.masks[self._frame_idx],
            int(self.x),
            int(self.y),
            Screen.COLOUR_BLUE,
        )


def spawn_scuba_diver(screen: "ScreenProtocol", app: "AsciiQuariumProtocol"):
    return [ScubaDiver(screen, app)]
