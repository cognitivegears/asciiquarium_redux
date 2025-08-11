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
from .entities.specials import FishHook, spawn_fishhook, spawn_fishhook_to, spawn_treasure_chest
from .entities.specials.treasure_chest import TreasureChest


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
        self.app = None
        self.screen = None
        self.settings = Settings()
        self._flush_hook = None
        self._accum = 0.0
        self._target_dt = 1.0 / max(1, self.settings.fps)
        # Rebuild control for live option changes
        self._rebuild_due_at = 0.0
        self._rebuild_pending = False

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
        cols = int(cols)
        rows = int(rows)
        if self.screen.width == cols and self.screen.height == rows:
            return
        # Mark a rebuild pending at next tick to coalesce with any option changes
        self.screen.width = cols
        self.screen.height = rows
        self.screen._alloc()
        # Defer rebuild to tick loop to avoid cascading rebuilds
        self._schedule_rebuild(delay=0.0)

    def set_options(self, options: dict):
        needs_rebuild = self._apply_options(options)
        if needs_rebuild:
            # Throttle rebuilds to avoid excessive work while dragging sliders
            self._schedule_rebuild(delay=0.15)

    def _schedule_rebuild(self, delay: float = 0.0):
        try:
            now = time.time()
        except Exception:
            now = 0.0
        self._rebuild_due_at = now + max(0.0, delay)
        self._rebuild_pending = True

    def _apply_options(self, options: dict) -> bool:
        needs_rebuild = False
        EPS = 1e-6

        # Basic subset mapped to Settings
        if "fps" in options:
            try:
                self.settings.fps = max(5, min(120, int(options["fps"])))
                # Update pacing immediately; no rebuild necessary
                self._target_dt = 1.0 / max(1, self.settings.fps)
            except Exception:
                pass

        if "density" in options:
            try:
                new_val = float(options["density"])
                old_val = float(getattr(self.settings, "density", new_val))
                if abs(new_val - old_val) > EPS:
                    self.settings.density = new_val
                    # Incremental adjustment; no rebuild needed
                    if self.app is not None and self.screen is not None:
                        try:
                            self.app.adjust_populations(self.screen)  # type: ignore[attr-defined]
                        except Exception:
                            # Fallback to rebuild on failure
                            needs_rebuild = True
            except Exception:
                pass

        if "speed" in options:
            try:
                self.settings.speed = float(options["speed"])
            except Exception:
                pass

        if "color" in options:
            try:
                self.settings.color = str(options["color"]).lower()
            except Exception:
                pass

        if "seed" in options:
            val = options["seed"]
            try:
                new_seed = int(val) if val not in (None, "", "random") else None
            except Exception:
                new_seed = None
            if new_seed != getattr(self.settings, "seed", None):
                self.settings.seed = new_seed
                needs_rebuild = True

        # Web UI booleans
        if "chest" in options:
            try:
                prev = bool(getattr(self.settings, "chest_enabled", True))
                new_val = bool(options["chest"])  # type: ignore[attr-defined]
                if new_val != prev:
                    self.settings.chest_enabled = new_val  # type: ignore[attr-defined]
                    # Live toggle of treasure chest without full rebuild
                    if self.app is not None and self.screen is not None:
                        if not new_val:
                            # Remove any existing chest from decor
                            self.app.decor = [d for d in self.app.decor if not isinstance(d, TreasureChest)]
                        else:
                            # Add one if none present
                            if not any(isinstance(d, TreasureChest) for d in self.app.decor):
                                try:
                                    self.app.decor.extend(spawn_treasure_chest(self.screen, self.app))  # type: ignore[arg-type]
                                except Exception:
                                    pass
            except Exception:
                pass
        if "castle" in options:
            try:
                self.settings.castle_enabled = bool(options["castle"])  # type: ignore[attr-defined]
            except Exception:
                pass

        if "turn" in options:
            try:
                self.settings.fish_turn_enabled = bool(options["turn"])  # type: ignore[attr-defined]
            except Exception:
                pass

        # Fish controls
        for key_map in [
            ("fish_direction_bias", "fish_direction_bias", float),
            ("fish_speed_min", "fish_speed_min", float),
            ("fish_speed_max", "fish_speed_max", float),
            ("fish_bubble_min", "fish_bubble_min", float),
            ("fish_bubble_max", "fish_bubble_max", float),
            ("fish_turn_chance_per_second", "fish_turn_chance_per_second", float),
            ("fish_turn_min_interval", "fish_turn_min_interval", float),
            ("fish_turn_shrink_seconds", "fish_turn_shrink_seconds", float),
            ("fish_turn_expand_seconds", "fish_turn_expand_seconds", float),
            ("fish_scale", "fish_scale", float),
        ]:
            src, dst, typ = key_map
            if src in options:
                try:
                    new_val = typ(options[src])
                    old_val = getattr(self.settings, dst)
                    if (isinstance(new_val, float) and isinstance(old_val, float) and abs(new_val - old_val) > EPS) or (not isinstance(new_val, float) and new_val != old_val):
                        setattr(self.settings, dst, new_val)
                        if dst in ("fish_scale",) and self.app is not None and self.screen is not None:
                            try:
                                self.app.adjust_populations(self.screen)  # type: ignore[attr-defined]
                            except Exception:
                                needs_rebuild = True
                except Exception:
                    pass

        # Seaweed
        for key_map in [
            ("seaweed_scale", "seaweed_scale", float),
            ("seaweed_sway_min", "seaweed_sway_min", float),
            ("seaweed_sway_max", "seaweed_sway_max", float),
            ("seaweed_lifetime_min", "seaweed_lifetime_min", float),
            ("seaweed_lifetime_max", "seaweed_lifetime_max", float),
            ("seaweed_regrow_delay_min", "seaweed_regrow_delay_min", float),
            ("seaweed_regrow_delay_max", "seaweed_regrow_delay_max", float),
            ("seaweed_growth_rate_min", "seaweed_growth_rate_min", float),
            ("seaweed_growth_rate_max", "seaweed_growth_rate_max", float),
            ("seaweed_shrink_rate_min", "seaweed_shrink_rate_min", float),
            ("seaweed_shrink_rate_max", "seaweed_shrink_rate_max", float),
        ]:
            src, dst, typ = key_map
            if src in options:
                try:
                    new_val = typ(options[src])
                    old_val = getattr(self.settings, dst)
                    if (isinstance(new_val, float) and isinstance(old_val, float) and abs(new_val - old_val) > EPS) or (not isinstance(new_val, float) and new_val != old_val):
                        setattr(self.settings, dst, new_val)
                        if dst in ("seaweed_scale",) and self.app is not None and self.screen is not None:
                            try:
                                self.app.adjust_populations(self.screen)  # type: ignore[attr-defined]
                            except Exception:
                                needs_rebuild = True
                except Exception:
                    pass

        # Scene & spawn
        for key_map in [
            ("waterline_top", "waterline_top", int),
            ("chest_burst_seconds", "chest_burst_seconds", float),
            ("spawn_start_delay_min", "spawn_start_delay_min", float),
            ("spawn_start_delay_max", "spawn_start_delay_max", float),
            ("spawn_interval_min", "spawn_interval_min", float),
            ("spawn_interval_max", "spawn_interval_max", float),
            ("spawn_max_concurrent", "spawn_max_concurrent", int),
            ("spawn_cooldown_global", "spawn_cooldown_global", float),
        ]:
            src, dst, typ = key_map
            if src in options:
                try:
                    old_val = getattr(self.settings, dst)
                    new_val = typ(options[src])
                    if (isinstance(new_val, float) and isinstance(old_val, float) and abs(new_val - old_val) > EPS) or (not isinstance(new_val, float) and new_val != old_val):
                        setattr(self.settings, dst, new_val)
                        if dst == "waterline_top":
                            # Live-update fish constraints to new waterline
                            if self.app is not None:
                                for f in getattr(self.app, "fish", []):
                                    try:
                                        setattr(f, "waterline_top", int(new_val))
                                        setattr(f, "water_rows", 4)
                                    except Exception:
                                        pass
                        if dst == "chest_burst_seconds" and self.app is not None:
                            for d in getattr(self.app, "decor", []):
                                if isinstance(d, TreasureChest):
                                    try:
                                        d.burst_period = float(new_val)
                                    except Exception:
                                        pass
                except Exception:
                    pass

        # Special weights
        weights = {
            "shark": options.get("w_shark"),
            "fishhook": options.get("w_fishhook"),
            "whale": options.get("w_whale"),
            "ship": options.get("w_ship"),
            "ducks": options.get("w_ducks"),
            "dolphins": options.get("w_dolphins"),
            "swan": options.get("w_swan"),
            "monster": options.get("w_monster"),
            "big_fish": options.get("w_big_fish"),
        }
        for k, v in weights.items():
            if v is not None:
                try:
                    self.settings.specials_weights[k] = float(v)
                except Exception:
                    pass

        # Fishhook
        if "fishhook_dwell_seconds" in options:
            try:
                self.settings.fishhook_dwell_seconds = float(options["fishhook_dwell_seconds"])  # type: ignore[assignment]
            except Exception:
                pass

        return needs_rebuild

    def tick(self, dt_ms: float):
        if not self.app or not self.screen:
            return
        dt = max(0.0, min(0.2, float(dt_ms) / 1000.0))
        # Apply pending rebuilds just before stepping the simulation
        if self._rebuild_pending:
            try:
                now = time.time()
            except Exception:
                now = 0.0
            if now >= self._rebuild_due_at:
                self._rebuild_pending = False
                self.app.rebuild(self.screen)  # type: ignore[arg-type]
                # Recompute target dt in case FPS changed
                self._target_dt = 1.0 / max(1, self.settings.fps)
        else:
            # Ensure populations match current density/scale without rebuilds
            try:
                self.app.adjust_populations(self.screen)  # type: ignore[attr-defined]
            except Exception:
                pass
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
