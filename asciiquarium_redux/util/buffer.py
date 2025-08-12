from __future__ import annotations

from typing import List, Tuple, Optional
from ..screen_compat import Screen


Cell = Tuple[str, int]


class DoubleBufferedScreen:
    """A thin wrapper around asciimatics Screen that buffers draw calls per frame
    and flushes only diffs to the real screen to reduce flicker.

    Supports just the subset of the Screen API that this app uses: width, height,
    print_at, clear, and a flush() method to push the back buffer to the front.
    """

    def __init__(self, screen: Screen):
        self._s = screen
        self._w = screen.width
        self._h = screen.height
        self._front: List[List[Cell]] = []
        self._back: List[List[Cell]] = []
        self._init_buffers(self._w, self._h)

    def _init_buffers(self, w: int, h: int) -> None:
        blank_row: List[Cell] = [(' ', Screen.COLOUR_WHITE)] * w
        self._front = [list(blank_row) for _ in range(h)]
        self._back = [list(blank_row) for _ in range(h)]

    @property
    def width(self) -> int:
        return self._s.width

    @property
    def height(self) -> int:
        return self._s.height

    def _ensure_size(self) -> None:
        if self._w != self._s.width or self._h != self._s.height:
            self._w = self._s.width
            self._h = self._s.height
            self._init_buffers(self._w, self._h)

    def clear(self) -> None:
        # Reset back buffer to blanks for the new frame
        self._ensure_size()
        w, h = self._w, self._h
        blank_row: List[Cell] = [(' ', Screen.COLOUR_WHITE)] * w
        for y in range(h):
            self._back[y] = list(blank_row)

    def print_at(self, text: str, x: int, y: int, colour: Optional[int] = None, *args, **kwargs) -> None:  # type: ignore[override]
        if text is None:
            return
        self._ensure_size()
        if y < 0 or y >= self._h:
            return
        if x >= self._w:
            return
        col: int = Screen.COLOUR_WHITE if colour is None else int(colour)
        # Clip left
        start = 0
        if x < 0:
            start = -x
            x = 0
        # Clip right
        max_len = min(len(text) - start, self._w - x)
        if max_len <= 0:
            return
        row = self._back[y]
        for i in range(max_len):
            ch = text[start + i]
            row[x + i] = (ch, col)

    def flush(self) -> None:
        """Compute diffs and emit print_at calls to the real screen, then refresh."""
        self._ensure_size()
        w, h = self._w, self._h
        for y in range(h):
            front_row = self._front[y]
            back_row = self._back[y]
            run_colour: Optional[int] = None
            run_start: Optional[int] = None
            for x in range(w + 1):  # sentinel at end
                if x < w and back_row[x] != front_row[x]:
                    ch, col = back_row[x]
                    if run_colour is None:
                        run_colour = col
                        run_start = x
                    elif col != run_colour:
                        # flush previous run
                        if run_start is not None and x > run_start:
                            s = ''.join(c for c, _ in back_row[run_start:x])
                            self._s.print_at(s, run_start, y, colour=run_colour)
                        run_colour = col
                        run_start = x
                else:
                    if run_colour is not None and run_start is not None:
                        s = ''.join(c for c, _ in back_row[run_start:x])
                        self._s.print_at(s, run_start, y, colour=run_colour)
                        run_colour = None
                        run_start = None
            # Copy back->front row
            self._front[y] = list(back_row)
        self._s.refresh()
