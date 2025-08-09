from __future__ import annotations

from typing import List, Tuple
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


def aabb_overlap(ax: int, ay: int, aw: int, ah: int, bx: int, by: int, bw: int, bh: int) -> bool:
    return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)
