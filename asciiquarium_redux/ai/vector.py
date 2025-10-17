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

    def __truediv__(self, divisor: float) -> "Vec2":
        if divisor == 0:
            return Vec2(0.0, 0.0)
        return Vec2(self.x / divisor, self.y / divisor)

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> "Vec2":
        length = self.length()
        if length <= 1e-6:
            return Vec2(0.0, 0.0)
        return self / length

    def clamp_length(self, max_len: float) -> "Vec2":
        length = self.length()
        if length <= max_len or length == 0:
            return self
        return self * (max_len / length)

    @staticmethod
    def zero() -> "Vec2":
        return Vec2(0.0, 0.0)
