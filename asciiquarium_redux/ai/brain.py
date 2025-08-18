from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Tuple, Optional, Protocol, List
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
    def shelters(self) -> Iterable[Vec2]: ...
    def size_of(self, fish_id: int) -> int: ...


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
    wander_tau: float = 1.6
    eat_gain: float = 1.2
    hide_gain: float = 1.5
    idle_gain: float = 0.8
    chase_gain: float = 0.9
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
        shelters = list(self.sense.shelters())
        obstacles = list(self.sense.obstacles(self.fish_id, self.config.obstacle_radius))
        # Utilities
        alpha = 0.35
        beta = 0.35
        food_pull = 1.0 / (1.0 + alpha * dist_food)
        fear = 1.0 / (1.0 + beta * dist_pred)
        social = min(1.0, max(0.0, len(neigh) / 8.0))
        curiosity = 1.0 - 0.5 * social
        # Idle tendency grows with size and low hunger/fear
        try:
            my_size = max(1, int(self.sense.size_of(self.fish_id)))
        except Exception:
            my_size = 3
        size_scale = min(1.0, 0.25 + 0.2 * (my_size - 1))  # bigger fish idle more
        # Personality scaling
        food_pull *= self.personality.hunger
        fear *= self.personality.fear
        social *= self.personality.social
        curiosity *= self.personality.curiosity
        idle_pull = max(0.0, size_scale * (1.0 - 0.6 * self.hunger) * (1.0 - 0.7 * fear))
        # Chase tendency: when social/curiosity are moderate and not fearful/hungry
        chase_pull = max(0.0, 0.6 * social + 0.4 * curiosity) * (1.0 - 0.5 * fear)
        # Action utilities
        utilities = {
            "EAT": food_pull * self.eat_gain,
            "HIDE": fear * self.hide_gain,
            "FLOCK": social * 1.0,
            "CHASE": chase_pull * self.chase_gain,
            "IDLE": idle_pull * self.idle_gain,
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
            # Prefer steering toward a shelter roughly aligned with escaping from the predator
            best_target: Optional[Vec2] = None
            best_dot = -1.0
            if shelters:
                away = dir_pred.normalized()
                for s in shelters:
                    to_s = (s - pos).normalized()
                    d = max(-1.0, min(1.0, to_s.dot(away)))
                    if d > best_dot:
                        best_dot = d
                        best_target = s
            if best_target is not None:
                components.append((seek(pos, best_target, self.config.max_speed), self.hide_gain))
            else:
                components.append((dir_pred * self.hide_gain, 1.0))
            components.append((st_avoid(pos, obstacles, self.config.obstacle_radius), 0.7))
        elif action == "FLOCK":
            neigh_pos = [p for _, p, _ in neigh]
            neigh_vel = [v for _, _, v in neigh]
            components.append((st_align(vel, neigh_vel), self.flock_alignment))
            components.append((st_cohere(pos, neigh_pos), self.flock_cohesion))
            components.append((st_separate(pos, neigh_pos, self.config.separation_radius), self.flock_separation))
        elif action == "CHASE":
            # Seek a similarly-sized neighbor (playful chase)
            try:
                my_sz = max(1, int(self.sense.size_of(self.fish_id)))
            except Exception:
                my_sz = 3
            peer_id: Optional[int] = None
            peer_pos: Optional[Vec2] = None
            best_d2 = float("inf")
            for nid, p, v in neigh:
                try:
                    ns = max(1, int(self.sense.size_of(nid)))
                except Exception:
                    ns = my_sz
                # Similar size within +-1 row
                if abs(ns - my_sz) <= 1:
                    d2 = (p.x - pos.x) ** 2 + (p.y - pos.y) ** 2
                    if d2 < best_d2:
                        best_d2 = d2
                        peer_id = nid
                        peer_pos = p
            if peer_pos is not None:
                components.append((seek(pos, peer_pos, self.config.max_speed), self.chase_gain))
            else:
                # Fallback to explore if no peer found
                w = st_wander(self._noise.step(), self.config.max_speed)
                components.append((w, 0.5))
        elif action == "IDLE":
            # Apply a small braking force to linger around current spot
            components.append((Vec2(-vel.x, -vel.y), 0.6))
            # Add tiny wander to avoid perfect stillness
            components.append((st_wander(self._noise.step(), self.config.max_speed), 0.1))
        elif action == "EXPLORE":
            w = st_wander(self._noise.step(), self.config.max_speed * 0.7)
            components.append((w, 0.5))
        # Baselines always on
        neigh_pos = [p for _, p, _ in neigh]
        components.append((st_separate(pos, neigh_pos, self.config.separation_radius), self.baseline_separation))
        components.append((st_avoid(pos, obstacles, self.config.obstacle_radius), self.baseline_avoid))
        # Integrate force into velocity (clamped)
        # Slightly reduce max force to smooth movements
        new_vel = compose_velocity(
            vel,
            components,
            self.config.max_speed * 0.9,
            self.config.max_force * 0.85,
        )
        # Update hunger dynamics
        eaten = 1.0 if (action == "EAT" and dist_food < 1.2) else 0.0
        self.hunger = max(0.0, min(1.0, self.hunger + 0.03 * dt - eaten * 0.5))
        return new_vel
