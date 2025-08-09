from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import List, Tuple

from asciimatics.screen import Screen
import math


# ------------------------------
# Simple helpers
# ------------------------------


def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def parse_sprite(s: str) -> List[str]:
    lines = s.splitlines()
    # Drop leading/trailing empty lines introduced by triple quotes
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
        # Clip left/right
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


# ------------------------------
# Environment sprites & data
# ------------------------------


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


# Minimal fish set (subset of originals)
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


def random_fish_frames(direction: int) -> List[List[str]]:
    # direction: +1 => right, -1 => left
    return random.choice(FISH_RIGHT if direction > 0 else FISH_LEFT)


# ------------------------------
# Entities
# ------------------------------


@dataclass
class Seaweed:
    x: int
    base_y: int
    height: int
    phase: int

    def frames(self) -> Tuple[List[str], List[str]]:
        left = []
        right = []
        for i in range(self.height):
            if i % 2 == 0:
                left.append("(")
                right.append(" )")
            else:
                left.append("")
                right.append("")
        # Normalize to same height with spaces
        maxw = max(len("".join(left)), len("\n".join(right)))
        a = ["(" if i % 2 == 0 else "" for i in range(self.height)]
        b = [" )" if i % 2 == 0 else "" for i in range(self.height)]
        frame1 = [s.ljust(2) for s in a]
        frame2 = [s.ljust(2) for s in b]
        return frame1, frame2

    def draw(self, screen: Screen, frame_no: int):
        f1, f2 = self.frames()
        sway = ((frame_no // 4) + self.phase) % 2
        rows = f1 if sway == 0 else f2
        for i, row in enumerate(rows):
            y = self.base_y - (self.height - 1 - i)
            if 0 <= y < screen.height:
                screen.print_at(row, self.x, y, colour=Screen.COLOUR_GREEN)


@dataclass
class Bubble:
    x: int
    y: int
    lifetime: float = 0

    def update(self, dt: float):
        self.lifetime += dt
        # Rise up at ~10 chars per second
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

    def draw(self, screen: Screen):
        idx = min(len(self.FRAMES) - 1, self.age_frames // 4)
        lines = self.FRAMES[idx]
        draw_sprite(screen, lines, self.x - 4, self.y - 2, Screen.COLOUR_RED)


@dataclass
class Fish:
    frames: List[List[str]]
    x: int
    y: int
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
        self.x += self.vx * dt * 20.0  # speed tuning
        self.next_bubble -= dt
        if self.next_bubble <= 0:
            # Place bubble near mid-height at trailing or leading edge depending on direction
            by = int(self.y + self.height // 2)
            bx = int(self.x + (self.width if self.vx > 0 else -1))
            bubbles.append(Bubble(x=bx, y=by))
            self.next_bubble = random.uniform(2.0, 5.0)

        # Respawn when fully offscreen
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

    # Hooking support
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


# ------------------------------
# Main application
# ------------------------------


class AsciiQuarium:
    def __init__(self):
        self.seaweed: List[Seaweed] = []
        self.fish: List[Fish] = []
        self.bubbles: List[Bubble] = []
        self.splats: List[Splat] = []
        self.specials: List["Actor"] = []
        self._paused = False
        self._special_timer = random.uniform(3.0, 8.0)

    def rebuild(self, screen: Screen):
        self.seaweed.clear()
        self.fish.clear()
        self.bubbles.clear()
        self.splats.clear()
        self.specials.clear()
        self._special_timer = random.uniform(3.0, 8.0)

        # Seaweed density
        count = max(3, screen.width // 15)
        for _ in range(count):
            h = random.randint(3, 6)
            x = random.randint(1, max(1, screen.width - 3))
            base_y = screen.height - 2
            self.seaweed.append(Seaweed(x=x, base_y=base_y, height=h, phase=random.randint(0, 1)))

        # Fish count proportional to area under waterline
        water_top = 5
        area = max(1, (screen.height - (water_top + 4)) * screen.width)
        fcount = max(4, area // 350)
        colours = [
            Screen.COLOUR_CYAN,
            Screen.COLOUR_YELLOW,
            Screen.COLOUR_GREEN,
            Screen.COLOUR_RED,
            Screen.COLOUR_MAGENTA,
            Screen.COLOUR_BLUE,
            Screen.COLOUR_WHITE,
        ]
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
        # Tile segments to cover width
        tiled = []
        seg_len = len(WATER_SEGMENTS[0])
        repeat = screen.width // seg_len + 2
        for seg in WATER_SEGMENTS:
            tiled.append((seg * repeat)[: screen.width])
        # Place at y offsets similar to original (starting at 5)
        for i, row in enumerate(tiled):
            y = 5 + i
            if y < screen.height:
                screen.print_at(row, 0, y, colour=Screen.COLOUR_CYAN)

    def draw_castle(self, screen: Screen):
        lines = CASTLE
        w, h = sprite_size(lines)
        x = max(0, screen.width - w - 2)
        y = max(0, screen.height - h - 1)
        draw_sprite(screen, lines, x, y, Screen.COLOUR_WHITE)

    def update(self, dt: float, screen: Screen, frame_no: int):
        # Update entities
        if not self._paused:
            for f in self.fish:
                f.update(dt, screen, self.bubbles)
            # Update bubbles and cull
            for b in self.bubbles:
                b.update(dt)
            # Bubbles pop at waterline (~y <= 6)
            self.bubbles = [b for b in self.bubbles if b.y > 6]
            # Specials update & cull
            for a in list(self.specials):
                a.update(dt, screen, self)
            self.specials = [a for a in self.specials if getattr(a, "active", True)]
            # Splats age
            for s in self.splats:
                s.update()
            self.splats = [s for s in self.splats if s.active]

            # Maybe spawn a new special if none present
            if not self.specials:
                self._special_timer -= dt
                if self._special_timer <= 0:
                    self.spawn_random(screen)
                    self._special_timer = random.uniform(8.0, 20.0)

        # Draw in depth order: waterline -> castle -> seaweed -> fish -> bubbles -> splats -> specials
        self.draw_waterline(screen)
        self.draw_castle(screen)
        for s in self.seaweed:
            s.draw(screen, frame_no)
        for f in self.fish:
            f.draw(screen)
        for b in self.bubbles:
            b.draw(screen)
        for s in self.splats:
            s.draw(screen)

        # Update specials draw last (foreground)
        for a in list(self.specials):
            a.draw(screen)

    # Random event spawner
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


# ------------------------------
# Actor base class & concrete actors
# ------------------------------


class Actor:
    def update(self, dt: float, screen: Screen, app: "AsciiQuarium") -> None: ...
    def draw(self, screen: Screen) -> None: ...
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
        # Collide with fish
        for f in list(app.fish):
            if f.hooked:
                continue
            if aabb_overlap(int(self.x), int(self.y), self.w, self.h, int(f.x), int(f.y), f.width, f.height):
                app.splats.append(Splat(x=int(f.x + f.width // 2), y=int(f.y + f.height // 2)))
                app.fish.remove(f)
        # Deactivate when offscreen
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen) -> None:
        # Mirror for left by reversing lines
        if self.dir > 0:
            draw_sprite(screen, self.frame, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            mirrored = [line[::-1] for line in self.frame]
            draw_sprite(screen, mirrored, int(self.x), int(self.y), Screen.COLOUR_WHITE)


class FishHook(Actor):
    def __init__(self, screen: Screen, app: "AsciiQuarium"):
        self.x = random.randint(10, max(11, screen.width - 10))
        self.y = -4
        self.state = "lowering"  # lowering|retracting
        self.speed = 15.0
        self.caught: Fish | None = None
        self._active = True

    @property
    def active(self) -> bool:
        return _bool(self._active)

    def update(self, dt: float, screen: Screen, app: "AsciiQuarium") -> None:
        if self.state == "lowering":
            # Stop at 3/4 depth or until catch happens
            if self.y + 6 < int(screen.height * 0.75):
                self.y += self.speed * dt
                # Try to catch a fish
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
            # Retract upwards
            self.y -= self.speed * dt
            hx = int(self.x + 1)
            hy = int(self.y + 2)
            if self.caught:
                self.caught.follow_hook(hx, hy)
            if self.y <= 0:
                # Remove hooked fish at surface
                if self.caught and self.caught in app.fish:
                    app.fish.remove(self.caught)
                self._active = False

    def draw(self, screen: Screen) -> None:
        # Draw line from top to hook
        top = -50
        line_len = int(self.y) - top
        for i in range(line_len):
            ly = top + i
            if 0 <= ly < screen.height:
                screen.print_at("|", self.x + 7, ly, colour=Screen.COLOUR_GREEN)
        # Draw hook
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
        draw_sprite(screen, hook, self.x, int(self.y), Screen.COLOUR_GREEN)


def _bool(v: bool) -> bool:
    return True if v else False


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
        self.x += self.speed * dt / 2  # slow whale
        self.spout_frame = (self.spout_frame + 1) % 20
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen) -> None:
        # Spout every few frames
        if self.spout_frame < 10:
            sp = ["   :", "   :", "  . .", " .-:-."]
            for i, row in enumerate(sp[: max(0, self.spout_frame // 3)]):
                screen.print_at(row, int(self.x) + (1 if self.dir > 0 else 11), i, colour=Screen.COLOUR_CYAN)
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

    def draw(self, screen: Screen) -> None:
        img = self.frame_a if self.dir > 0 else [line[::-1] for line in self.frame_a]
        draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_YELLOW)


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

    def draw(self, screen: Screen) -> None:
        for i in range(3):
            px = int(self.x + i * self.distance)
            py = int(self.base_y + 3 * math.sin((self.t * 2 + i) * 1.2))
            img = self.dolph if self.dir > 0 else [line[::-1] for line in self.dolph]
            draw_sprite(screen, img, px, py, Screen.COLOUR_CYAN)


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

    def draw(self, screen: Screen) -> None:
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

    def draw(self, screen: Screen) -> None:
        img = self.img if self.dir > 0 else [line[::-1] for line in self.img]
        draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_GREEN)


# Spawner helpers
def spawn_shark(screen: Screen, app: "AsciiQuarium") -> List[Actor]:
    return [Shark(screen, app)]


def spawn_fishhook(screen: Screen, app: "AsciiQuarium") -> List[Actor]:
    return [FishHook(screen, app)]


def spawn_whale(screen: Screen, app: "AsciiQuarium") -> List[Actor]:
    return [Whale(screen, app)]


def spawn_ducks(screen: Screen, app: "AsciiQuarium") -> List[Actor]:
    return [Ducks(screen, app)]


def spawn_dolphins(screen: Screen, app: "AsciiQuarium") -> List[Actor]:
    return [Dolphins(screen, app)]


def spawn_swan(screen: Screen, app: "AsciiQuarium") -> List[Actor]:
    return [Swan(screen, app)]


def spawn_monster(screen: Screen, app: "AsciiQuarium") -> List[Actor]:
    return [Monster(screen, app)]


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

    def draw(self, screen: Screen) -> None:
        img = self.img if self.dir > 0 else [line[::-1] for line in self.img]
        draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)


def spawn_ship(screen: Screen, app: "AsciiQuarium") -> List[Actor]:
    return [Ship(screen, app)]


def run(screen: Screen):
    app = AsciiQuarium()
    app.rebuild(screen)

    last = time.time()
    frame_no = 0

    while True:
        now = time.time()
        dt = min(0.1, now - last)  # cap delta to avoid big jumps
        last = now

        # Input
        ev = screen.get_key()
        if ev in (ord("q"), ord("Q")):
            return
        if ev in (ord("p"), ord("P")):
            app._paused = not app._paused
        if ev in (ord("r"), ord("R")):
            app.rebuild(screen)

        screen.clear()
        app.update(dt, screen, frame_no)
        screen.refresh()
        frame_no += 1

        # Try to target ~20 FPS
        time.sleep(0.05)


if __name__ == "__main__":
    Screen.wrapper(run)
