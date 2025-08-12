from __future__ import annotations

"""
Web backend bridge for running in Pyodide (WebAssembly) and drawing to an HTML5 Canvas.

This module is designed to be imported inside the browser. It avoids using
asciimatics APIs and provides a tiny Screen-like surface that our app draws on.

The JavaScript side should set a flush hook via set_js_flush_hook(fn), where fn
accepts a list of batches: [{"y": int, "x": int, "text": str, "colour": str}].
"""

import time
from typing import Callable, List, Optional

from ...app import AsciiQuarium
from ...util.settings import Settings
from ...entities.specials import FishHook, spawn_fishhook, spawn_fishhook_to, spawn_treasure_chest
from ...entities.specials.treasure_chest import TreasureChest
from .web_screen import WebScreen
from ...util.types import FlushHook, FlushBatch

# Rebuild delay constants to coalesce noisy changes
REBUILD_DELAY_RESIZE = 0.0
REBUILD_DELAY_THROTTLE = 0.15


class WebApp:
    def __init__(self):
        self.app = None
        self.screen = None
        self.settings = Settings()
        self._flush_hook: Optional[FlushHook] = None
        self._accum = 0.0
        self._target_dt = 1.0 / max(1, self.settings.fps)
        # Rebuild control for live option changes
        self._rebuild_due_at = 0.0
        self._rebuild_pending = False
        # Numeric tolerance for float changes used in option comparisons
        self._EPS = 1e-6

    # JS integration
    def set_js_flush_hook(self, fn: FlushHook) -> None:
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
        self._schedule_rebuild(delay=REBUILD_DELAY_RESIZE)

    def set_options(self, options: dict):
        needs_rebuild = self._apply_options(options)
        if needs_rebuild:
            # Throttle rebuilds to avoid excessive work while dragging sliders
            self._schedule_rebuild(delay=REBUILD_DELAY_THROTTLE)

    def _schedule_rebuild(self, delay: float = 0.0):
        try:
            now = time.time()
        except Exception:
            now = 0.0
        self._rebuild_due_at = now + max(0.0, delay)
        self._rebuild_pending = True

    def _apply_options(self, options: dict) -> bool:
        # Aggregate rebuild requests from sub-areas
        needs_rebuild = False
        needs_rebuild |= self._apply_basic(options)
        needs_rebuild |= self._apply_booleans(options)
        needs_rebuild |= self._apply_fish(options)
        needs_rebuild |= self._apply_seaweed(options)
        needs_rebuild |= self._apply_scene_spawn(options)
        self._apply_special_weights(options)
        self._apply_fishhook(options)
        return bool(needs_rebuild)

    # ---- Option helpers ----
    def _apply_basic(self, options: dict) -> bool:
        needs_rebuild = False
        if "fps" in options:
            try:
                self.settings.fps = max(5, min(120, int(options["fps"])))
                self._target_dt = 1.0 / max(1, self.settings.fps)
            except Exception:
                pass
        if "density" in options:
            try:
                new_val = float(options["density"])
                old_val = float(getattr(self.settings, "density", new_val))
                if abs(new_val - old_val) > self._EPS:
                    self.settings.density = new_val
                    if self.app is not None and self.screen is not None:
                        try:
                            self.app.adjust_populations(self.screen)  # type: ignore[attr-defined]
                        except Exception:
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
        return needs_rebuild

    def _apply_booleans(self, options: dict) -> bool:
        needs_rebuild = False
        if "chest" in options:
            try:
                prev = bool(getattr(self.settings, "chest_enabled", True))
                new_val = bool(options["chest"])  # type: ignore[attr-defined]
                if new_val != prev:
                    self.settings.chest_enabled = new_val  # type: ignore[attr-defined]
                    if self.app is not None and self.screen is not None:
                        if not new_val:
                            self.app.decor = [d for d in self.app.decor if not isinstance(d, TreasureChest)]
                        else:
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
        return needs_rebuild

    def _apply_fish(self, options: dict) -> bool:
        needs_rebuild = False
        for src, dst, typ in [
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
            if src in options:
                try:
                    new_val = typ(options[src])
                    old_val = getattr(self.settings, dst)
                    changed = (isinstance(new_val, float) and isinstance(old_val, float) and abs(new_val - old_val) > self._EPS) or (not isinstance(new_val, float) and new_val != old_val)
                    if changed:
                        setattr(self.settings, dst, new_val)
                        if dst in ("fish_scale",) and self.app is not None and self.screen is not None:
                            try:
                                self.app.adjust_populations(self.screen)  # type: ignore[attr-defined]
                            except Exception:
                                needs_rebuild = True
                except Exception:
                    pass
        return needs_rebuild

    def _apply_seaweed(self, options: dict) -> bool:
        needs_rebuild = False
        for src, dst, typ in [
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
            if src in options:
                try:
                    new_val = typ(options[src])
                    old_val = getattr(self.settings, dst)
                    changed = (isinstance(new_val, float) and isinstance(old_val, float) and abs(new_val - old_val) > self._EPS) or (not isinstance(new_val, float) and new_val != old_val)
                    if changed:
                        setattr(self.settings, dst, new_val)
                        if dst in ("seaweed_scale",) and self.app is not None and self.screen is not None:
                            try:
                                self.app.adjust_populations(self.screen)  # type: ignore[attr-defined]
                            except Exception:
                                needs_rebuild = True
                except Exception:
                    pass
        return needs_rebuild

    def _apply_scene_spawn(self, options: dict) -> bool:
        needs_rebuild = False
        for src, dst, typ in [
            ("waterline_top", "waterline_top", int),
            ("chest_burst_seconds", "chest_burst_seconds", float),
            ("spawn_start_delay_min", "spawn_start_delay_min", float),
            ("spawn_start_delay_max", "spawn_start_delay_max", float),
            ("spawn_interval_min", "spawn_interval_min", float),
            ("spawn_interval_max", "spawn_interval_max", float),
            ("spawn_max_concurrent", "spawn_max_concurrent", int),
            ("spawn_cooldown_global", "spawn_cooldown_global", float),
        ]:
            if src in options:
                try:
                    old_val = getattr(self.settings, dst)
                    new_val = typ(options[src])
                    changed = (isinstance(new_val, float) and isinstance(old_val, float) and abs(new_val - old_val) > self._EPS) or (not isinstance(new_val, float) and new_val != old_val)
                    if changed:
                        setattr(self.settings, dst, new_val)
                        if dst == "waterline_top":
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
        return needs_rebuild

    def _apply_special_weights(self, options: dict) -> None:
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

    def _apply_fishhook(self, options: dict) -> None:
        if "fishhook_dwell_seconds" in options:
            try:
                self.settings.fishhook_dwell_seconds = float(options["fishhook_dwell_seconds"])  # type: ignore[assignment]
            except Exception:
                pass

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
