from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Tuple, Union, List, Dict, Any, Optional, TYPE_CHECKING
import logging
from ..shared import CommonKeyEvent, CommonMouseEvent, EventProcessor

if TYPE_CHECKING:
    from ...screen_compat import Screen
    from ...util.buffer import DoubleBufferedScreen


class RenderContext(Protocol):
    def size(self) -> Tuple[int, int]:
        ...

    def clear(self) -> None:
        ...

    def print_at(self, text: str, x: int, y: int, colour: Optional[int] = None) -> None:
        """Print text at specific coordinates."""
        ...

    def flush(self) -> None:
        ...


@dataclass
class KeyEvent:
    key: str


@dataclass
class MouseEvent:
    x: int
    y: int
    button: int


class EventStream(Protocol):
    def poll(self) -> List[Union[KeyEvent, MouseEvent]]:
        ...


class TerminalRenderContext:
    def __init__(self, screen: "Screen", db_screen: "DoubleBufferedScreen") -> None:
        self._screen = screen
        self._db = db_screen

    def size(self) -> Tuple[int, int]:
        return self._screen.width, self._screen.height

    def clear(self) -> None:
        self._db.clear()

    def print_at(self, text: str, x: int, y: int, colour: Optional[int] = None) -> None:
        """Print text at specific coordinates."""
        # colour is handled internally by app/util for terminal path
        self._db.print_at(text, x, y, colour)

    def flush(self) -> None:
        self._db.flush()


class TerminalEventStream:
    def __init__(self, screen: "Screen") -> None:
        self._screen = screen
        self._event_processor = EventProcessor()

    def register_key_handler(self, key: str, handler) -> None:
        """Register a handler for a specific key using shared event processing."""
        self._event_processor.register_key_handler(key, handler)

    def register_mouse_handler(self, handler) -> None:
        """Register a handler for mouse events using shared event processing."""
        self._event_processor.register_mouse_handler(handler)

    def poll(self) -> List[Union[KeyEvent, MouseEvent]]:
        events: List[Union[KeyEvent, MouseEvent]] = []
        while True:
            ev = self._screen.get_event()
            if not ev:
                break
            # Asciimatics event objects: detect keys and mouse
            et = type(ev).__name__
            if et == "KeyboardEvent":
                try:
                    ch = chr(getattr(ev, "key_code"))
                except Exception:
                    ch = ""
                if ch:
                    key_event = KeyEvent(key=ch)
                    events.append(key_event)

                    # Process through shared event handler if registered
                    common_event = CommonKeyEvent.from_char(ch)
                    self._event_processor.process_key_event(common_event)

            elif et == "MouseEvent":
                x = getattr(ev, "x", 0)
                y = getattr(ev, "y", 0)
                b = getattr(ev, "buttons", 0)
                # Normalize to 1 for left if any button
                btn = 1 if b else 0
                mouse_event = MouseEvent(x=x, y=y, button=btn)
                events.append(mouse_event)

                # Process through shared event handler if registered
                common_event = CommonMouseEvent.from_coords(x, y, btn)
                self._event_processor.process_mouse_event(common_event)

        return events


class TkRenderContext:
    def __init__(self, tk_root: Any, canvas: Any, cols: int, rows: int, cell_w: int, cell_h: int, font: Any = None) -> None:
        self.root = tk_root
        self.canvas = canvas
        self.cols = cols
        self.rows = rows
        self.cell_w = cell_w
        self.cell_h = cell_h
        self.font = font
        # Back buffers
        self._buffer: List[List[str]] = [[" "] * cols for _ in range(rows)]
        self._colbuf: List[List[int]] = [[7] * cols for _ in range(rows)]  # default white
        self._dirty: set[Tuple[int, int]] = set()
        self._text_ids: Dict[Tuple[int, int], int] = {}

    def size(self) -> Tuple[int, int]:
        return self.cols, self.rows

    def clear(self) -> None:
        for y in range(self.rows):
            row = self._buffer[y]
            crow = self._colbuf[y]
            for x in range(self.cols):
                if row[x] != " ":
                    row[x] = " "
                    self._dirty.add((x, y))
                crow[x] = 7

    def print_at(self, text: str, x: int, y: int, colour: Optional[int] = None) -> None:
        if text is None:
            return
        if y < 0 or y >= self.rows or x >= self.cols:
            return
        start = 0
        if x < 0:
            start = -x
            x = 0
        idx_col = 7 if colour is None else int(colour)
        max_len = min(len(text) - start, self.cols - x)
        if max_len <= 0:
            return
        for i in range(max_len):
            ch = text[start + i]
            if self._buffer[y][x + i] != ch or self._colbuf[y][x + i] != idx_col:
                self._buffer[y][x + i] = ch
                self._colbuf[y][x + i] = idx_col
                self._dirty.add((x + i, y))

    def flush(self) -> None:
        # Draw dirty cells as individual text items. Simple but effective for now.
        try:
            for (x, y) in list(self._dirty):
                self._dirty.discard((x, y))
                key = (x, y)
                ch = self._buffer[y][x]
                col = self._colbuf[y][x]
                px = x * self.cell_w + self.cell_w // 2
                py = y * self.cell_h + self.cell_h // 2
                tid = self._text_ids.get(key)
                fill = _colour_to_fill(col)
                draw_text = "" if ch == " " else ch
                if tid is None:
                    if self.font is not None:
                        tid = self.canvas.create_text(px, py, text=draw_text, anchor="center", font=self.font, fill=fill)
                    else:
                        tid = self.canvas.create_text(px, py, text=draw_text, anchor="center", fill=fill)
                    self._text_ids[key] = tid
                else:
                    self.canvas.itemconfigure(tid, text=draw_text, fill=fill)
            self.canvas.update_idletasks()
        except KeyboardInterrupt:
            # Allow outer layers to handle a graceful shutdown
            raise
        except Exception:
            # Swallow errors that can happen during teardown (e.g., widget destroyed)
            pass

    def resize(self, cols: int, rows: int) -> None:
        # Reset buffers and visual cache on resize
        cols = max(1, int(cols))
        rows = max(1, int(rows))
        if cols == self.cols and rows == self.rows:
            return
        self.cols = cols
        self.rows = rows
        self._buffer = [[" "] * cols for _ in range(rows)]
        self._colbuf = [[7] * cols for _ in range(rows)]
        self._dirty.clear()
        self._text_ids.clear()
        try:
            self.canvas.delete("all")
        except Exception as e:
            logging.warning(f"Failed to clear TkInter canvas: {e}")


def _colour_to_fill(col: int) -> str:
    # Map asciimatics Screen colour ints to Tk fill colours
    mapping = {
        0: "#000000",  # black
        1: "#ff5555",  # red
        2: "#55ff55",  # green
        3: "#ffff55",  # yellow
        4: "#5555ff",  # blue
        5: "#ff55ff",  # magenta
        6: "#55ffff",  # cyan
        7: "#ffffff",  # white
    }
    return mapping.get(int(col) & 7, "#ffffff")


class TkEventStream:
    def __init__(self, tk_root: Any) -> None:
        self.root = tk_root
        self._queue: List[Union[KeyEvent, MouseEvent]] = []
        # Bind events
        self.root.bind("<Key>", self._on_key)
        self.root.bind("<Button-1>", self._on_click)

    def _on_key(self, event: Any) -> None:
        if event.char:
            self._queue.append(KeyEvent(key=event.char))

    def _on_click(self, event: Any) -> None:
        # Convert pixel to cell based on a stored grid on the root
        cell_w = getattr(self.root, "_cell_w", 10)
        cell_h = getattr(self.root, "_cell_h", 18)
        x = int(event.x // cell_w)
        y = int(event.y // cell_h)
        self._queue.append(MouseEvent(x=x, y=y, button=1))

    def poll(self) -> List[Union[KeyEvent, MouseEvent]]:
        evs = self._queue
        self._queue = []
        return evs
