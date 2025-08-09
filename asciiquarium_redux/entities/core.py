from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Tuple
from asciimatics.screen import Screen

from ..util import parse_sprite, sprite_size, draw_sprite


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
        parse_sprite(
                r"""
             \:.
\;,   ,;\\\\\, ,
    \\\\\;;:::::::o
    ///;;::::::::<
 /;` ``/////``
"""
        ),
        parse_sprite(
                r"""
    __
><_'>
     '
"""
        ),
        parse_sprite(
                r"""
     ..\,
>='   ('>
    '''/''
"""
        ),
        parse_sprite(
                r"""
     \
    / \
>=_('>
    \_/
     /
"""
        ),
        parse_sprite(
                r"""
    ,\
>=('>
    '/
"""
        ),
        parse_sprite(
                r"""
    __
\\/ o\\
/\\__/
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
    parse_sprite(
        r"""
      .:/
   ,,///;,   ,;/
 o:::::::;;///
>::::::::;;\\\\\\
  ''\\\\\\\\\\\'' ';\
"""
    ),
    parse_sprite(
        r"""
 __
<'_><
 `
"""
    ),
    parse_sprite(
        r"""
  ,/..
<')   `=<
 ``\```
"""
    ),
    parse_sprite(
        r"""
  /
 / \
<')_=<
 \_/
  \
"""
    ),
    parse_sprite(
        r"""
 /,
<')=<
 \`
"""
    ),
    parse_sprite(
        r"""
 __
/o \\
\__/\\
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
    # Hook interaction state
    hooked: bool = False
    hook_dx: int = 0
    hook_dy: int = 0

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

    # Hook API used by FishHook special
    def attach_to_hook(self, hook_x: int, hook_y: int):
        self.hooked = True
        self.hook_dx = int(self.x) - hook_x
        self.hook_dy = int(self.y) - hook_y
        self.vx = 0.0

    def follow_hook(self, hook_x: int, hook_y: int):
        if self.hooked:
            self.x = hook_x + self.hook_dx
            self.y = hook_y + self.hook_dy
