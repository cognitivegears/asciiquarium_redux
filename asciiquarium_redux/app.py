from __future__ import annotations

import random
import time
from typing import List

from asciimatics.screen import Screen

from .util import sprite_size, draw_sprite
from .environment import WATER_SEGMENTS, CASTLE
from .settings import Settings
from .entities.core import Seaweed, Bubble, Splat, Fish, random_fish_frames
from .entities.base import Actor
from .entities.specials import (
    spawn_shark,
    spawn_fishhook,
    spawn_whale,
    spawn_ship,
    spawn_ducks,
    spawn_dolphins,
    spawn_swan,
    spawn_monster,
)


class AsciiQuarium:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.seaweed = []  # type: List[Seaweed]
        self.fish = []  # type: List[Fish]
        self.bubbles = []  # type: List[Bubble]
        self.splats = []  # type: List[Splat]
        self.specials = []  # type: List[Actor]
        self._paused = False
        self._special_timer = random.uniform(3.0, 8.0)
        self._show_help = False
        self._seaweed_tick = 0.0

    def rebuild(self, screen: Screen):
        self.seaweed.clear()
        self.fish.clear()
        self.bubbles.clear()
        self.splats.clear()
        self.specials.clear()
        self._special_timer = random.uniform(3.0, 8.0)
        self._seaweed_tick = 0.0

        count = max(1, int((screen.width // 15) * self.settings.density))
        for _ in range(count):
            h = random.randint(3, 6)
            x = random.randint(1, max(1, screen.width - 3))
            base_y = screen.height - 2
            self.seaweed.append(Seaweed(x=x, base_y=base_y, height=h, phase=random.randint(0, 1)))

        water_top = 5
        area = max(1, (screen.height - (water_top + 4)) * screen.width)
        fcount = max(2, int(area // 350 * self.settings.density))
        colours = self._palette(screen)
        for _ in range(fcount):
            direction = random.choice([-1, 1])
            frames = random_fish_frames(direction)
            w, h = sprite_size(frames)
            y = random.randint(max(9, 1), max(9, screen.height - h - 2))
            x = (-w if direction > 0 else screen.width)
            vx = random.uniform(0.6, 2.5) * direction
            colour = random.choice(colours)
            self.fish.append(Fish(frames=frames, x=x, y=y, vx=vx, colour=colour))

    def draw_waterline(self, screen: Screen):
        seg_len = len(WATER_SEGMENTS[0])
        repeat = screen.width // seg_len + 2
        for i, seg in enumerate(WATER_SEGMENTS):
            row = (seg * repeat)[: screen.width]
            y = 5 + i
            if y < screen.height:
                colour = Screen.COLOUR_WHITE if self.settings.color == "mono" else Screen.COLOUR_CYAN
                screen.print_at(row, 0, y, colour=colour)

    def draw_castle(self, screen: Screen):
        lines = CASTLE
        w, h = sprite_size(lines)
        x = max(0, screen.width - w - 2)
        y = max(0, screen.height - h - 1)
        draw_sprite(screen, lines, x, y, Screen.COLOUR_WHITE)

    def update(self, dt: float, screen: Screen, frame_no: int):
        dt *= self.settings.speed
        if not self._paused:
            self._seaweed_tick += dt
            for f in self.fish:
                f.update(dt, screen, self.bubbles)
            for b in self.bubbles:
                b.update(dt)
            self.bubbles = [b for b in self.bubbles if b.y > 6]
            for a in list(self.specials):
                a.update(dt, screen, self)
            self.specials = [a for a in self.specials if getattr(a, "active", True)]
            for s in self.splats:
                s.update()
            self.splats = [s for s in self.splats if s.active]
            if not self.specials:
                self._special_timer -= dt
                if self._special_timer <= 0:
                    self.spawn_random(screen)
                    self._special_timer = random.uniform(8.0, 20.0)

        # Draw pass
        self.draw_waterline(screen)
        self.draw_castle(screen)
        mono = self.settings.color == "mono"
        for s in self.seaweed:
            tick = int(self._seaweed_tick / 0.25)
            s.draw(screen, tick, mono)
        for f in self.fish:
            if mono:
                draw_sprite(screen, f.frames, int(f.x), int(f.y), Screen.COLOUR_WHITE)
            else:
                f.draw(screen)
        for b in self.bubbles:
            if mono:
                if 0 <= b.y < screen.height:
                    ch = random.choice([".", "o", "O"])
                    screen.print_at(ch, b.x, b.y, colour=Screen.COLOUR_WHITE)
            else:
                b.draw(screen)
        for s in self.splats:
            s.draw(screen, mono)
        for a in list(self.specials):
            try:
                a.draw(screen, mono)  # type: ignore[call-arg]
            except TypeError:
                a.draw(screen)
        if self._show_help:
            self._draw_help(screen)

    def spawn_random(self, screen: Screen):
        choices = [
            spawn_shark,
            spawn_fishhook,
            spawn_whale,
            spawn_ship,
            spawn_ducks,
            spawn_dolphins,
            spawn_swan,
            spawn_monster,
        ]
        spawner = random.choice(choices)
        self.specials.extend(spawner(screen, self))

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
            "  h/?: toggle this help",
        ]
        x, y = 2, 1
        width = max(len(s) for s in lines) + 4
        height = len(lines) + 2
        screen.print_at("+" + "-" * (width - 2) + "+", x, y, colour=Screen.COLOUR_WHITE)
        for i, row in enumerate(lines, start=1):
            screen.print_at("|" + row.ljust(width - 2) + "|", x, y + i, colour=Screen.COLOUR_WHITE)
        screen.print_at("+" + "-" * (width - 2) + "+", x, y + height - 1, colour=Screen.COLOUR_WHITE)


def run(screen: Screen, settings: Settings):
    app = AsciiQuarium(settings)
    app.rebuild(screen)

    last = time.time()
    frame_no = 0
    target_dt = 1.0 / max(1, settings.fps)

    while True:
        now = time.time()
        dt = min(0.1, now - last)
        last = now

        ev = screen.get_key()
        if ev in (ord("q"), ord("Q")):
            return
        if ev in (ord("p"), ord("P")):
            app._paused = not app._paused
        if ev in (ord("r"), ord("R")):
            app.rebuild(screen)
        if ev in (ord("h"), ord("H"), ord("?")):
            app._show_help = not app._show_help

        screen.clear()
        app.update(dt, screen, frame_no)
        screen.refresh()
        frame_no += 1

        elapsed = time.time() - now
        sleep_for = max(0.0, target_dt - elapsed)
        time.sleep(sleep_for)
