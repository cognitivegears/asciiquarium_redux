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

        # Force whale body to stay blue only: convert 'C' (cyan) to 'B' (blue)
        mask_right = [ln.replace('C', 'B') for ln in mask_right]
        mask_left = [ln.replace('C', 'B') for ln in mask_left]

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

        # Compose frames per direction with variable spout height to preserve up/down motion.
        # Also build per-frame masks padded to the spout height for correct colour alignment.
        no_spout_top = ["", "", ""]

        # Right-facing
        frames_right: List[List[str]] = []
        masks_right: List[List[str]] = []
        for _ in range(5):
            frames_right.append(no_spout_top + whale_right)
            masks_right.append([""] * len(no_spout_top) + mask_right)
        # Transitional in-between height before the first spout frame to avoid skipping
        frames_right.append(["", ""] + whale_right)
        masks_right.append(["", ""] + mask_right)
        for sp in spout_frames:
            frames_right.append(_indent_lines(sp, 1) + whale_right)
            masks_right.append([""] * len(sp) + mask_right)
        # Transitional in-between height before returning to no-spout to avoid skipping
        frames_right.append(["", ""] + whale_right)
        masks_right.append(["", ""] + mask_right)
        self.frames_right = frames_right
        self.masks_right = masks_right

        # Left-facing
        frames_left: List[List[str]] = []
        masks_left: List[List[str]] = []
        for _ in range(5):
            frames_left.append(no_spout_top + whale_left)
            masks_left.append([""] * len(no_spout_top) + mask_left)
        # Transitional in-between height before the first spout frame to avoid skipping
        frames_left.append(["", ""] + whale_left)
        masks_left.append(["", ""] + mask_left)
        for sp in spout_frames:
            frames_left.append(_indent_lines(sp, 11) + whale_left)
            masks_left.append([""] * len(sp) + mask_left)
        # Transitional in-between height before returning to no-spout to avoid skipping
        frames_left.append(["", ""] + whale_left)
        masks_left.append(["", ""] + mask_left)
        self.frames_left = frames_left
        self.masks_left = masks_left

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
            msk = self.masks_right[self._frame_idx]
        else:
            img = self.frames_left[self._frame_idx]
            msk = self.masks_left[self._frame_idx]
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_BLUE)
        else:
            # Default to blue for any mask gaps so the whale always stays blue
            draw_sprite_masked(screen, img, msk, int(self.x), int(self.y), Screen.COLOUR_BLUE)


def spawn_whale(screen: Screen, app):
    return [Whale(screen, app)]
