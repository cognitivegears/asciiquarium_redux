"""Terminal and Tk backends: render and event abstractions."""

from .term_backends import (
    RenderContext,
    EventStream,
    KeyEvent,
    MouseEvent,
    TerminalRenderContext,
    TerminalEventStream,
    TkRenderContext,
    TkEventStream,
)

__all__ = [
    "RenderContext",
    "EventStream",
    "KeyEvent",
    "MouseEvent",
    "TerminalRenderContext",
    "TerminalEventStream",
    "TkRenderContext",
    "TkEventStream",
]
