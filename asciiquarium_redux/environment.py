from __future__ import annotations

from .util import parse_sprite

WATER_SEGMENTS = [
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
    "^^^^ ^^^  ^^^   ^^^    ^^^^      ",
    "^^^^      ^^^^     ^^^    ^^     ",
    "^^      ^^^^      ^^^    ^^^^^^  ",
]

CASTLE = parse_sprite(
    r"""
               T~~
               |
              /^\
             /   \
 _   _   _  /     \  _   _   _
[ ]_[ ]_[ ]/ _   _ \[ ]_[ ]_[ ]
|_=__-_ =_|_[ ]_[ ]_|_=-___-__|
 | _- =  | =_ = _    |= _=   |
 |= -[]  |- = _ =    |_-=_[] |
 | =_    |= - ___    | =_ =  |
 |=  []- |-  /| |\   |=_ =[] |
 |- =_   | =| | | |  |- = -  |
 |_______|__|_|_|_|__|_______|
"""
)

CASTLE_MASK = parse_sprite(
        r"""
                                RR

                            yyy
                         y   y
                        y     y
                     y       y



                            yyy
                         yy yy
                        y y y y
                        yyyyyyy
"""
)


def waterline_row(idx: int, width: int) -> str:
    """Build the repeated waterline row string for the given row index and width.

    Pure function used by drawing and collision detection to ensure identical
    tiling semantics in one place.
    """
    if idx < 0 or idx >= len(WATER_SEGMENTS):
        return ""
    seg = WATER_SEGMENTS[idx]
    seg_len = len(seg)
    repeat = width // seg_len + 2
    return (seg * repeat)[: width]
