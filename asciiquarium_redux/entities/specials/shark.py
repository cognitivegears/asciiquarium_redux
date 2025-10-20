from __future__ import annotations

import random
from ...screen_compat import Screen
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ...protocols import ScreenProtocol, AsciiQuariumProtocol

from ...util import parse_sprite, sprite_size, draw_sprite, draw_sprite_masked, draw_sprite_masked_with_bg
from ..core import Splat
from ..base import Actor
from ...constants import (
    SHARK_SPEED,
    MOVEMENT_MULTIPLIER,
    SHARK_TEETH_OFFSET_RIGHT_X,
    SHARK_TEETH_OFFSET_RIGHT_Y,
    SHARK_TEETH_OFFSET_LEFT_X,
    SHARK_TEETH_OFFSET_LEFT_Y,
)


class Shark(Actor):
    def __init__(self, screen: "ScreenProtocol", app: "AsciiQuariumProtocol"):
        self.app = app
        self.dir = random.choice([-1, 1])
        self.speed = SHARK_SPEED * self.dir
        self.y = random.randint(max(9, 1), max(9, screen.height - 10))

        # Shark images and masks copied from asciiquarium.pl (@shark_image/@shark_mask),
        # with '?' placeholders treated as spaces here for fidelity.
        right_img_raw = parse_sprite(
            r"""
??????????????????????????????__
?????????????????????????????( `\
??,??????????????????????????)   `\
;' `.????????????????????????(     `\__
?;   `.?????????????__..---''          `~~~~-._
??`.   `.____...--''                       (b  `--._
????>                     _.-'      .((      ._     )
??.`.-`--...__         .-'     -.___.....-(|/|/|/|/'
?;.'?????????`. ...----`.___.',,,_______......---'
?'???????????'-'
"""
        )
        left_img_raw = parse_sprite(
            r"""
?????????????????????__
????????????????????/' )
??????????????????/'   (??????????????????????????,
??????????????__/'     )????????????????????????.' `;
??????_.-~~~~'          ``---..__?????????????.'   ;
?_.--'  b)                       ``--...____.'   .'
(     _.      )).      `-._                     <
?`\|\|\|\|)-.....___.-     `-.         __...--'-.'.
???`---......_______,,,`.___.'----... .'?????????`.;
?????????????????????????????????????`-`???????????`
"""
        )
        # Keep '?' placeholders in sprite data; renderer treats them as transparent
        self.img_right = right_img_raw
        self.img_left = left_img_raw

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
        self._teeth_dx_right = SHARK_TEETH_OFFSET_RIGHT_X
        self._teeth_dy_right = SHARK_TEETH_OFFSET_RIGHT_Y
        self._teeth_dx_left = SHARK_TEETH_OFFSET_LEFT_X
        self._teeth_dy_left = SHARK_TEETH_OFFSET_LEFT_Y

        # Dimensions and spawn X based on direction (use per-direction widths)
        wr, hr = sprite_size(self.img_right)
        wl, hl = sprite_size(self.img_left)
        self._w_right, self._h_right = wr, hr
        self._w_left, self._h_left = wl, hl
        # Spawn at scene edges so shark traverses the entire scene when panning
        try:
            scene_w = int(getattr(getattr(app, "settings", None), "scene_width", screen.width))
        except Exception:
            scene_w = screen.width
        self.x = -wr if self.dir > 0 else scene_w
        self._active = True

    @property
    def active(self) -> bool:  # type: ignore[override]
        return self._active

    def update(self, dt: float, screen: "ScreenProtocol", app: "AsciiQuariumProtocol") -> None:
        self.x += self.speed * dt * MOVEMENT_MULTIPLIER
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
                app.splats.append(Splat(x=tx, y=ty, coord_space="scene"))
                app.fish.remove(f)
        # Off-screen deactivation so spawner can schedule the next special
        try:
            scene_w = int(getattr(getattr(app, "settings", None), "scene_width", screen.width))
        except Exception:
            scene_w = screen.width
        if (self.dir > 0 and self.x > scene_w) or (self.dir < 0 and self.x < -self._w_left):
            self._active = False

    def draw(self, screen: "ScreenProtocol", mono: bool = False) -> None:
        if self.dir > 0:
            img = self.img_right
            msk = self.mask_right
        else:
            img = self.img_left
            msk = self.mask_left

        self.draw_sprite(
            self.app,
            screen,
            img,
            msk,
            int(self.x),
            int(self.y),
            Screen.COLOUR_CYAN,
        )


def spawn_shark(screen: "ScreenProtocol", app: "AsciiQuariumProtocol"):
    return [Shark(screen, app)]
