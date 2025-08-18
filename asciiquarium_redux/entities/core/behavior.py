from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...screen_compat import Screen
    from ...protocols import AsciiQuariumProtocol
    from .fish import Fish


@dataclass
class BehaviorResult:
    desired_vx: Optional[float] = None
    desired_vy: Optional[float] = None
    request_turn: bool = False


class BehaviorEngine:
    def step(self, fish: "Fish", dt: float, screen: "Screen", app: "AsciiQuariumProtocol") -> BehaviorResult:
        raise NotImplementedError


class ClassicBehaviorEngine(BehaviorEngine):
    """Classic random-within-bounds behavior."""

    def step(self, fish: "Fish", dt: float, screen: "Screen", app: "AsciiQuariumProtocol") -> BehaviorResult:
        res = BehaviorResult()
        # Turn chance (classic)
        if not fish.hooked and fish.turn_enabled:
            fish.next_turn_ok_in = max(0.0, float(fish.next_turn_ok_in) - dt)
            if not fish.turning and fish.next_turn_ok_in <= 0.0:
                if random.random() < max(0.0, float(fish.turn_chance_per_second)) * dt:
                    res.request_turn = True
        # Horizontal speed target drift
        if not fish.hooked:
            if fish.speed_target <= 0.0:
                fish.speed_target = max(fish.speed_min, min(fish.speed_max, abs(fish.vx)))
            fish.speed_change_in -= dt
            if fish.speed_change_in <= 0.0:
                fish.speed_target = random.uniform(fish.speed_min, fish.speed_max)
                fish.speed_change_in = random.uniform(fish.speed_change_interval_min, fish.speed_change_interval_max)
            sign = 1.0 if fish.vx >= 0.0 else -1.0
            res.desired_vx = sign * float(fish.speed_target)
        # Vertical drift
        v_max = max(0.0, float(getattr(app.settings, "fish_vertical_speed_max", 0.3)))
        if not fish.hooked and v_max > 0.0:
            if random.random() < 0.8 * dt:
                new_vy = random.uniform(-v_max, v_max)
                min_mag = min(0.3, v_max * 0.5)
                if abs(new_vy) < min_mag:
                    new_vy = min_mag if new_vy >= 0 else -min_mag
                res.desired_vy = new_vy
        return res


class AIBehaviorEngine(BehaviorEngine):
    """Utility-AI driven behavior using FishBrain for impulses like eat, hide, flock."""

    def step(self, fish: "Fish", dt: float, screen: "Screen", app: "AsciiQuariumProtocol") -> BehaviorResult:
        res = BehaviorResult()
        # AI turn cool-down and intent gating
        # Larger fish are lazier: scale cooldown by height (more rows -> longer cooldown)
        height_bias = max(1.0, float(getattr(fish, "height", 1)))
        base_cooldown = float(getattr(app.settings, "ai_turn_base_cooldown", 1.2))
        size_factor = float(getattr(app.settings, "ai_turn_size_factor", 0.08))
        cooldown = base_cooldown * (1.0 + size_factor * (height_bias - 1.0))
        # Decrement AI brain cooldown timer if present
        if getattr(fish, "_brain", None) is not None:
            try:
                fish._brain.turn_cooldown = max(0.0, float(getattr(fish._brain, "turn_cooldown", 0.0)) - dt)
            except Exception:
                pass
        try:
            from ...ai.brain import FishBrain  # local import to avoid cycles at import time
            from ...ai.vector import Vec2
            try:
                from ...ai.steering import SteeringConfig as _SteeringCfg
            except Exception:
                _SteeringCfg = None  # type: ignore

            if fish._brain is None and FishBrain is not None:
                max_speed = max(fish.speed_min, fish.speed_max)
                cfg = (
                    _SteeringCfg(
                        max_speed=max_speed,
                        max_force=max_speed,
                        separation_radius=float(getattr(app.settings, "ai_separation_radius", 3.0)),
                        obstacle_radius=float(getattr(app.settings, "ai_obstacle_radius", 3.0)),
                        align_weight=float(getattr(app.settings, "ai_flock_alignment", 0.8)),
                        cohere_weight=float(getattr(app.settings, "ai_flock_cohesion", 0.5)),
                        separate_weight=float(getattr(app.settings, "ai_flock_separation", 1.2)),
                        avoid_weight=float(getattr(app.settings, "ai_baseline_avoid", 0.9)),
                        wander_weight=float(getattr(app.settings, "ai_explore_gain", 0.6)),
                    )
                    if _SteeringCfg is not None
                    else None
                )
                import random as _rand
                rng = _rand.Random(_rand.randrange(1 << 30))
                fish._brain = FishBrain(
                    fish_id=id(fish),
                    rng=rng,
                    sense=app,  # type: ignore[arg-type]
                    config=cfg,  # type: ignore[arg-type]
                    util_temp=float(getattr(app.settings, "ai_action_temperature", 0.6)),
                    wander_tau=float(getattr(app.settings, "ai_wander_tau", 1.2)),
                    eat_gain=float(getattr(app.settings, "ai_eat_gain", 1.2)),
                    hide_gain=float(getattr(app.settings, "ai_hide_gain", 1.5)),
                    flock_alignment=float(getattr(app.settings, "ai_flock_alignment", 0.8)),
                    flock_cohesion=float(getattr(app.settings, "ai_flock_cohesion", 0.5)),
                    flock_separation=float(getattr(app.settings, "ai_flock_separation", 1.2)),
                    baseline_separation=float(getattr(app.settings, "ai_baseline_separation", 0.6)),
                    baseline_avoid=float(getattr(app.settings, "ai_baseline_avoid", 0.9)),
                )

            if fish._brain is not None:
                pos = Vec2(float(fish.x), float(fish.y))
                vel = Vec2(float(fish.vx), float(fish.vy))
                new_vel = fish._brain.update(dt, pos, vel)
                # desired vx and vy from AI
                res.desired_vx = float(new_vel.x)
                v_max_ai = max(0.0, float(getattr(app.settings, "fish_vertical_speed_max", 0.3)))
                res.desired_vy = max(-v_max_ai, min(v_max_ai, float(new_vel.y)))
                # request turn if desired direction differs AND there's a reason AND cooldown elapsed
                desired_sign = 1 if new_vel.x > 0 else (-1 if new_vel.x < 0 else 0)
                current_sign = 1 if fish.vx >= 0 else -1
                reason = None
                if getattr(fish._brain, "last_action", None) in ("EAT", "HIDE", "FLOCK"):
                    reason = fish._brain.last_action
                # bigger fish are extra lazy: require stronger reason except EAT
                if reason == "FLOCK" and height_bias >= 4.0:
                    # occasionally skip flock-motivated turns for large fish unless cooldown is fully elapsed
                    pass  # reason remains FLOCK but will still honor cooldown
                if desired_sign != 0 and desired_sign != current_sign and reason is not None:
                    if float(getattr(fish._brain, "turn_cooldown", 0.0)) <= 0.0 and not fish.turning:
                        res.request_turn = True
                        fish._brain.turn_cooldown = cooldown
        except Exception:
            pass
        return res
