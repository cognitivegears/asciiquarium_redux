from __future__ import annotations

import random
from typing import List
from asciimatics.screen import Screen

from ...util import parse_sprite, sprite_size, draw_sprite_masked, draw_sprite
from ..base import Actor


def _indent_lines(lines: List[str], n: int) -> List[str]:
    pad = ' ' * n
    out: List[str] = []
    for ln in lines:
        if ln.strip():
            out.append(pad + ln)
        else:
            out.append(ln)
    return out


def _compose_frames(base: List[str], sp_align: int, spout_frames: List[List[str]]) -> List[List[str]]:
    frames: List[List[str]] = []
    # 5 frames: no spout (three blank lines)
    no_spout_top = ["", "", ""]
    frames.extend([no_spout_top + base for _ in range(5)])
    # Spout frames
    for sp in spout_frames:
        frames.append(_indent_lines(sp, sp_align) + base)
    return frames


class Whale(Actor):
    def __init__(self, screen: Screen, app):
                self.dir = random.choice([-1, 1])
                # Keep whale relatively slow, similar to Perl pacing
                self.speed = 10.0 * self.dir
                self.y = 0

                # Base whale images (Perl asciiquarium) and colour masks by direction
                whale_right_raw = parse_sprite(
                        r"""
        .-----:
      .'       `.
,????/       (o) \
\`._/          ,__)
"""
                )
                whale_left_raw = parse_sprite(
                        r"""
    :-----.
  .'       `.
 / (o)       \????,
(__,          \_.'/
"""
                )
                # Replace placeholders with spaces
                whale_right = [ln.replace('?', ' ') for ln in whale_right_raw]
                whale_left = [ln.replace('?', ' ') for ln in whale_left_raw]
                mask_right = parse_sprite(
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
                mask_left = parse_sprite(
                        r"""
     C C
 CCCCCCC
 C  C  C
    BBBBBBB
  BB       BB
 B BWB       B    B
BBBB          BBBBB
"""
                )

                # Water spout animation frames (Perl asciiquarium)
                spout_frames = [
                        parse_sprite(
                                r"""


    :
"""
                        ),
                        parse_sprite(
                                r"""

    :
    :
"""
                        ),
                        parse_sprite(
                                r"""
    . .
    -:-
     :
"""
                        ),
                        parse_sprite(
                                r"""
    . .
   .-:-.
     :
"""
                        ),
                        parse_sprite(
                                r"""
  . .
'.-:-.'
'  :  '
"""
                        ),
                        parse_sprite(
                                r"""

 .- -.
;  :  ;
"""
                        ),
                        parse_sprite(
                                r"""


;     ;
"""
                        ),
                ]

                # Compose frames per direction, aligning spout per Perl (1 for RTL, 11 for LTR)
                self.frames_right = _compose_frames(whale_right, 1, spout_frames)
                self.frames_left = _compose_frames(whale_left, 11, spout_frames)
                self.mask_right = mask_right
                self.mask_left = mask_left

                # Animation state
                self._frame_idx = 0
                self._frame_t = 0.0
                self._frame_dt = 0.25

                # Spawn X per direction (Perl uses -18 for LTR and width-2 for RTL)
                w_r, _ = sprite_size(whale_right)
                w_l, _ = sprite_size(whale_left)
                self._w_right, self._w_left = w_r, w_l
                self.x = -18 if self.dir > 0 else screen.width - 2
                self._active = True

    @property
    def active(self) -> bool:  # type: ignore[override]
        return self._active

    def update(self, dt: float, screen: Screen, app) -> None:
        self.x += self.speed * dt / 2
        self._frame_t += dt
        if self._frame_t >= self._frame_dt:
            self._frame_t = 0.0
            # advance/cycle through frames
            total = len(self.frames_right) if self.dir > 0 else len(self.frames_left)
            self._frame_idx = (self._frame_idx + 1) % total
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x < -self._w_left):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        if self.dir > 0:
            img = self.frames_right[self._frame_idx]
            msk = self.mask_right
        else:
            img = self.frames_left[self._frame_idx]
            msk = self.mask_left
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            draw_sprite_masked(screen, img, msk, int(self.x), int(self.y), Screen.COLOUR_WHITE)


def spawn_whale(screen: Screen, app):
    return [Whale(screen, app)]
