from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from ...util.types import FlushBatch

# Minimal colour mapping compatible with Screen.COLOUR_* semantics
COLOUR_TO_HEX: Dict[int, str] = {
    0: "#000000",  # BLACK
    1: "#ff0000",  # RED
    2: "#00ff00",  # GREEN
    3: "#ffff00",  # YELLOW
    4: "#0000ff",  # BLUE
    5: "#ff00ff",  # MAGENTA
    6: "#00ffff",  # CYAN
    7: "#ffffff",  # WHITE
}


@dataclass
class WebScreen:
    width: int
    height: int
    colour_mode: str = "auto"
    _chars: List[List[str]] = field(default_factory=list)
    _fg: List[List[int]] = field(default_factory=list)
    _batches: List[FlushBatch] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._alloc()

    def _alloc(self) -> None:
        self._chars = [[" "] * self.width for _ in range(self.height)]
        self._fg = [[7] * self.width for _ in range(self.height)]  # default white
        self._batches = []

    def clear(self) -> None:
        for y in range(self.height):
            row = self._chars[y]
            for x in range(self.width):
                row[x] = " "
        # Don't need to reset colours every frame
        self._batches.clear()

    def print_at(self, text: str, x: int, y: int, colour: Optional[Union[int, Any]] = None, *args: Any, **kwargs: Any) -> None:
        colour = 7 if colour is None else int(colour)
        if y < 0 or y >= self.height:
            return
        if x >= self.width:
            return
        if x < 0:
            # clip left
            text = text[-x:]
            x = 0
        max_len = self.width - x
        if max_len <= 0:
            return
        text = text[:max_len]
        chars = self._chars[y]
        fg = self._fg[y]
        for i, ch in enumerate(text):
            chars[x + i] = ch
            fg[x + i] = colour

    def has_resized(self) -> bool:
        return False

    def flush_batches(self) -> List[FlushBatch]:
        # Build minimal horizontal runs per row to reduce draw calls
        batches: List[FlushBatch] = []
        for y in range(self.height):
            row = self._chars[y]
            cols = self._fg[y]
            x = 0
            while x < self.width:
                col = cols[x]
                if row[x] == " ":
                    x += 1
                    continue
                start = x
                buf_chars = [row[x]]
                x += 1
                while x < self.width and cols[x] == col and row[x] != " ":
                    buf_chars.append(row[x])
                    x += 1
                text = "".join(buf_chars)
                batches.append({
                    "y": int(y),
                    "x": int(start),
                    "text": str(text),
                    "colour": str(COLOUR_TO_HEX.get(col, "#ffffff")),
                })
        return batches

    def refresh(self) -> None:
        """Update the physical display with current buffer contents."""
        # For web backend, refresh is handled by flush_batches()
        pass

    def get_event(self) -> Any:
        """Get the next input event from the event queue."""
        # Web backend handles events via WebSocket, not direct polling
        return None
