from __future__ import annotations

# Copied from top-level main.py so the package is runnable as a console script.
# Keep this file as the authoritative runtime; consider refactoring the repo to use this module from main.py.

import random
import time
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import argparse
import os
from pathlib import Path
import tomllib

from asciimatics.screen import Screen
import math


def parse_sprite(s: str) -> List[str]:
    lines = s.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def sprite_size(lines: List[str]) -> Tuple[int, int]:
    if not lines:
        return 0, 0
    return max(len(l) for l in lines), len(lines)


def draw_sprite(screen: Screen, lines: List[str], x: int, y: int, colour: int):
    max_y = screen.height - 1
    max_x = screen.width - 1
    for dy, row in enumerate(lines):
        sy = y + dy
        if sy < 0 or sy > max_y:
            continue
        if x > max_x or x + len(row) < 0:
            continue
        start = 0
        if x < 0:
            start = -x
        visible = row[start : max(0, min(len(row), max_x - x + 1))]
        if visible:
            screen.print_at(visible, x + start, sy, colour=colour)


def aabb_overlap(ax: int, ay: int, aw: int, ah: int, bx: int, by: int, bw: int, bh: int) -> bool:
    return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)


WATER_SEGMENTS = [
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
    "^^^^ ^^^  ^^^   ^^^    ^^^^      ",
    "^^^^      ^^^^     ^^^    ^^     ",
    "^^      ^^^^      ^^^    ^^^^^^  ",
]

CASTLE = parse_sprite(
    r"""
               T~~
               |
              /^\
             /   \
 _   _   _  /     \  _   _   _
[ ]_[ ]_[ ]/ _   _ \[ ]_[ ]_[ ]
|_=__-_ =_|_[ ]_[ ]_|_=-___-__|
 | _- =  | =_ = _    |= _=   |
 |= -[]  |- = _ =    |_-=_[] |
 | =_    |= - ___    | =_ =  |
 |=  []- |-  /| |\   |=_ =[] |
 |- =_   | =| | | |  |- = -  |
 |_______|__|_|_|_|__|_______|
"""
)

FISH_RIGHT = [
    parse_sprite(
        r"""
       \
     ...\..,
\  /'       \
 >=     (  ' >
/  \      / /
    `"'"'/'
"""
    ),
    parse_sprite(
        r"""
    \
\ /--\
>=  (o>
/ \__/
    /
"""
    ),
]

FISH_LEFT = [
    parse_sprite(
        r"""
      /
  ,../...
 /       '\  /
< '  )     =<
 \ \      /  \
  `\'"'"'
"""
    ),
    parse_sprite(
        r"""
  /
 /--\ /
<o)  =<
 \__/ \
  \
"""
    ),
]


def random_fish_frames(direction: int) -> List[str]:
    return random.choice(FISH_RIGHT if direction > 0 else FISH_LEFT)


@dataclass
class Seaweed:
    x: int
    base_y: int
    height: int
    phase: int

    def frames(self) -> Tuple[List[str], List[str]]:
        a = ["(" if i % 2 == 0 else "" for i in range(self.height)]
        b = [" )" if i % 2 == 0 else "" for i in range(self.height)]
        frame1 = [s.ljust(2) for s in a]
        frame2 = [s.ljust(2) for s in b]
        return frame1, frame2

    def draw(self, screen: Screen, tick: int, mono: bool = False):
        f1, f2 = self.frames()
        sway = ((tick) + self.phase) % 2
        rows = f1 if sway == 0 else f2
        for i, row in enumerate(rows):
            y = self.base_y - (self.height - 1 - i)
            if 0 <= y < screen.height:
                screen.print_at(row, self.x, y, colour=Screen.COLOUR_WHITE if mono else Screen.COLOUR_GREEN)


@dataclass
class Bubble:
    x: int
    y: int
    lifetime: float = 0

    def update(self, dt: float):
        self.lifetime += dt
        self.y -= max(1, int(10 * dt))

    def draw(self, screen: Screen):
        if 0 <= self.y < screen.height:
            ch = random.choice([".", "o", "O"])
            screen.print_at(ch, self.x, self.y, colour=Screen.COLOUR_CYAN)


@dataclass
class Splat:
    x: int
    y: int
    age_frames: int = 0
    max_frames: int = 15

    FRAMES: List[List[str]] = field(
        default_factory=lambda: [
            parse_sprite(
                r"""

   .
  ***
   '

"""
            ),
            parse_sprite(
                r"""

 ",*;`
 "*,**
 *"'~'

"""
            ),
            parse_sprite(
                r"""
  , ,
 " ","'
 *" *'"
  " ; .

"""
            ),
            parse_sprite(
                r"""
* ' , ' `
' ` * . '
 ' `' ",'
* ' " * .
" * ', '
"""
            ),
        ]
    )

    def update(self):
        self.age_frames += 1

    @property
    def active(self) -> bool:
        return self.age_frames < self.max_frames

    def draw(self, screen: Screen, mono: bool = False):
        idx = min(len(self.FRAMES) - 1, self.age_frames // 4)
        lines = self.FRAMES[idx]
        draw_sprite(screen, lines, self.x - 4, self.y - 2, Screen.COLOUR_WHITE if mono else Screen.COLOUR_RED)


@dataclass
class Fish:
    frames: List[str]
    x: float
    y: float
    vx: float
    colour: int
    next_bubble: float = field(default_factory=lambda: random.uniform(1.5, 4.0))

    @property
    def width(self) -> int:
        return max(len(r) for r in self.frames)

    @property
    def height(self) -> int:
        return len(self.frames)

    def update(self, dt: float, screen: Screen, bubbles: List[Bubble]):
        self.x += self.vx * dt * 20.0
        self.next_bubble -= dt
        if self.next_bubble <= 0:
            by = int(self.y + self.height // 2)
            bx = int(self.x + (self.width if self.vx > 0 else -1))
            bubbles.append(Bubble(x=bx, y=by))
            self.next_bubble = random.uniform(2.0, 5.0)
        if self.vx > 0 and self.x > screen.width:
            self.respawn(screen, direction=1)
        elif self.vx < 0 and self.x + self.width < 0:
            self.respawn(screen, direction=-1)

    def respawn(self, screen: Screen, direction: int):
        self.frames = random_fish_frames(direction)
        self.vx = random.uniform(0.6, 2.5) * direction
        self.y = random.randint(max(9, 1), max(9, screen.height - self.height - 2))
        self.x = -self.width if direction > 0 else screen.width

    def draw(self, screen: Screen):
        draw_sprite(screen, self.frames, int(self.x), int(self.y), self.colour)

    hooked: bool = False
    hook_dx: int = 0
    hook_dy: int = 0

    def attach_to_hook(self, hook_x: int, hook_y: int):
        self.hooked = True
        self.hook_dx = int(self.x) - hook_x
        self.hook_dy = int(self.y) - hook_y
        self.vx = 0.0

    def follow_hook(self, hook_x: int, hook_y: int):
        if self.hooked:
            self.x = hook_x + self.hook_dx
            self.y = hook_y + self.hook_dy


class AsciiQuarium:
    def __init__(self, settings: "Settings"):
        self.settings = settings
        self.seaweed: List[Seaweed] = []
        self.fish: List[Fish] = []
        self.bubbles: List[Bubble] = []
        self.splats: List[Splat] = []
        self.specials: List["Actor"] = []
        self._paused = False
        self._special_timer = random.uniform(3.0, 8.0)
        self._show_help = False
        self._seaweed_tick = 0

    def rebuild(self, screen: Screen):
        self.seaweed.clear()
        self.fish.clear()
        self.bubbles.clear()
        self.splats.clear()
        self.specials.clear()
        self._special_timer = random.uniform(3.0, 8.0)
        self._seaweed_tick = 0

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
        tiled = []
        seg_len = len(WATER_SEGMENTS[0])
        repeat = screen.width // seg_len + 2
        for seg in WATER_SEGMENTS:
            tiled.append((seg * repeat)[: screen.width])
        for i, row in enumerate(tiled):
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

        self.draw_waterline(screen)
        self.draw_castle(screen)
        mono = self.settings.color == "mono"
        for s in self.seaweed:
            tick = int(self._seaweed_tick / 0.25)
            s.draw(screen, tick, mono)
        for f in self.fish:
            if self.settings.color == "mono":
                draw_sprite(screen, f.frames, int(f.x), int(f.y), Screen.COLOUR_WHITE)
            else:
                f.draw(screen)
        for b in self.bubbles:
            if self.settings.color == "mono":
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


@dataclass
class Settings:
    fps: int = 20
    density: float = 1.0
    color: str = "auto"
    seed: Optional[int] = None
    speed: float = 0.75


def _find_config_paths() -> List[Path]:
    paths: List[Path] = []
    cwd = Path.cwd()
    paths.append(cwd / ".asciiquarium.toml")
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        paths.append(Path(xdg) / "asciiquarium-redux" / "config.toml")
    home = Path.home()
    paths.append(home / ".config" / "asciiquarium-redux" / "config.toml")
    return [p for p in paths if p.exists()]


def _load_toml(path: Path) -> dict:
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def load_settings_from_sources(argv: Optional[List[str]] = None) -> Settings:
    s = Settings()
    for p in _find_config_paths():
        data = _load_toml(p)
        render = data.get("render", {})
        scene = data.get("scene", {})
        if "fps" in render:
            s.fps = int(render.get("fps", s.fps))
        if "color" in render:
            s.color = str(render.get("color", s.color))
        if "density" in scene:
            try:
                s.density = float(scene.get("density", s.density))
            except Exception:
                pass
        if "seed" in scene:
            seed_val = scene.get("seed")
            if isinstance(seed_val, int):
                s.seed = seed_val
            elif isinstance(seed_val, str) and seed_val.lower() == "random":
                s.seed = None
        if "speed" in scene:
            try:
                s.speed = float(scene.get("speed", s.speed))
            except Exception:
                pass
        break
    parser = argparse.ArgumentParser(description="Asciiquarium Redux")
    parser.add_argument("--fps", type=int)
    parser.add_argument("--density", type=float)
    parser.add_argument("--color", choices=["auto", "mono", "16", "256"])
    parser.add_argument("--seed", type=int)
    parser.add_argument("--speed", type=float)
    args = parser.parse_args(argv)

    if args.fps is not None:
        s.fps = max(5, min(120, args.fps))
    if args.density is not None:
        s.density = max(0.1, min(5.0, args.density))
    if args.color is not None:
        s.color = args.color
    if args.seed is not None:
        s.seed = args.seed
    if args.speed is not None:
        s.speed = max(0.1, min(3.0, args.speed))
    return s


class Actor:
    def update(self, dt: float, screen: Screen, app: "AsciiQuarium") -> None: ...
    def draw(self, screen: Screen, mono: bool = False) -> None: ...
    @property
    def active(self) -> bool: ...


class Shark(Actor):
    def __init__(self, screen: Screen, app: "AsciiQuarium"):
        self.dir = random.choice([-1, 1])
        self.speed = 2.0 * self.dir
        self.y = random.randint(max(9, 1), max(9, screen.height - 10))
        self.frame = parse_sprite(r"""
  __     __
 (  `-._/  )
  \   o  _/
  /  __  \
 /__/  \__\
""")
        self.w, self.h = sprite_size(self.frame)
        self.x = -self.w if self.dir > 0 else screen.width
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app: "AsciiQuarium") -> None:
        self.x += self.speed * dt * 20.0
        for f in list(app.fish):
            if f.hooked:
                continue
            if aabb_overlap(int(self.x), int(self.y), self.w, self.h, int(f.x), int(f.y), f.width, f.height):
                app.splats.append(Splat(x=int(f.x + f.width // 2), y=int(f.y + f.height // 2)))
                app.fish.remove(f)
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        if self.dir > 0:
            draw_sprite(screen, self.frame, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            mirrored = [line[::-1] for line in self.frame]
            draw_sprite(screen, mirrored, int(self.x), int(self.y), Screen.COLOUR_WHITE)


class FishHook(Actor):
    def __init__(self, screen: Screen, app: "AsciiQuarium"):
        self.x = random.randint(10, max(11, screen.width - 10))
        self.y = -4
        self.state = "lowering"
        self.speed = 15.0
        self.caught: Fish | None = None
        self._active = True

    @property
    def active(self) -> bool:
        return True if self._active else False

    def update(self, dt: float, screen: Screen, app: "AsciiQuarium") -> None:
        if self.state == "lowering":
            if self.y + 6 < int(screen.height * 0.75):
                self.y += self.speed * dt
                hx = int(self.x + 1)
                hy = int(self.y + 2)
                for f in app.fish:
                    if f.hooked:
                        continue
                    if aabb_overlap(hx, hy, 1, 1, int(f.x), int(f.y), f.width, f.height):
                        self.caught = f
                        f.attach_to_hook(hx, hy)
                        self.state = "retracting"
                        break
            else:
                self.state = "retracting"
        else:
            self.y -= self.speed * dt
            hx = int(self.x + 1)
            hy = int(self.y + 2)
            if self.caught:
                self.caught.follow_hook(hx, hy)
            if self.y <= 0:
                if self.caught and self.caught in app.fish:
                    app.fish.remove(self.caught)
                self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        top = -50
        line_len = int(self.y) - top
        for i in range(line_len):
            ly = top + i
            if 0 <= ly < screen.height:
                screen.print_at("|", self.x + 7, ly, colour=Screen.COLOUR_WHITE if mono else Screen.COLOUR_GREEN)
        hook = parse_sprite(
            r"""
       o
      ||
      ||
/ \   ||
  \__//
  `--'
"""
        )
        draw_sprite(screen, hook, self.x, int(self.y), Screen.COLOUR_WHITE if mono else Screen.COLOUR_GREEN)


class Whale(Actor):
    def __init__(self, screen: Screen, app: "AsciiQuarium"):
        self.dir = random.choice([-1, 1])
        self.speed = 10.0 * self.dir
        self.x = -18 if self.dir > 0 else screen.width
        self.y = 0
        self.base = parse_sprite(
            r"""
        .-----:
      .'       `.
 / (o)       \
(__,          \_.'
"""
        )
        self.w, self.h = sprite_size(self.base)
        self.spout_frame = 0
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app: "AsciiQuarium") -> None:
        self.x += self.speed * dt / 2
        self.spout_frame = (self.spout_frame + 1) % 20
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        if self.spout_frame < 10:
            sp = ["   :", "   :", "  . .", " .-:-."]
            for i, row in enumerate(sp[: max(0, self.spout_frame // 3)]):
                colour = Screen.COLOUR_WHITE if mono else Screen.COLOUR_CYAN
                screen.print_at(row, int(self.x) + (1 if self.dir > 0 else 11), i, colour=colour)
        img = self.base if self.dir > 0 else [line[::-1] for line in self.base]
        draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)


class Ducks(Actor):
    def __init__(self, screen: Screen, app: "AsciiQuarium"):
        self.dir = random.choice([-1, 1])
        self.speed = 10.0 * self.dir
        self.x = -30 if self.dir > 0 else screen.width
        self.y = 5
        self.frame_a = parse_sprite(r"""
      _  _  _
,____(')=,____(')=,____(')<
 \~~= ')  \~~= ')  \~~= ')
""")
        self.w, self.h = sprite_size(self.frame_a)
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app: "AsciiQuarium") -> None:
        self.x += self.speed * dt
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.frame_a if self.dir > 0 else [line[::-1] for line in self.frame_a]
        draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE if mono else Screen.COLOUR_YELLOW)


class Dolphins(Actor):
    def __init__(self, screen: Screen, app: "AsciiQuarium"):
        self.dir = random.choice([-1, 1])
        self.speed = 20.0 * self.dir
        self.x = -13 if self.dir > 0 else screen.width
        self.base_y = 5
        self.t = 0.0
        self.distance = 15 * self.dir
        self.dolph = parse_sprite(
            r"""
     ,
   _/(__
.-'a    `-._/)
'^^~\)''''~~\)
"""
        )
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app: "AsciiQuarium") -> None:
        self.t += dt
        self.x += self.speed * dt
        if (self.dir > 0 and self.x > screen.width + 30) or (self.dir < 0 and self.x < -30):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        for i in range(3):
            px = int(self.x + i * self.distance)
            py = int(self.base_y + 3 * math.sin((self.t * 2 + i) * 1.2))
            img = self.dolph if self.dir > 0 else [line[::-1] for line in self.dolph]
            draw_sprite(screen, img, px, py, Screen.COLOUR_WHITE if mono else Screen.COLOUR_CYAN)


class Swan(Actor):
    def __init__(self, screen: Screen, app: "AsciiQuarium"):
        self.dir = random.choice([-1, 1])
        self.speed = 10.0 * self.dir
        self.x = -10 if self.dir > 0 else screen.width
        self.y = 1
        self.img = parse_sprite(
            r"""
       ___
,_    / _,\
| \   \\ \|
|  \_  \\\\
(_   \_) \
(\_   `   \
 \   -=~  /
"""
        )
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app: "AsciiQuarium") -> None:
        self.x += self.speed * dt
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + 10 < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.img if self.dir > 0 else [line[::-1] for line in self.img]
        draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)


class Monster(Actor):
    def __init__(self, screen: Screen, app: "AsciiQuarium"):
        self.dir = random.choice([-1, 1])
        self.speed = 15.0 * self.dir
        self.x = -40 if self.dir > 0 else screen.width
        self.y = 2
        self.img = parse_sprite(
            r"""
   ____
 _/ o  \____
/  __       \
\_/  \_______)
"""
        )
        self.w, self.h = sprite_size(self.img)
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app: "AsciiQuarium") -> None:
        self.x += self.speed * dt
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.img if self.dir > 0 else [line[::-1] for line in self.img]
        draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE if mono else Screen.COLOUR_GREEN)


class Ship(Actor):
    def __init__(self, screen: Screen, app: "AsciiQuarium"):
        self.dir = random.choice([-1, 1])
        self.speed = 10.0 * self.dir
        self.x = -24 if self.dir > 0 else screen.width
        self.y = 0
        self.img = parse_sprite(
            r"""
     |    |    |
    )_)  )_)  )_)
   )___))___))___)\
  )____)____)_____)\\\
_____|____|____|____\\\\\__
\                   /
"""
        )
        self.w, self.h = sprite_size(self.img)
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app: "AsciiQuarium") -> None:
        self.x += self.speed * dt
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.img if self.dir > 0 else [line[::-1] for line in self.img]
        draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)


ActorType = Actor  # alias for hints


def spawn_shark(screen: Screen, app: "AsciiQuarium") -> List[ActorType]:
    return [Shark(screen, app)]


def spawn_fishhook(screen: Screen, app: "AsciiQuarium") -> List[ActorType]:
    return [FishHook(screen, app)]


def spawn_whale(screen: Screen, app: "AsciiQuarium") -> List[ActorType]:
    return [Whale(screen, app)]


def spawn_ducks(screen: Screen, app: "AsciiQuarium") -> List[ActorType]:
    return [Ducks(screen, app)]


def spawn_dolphins(screen: Screen, app: "AsciiQuarium") -> List[ActorType]:
    return [Dolphins(screen, app)]


def spawn_swan(screen: Screen, app: "AsciiQuarium") -> List[ActorType]:
    return [Swan(screen, app)]


def spawn_monster(screen: Screen, app: "AsciiQuarium") -> List[ActorType]:
    return [Monster(screen, app)]


def spawn_ship(screen: Screen, app: "AsciiQuarium") -> List[ActorType]:
    return [Ship(screen, app)]


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
