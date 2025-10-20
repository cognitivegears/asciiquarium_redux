from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ...protocols import AsciiQuariumProtocol
    from ...screen_compat import Screen
else:
    from ...screen_compat import Screen

from ...util import draw_sprite, draw_sprite_masked, draw_sprite_masked_with_bg, randomize_colour_mask
from .behavior import BehaviorEngine, ClassicBehaviorEngine, AIBehaviorEngine
from .fish_assets import (
    FISH_RIGHT,
    FISH_LEFT,
    FISH_RIGHT_MASKS,
    FISH_LEFT_MASKS,
)
from .bubble import Bubble
from .splat import Splat
from ...constants import (
    MOVEMENT_MULTIPLIER,
    FISH_DEFAULT_SPEED_MIN,
    FISH_DEFAULT_SPEED_MAX,
    FISH_BUBBLE_DEFAULT_MIN,
    FISH_BUBBLE_DEFAULT_MAX,
    FISH_BUBBLE_INTERVAL_MIN,
    FISH_BUBBLE_INTERVAL_MAX,
    FISH_TURN_SHRINK_DURATION,
    FISH_TURN_EXPAND_DURATION,
    FISH_TURN_COOLDOWN_MIN,
    FISH_TURN_COOLDOWN_MAX,
)

# Optional AI imports are local to avoid import cycles at module import
try:
    from ...ai.brain import FishBrain
    from ...ai.vector import Vec2
    from ...ai.steering import SteeringConfig
except Exception:  # pragma: no cover - AI optional
    FishBrain = None  # type: ignore[assignment]
    Vec2 = None  # type: ignore[assignment]
    SteeringConfig = None  # type: ignore[assignment]


@dataclass
class Fish:
    """Main fish entity representing the core population of the aquarium.

    Fish are the primary animated entities in the simulation, providing visual interest
    through movement, bubble generation, and interactive behaviors. Each fish maintains
    its own state for position, velocity, appearance, and behavioral parameters.

    Key Features:
        **Movement System**: Fish move horizontally across the screen with configurable
        speed ranges and turning animations. Movement includes smooth direction changes
        with shrink/expand animations during turns.

        **Bubble Generation**: Fish periodically generate bubble entities at randomized
        intervals, contributing to the aquatic atmosphere.

        **Interactive Behavior**: Fish can be caught by fishhooks, with collision
        detection and hook-following mechanics.

        **Visual Customization**: Support for different fish sprites, colors, and
        z-depth layering for visual depth.

        **Behavioral Configuration**: Extensive configuration options for movement
        speed, bubble timing, turning behavior, and movement constraints.

    Architecture:
        The Fish class follows a data-oriented design using dataclasses for efficient
        memory layout and serialization. It implements the Actor protocol for consistent
        update/render behavior within the entity system.

    State Management:
        - **Position State**: x, y coordinates with floating-point precision
        - **Movement State**: velocity (vx), speed constraints, and turning phases
        - **Visual State**: sprite frames, color, z-depth, and color masks
        - **Interaction State**: hook attachment and displacement tracking
        - **Timing State**: bubble generation and turn cooldown timers

    Performance:
        Fish entities are designed for high-frequency updates (20-60 FPS) with
        minimal computational overhead. Movement calculations use simple linear
        interpolation, and collision detection is optimized for common cases.

    Attributes:
        frames (List[str]): Sprite frames for fish appearance (typically 2-4 lines)
        x (float): Horizontal position with sub-pixel precision
        y (float): Vertical position with sub-pixel precision
        vx (float): Horizontal velocity (positive = rightward movement)
        colour (int): Color index for terminal/display rendering
        z (int): Z-depth for layering (higher values draw on top). Default: 3-20
        colour_mask (List[str] | None): Optional color mask for advanced rendering

        next_bubble (float): Countdown timer until next bubble generation
        hooked (bool): Whether fish is attached to a fishhook
        hook_dx (int): Horizontal displacement when hooked
        hook_dy (int): Vertical displacement when hooked

        speed_min/max (float): Velocity range constraints for movement
        bubble_min/max (float): Interval range for bubble generation timing

        band_low_frac/high_frac (float): Vertical movement constraints as screen fractions
        waterline_top (int): Top row of water area for positioning
        water_rows (int): Number of water surface rows to avoid

        turning (bool): Whether fish is currently performing turn animation
        turn_phase (str): Current turn state - "idle", "shrink", "flip", or "expand"
        turn_t (float): Timer for current turn phase
        turn_shrink/expand_seconds (float): Duration of turn animation phases
        base_speed (float): Original speed before turn modifications
        next_turn_ok_in (float): Cooldown timer preventing frequent turns

        turn_enabled (bool): Global setting for turn animation system
        turn_chance_per_second (float): Probability of initiating turn per second
        turn_min_interval (float): Minimum time between turn attempts

    Example:
        >>> from asciiquarium_redux.entities.core.fish_assets import random_fish_frames
        >>>
        >>> # Create a basic fish
        >>> frames = random_fish_frames()
        >>> fish = Fish(
        ...     frames=frames,
        ...     x=10.0, y=15.0, vx=1.5,
        ...     colour=Screen.COLOUR_YELLOW
        ... )
        >>>
        >>> # Configure behavior
        >>> fish.speed_min = 0.8
        >>> fish.speed_max = 2.0
        >>> fish.bubble_min = 1.5
        >>> fish.bubble_max = 4.0
        >>>
        >>> # Update in game loop
        >>> fish.update(dt=0.016, screen=screen, app=aquarium)
        >>> fish.draw(screen, mono=False)

    See Also:
        - Bubble: Entities generated by fish bubble system
        - FishHook: Interactive entity that can catch fish
        - random_fish_frames(): Factory function for fish sprite generation
        - Entity System Documentation: docs/ENTITY_SYSTEM.md
    """

    frames: List[str]
    x: float
    y: float
    vx: float
    colour: int
    vy: float = 0.0
    # Z-depth for layering between fish (higher draws on top)
    z: int = field(default_factory=lambda: random.randint(3, 20))
    colour_mask: List[str] | None = None
    next_bubble: float = field(default_factory=lambda: random.uniform(FISH_BUBBLE_INTERVAL_MIN, FISH_BUBBLE_INTERVAL_MAX))
    # Hook interaction state
    hooked: bool = False
    hook_dx: int = 0
    hook_dy: int = 0
    # Configurable movement and bubble behavior
    speed_min: float = FISH_DEFAULT_SPEED_MIN
    speed_max: float = FISH_DEFAULT_SPEED_MAX
    bubble_min: float = FISH_BUBBLE_DEFAULT_MIN
    bubble_max: float = FISH_BUBBLE_DEFAULT_MAX
    # Speed modulation (acceleration-limited)
    accel_per_sec: float = 2.0  # how fast speed can change (units/sec^2)
    speed_target: float = 0.0   # desired speed magnitude (non-AI)
    speed_change_in: float = field(default_factory=lambda: random.uniform(1.5, 4.0))
    speed_change_interval_min: float = 1.5
    speed_change_interval_max: float = 4.0
    desired_vx: float = 0.0     # desired vx for smoothing (AI or non-AI)
    # Y-band as fractions of screen height, plus waterline context
    band_low_frac: float = 0.0
    band_high_frac: float = 1.0
    waterline_top: int = 5
    water_rows: int = 3
    # Turning state
    turning: bool = False
    turn_phase: str = "idle"  # shrink | flip | expand | idle
    turn_t: float = 0.0
    turn_shrink_seconds: float = FISH_TURN_SHRINK_DURATION
    turn_expand_seconds: float = FISH_TURN_EXPAND_DURATION
    base_speed: float = 0.0
    next_turn_ok_in: float = field(default_factory=lambda: random.uniform(FISH_TURN_COOLDOWN_MIN, FISH_TURN_COOLDOWN_MAX))
    # Global fish settings references (populated by app)
    turn_enabled: bool = True
    turn_chance_per_second: float = 0.01
    turn_min_interval: float = 6.0
    # Optional AI brain (constructed by first update if enabled)
    _brain: Any = None
    # Species/type info
    species_id: int = -1
    # Logical size bucket; by default set from sprite height at creation
    size_bucket: int = 0

    @property
    def width(self) -> int:
        return max(len(row) for row in self.frames)

    @property
    def height(self) -> int:
        return len(self.frames)

    @property
    def size(self) -> int:
        """Logical fish size derived from sprite height.

        Size is defined as the number of rows in the fish's ASCII art, which
        is consistent per sprite type. This provides a stable measure that can
        be used for behaviors, sorting, or interactions without guessing.
        """
        return self.height

    # --- Scene coordinate properties for large scene support ---
    @property
    def scene_x(self) -> float:
        return getattr(self, '_scene_x', self.x)

    @scene_x.setter
    def scene_x(self, value: float) -> None:
        self._scene_x = value
        self.x = value

    @property
    def scene_y(self) -> float:
        return getattr(self, '_scene_y', self.y)

    @scene_y.setter
    def scene_y(self, value: float) -> None:
        self._scene_y = value
        self.y = value

    def update(self, dt: float, screen: "Screen", app: "AsciiQuariumProtocol") -> None:
        """Update fish behavior including movement, turning, and bubble generation.

        Args:
            dt: Delta time since last update (seconds)
            screen: Screen interface for boundary checking
            app: Main application instance for spawning bubbles
        """
        # Select behavior engine once per update
        use_ai = bool(getattr(app.settings, "ai_enabled", False))
        engine: BehaviorEngine = AIBehaviorEngine() if use_ai else ClassicBehaviorEngine()

        # Movement with speed ramp depending on turning phase
        speed_scale = 1.0
        if self.turning:
            if self.turn_phase == "shrink":
                speed_scale = max(0.0, 1.0 - (self.turn_t / max(0.001, self.turn_shrink_seconds)))
            elif self.turn_phase == "expand":
                speed_scale = min(1.0, (self.turn_t / max(0.001, self.turn_expand_seconds)))
            else:
                speed_scale = 0.0

        # Behavior engine proposes desired velocities and turn request
        try:
            behavior = engine.step(self, dt, screen, app)
        except Exception:
            behavior = None
        if behavior is not None:
            if behavior.request_turn and not self.turning and not self.hooked:
                self.start_turn()
            if behavior.desired_vx is not None:
                self.desired_vx = float(behavior.desired_vx)
            if behavior.desired_vy is not None:
                self.vy = float(behavior.desired_vy)

        if not use_ai:
            # Random turning based on turn_chance_per_second
            self.next_turn_ok_in -= dt
            if (self.turn_enabled and
                    self.turn_chance_per_second > 0 and
                    not self.turning and
                    not self.hooked and
                    self.next_turn_ok_in <= 0):
                if random.random() < (self.turn_chance_per_second * dt):
                    self.start_turn()

        # Apply acceleration-limited change toward desired_vx (if set)
        if not self.hooked:
            try:
                dv = float(self.desired_vx) - float(self.vx)
            except Exception:
                dv = 0.0
            max_step = max(0.0, float(self.accel_per_sec) * dt)
            if dv > max_step:
                self.vx += max_step
            elif dv < -max_step:
                self.vx -= max_step
            else:
                self.vx += dv
            # Clamp to min/max speeds (preserve sign). Allow near-zero when AI is idling.
            mag = abs(self.vx)
            if mag > 0.0:
                min_speed = self.speed_min
                try:
                    if getattr(app.settings, "ai_enabled", False) and getattr(self, "_brain", None) is not None:
                        if getattr(self._brain, "last_action", None) == "IDLE":
                            min_speed = float(getattr(app.settings, "ai_idle_min_speed", 0.0))
                except Exception:
                    pass
                mag = max(min_speed, min(self.speed_max, mag))
                self.vx = mag if self.vx >= 0 else -mag
            # Additional damping when idling to settle quickly
            try:
                if getattr(app.settings, "ai_enabled", False) and getattr(self, "_brain", None) is not None:
                    if getattr(self._brain, "last_action", None) == "IDLE":
                        damp = float(getattr(app.settings, "ai_idle_damping_per_sec", 0.8))
                        k = max(0.0, min(1.0, damp * dt))
                        self.vx *= (1.0 - k)
            except Exception:
                pass

        # Kinematics integration (horizontal)
        self.scene_x += self.vx * dt * MOVEMENT_MULTIPLIER * speed_scale
        # If fish tank mode is enabled, clamp at margins and force a turn if crossed
        try:
            if bool(getattr(app.settings, "fish_tank", False)) and not self.hooked:
                margin = max(0, int(getattr(app.settings, "fish_tank_margin", 3)))
                left_limit = 0 + margin
                right_limit = screen.width - self.width - margin
                # Clamp within bounds first
                if self.scene_x > right_limit:
                    self.scene_x = float(right_limit)
                    if not self.turning and self.vx > 0:
                        # Initiate turn immediately at boundary
                        self.start_turn()
                        # Apply AI turn cooldown after forced boundary turn (deduplicated)
                        self._apply_turn_cooldown(app)
                elif self.scene_x < left_limit:
                    self.scene_x = float(left_limit)
                    if not self.turning and self.vx < 0:
                        self.start_turn()
                        # Apply AI turn cooldown after forced boundary turn (deduplicated)
                        self._apply_turn_cooldown(app)
                # While turning, ensure we do not drift beyond boundaries due to shrink phase momentum
                if self.turning:
                    if self.vx > 0 and self.scene_x > right_limit:
                        self.scene_x = float(right_limit)
                    elif self.vx < 0 and self.scene_x < left_limit:
                        self.scene_x = float(left_limit)
        except Exception:
            pass

        # Vertical vy already handled by behavior engine for both modes

        # Vertical bounds handling
        v_max = max(0.0, float(getattr(app.settings, "fish_vertical_speed_max", 0.3)))
        top_bound = max(self.waterline_top + self.water_rows + 1, 1)
        bottom_bound = max(top_bound, screen.height - self.height - 2)
        # Apply extra vertical damping when idling to reduce jitter
        try:
            if getattr(app.settings, "ai_enabled", False) and getattr(self, "_brain", None) is not None:
                if getattr(self._brain, "last_action", None) == "IDLE":
                    vy_damp = float(getattr(app.settings, "ai_idle_vy_damping_per_sec", 1.2))
                    k = max(0.0, min(1.0, vy_damp * dt))
                    self.vy *= (1.0 - k)
        except Exception:
            pass
        next_y = self.scene_y + self.vy * dt
        if next_y < top_bound:
            self._handle_vertical_bound(True, v_max, top_bound, bottom_bound)
        elif next_y > bottom_bound:
            self._handle_vertical_bound(False, v_max, top_bound, bottom_bound)
        else:
            self.scene_y = next_y

        # Mouth collision with fish food flakes
        try:
            from ..specials import FishFoodFlake  # type: ignore
            mx = int(self.scene_x + (self.width - 1 if self.vx > 0 else 0))
            my = int(self.scene_y + self.height // 2)
            # Prefer fish food: if any active flakes are present and intersect, consume them
            ate_food = False
            for s in list(app.specials):
                if isinstance(s, FishFoodFlake) and getattr(s, "active", True):
                    sx, sy = int(getattr(s, "x", 0)), int(getattr(s, "y", 0))
                    if abs(sx - mx) <= 1 and abs(sy - my) <= 0:
                        setattr(s, "_active", False)
                        if getattr(self, "_brain", None) is not None:
                            try:
                                self._brain.hunger = max(0.0, float(self._brain.hunger) - 0.5)
                            except Exception:
                                pass
                        ate_food = True
                        break
            # If very hungry and didn't find fish food to eat, allow predation on smaller fish
            if not ate_food and getattr(self, "_brain", None) is not None:
                try:
                    if float(self._brain.hunger) >= float(getattr(self._brain, "hunt_threshold", 0.8)):
                        for other in list(app.fish):
                            if other is self:
                                continue
                            # Only eat strictly smaller fish by height
                            if int(other.height) >= int(self.height):
                                continue
                            ox, oy = int(other.x), int(other.y + other.height // 2)
                            if abs(ox - mx) <= 1 and abs(oy - my) <= 0:
                                # Visual splat effect at predation point (scene coords)
                                try:
                                    app.splats.append(Splat(x=int(self.scene_x + (self.width - 1 if self.vx > 0 else 0)), y=int(self.scene_y + self.height // 2), coord_space="scene"))
                                except Exception:
                                    pass
                                # Immediately respawn the prey elsewhere to prevent population drop
                                try:
                                    import random as _r
                                    other.respawn(screen, direction=1 if _r.random() < 0.5 else -1)
                                except Exception:
                                    # Fallback: move off-screen and zero velocity
                                    other.x = -9999
                                    other.y = -9999
                                    other.vx = 0.0
                                # Reduce hunger more modestly than fish food
                                self._brain.hunger = max(0.0, float(self._brain.hunger) - 0.35)
                                break
                except Exception:
                    pass
        except Exception:
            pass

        # Bubbles
        self.next_bubble -= dt
        if self.next_bubble <= 0:
            bubble_y = int(self.scene_y + self.height // 2)
            view_off = int(getattr(app.settings, "scene_offset", 0))
            bubble_x = int(self.scene_x - view_off + (self.width if self.vx > 0 else -1))
            app.bubbles.append(Bubble(x=bubble_x, y=bubble_y))
            self.next_bubble = random.uniform(self.bubble_min, self.bubble_max)

        # Respawn when leaving scene bounds (scene mode): reappear off current view
        if not bool(getattr(app.settings, "fish_tank", False)):
            scene_width = int(getattr(app.settings, 'scene_width', screen.width))
            if self.vx > 0 and self.scene_x > scene_width:
                self.respawn_out_of_view(screen, app, direction=1)
            elif self.vx < 0 and self.scene_x + self.width < 0:
                self.respawn_out_of_view(screen, app, direction=-1)


        # Advance turn animation
        if self.turning:
            self.turn_t += dt
            if self.turn_phase == "shrink" and self.turn_t >= self.turn_shrink_seconds:
                self.finish_shrink_and_flip()
            elif self.turn_phase == "expand" and self.turn_t >= self.turn_expand_seconds:
                self.turning = False
                self.turn_phase = "idle"
                self.turn_t = 0.0
                self.next_turn_ok_in = max(
                    self.turn_min_interval,
                    random.uniform(
                        self.turn_min_interval,
                        self.turn_min_interval + (FISH_TURN_COOLDOWN_MAX - FISH_TURN_COOLDOWN_MIN),
                    ),
                )

    def _apply_turn_cooldown(self, app: "AsciiQuariumProtocol") -> None:
        """Apply AI turn cooldown after a forced boundary turn (deduplicated)."""
        if getattr(self, "_brain", None) is not None:
            try:
                height_bias = max(1.0, float(self.height))
                base_cd = float(getattr(app.settings, "ai_turn_base_cooldown", 1.2))
                size_fac = float(getattr(app.settings, "ai_turn_size_factor", 0.08))
                self._brain.turn_cooldown = base_cd * (1.0 + size_fac * (height_bias - 1.0))
            except Exception:
                pass

    def _handle_vertical_bound(self, at_top: bool, v_max: float, top_bound: float, bottom_bound: float) -> None:
        """Resolve vertical collision at top/bottom by stopping or reflecting vy."""
        if random.random() < 0.5:
            self.vy = 0.0
        else:
            if self.vy != 0:
                self.vy = abs(self.vy) if at_top else -abs(self.vy)
            else:
                val = random.uniform(0.05, v_max)
                self.vy = val if at_top else -val
        self.scene_y = float(top_bound if at_top else bottom_bound)

    def respawn(self, screen: Screen, direction: int):
        # choose new frames and matching mask
        if direction > 0:
            frame_choices = list(zip(FISH_RIGHT, FISH_RIGHT_MASKS))
        else:
            frame_choices = list(zip(FISH_LEFT, FISH_LEFT_MASKS))
        frames, colour_mask = random.choice(frame_choices)
        self.frames = frames
        self.colour_mask = randomize_colour_mask(colour_mask)
        # Pick a new horizontal speed within bounds and set direction
        self.vx = random.uniform(self.speed_min, self.speed_max) * direction
        # Reset speed modulation targets
        self.speed_target = abs(self.vx)
        self.desired_vx = self.vx
        self.speed_change_in = random.uniform(self.speed_change_interval_min, self.speed_change_interval_max)

        # compute y-band respecting waterline and screen size
        default_low_y = max(self.waterline_top + self.water_rows + 1, 1)
        min_y = max(default_low_y, int(screen.height * self.band_low_frac))
        max_y = min(screen.height - self.height - 2, int(screen.height * self.band_high_frac) - 1)
        if max_y < min_y:
            min_y = max(1, default_low_y)
            max_y = max(min_y, screen.height - self.height - 2)

        # Ensure bounds are valid to prevent infinite loops or crashes
        if max_y < min_y or screen.height < self.height + 4:
            # Fallback for very small screens: place fish in middle
            self.y = max(1, min(screen.height - self.height - 1, screen.height // 2))
            self.scene_y = self.y
        else:
            self.y = random.randint(min_y, max(min_y, max_y))
            self.scene_y = self.y
        self.x = -self.width if direction > 0 else screen.width
        self.scene_x = self.x
        # Reset turning animation state on respawn, but keep cooldown timer so turns still happen across respawns
        self.turning = False
        self.turn_phase = "idle"
        self.turn_t = 0.0

    def respawn_out_of_view(self, screen: "Screen", app: "AsciiQuariumProtocol", direction: int) -> None:
        """Respawn at a random scene position that is not within the current view window.

        In scene mode: fish reappear somewhere in the wider scene but never popping into the visible window.
        In fish-tank mode: fallback to classic edge respawn.
        """
        try:
            if bool(getattr(app.settings, "fish_tank", False)):
                # Classic behavior in tank mode
                self.respawn(screen, direction)
                return
            scene_w = int(getattr(app.settings, "scene_width", screen.width))
            off = int(getattr(app.settings, "scene_offset", 0))
        except Exception:
            self.respawn(screen, direction)
            return

        # Re-roll frames/colour/speed as in respawn()
        if direction > 0:
            frame_choices = list(zip(FISH_RIGHT, FISH_RIGHT_MASKS))
        else:
            frame_choices = list(zip(FISH_LEFT, FISH_LEFT_MASKS))
        frames, colour_mask = random.choice(frame_choices)
        self.frames = frames
        self.colour_mask = randomize_colour_mask(colour_mask)
        self.vx = random.uniform(self.speed_min, self.speed_max) * direction
        self.speed_target = abs(self.vx)
        self.desired_vx = self.vx
        self.speed_change_in = random.uniform(self.speed_change_interval_min, self.speed_change_interval_max)

        # Vertical band
        default_low_y = max(self.waterline_top + self.water_rows + 1, 1)
        min_y = max(default_low_y, int(screen.height * self.band_low_frac))
        max_y = min(screen.height - self.height - 2, int(screen.height * self.band_high_frac) - 1)
        if max_y < min_y:
            min_y = max(1, default_low_y)
            max_y = max(min_y, screen.height - self.height - 2)
        if max_y < min_y or screen.height < self.height + 4:
            self.y = max(1, min(screen.height - self.height - 1, screen.height // 2))
            self.scene_y = self.y
        else:
            self.y = random.randint(min_y, max(min_y, max_y))
            self.scene_y = self.y

        # Pick a scene_x outside the current view
        fish_w = self.width
        view_lo = off
        view_hi = off + screen.width
        left_lo, left_hi = 0, max(0, view_lo - fish_w)
        right_lo, right_hi = max(0, view_hi), max(0, scene_w - fish_w)
        ranges: list[tuple[int, int]] = []
        if left_hi > left_lo:
            ranges.append((left_lo, left_hi))
        if right_hi > right_lo:
            ranges.append((right_lo, right_hi))
        if ranges:
            lo, hi = random.choice(ranges)
            self.scene_x = float(random.randint(lo, max(lo, hi)))
        else:
            # Fallback if the view covers the entire scene
            self.scene_x = float(-fish_w if direction > 0 else scene_w + 1)
        self.x = self.scene_x
        # Reset turning state
        self.turning = False
        self.turn_phase = "idle"
        self.turn_t = 0.0

    def draw(self, screen: Screen):
        lines = self.frames
        mask = self.colour_mask
        x_off = 0
        # During turning, render a sliced/narrowed view to simulate columns disappearing/appearing
        if self.turning:
            w = self.width
            # Compute current visible width based on phase
            if self.turn_phase == "shrink":
                frac = max(0.0, 1.0 - (self.turn_t / max(0.001, self.turn_shrink_seconds)))
                vis = max(1, int(round(w * frac)))
                if vis % 2 == 0 and vis > 1:
                    vis -= 1
            elif self.turn_phase == "expand":
                frac = min(1.0, (self.turn_t / max(0.001, self.turn_expand_seconds)))
                vis = max(1, int(round(w * frac)))
                if vis % 2 == 0 and vis > 1:
                    vis -= 1
            else:
                vis = 1
            # Accordion compression: for each row, keep glyphs, drop spaces, and center a slice of length `vis`.
            # This guarantees each non-empty row retains at least one glyph until vis=1.
            def _compress_row(row: str, target: int) -> str:
                # Collect glyphs (non-space)
                glyphs = [ch for ch in row if ch != ' ']
                if not glyphs:
                    return ' ' * max(1, target)
                # Choose centered slice of glyphs of length <= target
                k = min(len(glyphs), max(1, target))
                start = (len(glyphs) - k) // 2
                sel = glyphs[start:start + k]
                # Center within target width
                pad = max(0, target - len(sel))
                left = pad // 2
                right = pad - left
                return (' ' * left) + ''.join(sel) + (' ' * right)
            def _compress_mask_row(row: str, mrow: str, target: int) -> str:
                # Mirror the selection logic used in _compress_row to align colours with kept glyphs
                pairs = [(ch, (mrow[i] if i < len(mrow) else ' ')) for i, ch in enumerate(row) if ch != ' ']
                if not pairs:
                    return ' ' * max(1, target)
                k = min(len(pairs), max(1, target))
                start = (len(pairs) - k) // 2
                sel = pairs[start:start + k]
                mchars = [mc for (_, mc) in sel]
                pad = max(0, target - len(mchars))
                left = pad // 2
                right = pad - left
                return (' ' * left) + ''.join(mchars) + (' ' * right)
            # Apply compression per row
            new_lines: List[str] = []
            new_mask: Optional[List[str]] = [] if mask is not None else None
            for dy, row in enumerate(lines):
                new_lines.append(_compress_row(row, vis))
                if new_mask is not None:
                    mrow = mask[dy] if dy < len(mask) else ''  # type: ignore[index]
                    new_mask.append(_compress_mask_row(row, mrow, vis))
            lines = new_lines
            if new_mask is not None:
                mask = new_mask  # type: ignore[assignment]
            # Shift draw position so the center stays stable during shrink/expand
            left = (w - vis) // 2
            x_off = left
        if mask is not None:
            solid_fish_setting = bool(getattr(self, "solid_fish", True))
            app_ref = getattr(self, "app", None)
            if app_ref is not None:
                try:
                    solid_fish_setting = bool(getattr(app_ref.settings, "solid_fish", solid_fish_setting))
                except Exception:
                    pass
            if solid_fish_setting:
                # Fill the silhouette row span with the fish base colour first, then draw coloured glyphs
                draw_sprite_masked_with_bg(screen, lines, mask, int(self.x) + x_off, int(self.y), self.colour, self.colour)
            else:
                draw_sprite_masked(screen, lines, mask, int(self.x) + x_off, int(self.y), self.colour)
        else:
            draw_sprite(screen, lines, int(self.x) + x_off, int(self.y), self.colour)

    # Hook API used by FishHook special
    def attach_to_hook(self, hook_x: int, hook_y: int):
        self.hooked = True
        self.hook_dx = int(self.x) - hook_x
        self.hook_dy = int(self.y) - hook_y
        self.vx = 0.0

    def follow_hook(self, hook_x: int, hook_y: int):
        if self.hooked:
            self.x = hook_x + self.hook_dx
            self.y = hook_y + self.hook_dy
            # Keep scene coordinates in sync with visual position
            self.scene_x = self.x
            self.scene_y = self.y

    # Turning control
    def start_turn(self):
        if self.turning or self.hooked:
            return
        self.turning = True
        self.turn_phase = "shrink"
        self.turn_t = 0.0
        self.base_speed = self.vx

    def finish_shrink_and_flip(self):
        # At the narrowest point: flip direction and frames, stop, then expand and ramp speed
        # Determine current and new directions
        curr_dir = 1 if self.vx > 0 else -1
        new_dir = -curr_dir
        # Swap to opposite direction frames, preserving the same sprite index when possible
        from .fish_assets import FISH_RIGHT, FISH_LEFT
        src_list = FISH_RIGHT if curr_dir > 0 else FISH_LEFT
        dst_list = FISH_RIGHT if new_dir > 0 else FISH_LEFT
        # Try to locate current frames' index in its source list for a stable mapping
        idx: Optional[int] = None
        try:
            for i, spr in enumerate(src_list):
                if spr == self.frames:
                    idx = i
                    break
        except Exception:
            idx = None
        if idx is not None and 0 <= idx < len(dst_list):
            self.frames = dst_list[idx]
        else:
            # Fallback: choose the closest by height to avoid mismatches if not found
            curr_h = self.height
            candidates = list(dst_list)
            self.frames = min(candidates, key=lambda fr: abs(len(fr) - curr_h))
        # Preserve existing colours when turning by mirroring the current colour_mask
        if self.colour_mask is not None:
            try:
                old_mask = self.colour_mask
                new_mask: list[str] = []
                # Helper to center-crop or pad a row to a desired length
                def _fit(row: str, target_len: int) -> str:
                    if len(row) == target_len:
                        return row
                    if len(row) > target_len:
                        # center-crop
                        drop = len(row) - target_len
                        left = drop // 2
                        return row[left:left+target_len]
                    # pad with spaces (default colour) to fit
                    pad = target_len - len(row)
                    left = pad // 2
                    right = pad - left
                    return (" " * left) + row + (" " * right)
                for dy, row in enumerate(self.frames):
                    src_row = old_mask[dy] if dy < len(old_mask) else ""
                    # mirror horizontally
                    mirrored = src_row[::-1]
                    new_mask.append(_fit(mirrored, len(row)))
                self.colour_mask = new_mask
            except Exception:
                # Fallback: keep previous mask to avoid colour jump
                pass
        else:
            self.colour_mask = None
        # Reverse velocity sign, magnitude picked from base_speed magnitude
        speed_mag = abs(self.base_speed) if self.base_speed != 0 else random.uniform(self.speed_min, self.speed_max)
        self.vx = speed_mag * new_dir
        # Continue to expand phase
        self.turn_phase = "expand"
        self.turn_t = 0.0
