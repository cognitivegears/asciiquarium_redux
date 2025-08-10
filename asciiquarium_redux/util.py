from __future__ import annotations

from typing import List, Tuple, Optional, Dict
from asciimatics.screen import Screen


def parse_sprite(s: str) -> List[str]:
    lines = s.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def sprite_size(lines: List[str]) -> Tuple[int, int]:
    if not lines:
        return 0, 0
    return max(len(l) for l in lines), len(lines)


def draw_sprite(screen: Screen, lines: List[str], x: int, y: int, colour: int) -> None:
    max_y = screen.height - 1
    max_x = screen.width - 1
    for dy, row in enumerate(lines):
        sy = y + dy
        if sy < 0 or sy > max_y:
            continue
        if x > max_x or x + len(row) < 0:
            continue
        start = 0
        if x < 0:
            start = -x
        visible = row[start : max(0, min(len(row), max_x - x + 1))]
        if visible:
            screen.print_at(visible, x + start, sy, colour=colour)


# Map single-character mask codes to asciimatics colours.
_MASK_COLOUR_MAP: Dict[str, int] = {
    'k': Screen.COLOUR_BLACK, 'K': Screen.COLOUR_BLACK,
    'r': Screen.COLOUR_RED, 'R': Screen.COLOUR_RED,
    'g': Screen.COLOUR_GREEN, 'G': Screen.COLOUR_GREEN,
    'y': Screen.COLOUR_YELLOW, 'Y': Screen.COLOUR_YELLOW,
    'b': Screen.COLOUR_BLUE, 'B': Screen.COLOUR_BLUE,
    'm': Screen.COLOUR_MAGENTA, 'M': Screen.COLOUR_MAGENTA,
    'c': Screen.COLOUR_CYAN, 'C': Screen.COLOUR_CYAN,
    'w': Screen.COLOUR_WHITE, 'W': Screen.COLOUR_WHITE,
}


def _mask_char_to_colour(ch: str, default_colour: int) -> Optional[int]:
    """Translate a single mask character to a Screen colour.

    Returns None to indicate transparency (skip draw) when mask char is space.
    """
    if ch == ' ':
        return default_colour
    return _MASK_COLOUR_MAP.get(ch, default_colour)


def draw_sprite_masked(
    screen: Screen,
    lines: List[str],
    mask: List[str],
    x: int,
    y: int,
    default_colour: int,
) -> None:
    """Draw a sprite with a per-character colour mask.

    The mask must be the same size as lines. Mask characters map to colours
    using _MASK_COLOUR_MAP; spaces in the mask are treated as transparent and
    will fall back to default_colour.
    """
    if not lines:
        return
    max_y = screen.height - 1
    max_x = screen.width - 1
    h = len(lines)
    for dy in range(h):
        row = lines[dy]
        mrow = mask[dy] if dy < len(mask) else ''
        sy = y + dy
        if sy < 0 or sy > max_y:
            continue
        if x > max_x or x + len(row) < 0:
            continue
        # Determine visible horizontal range
        start_idx = 0 if x >= 0 else -x
        end_idx = min(len(row), max_x - x + 1)
        if end_idx <= start_idx:
            continue
        # Walk the row, batching runs of same colour
        run_start = start_idx
        run_colour: Optional[int] = None
        for cx in range(start_idx, end_idx + 1):  # include sentinel at end
            if cx < end_idx:
                ch = row[cx]
                mch = mrow[cx] if cx < len(mrow) else ' '
                col = _mask_char_to_colour(mch, default_colour)
            else:
                # sentinel to flush any pending run
                ch = None  # type: ignore
                col = None

            if col != run_colour:
                # Flush previous run
                if run_colour is not None and cx > run_start:
                    segment = row[run_start:cx]
                    # Skip leading spaces so we don't overwrite background ahead of shapes
                    i = 0
                    while i < len(segment) and segment[i] == ' ':
                        i += 1
                    if i < len(segment):
                        screen.print_at(segment[i:], x + run_start + i, sy, colour=run_colour)
                run_start = cx
                run_colour = col
        # Note: loop flushes at sentinel


def randomize_colour_mask(mask: List[str]) -> List[str]:
    """Randomize digit placeholders 1..9 in a mask to random colour letters.

    Mirrors Perl's rand_color: replace '4' with 'W' (white), then each digit 1..9
    with a randomly chosen colour code from [c,C,r,R,y,Y,b,B,g,G,m,M].
    """
    import random as _random

    COLOUR_CODES = ['c','C','r','R','y','Y','b','B','g','G','m','M']

    # Choose a colour per digit consistently across all lines
    digit_map: Dict[str, str] = {}
    for d in '123456789':
        digit_map[d] = _random.choice(COLOUR_CODES)

    def _map_line(line: str) -> str:
        # First force eyes '4' to white 'W'
        line = line.replace('4', 'W')
        # Replace digits with the chosen colours
        out_chars = []
        for ch in line:
            if ch in digit_map:
                out_chars.append(digit_map[ch])
            else:
                out_chars.append(ch)
        return ''.join(out_chars)

    return [_map_line(ln) for ln in mask]


def aabb_overlap(ax: int, ay: int, aw: int, ah: int, bx: int, by: int, bw: int, bh: int) -> bool:
    return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)
