from __future__ import annotations

from dataclasses import dataclass
import random as _random


@dataclass
class LeakyNoise:
    """Leaky-integrator noise that produces smooth wander values.

    y <- (1 - a)*y + a * n, where n ~ U(-1,1). Smaller a => smoother.
    """

    rng: _random.Random
    alpha: float = 0.15
    state: float = 0.0

    def step(self) -> float:
        n = self.rng.uniform(-1.0, 1.0)
        a = max(0.0, min(1.0, float(self.alpha)))
        self.state = (1.0 - a) * self.state + a * n
        return self.state
