from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Tuple, Optional, Protocol
import random as _random
from .vector import Vec2
from .noise import LeakyNoise
from .steering import (
    SteeringConfig,
    seek,
    flee,
    align as st_align,
    cohere as st_cohere,
    separate as st_separate,
    avoid as st_avoid,
    wander as st_wander,
    compose_velocity,
)
from .utility import UtilitySelector


class WorldSense(Protocol):
    def nearest_food(self, fish_id: int) -> Tuple[Vec2, float]: ...
    def predator_vector(self, fish_id: int) -> Tuple[Vec2, float]: ...
    def neighbors(self, fish_id: int, radius_cells: float) -> Iterable[Tuple[int, Vec2, Vec2]]: ...
    def obstacles(self, fish_id: int, radius_cells: float) -> Iterable[Vec2]: ...
    def bounds(self) -> Tuple[int, int]: ...
    def nearest_prey(self, fish_id: int) -> Tuple[Vec2, float]: ...


@dataclass
class Personality:
    hunger: float = 1.0
    fear: float = 1.0
    social: float = 1.0
    curiosity: float = 1.0


@dataclass
class FishBrain:
    fish_id: int
    rng: _random.Random
    sense: WorldSense
    config: SteeringConfig
    util_temp: float = 0.6
    wander_tau: float = 1.2
    eat_gain: float = 1.2
    hide_gain: float = 1.5
    flock_alignment: float = 0.8
    flock_cohesion: float = 0.5
    flock_separation: float = 1.2
    baseline_separation: float = 0.6
    baseline_avoid: float = 0.9
    hunt_threshold: float = 0.8  # hunger level at which fish may hunt smaller fish
    personality: Personality = field(default_factory=Personality)

    # internal state
    hunger: float = 0.0
    _noise: LeakyNoise = field(init=False)
    _selector: UtilitySelector = field(init=False)
    # Expose last chosen action for higher-level behavior decisions (e.g., turning policy)
    last_action: Optional[str] = None
    # Cooldown timer controlling how often AI may request a turn
    turn_cooldown: float = 0.0

    def __post_init__(self) -> None:
        a = max(1e-3, min(5.0, float(self.wander_tau)))
        # Convert tau to alpha approximately: alpha = dt/tau; we apply per-tick externally, so keep as fraction
        self._noise = LeakyNoise(self.rng, alpha=1.0 / a)
        self._selector = UtilitySelector(self.rng, temperature=self.util_temp)

    def update(
        self,
        dt: float,
        pos: Vec2,
        vel: Vec2,
    ) -> Vec2:
        # Sense
        dir_food, dist_food = self.sense.nearest_food(self.fish_id)
        dir_pred, dist_pred = self.sense.predator_vector(self.fish_id)
        # If very hungry and no fish food around, consider hunting smaller fish
        if self.hunger >= self.hunt_threshold and (dist_food == float("inf") or dist_food > 9999.0):
            try:
                dir_prey, dist_prey = self.sense.nearest_prey(self.fish_id)
                if dist_prey < float("inf"):
                    dir_food, dist_food = dir_prey, dist_prey
            except Exception:
                pass
        neigh = list(self.sense.neighbors(self.fish_id, self.config.separation_radius))
        obstacles = list(self.sense.obstacles(self.fish_id, self.config.obstacle_radius))
        # Utilities
        alpha = 0.35
        beta = 0.35
        food_pull = 1.0 / (1.0 + alpha * dist_food)
        fear = 1.0 / (1.0 + beta * dist_pred)
        social = min(1.0, max(0.0, len(neigh) / 8.0))
        curiosity = 1.0 - 0.5 * social
        # Personality scaling
        food_pull *= self.personality.hunger
        fear *= self.personality.fear
        social *= self.personality.social
        curiosity *= self.personality.curiosity
        # Action utilities
        utilities = {
            "EAT": food_pull * self.eat_gain,
            "HIDE": fear * self.hide_gain,
            "FLOCK": social * 1.0,
            "EXPLORE": curiosity * 1.0,
        }
        action, _ = self._selector.softmax_choice(utilities)
        # remember last action for external policies
        self.last_action = action
        # Compose steering
        components: list[tuple[Vec2, float]] = []
        if action == "EAT" and dist_food < float("inf"):
            components.append((dir_food * self.eat_gain, 1.0))
        elif action == "HIDE" and dist_pred < float("inf"):
            components.append((dir_pred * self.hide_gain, 1.0))
            components.append((st_avoid(pos, obstacles, self.config.obstacle_radius), 0.7))
        elif action == "FLOCK":
            neigh_pos = [p for _, p, _ in neigh]
            neigh_vel = [v for _, _, v in neigh]
            components.append((st_align(vel, neigh_vel), self.flock_alignment))
            components.append((st_cohere(pos, neigh_pos), self.flock_cohesion))
            components.append((st_separate(pos, neigh_pos, self.config.separation_radius), self.flock_separation))
        elif action == "EXPLORE":
            w = st_wander(self._noise.step(), self.config.max_speed)
            components.append((w, 0.6))
        # Baselines always on
        neigh_pos = [p for _, p, _ in neigh]
        components.append((st_separate(pos, neigh_pos, self.config.separation_radius), self.baseline_separation))
        components.append((st_avoid(pos, obstacles, self.config.obstacle_radius), self.baseline_avoid))
        # Integrate force into velocity (clamped)
        new_vel = compose_velocity(vel, components, self.config.max_speed, self.config.max_force)
        # Update hunger dynamics
        eaten = 1.0 if (action == "EAT" and dist_food < 1.2) else 0.0
        self.hunger = max(0.0, min(1.0, self.hunger + 0.03 * dt - eaten * 0.5))
        return new_vel
