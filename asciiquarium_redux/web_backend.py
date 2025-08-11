from __future__ import annotations

"""
Web backend bridge for running in Pyodide (WebAssembly) and drawing to an HTML5 Canvas.

This module is designed to be imported inside the browser. It avoids using
asciimatics APIs and provides a tiny Screen-like surface that our app draws on.

The JavaScript side should set a flush hook via set_js_flush_hook(fn), where fn
accepts a list of batches: [{"y": int, "x": int, "text": str, "colour": str}].
"""

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

# In Pyodide, the standard curses module is unavailable. Importing the real
# asciimatics package pulls in curses. Provide a tiny shim so our core modules
# can import colour constants and type names without importing curses.
import sys
import types

if 'asciimatics' not in sys.modules:
    _am = types.ModuleType('asciimatics')
    _screen = types.ModuleType('asciimatics.screen')

    class _DummyScreen:
        # Colour constants used throughout the app
        COLOUR_BLACK = 0
        COLOUR_RED = 1
        COLOUR_GREEN = 2
        COLOUR_YELLOW = 3
        COLOUR_BLUE = 4
        COLOUR_MAGENTA = 5
        COLOUR_CYAN = 6
        COLOUR_WHITE = 7

    _screen.Screen = _DummyScreen  # type: ignore[attr-defined]
    _event = types.ModuleType('asciimatics.event')

    class _KeyboardEvent:  # placeholders for import-time references only
        pass

    class _MouseEvent:
        pass

    _event.KeyboardEvent = _KeyboardEvent  # type: ignore[attr-defined]
    _event.MouseEvent = _MouseEvent  # type: ignore[attr-defined]

    _exceptions = types.ModuleType('asciimatics.exceptions')

    class _ResizeScreenError(Exception):
        pass

    _exceptions.ResizeScreenError = _ResizeScreenError  # type: ignore[attr-defined]

    _am.screen = _screen  # type: ignore[attr-defined]
    _am.event = _event  # type: ignore[attr-defined]
    _am.exceptions = _exceptions  # type: ignore[attr-defined]
    sys.modules['asciimatics'] = _am
    sys.modules['asciimatics.screen'] = _screen
    sys.modules['asciimatics.event'] = _event
    sys.modules['asciimatics.exceptions'] = _exceptions

from .app import AsciiQuarium
from .settings import Settings
from .entities.specials import FishHook, spawn_fishhook, spawn_fishhook_to


# Minimal colour mapping compatible with Screen.COLOUR_* semantics
COLOUR_TO_HEX = {
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
    _batches: List[dict] = field(default_factory=list)

    def __post_init__(self):
        self._alloc()

    def _alloc(self):
        self._chars = [[" "] * self.width for _ in range(self.height)]
        self._fg = [[7] * self.width for _ in range(self.height)]  # default white
        self._batches = []

    def clear(self):
        for y in range(self.height):
            row = self._chars[y]
            for x in range(self.width):
                row[x] = " "
        # Don't need to reset colours every frame
        self._batches.clear()

    def print_at(self, text: str, x: int, y: int, colour: int = 7):
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

    def flush_batches(self) -> List[dict]:
        # Build minimal horizontal runs per row to reduce draw calls
        batches: List[dict] = []
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


class WebApp:
    def __init__(self):
        self.app: Optional[AsciiQuarium] = None
        self.screen: Optional[WebScreen] = None
        self.settings = Settings()
        self._flush_hook: Optional[Callable[[List[dict]], None]] = None
        self._accum = 0.0
        self._target_dt = 1.0 / max(1, self.settings.fps)

    # JS integration
    def set_js_flush_hook(self, fn: Callable[[List[dict]], None]) -> None:
        self._flush_hook = fn

    # Lifecycle
    def start(self, cols: int, rows: int, options: dict | None = None):
        if options:
            self._apply_options(options)
        self.settings.ui_backend = "web"
        self.screen = WebScreen(width=int(cols), height=int(rows), colour_mode=self.settings.color)
        self.app = AsciiQuarium(self.settings)
        self.app.rebuild(self.screen)  # type: ignore[arg-type]
        self._target_dt = 1.0 / max(1, self.settings.fps)

    def resize(self, cols: int, rows: int):
        if not self.screen or not self.app:
            return
        self.screen.width = int(cols)
        self.screen.height = int(rows)
        self.screen._alloc()
        self.app.rebuild(self.screen)  # type: ignore[arg-type]

    def set_options(self, options: dict):
        self._apply_options(options)

    def _apply_options(self, options: dict):
        # Basic subset mapped to Settings
        if "fps" in options:
            try:
                self.settings.fps = max(5, min(120, int(options["fps"])))
            except Exception:
                pass
        if "density" in options:
            try:
                self.settings.density = float(options["density"])
            except Exception:
                pass
        if "speed" in options:
            try:
                self.settings.speed = float(options["speed"])
            except Exception:
                pass
        if "color" in options:
            self.settings.color = str(options["color"]).lower()
        if "seed" in options:
            val = options["seed"]
            try:
                self.settings.seed = int(val) if val not in (None, "", "random") else None
            except Exception:
                self.settings.seed = None
        # Web UI booleans
        if "chest" in options:
            try:
                self.settings.chest_enabled = bool(options["chest"])  # type: ignore[attr-defined]
            except Exception:
                pass
        if "turn" in options:
            try:
                self.settings.fish_turn_enabled = bool(options["turn"])  # type: ignore[attr-defined]
            except Exception:
                pass

    def tick(self, dt_ms: float):
        if not self.app or not self.screen:
            return
        dt = max(0.0, min(0.2, float(dt_ms) / 1000.0))
        # Advance one frame at configured FPS pacing
        self._accum += dt
        while self._accum >= self._target_dt:
            self._accum -= self._target_dt
            self.screen.clear()
            self.app.update(self._target_dt, self.screen, 0)  # type: ignore[arg-type]
            if self._flush_hook:
                self._flush_hook(self.screen.flush_batches())

    # Input adapters (mirror app.run logic)
    def on_key(self, key: str):
        if not self.app or not self.screen:
            return
        k = key.lower()
        if k == "q":
            # No-op in web; page owns lifecycle
            return
        if k == "p":
            self.app._paused = not self.app._paused
            return
        if k == "r":
            self.app.rebuild(self.screen)  # type: ignore[arg-type]
            return
        if k in ("h", "?"):
            self.app._show_help = not self.app._show_help
            return
        if k == "t":
            # Force a random fish to turn
            import random
            candidates = [f for f in self.app.fish if not getattr(f, 'hooked', False)]
            if candidates:
                f = random.choice(candidates)
                try:
                    f.start_turn()
                except Exception:
                    pass
            return
        if k == " ":
            # Space: toggle hook (retract if present, else spawn)
            hooks = [a for a in self.app.specials if isinstance(a, FishHook) and a.active]
            if hooks:
                for h in hooks:
                    if hasattr(h, "retract_now"):
                        h.retract_now()
            else:
                self.app.specials.extend(spawn_fishhook(self.screen, self.app))  # type: ignore[arg-type]

    def on_mouse(self, x: int, y: int, button: int):
        if not self.app or not self.screen:
            return
        # Left click only
        if button != 1:
            return
        water_top = self.settings.waterline_top
        if water_top + 1 <= y <= self.screen.height - 2:
            hooks = [a for a in self.app.specials if isinstance(a, FishHook) and a.active]
            if hooks:
                for h in hooks:
                    if hasattr(h, "retract_now"):
                        h.retract_now()
            else:
                self.app.specials.extend(spawn_fishhook_to(self.screen, self.app, int(x), int(y)))  # type: ignore[arg-type]


# Singleton used by the JS side
web_app = WebApp()

# Convenience alias for JS to set the flush hook
def set_js_flush_hook(fn):
    web_app.set_js_flush_hook(fn)
