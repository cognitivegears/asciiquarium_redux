from __future__ import annotations

import random
import time
from typing import List

from typing import cast
from .screen_compat import Screen

from .util import sprite_size, draw_sprite, draw_sprite_masked, fill_rect, draw_sprite_masked_with_bg
from .util.buffer import DoubleBufferedScreen
from .entities.environment import WATER_SEGMENTS, CASTLE, CASTLE_MASK, waterline_row
from .util.settings import Settings
from .entities.core import Seaweed, Bubble, Splat, Fish, random_fish_frames
from .entities.base import Actor
from .entities.specials import (
    FishHook,
    spawn_shark,
    spawn_fishhook,
    spawn_fishhook_to,
    spawn_whale,
    spawn_ship,
    spawn_ducks,
    spawn_dolphins,
    spawn_swan,
    spawn_monster,
    spawn_big_fish,
    spawn_treasure_chest,
)


class AsciiQuarium:
    # Class-level attribute annotations for linters/type-checkers
    _mouse_buttons: int
    _last_mouse_event_time: float
    def __init__(self, settings: Settings):
        self.settings = settings
        self.seaweed = []  # type: List[Seaweed]
        self.fish = []  # type: List[Fish]
        self.bubbles = []  # type: List[Bubble]
        self.splats = []  # type: List[Splat]
        self.specials = []  # type: List[Actor]
        self.decor = []  # type: List[Actor]  # persistent background actors (e.g., treasure chest)
        self._paused = False
        self._special_timer = random.uniform(
            self.settings.spawn_start_delay_min, self.settings.spawn_start_delay_max
        )
        self._show_help = False
        self._seaweed_tick = 0.0
        self._time = 0.0
        self._last_spawn = {}
        self._global_cooldown_until = 0.0
        # Track mouse button state for debounce
        self._mouse_buttons = 0
        self._last_mouse_event_time = 0.0

    def rebuild(self, screen: Screen):
        self.seaweed.clear()
        self.fish.clear()
        self.bubbles.clear()
        self.splats.clear()
        self.specials.clear()
        self.decor.clear()
        self._special_timer = random.uniform(self.settings.spawn_start_delay_min, self.settings.spawn_start_delay_max)
        self._seaweed_tick = 0.0

        # Seaweed count (optional override by config)
        if self.settings.seaweed_count_base is not None and self.settings.seaweed_count_per_80_cols is not None:
            units = max(1.0, screen.width / 80.0)
            base = self.settings.seaweed_count_base
            per = self.settings.seaweed_count_per_80_cols
            count = max(1, int((base + per * units) * self.settings.density * self.settings.seaweed_scale))
        else:
            count = max(1, int((screen.width // 15) * self.settings.density * self.settings.seaweed_scale))
        for _ in range(count):
            h = random.randint(3, 6)
            x = random.randint(1, max(1, screen.width - 3))
            base_y = screen.height - 2
            sw = Seaweed(x=x, base_y=base_y, height=h, phase=random.randint(0, 1))
            # Apply configured lifecycle ranges (and initialize current params within those ranges)
            sw.sway_min = self.settings.seaweed_sway_min
            sw.sway_max = self.settings.seaweed_sway_max
            sw.lifetime_min_cfg = self.settings.seaweed_lifetime_min
            sw.lifetime_max_cfg = self.settings.seaweed_lifetime_max
            sw.regrow_delay_min_cfg = self.settings.seaweed_regrow_delay_min
            sw.regrow_delay_max_cfg = self.settings.seaweed_regrow_delay_max
            sw.growth_rate_min_cfg = self.settings.seaweed_growth_rate_min
            sw.growth_rate_max_cfg = self.settings.seaweed_growth_rate_max
            sw.shrink_rate_min_cfg = self.settings.seaweed_shrink_rate_min
            sw.shrink_rate_max_cfg = self.settings.seaweed_shrink_rate_max
            # initialize current dynamics based on configured ranges
            sw.sway_speed = random.uniform(sw.sway_min, sw.sway_max)
            sw.lifetime_max = random.uniform(sw.lifetime_min_cfg, sw.lifetime_max_cfg)
            sw.regrow_delay_max = random.uniform(sw.regrow_delay_min_cfg, sw.regrow_delay_max_cfg)
            sw.growth_rate = random.uniform(sw.growth_rate_min_cfg, sw.growth_rate_max_cfg)
            sw.shrink_rate = random.uniform(sw.shrink_rate_min_cfg, sw.shrink_rate_max_cfg)
            self.seaweed.append(sw)

        # Persistent decor: treasure chest
        if getattr(self.settings, "chest_enabled", True):
            try:
                self.decor.extend(spawn_treasure_chest(screen, self))
            except Exception:
                # Fail-safe: ignore decor errors so app still runs
                pass

        water_top = self.settings.waterline_top
        area = max(1, (screen.height - (water_top + 4)) * screen.width)
        # Fish count (optional override by config)
        if self.settings.fish_count_base is not None and self.settings.fish_count_per_80_cols is not None:
            units = max(1.0, screen.width / 80.0)
            base = int(self.settings.fish_count_base)
            per = float(self.settings.fish_count_per_80_cols)
            fcount = max(2, int((base + per * units) * self.settings.density * self.settings.fish_scale))
        else:
            fcount = max(2, int(area // 350 * self.settings.density * self.settings.fish_scale))
        colours = self._palette(screen)
        for _ in range(fcount):
            self.fish.append(self._make_one_fish(screen, colours))

    def draw_waterline(self, screen: Screen):
        for i, _ in enumerate(WATER_SEGMENTS):
            row = waterline_row(i, screen.width)
            y = self.settings.waterline_top + i
            if y < screen.height:
                colour = Screen.COLOUR_WHITE if self.settings.color == "mono" else Screen.COLOUR_CYAN
                screen.print_at(row, 0, y, colour=colour)

    def _waterline_row(self, idx: int, screen: Screen) -> str:
        if idx < 0 or idx >= len(WATER_SEGMENTS):
            return ""
        return waterline_row(idx, screen.width)

    def _bubble_hits_waterline(self, x: int, y: int, screen: Screen) -> bool:
        # Convert to index within waterline rows
        idx = y - self.settings.waterline_top
        if idx < 0 or idx >= len(WATER_SEGMENTS):
            return False
        if x < 0 or x >= screen.width:
            return False
        row = self._waterline_row(idx, screen)
        if not row:
            return False
        return row[x] != ' '

    def draw_castle(self, screen: Screen):
        lines = CASTLE
        w, h = sprite_size(lines)
        x = max(0, screen.width - w - 2)
        y = max(0, screen.height - h - 1)
        if self.settings.color == "mono":
            # In mono, still keep castle opaque within its silhouette
            draw_sprite_masked_with_bg(screen, lines, [''] * len(lines), x, y, Screen.COLOUR_WHITE, Screen.COLOUR_BLACK)
        else:
            # Opaque per-row background to prevent see-through, but no full-rect cutoffs
            draw_sprite_masked_with_bg(screen, lines, CASTLE_MASK, x, y, Screen.COLOUR_WHITE, Screen.COLOUR_BLACK)

    def update(self, dt: float, screen: Screen, frame_no: int):
        dt *= self.settings.speed
        if not self._paused:
            self._seaweed_tick += dt
            for s in self.seaweed:
                s.update(dt, screen)
            # Update decor (e.g., treasure chest) so it can emit bubbles
            for d in self.decor:
                try:
                    d.update(dt, screen, self)
                except TypeError:
                    # Support actors with older update signatures
                    d.update(dt, screen)  # type: ignore[misc]
            for f in self.fish:
                f.update(dt, screen, self.bubbles)
            survivors: List[Bubble] = []
            for b in self.bubbles:
                b.update(dt)
                # Kill bubble if it hits any visible waterline character
                if b.y < 0:
                    continue
                if self._bubble_hits_waterline(b.x, b.y, screen):
                    continue
                survivors.append(b)
            self.bubbles = survivors
            for a in list(self.specials):
                a.update(dt, screen, self)
            self.specials = [a for a in self.specials if getattr(a, "active", True)]
            for s in self.splats:
                s.update()
            self.splats = [s for s in self.splats if s.active]
            # advance app time and spawn timer regardless of current specials
            self._time += dt
            self._special_timer -= dt
            can_spawn_more = len(self.specials) < int(self.settings.spawn_max_concurrent)
            if can_spawn_more and self._special_timer <= 0 and self._time >= self._global_cooldown_until:
                self.spawn_random(screen)
                self._special_timer = random.uniform(self.settings.spawn_interval_min, self.settings.spawn_interval_max)

        # Draw pass
        self.draw_waterline(screen)
        mono = self.settings.color == "mono"
        # Draw seaweed first so it does not appear in front of decor like the treasure chest
        for s in self.seaweed:
            tick = int(self._seaweed_tick / 0.25)
            s.draw(screen, tick, mono)
        # Draw decor behind fish so fish appear in front, but in front of seaweed
        for d in self.decor:
            try:
                d.draw(screen, mono)  # type: ignore[call-arg]
            except TypeError:
                d.draw(screen)
        # Draw fish back-to-front by z to mimic Perl's fish_start..fish_end layering
        fish_to_draw = sorted(self.fish, key=lambda f: getattr(f, 'z', 0))
        for f in fish_to_draw:
            if mono:
                draw_sprite(screen, f.frames, int(f.x), int(f.y), Screen.COLOUR_WHITE)
            else:
                f.draw(screen)
        # Castle is rendered above fish in Perl (higher depth)
        if getattr(self.settings, "castle_enabled", True):
            self.draw_castle(screen)
        for b in self.bubbles:
            if mono:
                if 0 <= b.y < screen.height:
                    ch = random.choice([".", "o", "O"])
                    screen.print_at(ch, b.x, b.y, colour=Screen.COLOUR_WHITE)
            else:
                b.draw(screen)
        for a in list(self.specials):
            try:
                a.draw(screen, mono)  # type: ignore[call-arg]
            except TypeError:
                a.draw(screen)
        # Draw splats last so they appear above specials (e.g., shark)
        for s in self.splats:
            s.draw(screen, mono)
        if self._show_help:
            self._draw_help(screen)

    def spawn_random(self, screen: Screen):
        # Weighted random selection based on settings.specials_weights
        choices = [
            ("shark", spawn_shark),
            ("fishhook", spawn_fishhook),
            ("whale", spawn_whale),
            ("ship", spawn_ship),
            ("ducks", spawn_ducks),
            ("dolphins", spawn_dolphins),
            ("swan", spawn_swan),
            ("monster", spawn_monster),
            ("big_fish", spawn_big_fish),
        ]
        weighted = []
        now = self._time
        # Detect existing fishhook so we can avoid selecting it while active
        hook_active = any(isinstance(a, FishHook) and a.active for a in self.specials)
        for name, fn in choices:
            if name == "fishhook" and hook_active:
                continue
            w = float(self.settings.specials_weights.get(name, 1.0))
            if w <= 0:
                continue
            # filter by per-type cooldowns
            cd = float(self.settings.specials_cooldowns.get(name, 0.0))
            last = self._last_spawn.get(name, -1e9)
            if now - last < cd:
                continue
            weighted.append((w, name, fn))
        if not weighted:
            return
        total = sum(w for w, _, _ in weighted)
        r = random.uniform(0.0, total)
        acc = 0.0
        chosen_name = weighted[-1][1]
        spawner = weighted[-1][2]
        for w, name, fn in weighted:
            acc += w
            if r <= acc:
                spawner = fn
                chosen_name = name
                break
        self.specials.extend(spawner(screen, self))
        # register cooldowns
        self._last_spawn[chosen_name] = now
        if self.settings.spawn_cooldown_global > 0:
            self._global_cooldown_until = now + float(self.settings.spawn_cooldown_global)

    def _palette(self, screen: Screen) -> List[int]:
        if self.settings.color == "mono":
            return [Screen.COLOUR_WHITE]
        return [
            Screen.COLOUR_CYAN,
            Screen.COLOUR_YELLOW,
            Screen.COLOUR_GREEN,
            Screen.COLOUR_RED,
            Screen.COLOUR_MAGENTA,
            Screen.COLOUR_BLUE,
            Screen.COLOUR_WHITE,
        ]

    def _draw_help(self, screen: Screen):
        lines = [
            "Asciiquarium Redux",
            f"fps: {self.settings.fps}  density: {self.settings.density}  speed: {self.settings.speed}  color: {self.settings.color}",
            f"seed: {self.settings.seed if self.settings.seed is not None else 'random'}",
            "",
            "Controls:",
            "  q: quit    p: pause/resume    r: rebuild",
            "  Left-click: drop fishhook to clicked spot",
            "  h/?: toggle this help",
        ]
        x, y = 2, 1
        width = max(len(s) for s in lines) + 4
        height = len(lines) + 2
        screen.print_at("+" + "-" * (width - 2) + "+", x, y, colour=Screen.COLOUR_WHITE)
        for i, row in enumerate(lines, start=1):
            screen.print_at("|" + row.ljust(width - 2) + "|", x, y + i, colour=Screen.COLOUR_WHITE)
        screen.print_at("+" + "-" * (width - 2) + "+", x, y + height - 1, colour=Screen.COLOUR_WHITE)

    # --- Live population management helpers ---
    def _compute_target_counts(self, screen: Screen) -> tuple[int, int]:
        """Return (fish_count, seaweed_count) desired for current settings and screen size."""
        # Seaweed
        if self.settings.seaweed_count_base is not None and self.settings.seaweed_count_per_80_cols is not None:
            units = max(1.0, screen.width / 80.0)
            base = self.settings.seaweed_count_base
            per = self.settings.seaweed_count_per_80_cols
            sw_count = max(1, int((base + per * units) * self.settings.density * self.settings.seaweed_scale))
        else:
            sw_count = max(1, int((screen.width // 15) * self.settings.density * self.settings.seaweed_scale))

        # Fish
        water_top = self.settings.waterline_top
        area = max(1, (screen.height - (water_top + 4)) * screen.width)
        if self.settings.fish_count_base is not None and self.settings.fish_count_per_80_cols is not None:
            units = max(1.0, screen.width / 80.0)
            base = int(self.settings.fish_count_base)
            per = float(self.settings.fish_count_per_80_cols)
            fcount = max(2, int((base + per * units) * self.settings.density * self.settings.fish_scale))
        else:
            fcount = max(2, int(area // 350 * self.settings.density * self.settings.fish_scale))
        return fcount, sw_count

    def _make_one_fish(self, screen: Screen, palette: List[int] | None = None) -> Fish:
        # Direction with configurable bias towards rightward
        direction = 1 if random.random() < float(self.settings.fish_direction_bias) else -1
        frames = random_fish_frames(direction)
        w, h = sprite_size(frames)
        water_top = self.settings.waterline_top
        # initial y will be refined by Fish.respawn; use temp fallback
        y = random.randint(max(water_top + 3, 1), max(water_top + 3, screen.height - h - 2))
        x = (-w if direction > 0 else screen.width)
        vx = random.uniform(self.settings.fish_speed_min, self.settings.fish_speed_max) * direction
        colours = palette or self._palette(screen)
        colour = random.choice(colours)
        # Build initial colour mask consistent with frames
        from .entities.core import (
            FISH_RIGHT, FISH_LEFT, FISH_RIGHT_MASKS, FISH_LEFT_MASKS,
        )
        if direction > 0:
            pairs = list(zip(FISH_RIGHT, FISH_RIGHT_MASKS))
        else:
            pairs = list(zip(FISH_LEFT, FISH_LEFT_MASKS))
        # Find matching mask for chosen frames
        mask = None
        for fset, mset in pairs:
            if fset is frames:
                mask = mset
                break
        # If identity didn't match (due to equality semantics), fallback by size index
        if mask is None:
            try:
                idx = (FISH_RIGHT if direction > 0 else FISH_LEFT).index(frames)
                mask = (FISH_RIGHT_MASKS if direction > 0 else FISH_LEFT_MASKS)[idx]
            except ValueError:
                mask = None
        colour_mask = None
        if mask is not None and self.settings.color != "mono":
            from .util import randomize_colour_mask
            colour_mask = randomize_colour_mask(mask)
        f = Fish(
            frames=frames,
            x=x,
            y=y,
            vx=vx,
            colour=colour,
            colour_mask=colour_mask,
            speed_min=self.settings.fish_speed_min,
            speed_max=self.settings.fish_speed_max,
            bubble_min=self.settings.fish_bubble_min,
            bubble_max=self.settings.fish_bubble_max,
            band_low_frac=(self.settings.fish_y_band[0] if self.settings.fish_y_band else 0.0),
            band_high_frac=(self.settings.fish_y_band[1] if self.settings.fish_y_band else 1.0),
            waterline_top=self.settings.waterline_top,
            water_rows=len(WATER_SEGMENTS),
        )
        # Initialize bubble timer from configured range
        f.next_bubble = random.uniform(self.settings.fish_bubble_min, self.settings.fish_bubble_max)
        # Pass turning behavior config
        f.turn_enabled = bool(getattr(self.settings, "fish_turn_enabled", True))
        f.turn_chance_per_second = float(getattr(self.settings, "fish_turn_chance_per_second", 0.01))
        f.turn_min_interval = float(getattr(self.settings, "fish_turn_min_interval", 6.0))
        f.turn_shrink_seconds = float(getattr(self.settings, "fish_turn_shrink_seconds", 0.35))
        f.turn_expand_seconds = float(getattr(self.settings, "fish_turn_expand_seconds", 0.35))
        return f

    def _make_one_seaweed(self, screen: Screen) -> Seaweed:
        h = random.randint(3, 6)
        x = random.randint(1, max(1, screen.width - 3))
        base_y = screen.height - 2
        sw = Seaweed(x=x, base_y=base_y, height=h, phase=random.randint(0, 1))
        # Apply configured lifecycle ranges (and initialize current params within those ranges)
        sw.sway_min = self.settings.seaweed_sway_min
        sw.sway_max = self.settings.seaweed_sway_max
        sw.lifetime_min_cfg = self.settings.seaweed_lifetime_min
        sw.lifetime_max_cfg = self.settings.seaweed_lifetime_max
        sw.regrow_delay_min_cfg = self.settings.seaweed_regrow_delay_min
        sw.regrow_delay_max_cfg = self.settings.seaweed_regrow_delay_max
        sw.growth_rate_min_cfg = self.settings.seaweed_growth_rate_min
        sw.growth_rate_max_cfg = self.settings.seaweed_growth_rate_max
        sw.shrink_rate_min_cfg = self.settings.seaweed_shrink_rate_min
        sw.shrink_rate_max_cfg = self.settings.seaweed_shrink_rate_max
        # initialize current dynamics based on configured ranges
        sw.sway_speed = random.uniform(sw.sway_min, sw.sway_max)
        sw.lifetime_max = random.uniform(sw.lifetime_min_cfg, sw.lifetime_max_cfg)
        sw.regrow_delay_max = random.uniform(sw.regrow_delay_min_cfg, sw.regrow_delay_max_cfg)
        sw.growth_rate = random.uniform(sw.growth_rate_min_cfg, sw.growth_rate_max_cfg)
        sw.shrink_rate = random.uniform(sw.shrink_rate_min_cfg, sw.shrink_rate_max_cfg)
        return sw

    def adjust_populations(self, screen: Screen):
        """Incrementally add/remove fish and seaweed to match target counts without a full rebuild."""
        target_fish, target_sw = self._compute_target_counts(screen)
        # Adjust seaweed first (background)
        cur_sw = len(self.seaweed)
        if target_sw > cur_sw:
            for _ in range(target_sw - cur_sw):
                self.seaweed.append(self._make_one_seaweed(screen))
        elif target_sw < cur_sw:
            # Remove from end for predictability
            del self.seaweed[target_sw:]
        # Adjust fish
        cur_fish = len(self.fish)
        if target_fish > cur_fish:
            palette = self._palette(screen)
            for _ in range(target_fish - cur_fish):
                self.fish.append(self._make_one_fish(screen, palette))
        elif target_fish < cur_fish:
            del self.fish[target_fish:]


def run(screen: Screen, settings: Settings):
    # Import terminal-only dependencies lazily to keep web import graph clean.
    from asciimatics.event import KeyboardEvent, MouseEvent  # type: ignore
    from asciimatics.exceptions import ResizeScreenError  # type: ignore
    app = AsciiQuarium(settings)
    # Wrap the screen with a double buffer to reduce flicker
    db = DoubleBufferedScreen(screen)
    app.rebuild(screen)

    last = time.time()
    frame_no = 0
    target_dt = 1.0 / max(1, settings.fps)

    while True:
        now = time.time()
        dt = min(0.1, now - last)
        last = now

        # Keyboard or mouse event
        ev = screen.get_event()
        # Key handling
        key = ev.key_code if isinstance(ev, KeyboardEvent) else None
        if key in (ord("q"), ord("Q")):
            return
        if key in (ord("p"), ord("P")):
            app._paused = not app._paused
        if key in (ord("r"), ord("R")):
            app.rebuild(screen)
        if key in (ord("h"), ord("H"), ord("?")):
            app._show_help = not app._show_help
        # 't': force a random fish to start turning (debug/verification)
        if key in (ord("t"), ord("T")):
            candidates = [f for f in app.fish if not getattr(f, 'hooked', False)]
            if candidates:
                f = random.choice(candidates)
                try:
                    f.start_turn()
                except Exception:
                    pass
        # Spacebar: drop fishhook at random position (like random special)
        if key == ord(" "):
            # If a hook exists and is not retracting, command it to retract immediately
            hooks = [a for a in app.specials if isinstance(a, FishHook) and a.active]
            if hooks:
                # Retract existing hook on space
                for h in hooks:
                    if hasattr(h, "retract_now"):
                        h.retract_now()
            else:
                app.specials.extend(spawn_fishhook(screen, app))

    # Mouse handling: left-click spawns a targeted fishhook, or retracts if one is down
        if isinstance(ev, MouseEvent):
            # Spawn only on left button down transition (debounce)
            left_now = 1 if (ev.buttons & 1) else 0
            left_prev = 1 if (app._mouse_buttons & 1) else 0
            if left_now and not left_prev:
                click_x = int(ev.x)
                click_y = int(ev.y)
                water_top = settings.waterline_top
                # Only accept clicks below waterline and above bottom-1
                if water_top + 1 <= click_y <= screen.height - 2:
                    # If a hook exists, command it to retract on click
                    hooks = [a for a in app.specials if isinstance(a, FishHook) and a.active]
                    if hooks:
                        for h in hooks:
                            if hasattr(h, "retract_now"):
                                h.retract_now()
                    else:
                        app.specials.extend(spawn_fishhook_to(screen, app, click_x, click_y))
            app._mouse_buttons = ev.buttons
            app._last_mouse_event_time = now
        else:
            # If we haven't seen a mouse event for a short while, assume release.
            if app._mouse_buttons != 0 and (now - app._last_mouse_event_time) > 0.2:
                app._mouse_buttons = 0

        # Gracefully handle terminal resizes by restarting the UI loop
        # via Screen.wrapper catching ResizeScreenError.
        if screen.has_resized():
            raise ResizeScreenError("Screen resized")

        db.clear()
        app.update(dt, cast(Screen, db), frame_no)
        db.flush()
        frame_no += 1

        elapsed = time.time() - now
        sleep_for = max(0.0, target_dt - elapsed)
        time.sleep(sleep_for)
