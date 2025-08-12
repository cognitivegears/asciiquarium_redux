from __future__ import annotations

"""
Minimal compatibility shim providing asciimatics-like colour constants.

This lets the rest of the code import `Screen` for COLOUR_* values without
importing the real `asciimatics` package (useful for the web/Pyodide build).
"""


class Screen:
    # Colour constants matching asciimatics
    COLOUR_BLACK = 0
    COLOUR_RED = 1
    COLOUR_GREEN = 2
    COLOUR_YELLOW = 3
    COLOUR_BLUE = 4
    COLOUR_MAGENTA = 5
    COLOUR_CYAN = 6
    COLOUR_WHITE = 7

    # Common attributes/methods used in this project; actual implementation
    # will be provided by the real backend screens (terminal/tk/web).
    width: int
    height: int

    def clear(self) -> None:  # pragma: no cover - interface only
        ...

    def print_at(self, text: str, x: int, y: int, colour: int | None = None, *args, **kwargs) -> None:  # pragma: no cover - interface only
        ...

    def refresh(self) -> None:  # pragma: no cover - interface only
        ...

    def get_event(self):  # pragma: no cover - interface only
        ...

    def has_resized(self) -> bool:  # pragma: no cover - interface only
        ...
