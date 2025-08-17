from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Vec2:
    """Small immutable 2D vector for grid-space steering.

    Units are in screen cells (cols, rows). Keep it minimal and
    dependency-free. Methods return new vectors.
    """

    x: float
    y: float

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, k: float) -> "Vec2":
        return Vec2(self.x * k, self.y * k)

    __rmul__ = __mul__

    def __truediv__(self, k: float) -> "Vec2":
        if k == 0:
            return Vec2(0.0, 0.0)
        return Vec2(self.x / k, self.y / k)

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> "Vec2":
        l = self.length()
        if l <= 1e-6:
            return Vec2(0.0, 0.0)
        return self / l

    def clamp_length(self, max_len: float) -> "Vec2":
        l = self.length()
        if l <= max_len or l == 0:
            return self
        return self * (max_len / l)

    @staticmethod
    def zero() -> "Vec2":
        return Vec2(0.0, 0.0)
