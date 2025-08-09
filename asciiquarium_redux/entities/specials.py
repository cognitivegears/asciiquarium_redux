from __future__ import annotations

import random
import math
from typing import List
from dataclasses import dataclass
from asciimatics.screen import Screen

from ..util import parse_sprite, sprite_size, draw_sprite, aabb_overlap
from .core import Splat, Fish
from .base import Actor


class Shark(Actor):
    def __init__(self, screen: Screen, app):
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

    def update(self, dt: float, screen: Screen, app) -> None:
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
    def __init__(self, screen: Screen, app):
        self.x = random.randint(10, max(11, screen.width - 10))
        self.y = -4
        self.state = "lowering"
        self.speed = 15.0
        self.caught: Fish | None = None
        self._active = True

    @property
    def active(self) -> bool:
        return True if self._active else False

    def update(self, dt: float, screen: Screen, app) -> None:
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
    def __init__(self, screen: Screen, app):
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

    def update(self, dt: float, screen: Screen, app) -> None:
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
    def __init__(self, screen: Screen, app):
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

    def update(self, dt: float, screen: Screen, app) -> None:
        self.x += self.speed * dt
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.frame_a if self.dir > 0 else [line[::-1] for line in self.frame_a]
        draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE if mono else Screen.COLOUR_YELLOW)


class Dolphins(Actor):
    def __init__(self, screen: Screen, app):
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

    def update(self, dt: float, screen: Screen, app) -> None:
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
    def __init__(self, screen: Screen, app):
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

    def update(self, dt: float, screen: Screen, app) -> None:
        self.x += self.speed * dt
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + 10 < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.img if self.dir > 0 else [line[::-1] for line in self.img]
        draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)


class Monster(Actor):
    def __init__(self, screen: Screen, app):
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

    def update(self, dt: float, screen: Screen, app) -> None:
        self.x += self.speed * dt
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.img if self.dir > 0 else [line[::-1] for line in self.img]
        draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE if mono else Screen.COLOUR_GREEN)


class Ship(Actor):
    def __init__(self, screen: Screen, app):
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

    def update(self, dt: float, screen: Screen, app) -> None:
        self.x += self.speed * dt
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.img if self.dir > 0 else [line[::-1] for line in self.img]
        draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)


# Spawner helpers
def spawn_shark(screen: Screen, app) -> List[Actor]:
    return [Shark(screen, app)]


def spawn_fishhook(screen: Screen, app) -> List[Actor]:
    return [FishHook(screen, app)]


def spawn_whale(screen: Screen, app) -> List[Actor]:
    return [Whale(screen, app)]


def spawn_ducks(screen: Screen, app) -> List[Actor]:
    return [Ducks(screen, app)]


def spawn_dolphins(screen: Screen, app) -> List[Actor]:
    return [Dolphins(screen, app)]


def spawn_swan(screen: Screen, app) -> List[Actor]:
    return [Swan(screen, app)]


def spawn_monster(screen: Screen, app) -> List[Actor]:
    return [Monster(screen, app)]


def spawn_ship(screen: Screen, app) -> List[Actor]:
    return [Ship(screen, app)]
