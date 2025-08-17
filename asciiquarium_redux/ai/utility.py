from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, List
import math
import random as _random


AIAction = Tuple[str, float]


@dataclass
class UtilitySelector:
    rng: _random.Random
    temperature: float = 0.6

    def softmax_choice(self, utilities: Dict[str, float]) -> AIAction:
        # Softmax with temperature; lower temp => peakier
        t = max(1e-3, float(self.temperature))
        # Stabilize by subtracting max
        vals = list(utilities.items())
        if not vals:
            return ("EXPLORE", 1.0)
        m = max(v for _, v in vals)
        exps: List[Tuple[str, float]] = []
        s = 0.0
        for k, v in vals:
            e = math.exp((v - m) / t)
            exps.append((k, e))
            s += e
        r = self.rng.uniform(0.0, s)
        acc = 0.0
        for k, e in exps:
            acc += e
            if r <= acc:
                return (k, e / s)
        return (vals[-1][0], exps[-1][1] / s)
