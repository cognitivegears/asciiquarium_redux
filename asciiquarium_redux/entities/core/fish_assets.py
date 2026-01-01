from __future__ import annotations

import random
from typing import List

from ...util import parse_sprite


FISH_RIGHT = [
    parse_sprite(
        r"""
  _
><_>
"""
    ),
    parse_sprite(
        r"""
   _\_
\\/  o\
//\___=
   ''
"""
    ),
  parse_sprite(
    r"""
  .-----,
  \  ____\
 _ \/     \
| \/     O \
|          <
|_/\    (> /
   /\_____/
  /      /
  `-----'
"""
    ),
    parse_sprite(
        r"""
      \:.
\;,   ,;\\\,,
 \\\;;::::::(o
 ///;;::::::::<
/;` "`/////``
       /;`
"""
    ),
    parse_sprite(
        r"""
   ..--,
  `,.-``.
:-.'    @\
:.-,  >( <
  ',`-..'
    `-'
"""
    ),
    parse_sprite(
        r"""
      .
\_____)\_____
/--v____ __`<
        )/
        '
"""
    ),

  # old
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
\;,   ,;\\\\,,
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
\/ o\
/\__/
"""
        ),
]

FISH_LEFT = [
  parse_sprite(
    r"""
 _
<_><
"""
  ),
  parse_sprite(
    r"""
 _/_
/o  \//
=___/\\
  ``
"""
  ),
    parse_sprite(
    r"""
   ,-----.
  /____  /
 /     \/ _
/ O     \/ |
>          |
\ <)    /\_|
 \_____/\
  \      \
   `-----'
"""
    ),
    parse_sprite(
        r"""
      .:/
  ,,///;,   ,;/
 o)::::::;;///
>::::::::;;\\\
  ''\\\\\'" ';\
     ';\
"""
    ),
    parse_sprite(
        r"""
  ,--..
 .''-.,'
/@    `.-:
> )<  ,-.:
 `..-',`
   `-'
"""
    ),
    parse_sprite(
        r"""
      .
_____/(_____/
>'__ ____v--\
   \(
    `
"""
    ),

  # old ones
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
/o \/
\__/\
"""
    ),
]


FISH_RIGHT_MASKS = [
    parse_sprite(
        r"""
  1
1111
"""
    ),
    parse_sprite(
        r"""
   111
331  41
3311112
   11
"""
    ),
  parse_sprite(
    r"""
  3333333
  3  11111
 1 31     1
1 11     4 1
1          2
1111    33 1
   11111111
  3      3
  3333333
"""
    ),
    parse_sprite(
        r"""
      555
333   55522
 3332211111164
 33322111111116
333 555555522
       555
"""
    ),
    parse_sprite(
        r"""
   22222
  2111111
2221    41
2221  24 6
  2211111
    222
"""
    ),
    parse_sprite(
        r"""
      1
1111111111111
11111111 1142
        11
        1
"""
    ),
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
54116
 3
"""
    ),
    parse_sprite(
        r"""
  1121
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
 1
1111
"""
    ),
    parse_sprite(
        r"""
 111
14  133
2111133
  11
"""
    ),
  parse_sprite(
    r"""
   3333333
  11111  3
 1     13 1
1 4     11 1
2          1
1 33    1111
 11111113
  3      3
   3333333
"""
    ),
    parse_sprite(
        r"""
      555
    22555   333
 4611111122333
61111111122333
  225555555 333
     555
"""
    ),
    parse_sprite(
        r"""
  22222
 1111112
14    1222
6 42  1222
 1111122
   222
"""
    ),
    parse_sprite(
        r"""
      1
1111111111111
2411 11111111
   11
    1
"""
    ),

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
