from __future__ import annotations

import random
import math
from typing import List
from dataclasses import dataclass
from asciimatics.screen import Screen

from ..util import parse_sprite, sprite_size, draw_sprite, draw_sprite_masked, aabb_overlap, randomize_colour_mask
from .core import Splat, Fish
from .base import Actor


class Shark(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 2.0 * self.dir
        self.y = random.randint(max(9, 1), max(9, screen.height - 10))
        self.frame = parse_sprite(
            r"""
  __     __
 (  `-._/  )
  \   o  _/
  /  __  \
 /__/  \__\
"""
        )
        self.w, self.h = sprite_size(self.frame)
        self.x = -self.w if self.dir > 0 else screen.width
        # Mask: default white
        self.mask = ["W" * len(row) for row in self.frame]
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
        img = self.frame if self.dir > 0 else [line[::-1] for line in self.frame]
        msk = self.mask if self.dir > 0 else [line[::-1] for line in self.mask]
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            draw_sprite_masked(screen, img, msk, int(self.x), int(self.y), Screen.COLOUR_WHITE)


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
        self.mask = parse_sprite(
            r"""
                         C C
                     CCCCCCC
                     C  C  C
                BBBBBBB
            BB       BB
B    B       BWB B
BBBBB          BBBB
"""
        )
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
        msk = self.mask if self.dir > 0 else [line[::-1] for line in self.mask]
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            draw_sprite_masked(screen, img, msk, int(self.x), int(self.y), Screen.COLOUR_WHITE)


class Ducks(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 10.0 * self.dir
        self.x = -30 if self.dir > 0 else screen.width
        self.y = 5
        ducks_lr = [
            parse_sprite(
                r"""
      _  _  _
,____(')=,____(')=,____(')<
 \~~= ')  \~~= ')  \~~= ')
"""
            ),
            parse_sprite(
                r"""
      _  _  _
,____(')=,____(')<,____(')=
 \~~= ')  \~~= ')  \~~= ')
"""
            ),
            parse_sprite(
                r"""
      _  _  _
,____(')<,____(')=,____(')=
 \~~= ')  \~~= ')  \~~= ')
"""
            ),
        ]
        ducks_rl = [
            parse_sprite(
                r"""
  _  _  _
>(')____,=(')____,=(')____,
 (` =~~/  (` =~~/  (` =~~/
"""
            ),
            parse_sprite(
                r"""
  _  _  _
=(')____,>(')____,=(')____,
 (` =~~/  (` =~~/  (` =~~/
"""
            ),
            parse_sprite(
                r"""
  _  _  _
=(')____,=(')____,>(')____,
 (` =~~/  (` =~~/  (` =~~/
"""
            ),
        ]
        self.frames = ducks_lr if self.dir > 0 else ducks_rl
        duck_mask_lr = parse_sprite(
            r"""
      g          g          g
wwwwwgcgy  wwwwwgcgy  wwwwwgcgy
 wwww Ww    wwww Ww    wwww Ww
"""
        )
        duck_mask_rl = parse_sprite(
            r"""
  g          g          g
ygcgwwwww  ygcgwwwww  ygcgwwwww
 wW wwww    wW wwww    wW wwww
"""
        )
        self.mask = duck_mask_lr if self.dir > 0 else duck_mask_rl
        w_list = [sprite_size(f)[0] for f in self.frames]
        h_list = [sprite_size(f)[1] for f in self.frames]
        self.w, self.h = max(w_list), max(h_list)
        self._frame_idx = 0
        self._frame_t = 0.0
        self._frame_dt = 0.25
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app) -> None:
        self.x += self.speed * dt
        self._frame_t += dt
        if self._frame_t >= self._frame_dt:
            self._frame_t = 0.0
            self._frame_idx = (self._frame_idx + 1) % len(self.frames)
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.frames[self._frame_idx]
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            draw_sprite_masked(screen, img, self.mask, int(self.x), int(self.y), Screen.COLOUR_YELLOW)


class Dolphins(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 20.0 * self.dir
        self.x = -13 if self.dir > 0 else screen.width
        self.base_y = 5
        self.t = 0.0
        self.distance = 15 * self.dir
        dolph_lr = [
            parse_sprite(
                r"""
     ,
   _/(__
.-'a    `-._/)
'^^~\)''''~~\)
"""
            ),
            parse_sprite(
                r"""
     ,
   _/(__  __/)
.-'a    ``.~\)
'^^~(/''''
"""
            ),
        ]
        dolph_rl = [
            parse_sprite(
                r"""
        ,
      __)\_
(\_.-'    a`-.
(/~~````(/~^^`
"""
            ),
            parse_sprite(
                r"""
        ,
(\__  __)\_
(/~.''    a`-.
    ````\)~^^`
"""
            ),
        ]
        self.frames = dolph_lr if self.dir > 0 else dolph_rl
        # Masks from Perl: left-to-right has W far right; right-to-left has W near left
        if self.dir > 0:
            self.mask = parse_sprite(
                r"""


          W
"""
            )
        else:
            self.mask = parse_sprite(
                r"""


   W
"""
            )
        self._frame_idx = 0
        self._frame_t = 0.0
        self._frame_dt = 0.25
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app) -> None:
        self.t += dt
        self.x += self.speed * dt
        self._frame_t += dt
        if self._frame_t >= self._frame_dt:
            self._frame_t = 0.0
            self._frame_idx = (self._frame_idx + 1) % len(self.frames)
        if (self.dir > 0 and self.x > screen.width + 30) or (self.dir < 0 and self.x < -30):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        for i in range(3):
            frame = self.frames[(self._frame_idx + i) % len(self.frames)]
            px = int(self.x + i * self.distance)
            py = int(self.base_y + 3 * math.sin((self.t * 2 + i) * 1.2))
            if mono:
                draw_sprite(screen, frame, px, py, Screen.COLOUR_WHITE)
            else:
                draw_sprite_masked(screen, frame, self.mask, px, py, Screen.COLOUR_CYAN)


class Swan(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 10.0 * self.dir
        self.x = -10 if self.dir > 0 else screen.width
        self.y = 1
        swan_lr = [
            parse_sprite(
                r"""
       ___
,_    / _,\
| \   \\ \|
|  \_  \\\
(_   \_) \
(\_   `   \
 \   -=~  /
"""
            ),
            parse_sprite(
                r"""
       ___
,_    / _,\
| \   \\  \
|  \_  \\\
(_   \_) \
(\_   `   \
 \  ~=-  /
"""
            ),
        ]
        swan_rl = [
            parse_sprite(
                r"""
 ___
/,_ \    _,
|/ )/   / |
  //  _/  |
 / ( /   _)
/   `   _/)
\  ~=-   /
"""
            ),
            parse_sprite(
                r"""
 ___
/,_ \    _,
|/ )/   / |
  //  _/  |
 / ( /   _)
/   `   _/)
\   -=~  /
"""
            ),
        ]
        self.frames = swan_lr if self.dir > 0 else swan_rl
        self.mask = parse_sprite(
            r"""

     g
     yy
"""
        ) if self.dir > 0 else parse_sprite(
            r"""

 g
yy
"""
        )
        self._frame_idx = 0
        self._frame_t = 0.0
        self._frame_dt = 0.25
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app) -> None:
        self.x += self.speed * dt
        self._frame_t += dt
        if self._frame_t >= self._frame_dt:
            self._frame_t = 0.0
            self._frame_idx = (self._frame_idx + 1) % len(self.frames)
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + 10 < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.frames[self._frame_idx]
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            draw_sprite_masked(screen, img, self.mask, int(self.x), int(self.y), Screen.COLOUR_WHITE)


class Monster(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 15.0 * self.dir
        self.x = -64 if self.dir > 0 else screen.width
        self.y = 2
        self.frames = [
            parse_sprite(
                r"""
   ____
 _/ o  \____
/  __       \
\_/  \_______)
"""
            ),
            parse_sprite(
                r"""
   ____
 _/ O  \____
/  __       \
\_/  \______)
"""
            ),
            parse_sprite(
                r"""
   ____
 _/ o  \____
/  __       \
\_/  \_______)
"""
            ),
            parse_sprite(
                r"""
   ____
 _/ .  \____
/  __       \
\_/  \______)
"""
            ),
        ]
        w_list = [sprite_size(f)[0] for f in self.frames]
        h_list = [sprite_size(f)[1] for f in self.frames]
        self.w, self.h = max(w_list), max(h_list)
        # Build a simple mask indicating a white eye (W); body picks up default green
        self.mask_frames = []
        for fr in self.frames:
            m = []
            for row in fr:
                # mark the eye character 'o' / 'O' / '.' as white; else space to use default
                m.append(''.join('W' if ch in ('o','O','.') else ' ' for ch in row))
            self.mask_frames.append(m)
        self._frame_idx = 0
        self._frame_t = 0.0
        self._frame_dt = 0.25
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app) -> None:
        self.x += self.speed * dt
        self._frame_t += dt
        if self._frame_t >= self._frame_dt:
            self._frame_t = 0.0
            self._frame_idx = (self._frame_idx + 1) % len(self.frames)
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.frames[self._frame_idx]
        if self.dir < 0:
            img = [line[::-1] for line in img]
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            mask = self.mask_frames[self._frame_idx]
            if self.dir < 0:
                mask = [line[::-1] for line in mask]
            draw_sprite_masked(screen, img, mask, int(self.x), int(self.y), Screen.COLOUR_GREEN)


class Ship(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 10.0 * self.dir
        self.x = -24 if self.dir > 0 else screen.width
        self.y = 0
        ship_lr = [
            parse_sprite(
                r"""
     |    |    |
    )_)  )_)  )_)
   )___))___))___)\
  )____)____)_____)\\\
_____|____|____|____\\\\\__
\                   /
"""
            ),
            parse_sprite(
                r"""
     |    |    |
    )__) )__) )__)
   )___))___))___)\\
  )____)____)_____)\\\\
_____|____|____|____\\\\\\___
\                   /
"""
            ),
        ]
        ship_rl = [
            parse_sprite(
                r"""
         |    |    |
        (_(  (_(  (_(
      /(___((___((___(
    //(_____(____(____(
__///____|____|____|_____
    \                   /
"""
            ),
            parse_sprite(
                r"""
         |    |    |
        (__  (__  (__)
      /(___((___((___(\
    //(_____(____(____(\\
__///____|____|____|______
    \                   /
"""
            ),
        ]
        self.frames = ship_lr if self.dir > 0 else ship_rl
        # Use Perl masks for both animation frames to mirror exact color choices
        ship_mask_lr = [
            parse_sprite(
                r"""
     y    y    y

                  w
                   ww
yyyyyyyyyyyyyyyyyyyywwwyy
y                   y
"""
            ),
            parse_sprite(
                r"""
     y    y    y

                  w
                   ww
yyyyyyyyyyyyyyyyyyyywwwyy
y                   y
"""
            ),
        ]
        ship_mask_rl = [
            parse_sprite(
                r"""
         y    y    y

      w
    ww
yywwwyyyyyyyyyyyyyyyyyyyy
    y                   y
"""
            ),
            parse_sprite(
                r"""
         y    y    y

      w
    ww
yywwwyyyyyyyyyyyyyyyyyyyy
    y                   y
"""
            ),
        ]
        self.mask_frames = ship_mask_lr if self.dir > 0 else ship_mask_rl
        w_list = [sprite_size(f)[0] for f in self.frames]
        h_list = [sprite_size(f)[1] for f in self.frames]
        self.w, self.h = max(w_list), max(h_list)
        self._frame_idx = 0
        self._frame_t = 0.0
        self._frame_dt = 0.5
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: Screen, app) -> None:
        self.x += self.speed * dt
        self._frame_t += dt
        if self._frame_t >= self._frame_dt:
            self._frame_t = 0.0
            self._frame_idx = (self._frame_idx + 1) % len(self.frames)
        if (self.dir > 0 and self.x > screen.width) or (self.dir < 0 and self.x + self.w < 0):
            self._active = False

    def draw(self, screen: Screen, mono: bool = False) -> None:
        img = self.frames[self._frame_idx]
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            mask = self.mask_frames[self._frame_idx % len(self.mask_frames)]
            draw_sprite_masked(screen, img, mask, int(self.x), int(self.y), Screen.COLOUR_WHITE)


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


class BigFish(Actor):
    def __init__(self, screen: Screen, app):
        self.dir = random.choice([-1, 1])
        self.speed = 30.0 * (self.dir / abs(self.dir))
        if self.dir > 0:
            self.img = parse_sprite(
                r"""
 ______
`""-.  `````-----.....__
         `.  .      .       `-.
             :     .     .       `.
 ,     :   .    .          _ :
: `.   :                  (@) `._
 `. `..'     .     =`-.       .__)
     ;     .        =  ~  :     .-"
 .' .'`.   .    .  =.-'  `._ .'
: .'   :               .   .'
 '   .'  .    .     .   .-'
     .'____....----''.'='.
     ""             .'.'
                             ''"'`
"""
            )
            self.mask = parse_sprite(
                r"""
  111111
 11111  11111111111111111
      11  2      2       111
        1     2     2       11
  1     1   2    2          1 1
 1 11   1                  1W1 111
  11 1111     2     1111       1111
    1     2        1  1  1     111
  11 1111   2    2  1111  111 11
 1 11   1               2   11
  1   11  2    2     2   111
    111111111111111111111
    11             1111
                11111
"""
            )
            self.x = -34
        else:
            self.img = parse_sprite(
                r"""
                                                     ______
                    __.....-----'''''  .-""'
             .-'       .      .  .'
         .'       .     .     :
        : _          .    .   :     ,
 _.' (@)                  :   .' :
(__.       .-'=     .     `..' .'
 "-.     :  ~  =        .     ;
     `. _.'  `-.=  .    .   .'`. `.
         `.   .               :   `. :
             `-.   .     .    .  `.   `
                    `.=`.``----....____`.
                        `.`.             ""
                            '`"``
"""
            )
            self.mask = parse_sprite(
                r"""
                           111111
          11111111111111111  11111
       111       2      2  11
     11       2     2     1
    1 1          2    2   1     1
 111 1W1                  1   11 1
1111       1111     2     1111 11
 111     1  1  1        2     1
   11 111  1111  2    2   1111 11
     11   2               1   11 1
       111   2     2    2  11   1
          111111111111111111111
            1111             11
              11111
"""
            )
            self.x = screen.width
        self.w, self.h = sprite_size(self.img)
        max_height = 9
        min_height = max_height if screen.height - 15 <= max_height else (screen.height - 15)
        self.y = random.randint(max_height, max(min_height, max_height))
        # Randomize mask colours once to avoid per-frame flicker
        self._rand_mask = randomize_colour_mask(self.mask)
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
        if mono:
            draw_sprite(screen, img, int(self.x), int(self.y), Screen.COLOUR_WHITE)
        else:
            mask = self._rand_mask if self.dir > 0 else [line[::-1] for line in self._rand_mask]
            draw_sprite_masked(screen, img, mask, int(self.x), int(self.y), Screen.COLOUR_YELLOW)


def spawn_big_fish(screen: Screen, app) -> List[Actor]:
    return [BigFish(screen, app)]
