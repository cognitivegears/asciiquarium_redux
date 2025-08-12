from __future__ import annotations

from typing import Any
from ..screen_compat import Screen

class Actor:
    def update(self, dt: float, screen: Screen, app: Any) -> None: ...
    def draw(self, screen: Screen, mono: bool = False) -> None: ...
    @property
    def active(self) -> bool: ...
