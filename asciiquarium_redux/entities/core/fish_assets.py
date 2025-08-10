from __future__ import annotations

import random
from typing import List

from ...util import parse_sprite


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
\;,   ,;\\\\, ,
    \\\\;;:::::::o
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
  ''\\\\\\\\\'' ';\
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
