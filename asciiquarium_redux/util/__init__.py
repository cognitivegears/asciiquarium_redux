from __future__ import annotations

from typing import List, Tuple, Optional, Dict, TYPE_CHECKING
from ..screen_compat import Screen

if TYPE_CHECKING:
    pass  # Keep for future forward references if needed


def parse_sprite(s: str) -> List[str]:
    """Parse a sprite string into a list of lines with leading/trailing empty lines removed.

    Args:
        s: Raw sprite string with potential empty lines

    Returns:
        List of non-empty sprite lines
    """
    lines = s.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def sprite_size(lines: List[str]) -> Tuple[int, int]:
    """Calculate the size (width, height) of a sprite from its lines.

    Args:
        lines: List of sprite lines

    Returns:
        Tuple of (width, height) where width is max line length
    """
    if not lines:
        return 0, 0
    return max(len(l) for l in lines), len(lines)


def draw_sprite(screen: Screen, lines: List[str], x: int, y: int, colour: int) -> None:
    """Draw an unmasked sprite, treating spaces as transparent.

    Only non-space characters are printed so background/sprites behind are preserved.

    Args:
        screen: Screen object to draw on
        lines: Sprite lines to draw
        x: X position to draw at
        y: Y position to draw at
        colour: Color to use for drawing
    """
    max_y = screen.height - 1
    max_x = screen.width - 1
    for dy, row in enumerate(lines):
        sy = y + dy
        if sy < 0 or sy > max_y:
            continue
        if x > max_x or x + len(row) < 0:
            continue
        start_idx = 0 if x >= 0 else -x
        end_idx = min(len(row), max_x - x + 1)
        if end_idx <= start_idx:
            continue
        # Print contiguous non-space runs only
        run_start: Optional[int] = None
        for cx in range(start_idx, end_idx + 1):  # sentinel at end
            ch: Optional[str] = row[cx] if cx < end_idx else None
            if cx < end_idx and ch != ' ':
                if run_start is None:
                    run_start = cx
            else:
                if run_start is not None and cx > run_start:
                    segment = row[run_start:cx]
                    screen.print_at(segment, x + run_start, sy, colour=colour)
                    run_start = None


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

    Args:
        ch: Mask character to translate
        default_colour: Default colour to use for spaces

    Returns:
        Color code or None for transparency
    """
    if ch == ' ':
        # Space in mask means: draw using default colour (not transparent).
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
    using _MASK_COLOUR_MAP; spaces in the mask mean "use default_colour" for
    any non-space glyphs in the sprite.

    Args:
        screen: Screen object to draw on
        lines: Sprite lines to draw
        mask: Color mask lines corresponding to sprite
        x: X position to draw at
        y: Y position to draw at
        default_colour: Default color for unmasked areas
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
        # Walk the row, batching runs of same colour and non-space glyphs
        run_start = None
        run_colour: Optional[int] = None
        for cx in range(start_idx, end_idx + 1):  # include sentinel at end
            if cx < end_idx:
                ch = row[cx]
                mch = mrow[cx] if cx < len(mrow) else ' '
                col = _mask_char_to_colour(mch, default_colour)
                drawable = (ch != ' ' and col is not None)
            else:
                # sentinel to flush any pending run
                ch = None  # type: ignore
                col = None
                drawable = False

            if not drawable or col != run_colour:
                # Flush previous run
                if run_colour is not None and run_start is not None and cx > run_start:
                    segment = lines[dy][run_start:cx]
                    screen.print_at(segment, x + run_start, sy, colour=run_colour)
                run_start = cx if drawable else None
                run_colour = col if drawable else None

def fill_rect(screen: Screen, x: int, y: int, w: int, h: int, colour: int) -> None:
    """Fill a rectangular area with spaces in the given colour (opaque erase).

    This mimics Perl's default (non-transparent) entity rendering where spaces
    overwrite what's behind. Useful for solids like the castle.

    Args:
        screen: Screen object to draw on
        x: X position of rectangle
        y: Y position of rectangle
        w: Width of rectangle
        h: Height of rectangle
        colour: Color to fill with
    """
    if w <= 0 or h <= 0:
        return
    max_y = screen.height - 1
    max_x = screen.width - 1
    # Clip vertical bounds
    y0 = max(0, y)
    y1 = min(max_y, y + h - 1)
    if y1 < y0:
        return
    # Determine horizontal clipping once per row
    x0 = max(0, x)
    x1 = min(max_x, x + w - 1)
    if x1 < x0:
        return
    span = ' ' * (x1 - x0 + 1)
    for sy in range(y0, y1 + 1):
        screen.print_at(span, x0, sy, colour=colour)


def draw_sprite_masked_with_bg(
    screen: Screen,
    lines: List[str],
    mask: List[str],
    x: int,
    y: int,
    default_colour: int,
    bg_colour: int,
):
    """Draw a masked sprite with an opaque background span per row.

    For each row, first paint spaces from x..x+len(row)-1 in bg_colour to make
    sprite spaces opaque within the silhouette of that row, then draw the masked
    glyphs over the top. This avoids blanking a full rectangle and matches Perl
    behavior for sprites like the castle that are effectively non-transparent.
    """
    if not lines:
        return
    max_y = screen.height - 1
    max_x = screen.width - 1
    h = len(lines)
    for dy in range(h):
        row = lines[dy]
        if not row:
            continue
        sy = y + dy
        if sy < 0 or sy > max_y:
            continue
        # Determine silhouette span for this row (first..last non-space)
        first = None
        last = None
        for i, ch in enumerate(row):
            if ch != ' ':
                if first is None:
                    first = i
                last = i
        if first is None or last is None:
            # Entire row is spaces; nothing to fill or draw
            continue
        # Clip horizontally to screen
        start_idx = max(first, 0 if x >= 0 else -x)
        end_idx = min(last + 1, max_x - x + 1, len(row))
        if end_idx <= start_idx:
            continue
        span = ' ' * (end_idx - start_idx)
        screen.print_at(span, x + start_idx, sy, colour=bg_colour)
        # Now draw the masked row on top
        # Use the existing masked renderer for batching
        draw_sprite_masked(screen, [row], [mask[dy] if dy < len(mask) else ''], x, sy, default_colour)


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


__all__ = [
    "parse_sprite",
    "sprite_size",
    "draw_sprite",
    "draw_sprite_masked",
    "fill_rect",
    "draw_sprite_masked_with_bg",
    "randomize_colour_mask",
    "aabb_overlap",
]
