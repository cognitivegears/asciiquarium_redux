from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Tuple
from asciimatics.screen import Screen

from ..util import parse_sprite, sprite_size, draw_sprite, draw_sprite_masked, randomize_colour_mask


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


FISH_RIGHT_MASKS = [
    parse_sprite(
        r"""
       2
     1112111
6  11       1
 66     7  4 5
6  1      3 1
    11111311
"""
    ),
    parse_sprite(
        r"""
    2
6 1111
66  745
6 1111
    3
"""
    ),
    parse_sprite(
        r"""
       222
666   1122211
  6661111111114
  66611111111115
 666 113333311
"""
    ),
    parse_sprite(
        r"""
  11
61145
   3
"""
    ),
    parse_sprite(
        r"""
   1121
661   745
  111311
"""
    ),
    parse_sprite(
        r"""
   2
  1 1
661745
  111
   3
"""
    ),
    parse_sprite(
        r"""
  12
66745
  13
"""
    ),
    parse_sprite(
        r"""
  11
61 41
61111
"""
    ),
]

FISH_LEFT_MASKS = [
    parse_sprite(
        r"""
      2
  1112111
 1       11  6
5 4  7     66
 1 3      1  6
  11311111
"""
    ),
    parse_sprite(
        r"""
  2
 1111 6
547  66
 1111 6
  3
"""
    ),
    parse_sprite(
        r"""
      222
   1122211   666
 4111111111666
51111111111666
  113333311 666
"""
    ),
    parse_sprite(
        r"""
  11
54116
 3
"""
    ),
    parse_sprite(
        r"""
  1211
547   166
 113111
"""
    ),
    parse_sprite(
        r"""
  2
 1 1
547166
 111
  3
"""
    ),
    parse_sprite(
        r"""
 21
54766
 31
"""
    ),
    parse_sprite(
        r"""
 11
14 16
11116
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
    # Per-entity sway speed (seconds per sway toggle roughly)
    sway_speed: float = field(default_factory=lambda: random.uniform(0.18, 0.5))
    sway_t: float = 0.0
    # Lifecycle
    state: str = "alive"  # alive | growing | dying | dormant
    visible_height: float = -1.0  # -1 means init to full height in __post_init__
    lifetime_t: float = 0.0
    lifetime_max: float = field(default_factory=lambda: random.uniform(25.0, 60.0))
    regrow_delay_t: float = 0.0
    regrow_delay_max: float = field(default_factory=lambda: random.uniform(4.0, 12.0))
    growth_rate: float = field(default_factory=lambda: random.uniform(6.0, 12.0))  # rows/sec
    shrink_rate: float = field(default_factory=lambda: random.uniform(8.0, 16.0))  # rows/sec
    # Configurable ranges (used on regrowth). Set by app when constructing.
    sway_min: float = 0.18
    sway_max: float = 0.5
    lifetime_min_cfg: float = 25.0
    lifetime_max_cfg: float = 60.0
    regrow_delay_min_cfg: float = 4.0
    regrow_delay_max_cfg: float = 12.0
    growth_rate_min_cfg: float = 6.0
    growth_rate_max_cfg: float = 12.0
    shrink_rate_min_cfg: float = 8.0
    shrink_rate_max_cfg: float = 16.0

    def __post_init__(self):
        # Initialize visible height
        if self.visible_height < 0:
            self.visible_height = float(max(1, self.height))
        # Stagger lifetime so not all die together
        self.lifetime_t = random.uniform(0.0, self.lifetime_max * 0.4)

    def frames(self) -> Tuple[List[str], List[str]]:
        a = ["(" if i % 2 == 0 else "" for i in range(self.height)]
        b = [" )" if i % 2 == 0 else "" for i in range(self.height)]
        frame1 = [s.ljust(2) for s in a]
        frame2 = [s.ljust(2) for s in b]
        return frame1, frame2

    def update(self, dt: float, screen: Screen):
        # advance sway timer
        self.sway_t += dt
        # lifecycle
        if self.state == "alive":
            self.lifetime_t += dt
            if self.lifetime_t >= self.lifetime_max:
                self.state = "dying"
        elif self.state == "growing":
            self.visible_height = min(self.height, self.visible_height + self.growth_rate * dt)
            if int(self.visible_height + 0.001) >= self.height:
                self.visible_height = float(self.height)
                self.state = "alive"
                self.lifetime_t = 0.0
                self.lifetime_max = random.uniform(self.lifetime_min_cfg, self.lifetime_max_cfg)
        elif self.state == "dying":
            self.visible_height = max(0.0, self.visible_height - self.shrink_rate * dt)
            if self.visible_height <= 0.0:
                self.state = "dormant"
                self.regrow_delay_t = 0.0
        elif self.state == "dormant":
            self.regrow_delay_t += dt
            if self.regrow_delay_t >= self.regrow_delay_max:
                # Regrow with some variation
                self.height = random.randint(3, 6)
                self.phase = random.randint(0, 1)
                self.sway_speed = random.uniform(self.sway_min, self.sway_max)
                self.growth_rate = random.uniform(self.growth_rate_min_cfg, self.growth_rate_max_cfg)
                self.shrink_rate = random.uniform(self.shrink_rate_min_cfg, self.shrink_rate_max_cfg)
                self.visible_height = 0.0
                self.state = "growing"
                self.regrow_delay_max = random.uniform(self.regrow_delay_min_cfg, self.regrow_delay_max_cfg)

    def draw(self, screen: Screen, tick: int, mono: bool = False):
        f1, f2 = self.frames()
        # compute sway toggle based on per-entity timer and speed
        step = int(self.sway_t / max(0.05, self.sway_speed))
        sway = (step + self.phase) % 2
        rows = f1 if sway == 0 else f2
        # How many rows to draw from the bottom
        vis = max(0, min(self.height, int(self.visible_height)))
        start_idx = self.height - vis
        for i in range(start_idx, self.height):
            row = rows[i]
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
    colour_mask: List[str] | None = None
    next_bubble: float = field(default_factory=lambda: random.uniform(1.5, 4.0))
    # Hook interaction state
    hooked: bool = False
    hook_dx: int = 0
    hook_dy: int = 0
    # Configurable movement and bubble behavior
    speed_min: float = 0.6
    speed_max: float = 2.5
    bubble_min: float = 2.0
    bubble_max: float = 5.0
    # Y-band as fractions of screen height, plus waterline context
    band_low_frac: float = 0.0
    band_high_frac: float = 1.0
    waterline_top: int = 5
    water_rows: int = 3

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
            self.next_bubble = random.uniform(self.bubble_min, self.bubble_max)
        if self.vx > 0 and self.x > screen.width:
            self.respawn(screen, direction=1)
        elif self.vx < 0 and self.x + self.width < 0:
            self.respawn(screen, direction=-1)

    def respawn(self, screen: Screen, direction: int):
        # choose new frames and matching mask
        if direction > 0:
            choices = list(zip(FISH_RIGHT, FISH_RIGHT_MASKS))
        else:
            choices = list(zip(FISH_LEFT, FISH_LEFT_MASKS))
        frames, mask = random.choice(choices)
        self.frames = frames
        self.colour_mask = randomize_colour_mask(mask)
        self.vx = random.uniform(self.speed_min, self.speed_max) * direction
        # compute y-band respecting waterline and screen size
        default_low = max(self.waterline_top + self.water_rows + 1, 1)
        low = max(default_low, int(screen.height * self.band_low_frac))
        high = min(screen.height - self.height - 2, int(screen.height * self.band_high_frac) - 1)
        if high < low:
            low = max(1, default_low)
            high = max(low, screen.height - self.height - 2)
        self.y = random.randint(low, max(low, high))
        self.x = -self.width if direction > 0 else screen.width

    def draw(self, screen: Screen):
        if self.colour_mask is not None:
            draw_sprite_masked(screen, self.frames, self.colour_mask, int(self.x), int(self.y), self.colour)
        else:
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
