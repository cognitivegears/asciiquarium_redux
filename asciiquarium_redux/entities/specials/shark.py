from __future__ import annotations

import random
from asciimatics.screen import Screen

from ...util import parse_sprite, sprite_size, draw_sprite, draw_sprite_masked
from ..core import Splat, Fish
from ..base import Actor


class Shark(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 2.0 * self.dir
        self.y = random.randint(max(9, 1), max(9, screen.height - 10))

        # Shark images and masks copied from asciiquarium.pl (@shark_image/@shark_mask),
        # with '?' placeholders treated as spaces here for fidelity.
        right_img_raw = parse_sprite(
            r"""
                              __
                             ( `\
  ,??????????????????????????)   `\
;' `.????????????????????????(     `\__
 ;   `.?????????????__..---''          `~~~~-._
  `.   `.____...--''                       (b  `--._
    >                     _.-'      .((      ._     )
  .`.-`--...__         .-'     -.___.....-(|/|/|/|/'
 ;.'?????????`. ...----`.___.',,,_______......---'
 '???????????'-'
"""
        )
        left_img_raw = parse_sprite(
            r"""
                     __
                    /' )
                  /'   (??????????????????????????,
              __/'     )????????????????????????.' `;
      _.-~~~~'          ``---..__?????????????.'   ;
 _.--'  b)                       ``--...____.'   .'
(     _.      )).      `-._                     <
 `\|\|\|\|)-.....___.-     `-.         __...--'-.'.
   `---......_______,,,`.___.'----... .'?????????`.;
                                     `-`???????????`
"""
        )
        # Replace the placeholders with spaces
        self.img_right = [ln.replace('?', ' ') for ln in right_img_raw]
        self.img_left = [ln.replace('?', ' ') for ln in left_img_raw]

        right_mask_raw = parse_sprite(
            r"""




                                           cR

                                          cWWWWWWWW


"""
        )
        left_mask_raw = parse_sprite(
            r"""




        Rc

  WWWWWWWWc


"""
        )
        # Use exact collider offsets from Perl asciiquarium for parity
        # Right-moving: image X starts at -53, teeth X starts at -9 => dx=44; dy=7
        # Left-moving:  teeth X = x + 9 => dx=9; dy=7
        self.mask_right = right_mask_raw
        self.mask_left = left_mask_raw
        self._teeth_dx_right = 44
        self._teeth_dy_right = 7
        self._teeth_dx_left = 9
        self._teeth_dy_left = 7

        # Dimensions and spawn X based on direction (use per-direction widths)
        wr, hr = sprite_size(self.img_right)
        wl, hl = sprite_size(self.img_left)
        self._w_right, self._h_right = wr, hr
        self._w_left, self._h_left = wl, hl
        self.x = -wr if self.dir > 0 else screen.width
        self._active = True

    @property
    def active(self) -> bool:  # type: ignore[override]
        return self._active

    def update(self, dt: float, screen: Screen, app) -> None:
        self.x += self.speed * dt * 20.0
        # Collision parity: a single point collider at the teeth location
        if self.dir > 0:
            tx = int(self.x) + self._teeth_dx_right
            ty = int(self.y) + self._teeth_dy_right
        else:
            tx = int(self.x) + self._teeth_dx_left
            ty = int(self.y) + self._teeth_dy_left
        for f in list(app.fish):
            if f.hooked:
                continue
            # point-in-rect test
            if int(f.x) <= tx < int(f.x + f.width) and int(f.y) <= ty < int(f.y + f.height):
                # Spawn splat at the teeth position so it appears in front/at mouth
                app.splats.append(Splat(x=tx, y=ty))
                app.fish.remove(f)
        # Off-screen deactivation so spawner can schedule the next special
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x < -self._w_left):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        if self.dir > 0:
            img = self.img_right
            msk = self.mask_right
        else:
            img = self.img_left
            msk = self.mask_left
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            # Default colour matches Perl's CYAN body
            draw_sprite_masked(screen, img, msk, int(self.x), int(self.y), Screen.COLOUR_CYAN)


def spawn_shark(screen: Screen, app):
    return [Shark(screen, app)]
