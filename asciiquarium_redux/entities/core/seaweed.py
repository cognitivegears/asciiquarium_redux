from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Tuple, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ...protocols import ScreenProtocol, AsciiQuariumProtocol
    from ...screen_compat import Screen
else:
    from ...screen_compat import Screen
from ...constants import (
    SEAWEED_SWAY_SPEED_MIN_RANGE,
    SEAWEED_SWAY_SPEED_MAX_RANGE,
    SEAWEED_LIFETIME_MIN,
    SEAWEED_LIFETIME_MAX,
    SEAWEED_REGROW_DELAY_MIN,
    SEAWEED_REGROW_DELAY_MAX,
    SEAWEED_GROWTH_RATE_MIN,
    SEAWEED_GROWTH_RATE_MAX,
    SEAWEED_SHRINK_RATE_MIN,
    SEAWEED_SHRINK_RATE_MAX,
    SEAWEED_HEIGHT_MIN,
    SEAWEED_HEIGHT_MAX,
    SEAWEED_PHASE_MAX,
    SEAWEED_LIFETIME_STAGGER_FRACTION,
    SEAWEED_SWAY_SPEED_MIN,
)


@dataclass
class Seaweed:
    """Animated seaweed entity providing background movement and aquatic atmosphere.

    Seaweed entities create the underwater environment through gentle swaying animations
    and dynamic lifecycle management. They provide visual depth and contribute to the
    aquatic ambiance without interfering with fish movement or user interactions.

    Key Features:
        **Swaying Animation**: Continuous side-to-side movement with configurable timing
        and phase offsets to create natural underwater motion patterns.

        **Dynamic Lifecycle**: Seaweed grows, lives, dies, and regrows in cycles to
        maintain visual variety and prevent static backgrounds.

        **Configurable Growth**: Parametric control over growth rates, lifetimes,
        and regrowth delays for diverse behavioral patterns.

        **Visual Variety**: Randomized phase offsets and timing create unique
        movement patterns for each seaweed instance.

        **Performance Optimized**: Efficient state management and rendering for
        high entity counts without performance degradation.

    Architecture:
        The Seaweed class uses a finite state machine for lifecycle management
        (alive → dying → dormant → growing → alive) with smooth transitions
        between states. Visual rendering is computed dynamically based on sway
        timing and current lifecycle state.

    State Machine:
        - **alive**: Normal swaying animation with full visibility
        - **dying**: Gradual shrinking animation as seaweed disappears
        - **dormant**: Invisible state during regrowth delay period
        - **growing**: Gradual expansion as seaweed reappears

    Visual Rendering:
        Seaweed uses simple ASCII characters with alternating patterns to create
        the illusion of swaying underwater plants. The rendering system supports
        partial height display during growth/death transitions.

    Performance:
        Designed for high entity counts (10-50 seaweed per screen) with minimal
        computational overhead. State updates use simple timers and linear
        interpolation for smooth animations.

    Attributes:
        x (int): Horizontal position (column) on screen
        base_y (int): Bottom row position (typically screen.height - 2)
        height (int): Maximum seaweed height in rows
        phase (int): Initial phase offset for sway timing variation

        sway_speed (float): Speed of sway animation (seconds per cycle)
        sway_t (float): Current sway animation timer

        state (str): Current lifecycle state - "alive", "growing", "dying", "dormant"
        visible_height (float): Current visible height (for growth/shrink animations)

        lifetime_t (float): Current age timer
        lifetime_max (float): Maximum age before starting death transition

        regrow_delay_t (float): Timer during dormant state
        regrow_delay_max (float): Duration of dormant period before regrowth

        growth_rate (float): Speed of growth animation (rows per second)
        shrink_rate (float): Speed of death animation (rows per second)

        sway_min/max (float): Configurable range for sway speed variation
        lifetime_min_cfg/max_cfg (float): Configurable lifetime range
        regrow_delay_min_cfg/max_cfg (float): Configurable regrowth delay range
        growth_rate_min_cfg/max_cfg (float): Configurable growth speed range
        shrink_rate_min_cfg/max_cfg (float): Configurable shrink speed range

    Example:
        >>> # Create seaweed with basic parameters
        >>> seaweed = Seaweed(
        ...     x=25, base_y=22, height=8,
        ...     phase=random.randint(0, 31)
        ... )
        >>>
        >>> # Configure lifecycle parameters
        >>> seaweed.sway_min = 0.1
        >>> seaweed.sway_max = 0.6
        >>> seaweed.lifetime_min_cfg = 15.0
        >>> seaweed.lifetime_max_cfg = 45.0
        >>>
        >>> # Update in game loop
        >>> seaweed.update(dt=0.016, screen=screen, app=aquarium)
        >>> seaweed.draw(screen, mono=False)

    See Also:
        - AsciiQuarium.rebuild(): Method that spawns seaweed populations
        - Settings: Configuration for seaweed density and behavior
        - Entity System Documentation: docs/ENTITY_SYSTEM.md
    """

    x: int
    base_y: int
    height: int
    phase: int
    # Per-entity sway speed (seconds per sway toggle roughly)
    sway_speed: float = field(default_factory=lambda: random.uniform(SEAWEED_SWAY_SPEED_MIN_RANGE, SEAWEED_SWAY_SPEED_MAX_RANGE))
    sway_t: float = 0.0
    # Lifecycle
    state: str = "alive"  # alive | growing | dying | dormant
    visible_height: float = -1.0  # -1 means init to full height in __post_init__
    lifetime_t: float = 0.0
    lifetime_max: float = field(default_factory=lambda: random.uniform(SEAWEED_LIFETIME_MIN, SEAWEED_LIFETIME_MAX))
    regrow_delay_t: float = 0.0
    regrow_delay_max: float = field(default_factory=lambda: random.uniform(SEAWEED_REGROW_DELAY_MIN, SEAWEED_REGROW_DELAY_MAX))
    growth_rate: float = field(default_factory=lambda: random.uniform(SEAWEED_GROWTH_RATE_MIN, SEAWEED_GROWTH_RATE_MAX))  # rows/sec
    shrink_rate: float = field(default_factory=lambda: random.uniform(SEAWEED_SHRINK_RATE_MIN, SEAWEED_SHRINK_RATE_MAX))  # rows/sec
    # Configurable ranges (used on regrowth). Set by app when constructing.
    sway_min: float = SEAWEED_SWAY_SPEED_MIN_RANGE
    sway_max: float = SEAWEED_SWAY_SPEED_MAX_RANGE
    lifetime_min_cfg: float = SEAWEED_LIFETIME_MIN
    lifetime_max_cfg: float = SEAWEED_LIFETIME_MAX
    regrow_delay_min_cfg: float = SEAWEED_REGROW_DELAY_MIN
    regrow_delay_max_cfg: float = SEAWEED_REGROW_DELAY_MAX
    growth_rate_min_cfg: float = SEAWEED_GROWTH_RATE_MIN
    growth_rate_max_cfg: float = SEAWEED_GROWTH_RATE_MAX
    shrink_rate_min_cfg: float = SEAWEED_SHRINK_RATE_MIN
    shrink_rate_max_cfg: float = SEAWEED_SHRINK_RATE_MAX

    def __post_init__(self):
        # Initialize visible height
        if self.visible_height < 0:
            self.visible_height = float(max(1, self.height))
        # Stagger lifetime so not all die together
        self.lifetime_t = random.uniform(0.0, self.lifetime_max * SEAWEED_LIFETIME_STAGGER_FRACTION)

    def frames(self) -> Tuple[List[str], List[str]]:
        left_pattern = ["(" if row_index % 2 == 0 else "" for row_index in range(self.height)]
        right_pattern = [" )" if row_index % 2 == 0 else "" for row_index in range(self.height)]
        frame1 = [pattern.ljust(2) for pattern in left_pattern]
        frame2 = [pattern.ljust(2) for pattern in right_pattern]
        return frame1, frame2

    def update(self, dt: float, screen: "Screen", app: "AsciiQuariumProtocol") -> None:
        # advance sway timer
        self.sway_t += dt
        # lifecycle
        if self.state == "alive":
            self.lifetime_t += dt
            if self.lifetime_t >= self.lifetime_max:
                self.state = "dying"
        elif self.state == "growing":
            self.visible_height = min(self.height, self.visible_height + self.growth_rate * dt)
            if int(self.visible_height + 0.001) >= self.height:
                self.visible_height = float(self.height)
                self.state = "alive"
                self.lifetime_t = 0.0
                self.lifetime_max = random.uniform(self.lifetime_min_cfg, self.lifetime_max_cfg)
        elif self.state == "dying":
            self.visible_height = max(0.0, self.visible_height - self.shrink_rate * dt)
            if self.visible_height <= 0.0:
                self.state = "dormant"
                self.regrow_delay_t = 0.0
        elif self.state == "dormant":
            self.regrow_delay_t += dt
            if self.regrow_delay_t >= self.regrow_delay_max:
                # Regrow with some variation
                self.height = random.randint(SEAWEED_HEIGHT_MIN, SEAWEED_HEIGHT_MAX)
                self.phase = random.randint(0, SEAWEED_PHASE_MAX)
                self.sway_speed = random.uniform(self.sway_min, self.sway_max)
                self.growth_rate = random.uniform(self.growth_rate_min_cfg, self.growth_rate_max_cfg)
                self.shrink_rate = random.uniform(self.shrink_rate_min_cfg, self.shrink_rate_max_cfg)
                self.visible_height = 0.0
                self.state = "growing"
                self.regrow_delay_max = random.uniform(self.regrow_delay_min_cfg, self.regrow_delay_max_cfg)

    def draw(self, screen: Screen, tick: int, mono: bool = False):
        frame_left, frame_right = self.frames()
        # compute sway toggle based on per-entity timer and speed
        # Prevent division by zero by ensuring sway_speed is positive
        sway_step = int(self.sway_t / max(SEAWEED_SWAY_SPEED_MIN, self.sway_speed))
        sway_direction = (sway_step + self.phase) % 2
        current_frame = frame_left if sway_direction == 0 else frame_right
        # How many rows to draw from the bottom
        # Prevent negative height which could cause index errors
        safe_height = max(1, self.height)
        visible_rows = max(0, min(safe_height, int(self.visible_height)))
        start_row_index = safe_height - visible_rows
        for row_index in range(start_row_index, safe_height):
            row_content = current_frame[row_index]
            display_y = self.base_y - (safe_height - 1 - row_index)
            if 0 <= display_y < screen.height:
                screen.print_at(row_content, self.x, display_y, colour=Screen.COLOUR_WHITE if mono else Screen.COLOUR_GREEN)
