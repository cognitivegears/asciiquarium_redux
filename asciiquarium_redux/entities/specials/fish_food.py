from __future__ import annotations

import random
from typing import List

from typing import TYPE_CHECKING
from ..base import Actor
if TYPE_CHECKING:
    from ...protocols import ScreenProtocol, AsciiQuariumProtocol


class FishFoodFlake(Actor):
    """Single fish food flake that floats, then sinks with slight drift."""

    def __init__(self, screen: "ScreenProtocol", app: "AsciiQuariumProtocol", x: int):
        s = app.settings
        self.x: float = float(max(0, min(screen.width - 1, int(x))))
        self.y: float = float(int(s.waterline_top))  # float along surface
        # Phase: 0 = float, 1 = sink
        self._phase: int = 0
        # Float time before sinking
        try:
            tmin = float(getattr(s, "fish_food_float_seconds_min", 1.0))
            tmax = float(getattr(s, "fish_food_float_seconds_max", 3.0))
        except Exception:
            tmin, tmax = 1.0, 3.0
        if tmax < tmin:
            tmax = tmin
        self._float_t: float = random.uniform(tmin, tmax)
        # Surface horizontal drift
        self._surface_drift_speed: float = random.uniform(-2.0, 2.0)
        # Sinking params
        try:
            vy_min = float(getattr(s, "fish_food_sink_speed_min", 0.4))
            vy_max = float(getattr(s, "fish_food_sink_speed_max", 1.0))
        except Exception:
            vy_min, vy_max = 0.4, 1.0
        if vy_max < vy_min:
            vy_max = vy_min
        self._vy: float = random.uniform(vy_min, vy_max)
        self._drift_chance: float = float(getattr(s, "fish_food_drift_chance", 0.35))
        self._drift_speed: float = float(getattr(s, "fish_food_drift_speed", 1.0))
        self._active: bool = True

    @property
    def active(self) -> bool:
        return self._active

    def update(self, dt: float, screen: "ScreenProtocol", app: "AsciiQuariumProtocol") -> None:
        if not self._active:
            return
        if self._phase == 0:
            # Float with surface dispersion
            self._float_t -= dt
            self.x += self._surface_drift_speed * dt
            # Small jitter to spread
            if random.random() < 0.2:
                self.x += random.uniform(-0.5, 0.5)
            # Clamp to bounds and bounce surface drift
            if self.x < 0:
                self.x = 0
                self._surface_drift_speed = abs(self._surface_drift_speed)
            elif self.x > screen.width - 1:
                self.x = screen.width - 1
                self._surface_drift_speed = -abs(self._surface_drift_speed)
            if self._float_t <= 0:
                self._phase = 1
        else:
            # Sink with occasional lateral drift
            self.y += self._vy * dt
            if random.random() < max(0.0, self._drift_chance) * dt * 10.0:
                self.x += random.uniform(-self._drift_speed, self._drift_speed) * dt * 10.0
            if self.x < 0:
                self.x = 0
            elif self.x > screen.width - 1:
                self.x = screen.width - 1
            if int(self.y) >= screen.height - 1:
                self._active = False

    def draw(self, screen: "ScreenProtocol", mono: bool = False) -> None:
        if not self._active:
            return
        ch = "_"
        # Prefer yellow in colour mode else white
        try:
            col = screen.COLOUR_WHITE if mono else screen.COLOUR_YELLOW  # type: ignore[attr-defined]
        except Exception:
            col = 7 if mono else 3  # fallback: white=7, yellow=3
        xi = int(self.x)
        yi = int(self.y)
        if 0 <= yi < screen.height and 0 <= xi < screen.width:
            screen.print_at(ch, xi, yi, colour=col)


def spawn_fish_food(screen: "ScreenProtocol", app: "AsciiQuariumProtocol") -> List[FishFoodFlake]:
    s = app.settings
    try:
        cmin = int(getattr(s, "fish_food_count_min", 8))
        cmax = int(getattr(s, "fish_food_count_max", 20))
    except Exception:
        cmin, cmax = 8, 20
    if cmax < cmin:
        cmax = cmin
    count = max(1, random.randint(cmin, cmax))
    flakes: List[FishFoodFlake] = []
    # Choose a single drop point along the water surface, like a pinch of food
    x0 = random.randint(0, max(0, screen.width - 1))
    for _ in range(count):
        flakes.append(FishFoodFlake(screen, app, x0))
    return flakes
