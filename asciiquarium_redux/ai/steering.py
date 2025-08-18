from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple
from .vector import Vec2


@dataclass
class SteeringConfig:
    max_speed: float = 2.5  # cells/sec
    max_force: float = 2.0  # cells/sec^2 equivalent (per tick scale externally)
    separation_radius: float = 3.0
    obstacle_radius: float = 3.0
    align_weight: float = 0.8
    cohere_weight: float = 0.5
    separate_weight: float = 1.2
    avoid_weight: float = 0.9
    wander_weight: float = 0.6


def seek(pos: Vec2, target: Vec2, max_speed: float) -> Vec2:
    desired = (target - pos).normalized() * max_speed
    return desired


def flee(pos: Vec2, threat: Vec2, max_speed: float) -> Vec2:
    desired = (pos - threat).normalized() * max_speed
    return desired


def align(vel: Vec2, neighbor_vels: Iterable[Vec2]) -> Vec2:
    count = 0
    sum_v = Vec2.zero()
    for v in neighbor_vels:
        sum_v = sum_v + v
        count += 1
    if count == 0:
        return Vec2.zero()
    avg = sum_v * (1.0 / count)
    return avg


def cohere(pos: Vec2, neighbor_positions: Iterable[Vec2]) -> Vec2:
    count = 0
    sum_p = Vec2.zero()
    for p in neighbor_positions:
        sum_p = sum_p + p
        count += 1
    if count == 0:
        return Vec2.zero()
    center = sum_p * (1.0 / count)
    return center - pos


def separate(pos: Vec2, neighbor_positions: Iterable[Vec2], sep_radius: float) -> Vec2:
    steer = Vec2.zero()
    for p in neighbor_positions:
        diff = pos - p
        d = max(1e-6, diff.length())
        if d < sep_radius:
            steer = steer + diff.normalized() * (sep_radius - d)
    return steer


def avoid(pos: Vec2, obstacles: Iterable[Vec2], avoid_radius: float) -> Vec2:
    steer = Vec2.zero()
    for p in obstacles:
        diff = pos - p
        d = max(1e-6, diff.length())
        if d < avoid_radius:
            steer = steer + diff.normalized() * (avoid_radius - d)
    return steer


def wander(noise_val: float, max_speed: float) -> Vec2:
    # Map noise in [-1,1] to a direction with small bias changes
    angle = noise_val * 3.14159  # up to ~pi radians change
    # Simple unit vector from angle in X/Y; prefer horizontal bias
    from math import cos, sin
    # Use sin for x to avoid positive bias (E[sin(theta)] = 0 for symmetric theta)
    v = Vec2(sin(angle), 0.35 * cos(angle))
    return v.normalized() * max_speed


def compose_velocity(
    base_vel: Vec2,
    steering_components: Iterable[Tuple[Vec2, float]],
    max_speed: float,
    max_force: float,
) -> Vec2:
    # Sum weighted steering, clamp by max_force, then add to base velocity and clamp by max_speed
    force = Vec2.zero()
    for vec, w in steering_components:
        if w == 0.0:
            continue
        force = force + vec * w
    force = force.clamp_length(max_force)
    new_v = base_vel + force
    return new_v.clamp_length(max_speed)
