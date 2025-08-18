"""Main application controller module for Asciiquarium Redux.

This module contains the core AsciiQuarium class that orchestrates the entire
aquarium simulation. It manages entity lifecycles, handles user input, coordinates
rendering, and provides the main game loop for all supported backends.

Key Components:
    - AsciiQuarium: Central controller class managing the complete simulation
    - Entity Management: Spawning, updating, and cleanup of all aquarium entities
    - Animation Loop: Frame-based updates with delta-time calculations
    - User Interaction: Keyboard and mouse input handling across backends
    - Performance Management: FPS control and resource optimization

Architecture:
    The module follows a composition-based design where the AsciiQuarium class
    coordinates separate subsystems rather than implementing everything directly.
    This approach enables clean separation of concerns and easy testing.

Dependencies:
    - screen_compat: Backend abstraction for cross-platform rendering
    - entities: Complete entity system (fish, seaweed, bubbles, specials)
    - util.settings: Configuration management and parameter control
    - constants: Centralized magic numbers and default values

Usage:
    The AsciiQuarium class is typically instantiated by the runner module or
    directly in programmatic usage. It requires a Settings object and Screen
    implementation to operate.

Example:
    >>> from asciiquarium_redux.util.settings import Settings
    >>> from asciiquarium_redux.backends.terminal import TerminalScreen
    >>>
    >>> settings = Settings(fps=30, density=1.5)
    >>> aquarium = AsciiQuarium(settings)
    >>> screen = TerminalScreen()
    >>> aquarium.run(screen)

Performance:
    The module is optimized for 20-60 FPS animation with hundreds of entities.
    Performance-critical sections use efficient algorithms and minimal allocations.

See Also:
    - runner.py: CLI interface and backend selection
    - util.settings: Configuration system
    - entities/: Entity implementations
    - docs/ARCHITECTURE.md: System design overview
"""

from __future__ import annotations

import random
import time
import logging
from typing import List, Dict, Tuple, Optional, Union, Any, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .protocols import ScreenProtocol, AsciiQuariumProtocol, SettingsProtocol, ActorProtocol
    from .screen_compat import Screen
else:
    from .screen_compat import Screen

from .util import sprite_size, draw_sprite, draw_sprite_masked, fill_rect, draw_sprite_masked_with_bg
from .util.buffer import DoubleBufferedScreen
from .entities.environment import WATER_SEGMENTS, CASTLE, CASTLE_MASK, waterline_row
from .util.settings import Settings
from .entities.core import Seaweed, Bubble, Splat, Fish, random_fish_frames
from .entities.base import Actor
from .entities.specials import (
    FishHook,
    spawn_shark,
    spawn_fishhook,
    spawn_fishhook_to,
    spawn_whale,
    spawn_ship,
    spawn_ducks,
    spawn_dolphins,
    spawn_swan,
    spawn_monster,
    spawn_big_fish,
    spawn_treasure_chest,
    spawn_fish_food,
)
from .constants import (
    SCREEN_WIDTH_UNIT_DIVISOR,
    SEAWEED_DENSITY_WIDTH_DIVISOR,
    SEAWEED_HEIGHT_MIN,
    SEAWEED_HEIGHT_MAX,
    SEAWEED_PHASE_MAX,
    FISH_DENSITY_AREA_DIVISOR,
    SEAWEED_ANIMATION_STEP,
    FISH_MINIMUM_COUNT,
    MAX_DELTA_TIME,
)


class AsciiQuarium:
    """Main controller class for the ASCII art aquarium simulation.

    The AsciiQuarium class manages the complete lifecycle of the aquarium simulation,
    including entity spawning, animation, collision detection, and rendering. It serves
    as the central coordinator between the settings system, entity management, and
    screen backends.

    The class implements a frame-based animation system where all entities (fish, seaweed,
    bubbles, specials) are updated and rendered in each frame. It handles:

    - **Entity Management**: Spawning, updating, and cleanup of all aquarium entities
    - **Animation System**: Frame-based updates with configurable FPS and speed
    - **Collision Detection**: Interactions between entities (fish/shark, fishhook/fish)
    - **Special Events**: Timed spawning of special entities (sharks, whales, ships)
    - **User Interaction**: Mouse/keyboard input handling for interactive features
    - **Resource Management**: Efficient memory usage through entity pooling

    Architecture:
        The class follows a composition pattern where entities are managed in separate
        collections by type (fish, seaweed, bubbles, specials). Each entity implements
        the Actor protocol for consistent update/render behavior.

    Performance:
        - Double-buffered rendering for smooth animations
        - Delta-time based updates for frame-rate independence
        - Efficient collision detection using spatial partitioning
        - Memory pooling for frequently created/destroyed entities

    Attributes:
        settings (Settings): Configuration object controlling all simulation parameters
        seaweed (List[Seaweed]): Collection of seaweed entities providing background animation
        fish (List[Fish]): Main fish population that forms the core of the simulation
        bubbles (List[Bubble]): Bubble effects generated by fish and other entities
        splats (List[Splat]): Temporary splash effects from collisions and impacts
        specials (List[Actor]): Special entities like sharks, whales, ships, hooks
        decor (List[Actor]): Persistent background decoration (treasure chests, castles)

    Example:
        >>> from asciiquarium_redux.util.settings import Settings
        >>> from asciiquarium_redux.backends.terminal import TerminalScreen
        >>>
        >>> settings = Settings(fps=30, density=1.5, color="256")
        >>> aquarium = AsciiQuarium(settings)
        >>> screen = TerminalScreen()
        >>> aquarium.rebuild(screen)
        >>> aquarium.run(screen)  # Start the main animation loop

    See Also:
        - Settings: Configuration management for all simulation parameters
        - Actor: Base protocol for all animated entities
        - Screen: Backend abstraction for cross-platform rendering
        - Entity System Documentation: docs/ENTITY_SYSTEM.md
    """

    # Class-level attribute annotations for linters/type-checkers
    _mouse_buttons: int
    _last_mouse_event_time: float

    def __init__(self, settings: Settings) -> None:
        """Initialize the aquarium with the given settings.

        Sets up the core entity collections and initializes timing/state variables.
        The actual entity spawning happens in rebuild() when a screen is available.

        Args:
            settings: Configuration object with all simulation parameters

        Note:
            After initialization, call rebuild(screen) to populate the aquarium
            with entities before starting the animation loop.
        """
        self.settings: Settings = settings
        self.seaweed: List[Seaweed] = []
        self.fish: List[Fish] = []
        self.bubbles: List[Bubble] = []
        self.splats: List[Splat] = []
        self.specials: List[Actor] = []
        self.decor: List[Actor] = []  # persistent background actors (e.g., treasure chest)
        self._paused: bool = False
        self._special_timer: float = random.uniform(
            self.settings.spawn_start_delay_min, self.settings.spawn_start_delay_max
        )
        self._show_help: bool = False
        self._seaweed_tick: float = 0.0
        self._time: float = 0.0
        self._last_spawn: Dict[str, float] = {}
        self._global_cooldown_until: float = 0.0
        # Track mouse button state for debounce
        self._mouse_buttons: int = 0
        self._last_mouse_event_time: float = 0.0

    def rebuild(self, screen: Screen) -> None:
        """Initialize/reset all entities for the current screen size.

        This method performs a complete rebuild of the aquarium by clearing all
        existing entities and spawning new populations based on screen dimensions
        and current settings. It's called when starting the simulation or when
        the screen size changes.

        Args:
            screen: Screen interface for dimension calculations and spawning
        """
        self._clear_entities()
        self._initialize_seaweed(screen)
        self._initialize_decor(screen)
        self._initialize_fish(screen)

    def _clear_entities(self) -> None:
        """Clear all entity collections and reset timing state."""
        self.seaweed.clear()
        self.fish.clear()
        self.bubbles.clear()
        self.splats.clear()
        self.specials.clear()
        self.decor.clear()
        self._special_timer = random.uniform(self.settings.spawn_start_delay_min, self.settings.spawn_start_delay_max)
        self._seaweed_tick = 0.0

    def _initialize_seaweed(self, screen: Screen) -> None:
        """Create seaweed population based on screen size and settings.

        Args:
            screen: Screen interface for dimension calculations
        """
        # Calculate seaweed count (optional override by config)
        if self.settings.seaweed_count_base is not None and self.settings.seaweed_count_per_80_cols is not None:
            units: float = max(1.0, screen.width / SCREEN_WIDTH_UNIT_DIVISOR)
            base: int = self.settings.seaweed_count_base
            per: float = self.settings.seaweed_count_per_80_cols
            count: int = max(1, int((base + per * units) * self.settings.density * self.settings.seaweed_scale))
        else:
            count = max(1, int((screen.width // SEAWEED_DENSITY_WIDTH_DIVISOR) * self.settings.density * self.settings.seaweed_scale))

        # Create seaweed entities with randomized properties
        for _ in range(count):
            self.seaweed.append(self._make_one_seaweed(screen))

    def _initialize_decor(self, screen: Screen) -> None:
        """Create persistent decorative entities.

        Args:
            screen: Screen interface for positioning calculations
        """
        # Persistent decor: treasure chest
        if getattr(self.settings, "chest_enabled", True):
            try:
                self.decor.extend(spawn_treasure_chest(screen, self))
            except Exception as e:
                # Fail-safe: ignore decor errors so app still runs, but log the issue
                logging.warning(f"Failed to spawn treasure chest: {e}")

    def _initialize_fish(self, screen: Screen) -> None:
        """Create fish population based on screen size and settings.

        Args:
            screen: Screen interface for dimension calculations
        """
        water_top: int = self.settings.waterline_top
        area: int = max(1, (screen.height - (water_top + 4)) * screen.width)

        # Calculate fish count (optional override by config)
        if self.settings.fish_count_base is not None and self.settings.fish_count_per_80_cols is not None:
            units: float = max(1.0, screen.width / SCREEN_WIDTH_UNIT_DIVISOR)
            base: int = int(self.settings.fish_count_base)
            per: float = float(self.settings.fish_count_per_80_cols)
            fish_count: int = max(FISH_MINIMUM_COUNT, int((base + per * units) * self.settings.density * self.settings.fish_scale))
        else:
            fish_count = max(FISH_MINIMUM_COUNT, int(area // FISH_DENSITY_AREA_DIVISOR * self.settings.density * self.settings.fish_scale))

        # Create fish entities using a total-height budget to fit more small fish.
        colours: List[int] = self._palette(screen)
        # Define a nominal base height for budgeting and speed scaling
        base_height: float = 4.0
        target_total_height: int = max(
            FISH_MINIMUM_COUNT * int(base_height),
            int(fish_count * base_height),
        )
        total_height: int = 0
        # Bias selection toward smaller fish (weights inversely proportional to height)
        # and spawn small fish in small groups for visible flocking.
        while total_height < target_total_height:
            direction = self._determine_fish_direction()
            frames = self._choose_fish_frames_biased(direction)
            # If this is a small fish (height<=3), spawn 2-3 together near each other
            group_size = 1
            if len(frames) <= 3:
                group_size = random.randint(2, 3)
            for gi in range(group_size):
                frames_g = frames
                frames_g, colour_mask = self._select_fish_frames_and_mask(direction, colours, frames_g)
                x, y, vx = self._calculate_fish_positioning(direction, frames_g, screen)
                # Slight offset for group members
                if gi > 0:
                    x = max(0, min(screen.width - len(frames_g[0]) - 1, x + random.randint(-3, 3)))
                    y = max(self.settings.waterline_top + 5, min(screen.height - len(frames_g) - 2, y + random.randint(-1, 1)))
                fish = self._create_fish_entity(frames_g, x, y, vx, colour_mask, screen)
                self._configure_fish_behavior(fish)
                self.fish.append(fish)
                total_height += len(frames_g)
                if total_height >= target_total_height:
                    break

    def draw_waterline(self, screen: Screen) -> None:
        """Draw the animated waterline at the top of the aquarium.

        Args:
            screen: Screen interface for rendering operations
        """
        for segment_index, _ in enumerate(WATER_SEGMENTS):
            row: str = waterline_row(segment_index, screen.width)
            waterline_y: int = self.settings.waterline_top + segment_index
            if waterline_y < screen.height:
                colour: int = Screen.COLOUR_WHITE if self.settings.color == "mono" else Screen.COLOUR_CYAN
                screen.print_at(row, 0, waterline_y, colour=colour)

    def _waterline_row(self, segment_index: int, screen: Screen) -> str:
        """Get waterline row content for given segment index.

        Args:
            segment_index: Index of waterline segment (0-based)
            screen: Screen interface for width calculations

        Returns:
            Waterline row string for the segment
        """
        if segment_index < 0 or segment_index >= len(WATER_SEGMENTS):
            return ""
        return waterline_row(segment_index, screen.width)

    def _bubble_hits_waterline(self, bubble_x: int, bubble_y: int, screen: Screen) -> bool:
        """Check if bubble collides with waterline at given position.

        Args:
            bubble_x: Bubble x-coordinate
            bubble_y: Bubble y-coordinate
            screen: Screen interface for boundary checks

        Returns:
            True if bubble hits waterline, False otherwise
        """
        # Convert to index within waterline rows
        segment_index: int = bubble_y - self.settings.waterline_top
        if segment_index < 0 or segment_index >= len(WATER_SEGMENTS):
            return False
        if bubble_x < 0 or bubble_x >= screen.width:
            return False
        row: str = self._waterline_row(segment_index, screen)
        if not row:
            return False
        return row[bubble_x] != ' '

    def draw_castle(self, screen: Screen) -> None:
        """Draw the castle decoration in the bottom-right corner.

        Args:
            screen: Screen interface for rendering operations
        """
        lines: List[str] = CASTLE
        castle_width: int
        castle_height: int
        castle_width, castle_height = sprite_size(lines)
        castle_x: int = max(0, screen.width - castle_width - 2)
        castle_y: int = max(0, screen.height - castle_height - 1)
        if self.settings.color == "mono":
            # In mono, still keep castle opaque within its silhouette
            draw_sprite_masked_with_bg(screen, lines, [''] * len(lines), castle_x, castle_y, Screen.COLOUR_WHITE, Screen.COLOUR_BLACK)
        else:
            # Opaque per-row background to prevent see-through, but no full-rect cutoffs
            draw_sprite_masked_with_bg(screen, lines, CASTLE_MASK, castle_x, castle_y, Screen.COLOUR_WHITE, Screen.COLOUR_BLACK)

    def update(self, dt: float, screen: Screen, frame_no: int) -> None:
        """Update simulation state and render the current frame.

        This method coordinates the complete frame update cycle including entity
        updates, lifecycle management, and rendering in the correct layered order.

        Args:
            dt: Delta time since last update (in seconds)
            screen: Screen interface for rendering and dimension queries
            frame_no: Current frame number for debugging and timing
        """
        dt *= self.settings.speed

        if not self._paused:
            self._update_all_entities(dt, screen)
            self._maybe_restock(dt, screen)

        self._render_all_entities(screen)

    def _update_all_entities(self, dt: float, screen: Screen) -> None:
        """Update all entities and manage their lifecycles.

        This method coordinates entity updates, collision detection, cleanup of
        inactive entities, and spawning of new special entities. It maintains
        the simulation state and timing.

        Args:
            dt: Delta time since last update (in seconds)
            screen: Screen interface for boundary checks and spawning
        """
        self._seaweed_tick += dt

        # Update seaweed entities
        for seaweed in self.seaweed:
            seaweed.update(dt, screen, self)

        # Update decorative entities (treasure chest, etc.)
        self._update_decor_entities(dt, screen)

        # Update fish entities
        for fish in self.fish:
            fish.update(dt, screen, self)

        # Update and filter bubbles with collision detection
        self._update_bubble_entities(dt, screen)

        # Update special entities and filter inactive ones
        self._update_special_entities(dt, screen)

        # Update splat effects and filter inactive ones
        self._update_splat_entities(dt, screen)

        # Handle special entity spawning
        self._manage_special_spawning(dt, screen)

    def _maybe_restock(self, dt: float, screen: Screen) -> None:
        """Replenish fish if the population remains too low for too long."""
        if not getattr(self.settings, "restock_enabled", True):
            return
        target_fish_count, _ = self._compute_target_counts(screen)
        min_frac = float(getattr(self.settings, "restock_min_fraction", 0.6))
        threshold = max(1, int(target_fish_count * min_frac))
        # Track time under threshold
        if not hasattr(self, "_restock_timer"):
            self._restock_timer = 0.0  # type: ignore[attr-defined]
        if len(self.fish) < threshold:
            self._restock_timer += dt  # type: ignore[attr-defined]
        else:
            self._restock_timer = 0.0  # type: ignore[attr-defined]
        if self._restock_timer >= float(getattr(self.settings, "restock_after_seconds", 20.0)):
            # Add up to 25% of target or at least 1 fish, favoring smaller fish
            add_n = max(1, int(target_fish_count * 0.25))
            palette = self._palette(screen)
            for _ in range(add_n):
                self.fish.append(self._make_one_fish(screen, palette))
            self._restock_timer = 0.0  # type: ignore[attr-defined]

    def _update_decor_entities(self, dt: float, screen: Screen) -> None:
        """Update decorative entities with backwards compatibility.

        Args:
            dt: Delta time since last update
            screen: Screen interface for rendering context
        """
        for decoration in self.decor:
            try:
                decoration.update(dt, screen, self)
            except TypeError:
                # Support actors with older update signatures
                decoration.update(dt, screen)  # type: ignore[misc]

    def _update_bubble_entities(self, dt: float, screen: Screen) -> None:
        """Update bubbles with waterline collision detection and lifetime management.

        Args:
            dt: Delta time since last update
            screen: Screen interface for collision detection
        """
        survivors: List[Bubble] = []
        for bubble in self.bubbles:
            bubble.update(dt, screen, self)
            # Kill bubble if it hits any visible waterline character or exceeds lifetime
            if bubble.y < 0:
                continue
            if not bubble.active:  # Check bubble lifetime to prevent memory leaks
                continue
            if self._bubble_hits_waterline(bubble.x, bubble.y, screen):
                continue
            survivors.append(bubble)
        self.bubbles = survivors

    def _update_special_entities(self, dt: float, screen: Screen) -> None:
        """Update special entities and filter inactive ones.

        Args:
            dt: Delta time since last update
            screen: Screen interface for rendering context
        """
        for special_actor in list(self.specials):
            special_actor.update(dt, screen, self)
        self.specials = [special_actor for special_actor in self.specials if getattr(special_actor, "active", True)]

    def _update_splat_entities(self, dt: float, screen: Screen) -> None:
        """Update splat effects and filter inactive ones.

        Args:
            dt: Delta time since last update
            screen: Screen interface for rendering context
        """
        for splat in self.splats:
            splat.update(dt, screen, self)
        self.splats = [splat for splat in self.splats if splat.active]

    def _manage_special_spawning(self, dt: float, screen: Screen) -> None:
        """Handle timing and spawning of special entities.

        Args:
            dt: Delta time since last update
            screen: Screen interface for spawning calculations
        """
        # advance app time and spawn timer regardless of current specials
        self._time += dt
        self._special_timer -= dt
        can_spawn_more: bool = len(self.specials) < int(self.settings.spawn_max_concurrent)
        if can_spawn_more and self._special_timer <= 0 and self._time >= self._global_cooldown_until:
            self.spawn_random(screen)
            self._special_timer = random.uniform(self.settings.spawn_interval_min, self.settings.spawn_interval_max)

    def _render_all_entities(self, screen: Screen) -> None:
        """Render all entities in the correct layered order.

        This method draws all entities in the proper z-order to create the
        layered underwater scene. It handles both mono and color rendering modes.

        Args:
            screen: Screen interface for rendering operations
        """
        self.draw_waterline(screen)
        mono: bool = self.settings.color == "mono"

        # Draw entities in correct z-order: seaweed → decor → fish → castle → bubbles → specials → splats
        self._render_seaweed(screen, mono)
        self._render_decor(screen, mono)
        self._render_fish(screen, mono)
        self._render_castle(screen)
        self._render_bubbles(screen, mono)
        self._render_specials(screen, mono)
        self._render_splats(screen, mono)

        if self._show_help:
            self._draw_help(screen)

    # --- AI sensing hooks (lightweight, O(1) per fish) ---
    # These provide minimal implementations sufficient for steering; they avoid
    # heavy neighbor searches here. For now, neighbors() returns an empty list
    # to keep complexity O(1). Food and predator cues are approximated.

    def bounds(self) -> tuple[int, int]:
        # The double-buffer exposes Screen-like API; width/height are stable in a frame
        # We rely on the active buffer size from recent render path.
        # Fallback: typical UI size from settings.
        try:
            # mypy: ScreenProtocol provides width/height when passed in methods; here we use settings.
            return (self.settings.ui_cols, self.settings.ui_rows)
        except Exception:
            return (120, 40)

    def obstacles(self, fish_id: int, radius_cells: float):
        # Approximate castle bottom-right as an obstacle center; simple point obstacle
        # Map to a few static points near bottom corners for gentle avoid behavior.
        cols, rows = self.bounds()
        from .ai.vector import Vec2  # local import
        return [Vec2(cols - 8.0, rows - 6.0)]

    def neighbors(self, fish_id: int, radius_cells: float):
        # Provide a simple local neighborhood search for AI flocking/chase.
        from .ai.vector import Vec2
        radius2 = float(radius_cells) * float(radius_cells)
        me = None
        for f in self.fish:
            if id(f) == fish_id:
                me = f
                break
        if me is None:
            return []
        mx, my = float(me.x), float(me.y)
        out = []
        for other in self.fish:
            if other is me:
                continue
            dx = float(other.x) - mx
            dy = float(other.y) - my
            if dx * dx + dy * dy <= radius2:
                out.append((id(other), Vec2(float(other.x), float(other.y)), Vec2(float(other.vx), float(other.vy))))
        return out

    def nearest_food(self, fish_id: int):
        # If fish food flakes are present, steer toward the closest flake roughly.
        # Return (direction unit vector, distance). If none, distance=inf.
        from math import hypot
        from .ai.vector import Vec2
        from .entities.specials import FishFoodFlake  # type: ignore
        # Find the fish object by id
        fx: float | None = None
        fy: float | None = None
        for f in self.fish:
            if id(f) == fish_id:
                fx, fy = float(f.x), float(f.y)
                break
        if fx is None or fy is None:
            return (Vec2(0.0, 0.0), float("inf"))
        # Scan specials for fish food flakes positions (cheap linear scan)
        targets: list[tuple[float, float]] = []
        for s in self.specials:
            # Only consider actual fish food flakes that are active
            if isinstance(s, FishFoodFlake) and getattr(s, "active", True):
                targets.append((float(getattr(s, "x", 0.0)), float(getattr(s, "y", 0.0))))
        if not targets:
            return (Vec2(0.0, 0.0), float("inf"))
        # Pick nearest
        tx, ty, best_d = fx, fy, float("inf")
        for (x, y) in targets:
            d = hypot(x - fx, y - fy)
            if d < best_d:
                best_d = d
                tx, ty = x, y
        if best_d == float("inf") or best_d <= 1e-6:
            return (Vec2(0.0, 0.0), best_d)
        dir_vec = Vec2((tx - fx) / best_d, (ty - fy) / best_d)
        return (dir_vec, best_d)

    def predator_vector(self, fish_id: int):
        # Consider shark positions as predators; flee away from the closest teeth point approximated by entity x,y.
        from math import hypot
        from .ai.vector import Vec2
        fx: float | None = None
        fy: float | None = None
        for f in self.fish:
            if id(f) == fish_id:
                fx, fy = float(f.x), float(f.y)
                break
        if fx is None or fy is None:
            return (Vec2(0.0, 0.0), float("inf"))
        preds: list[tuple[float, float]] = []
        for s in self.specials:
            # Sharks have attributes x,y and update like other actors
            if s.__class__.__name__.lower() == "shark" and getattr(s, "active", True):
                preds.append((float(getattr(s, "x", 0.0)), float(getattr(s, "y", 0.0))))
        if not preds:
            return (Vec2(0.0, 0.0), float("inf"))
        # Find nearest predator and return normalized away-vector
        tx, ty, best_d = fx, fy, float("inf")
        for (x, y) in preds:
            d = hypot(x - fx, y - fy)
            if d < best_d:
                best_d = d
                tx, ty = x, y
        if best_d == float("inf") or best_d <= 1e-6:
            return (Vec2(0.0, 0.0), best_d)
        dir_away = Vec2((fx - tx) / best_d, (fy - ty) / best_d)
        return (dir_away, best_d)

    def nearest_prey(self, fish_id: int):
        """Find the closest smaller fish to the given fish, if any.

        Preference is to eat fish food; this is only used by the brain when hunger is high.
        Returns a unit direction vector and distance; distance=inf if none.
        """
        from math import hypot
        from .ai.vector import Vec2
        # Locate self and get size
        me = None
        for f in self.fish:
            if id(f) == fish_id:
                me = f
                break
        if me is None:
            return (Vec2(0.0, 0.0), float("inf"))
        mx, my = float(me.x), float(me.y)
        my_h = int(getattr(me, "height", len(me.frames)))
        best: tuple[float, float] | None = None
        best_d = float("inf")
        for other in self.fish:
            if other is me:
                continue
            # Only consider strictly smaller fish
            oh = int(getattr(other, "height", len(other.frames)))
            if oh >= my_h:
                continue
            # Exclude any special big fish types (by class name heuristic or presence in specials)
            cname = other.__class__.__name__.lower()
            if "big" in cname or "special" in cname:
                continue
            ox, oy = float(other.x), float(other.y)
            d = hypot(ox - mx, oy - my)
            if d < best_d:
                best_d = d
                best = (ox, oy)
        if best is None or best_d == float("inf"):
            return (Vec2(0.0, 0.0), float("inf"))
        bx, by = best
        if best_d <= 1e-6:
            return (Vec2(0.0, 0.0), best_d)
        return (Vec2((bx - mx) / best_d, (by - my) / best_d), best_d)

    # --- New AI world hooks ---
    def shelters(self):
        """Return rough shelter points (e.g., behind decor like castle/chest)."""
        cols, rows = self.bounds()
        from .ai.vector import Vec2
        pts = []
        # Castle bottom-right-ish corner if enabled
        if getattr(self.settings, "castle_enabled", True):
            pts.append(Vec2(max(2.0, cols - 10.0), max(2.0, rows - 6.0)))
        # Chest bottom-left-ish if present
        try:
            from .entities.specials import TreasureChest  # type: ignore
            for d in self.decor:
                if isinstance(d, TreasureChest):
                    pts.append(Vec2(float(d.x + 2), float(d.y)))
        except Exception:
            pass
        return pts

    def size_of(self, fish_id: int) -> int:
        for f in self.fish:
            if id(f) == fish_id:
                return int(getattr(f, "height", len(f.frames)))
        return 3

    def _render_seaweed(self, screen: Screen, mono: bool) -> None:
        """Render seaweed entities with animation.

        Args:
            screen: Screen interface for rendering
            mono: Whether to use monochrome rendering mode
        """
        for seaweed in self.seaweed:
            animation_tick: int = int(self._seaweed_tick / SEAWEED_ANIMATION_STEP)
            seaweed.draw(screen, animation_tick, mono)

    def _render_decor(self, screen: Screen, mono: bool) -> None:
        """Render decorative entities with backwards compatibility.

        Args:
            screen: Screen interface for rendering
            mono: Whether to use monochrome rendering mode
        """
        for decoration in self.decor:
            try:
                decoration.draw(screen, mono)  # type: ignore[call-arg]
            except TypeError:
                decoration.draw(screen)

    def _render_fish(self, screen: Screen, mono: bool) -> None:
        """Render fish entities with proper z-order sorting.

        Args:
            screen: Screen interface for rendering
            mono: Whether to use monochrome rendering mode
        """
        # Draw fish back-to-front by z to mimic Perl's fish_start..fish_end layering
        fish_to_draw: List[Fish] = sorted(self.fish, key=lambda fish: getattr(fish, 'z', 0))
        for fish in fish_to_draw:
            if mono:
                draw_sprite(screen, fish.frames, int(fish.x), int(fish.y), Screen.COLOUR_WHITE)
            else:
                fish.draw(screen)

    def _render_castle(self, screen: Screen) -> None:
        """Render castle decoration if enabled.

        Args:
            screen: Screen interface for rendering
        """
        if getattr(self.settings, "castle_enabled", True):
            self.draw_castle(screen)

    def _render_bubbles(self, screen: Screen, mono: bool) -> None:
        """Render bubble entities with visual variety.

        Args:
            screen: Screen interface for rendering
            mono: Whether to use monochrome rendering mode
        """
        for bubble in self.bubbles:
            if mono:
                if 0 <= bubble.y < screen.height:
                    bubble_char: str = random.choice([".", "o", "O"])
                    screen.print_at(bubble_char, bubble.x, bubble.y, colour=Screen.COLOUR_WHITE)
            else:
                bubble.draw(screen)

    def _render_specials(self, screen: Screen, mono: bool) -> None:
        """Render special entities with backwards compatibility.

        Args:
            screen: Screen interface for rendering
            mono: Whether to use monochrome rendering mode
        """
        for special_actor in list(self.specials):
            try:
                special_actor.draw(screen, mono)  # type: ignore[call-arg]
            except TypeError:
                special_actor.draw(screen)

    def _render_splats(self, screen: Screen, mono: bool) -> None:
        """Render splat effects on top of all other entities.

        Args:
            screen: Screen interface for rendering
            mono: Whether to use monochrome rendering mode
        """
        for splat in self.splats:
            splat.draw(screen, mono)

    def spawn_random(self, screen: Screen) -> None:
        """Spawn a random special entity based on configured weights and cooldowns.

        This method implements weighted random selection of special entities with
        support for per-type cooldowns and global spawn limits. It prevents
        duplicate fishhooks and respects timing constraints.

        Args:
            screen: Screen interface for positioning calculations
        """
        # Weighted random selection based on settings.specials_weights
        choices: List[Tuple[str, Any]] = [
            ("shark", spawn_shark),
            ("fishhook", spawn_fishhook),
            ("whale", spawn_whale),
            ("ship", spawn_ship),
            ("ducks", spawn_ducks),
            ("dolphins", spawn_dolphins),
            ("swan", spawn_swan),
            ("monster", spawn_monster),
            ("big_fish", spawn_big_fish),
        ]
        weighted_choices: List[Tuple[float, str, Any]] = []
        current_time: float = self._time
        # Detect existing fishhook so we can avoid selecting it while active
        hook_active: bool = any(isinstance(special, FishHook) and special.active for special in self.specials)
        for entity_name, spawn_function in choices:
            if entity_name == "fishhook" and hook_active:
                continue
            weight: float = float(self.settings.specials_weights.get(entity_name, 1.0))
            if weight <= 0:
                continue
            # filter by per-type cooldowns
            cooldown_duration: float = float(self.settings.specials_cooldowns.get(entity_name, 0.0))
            last_spawn_time: float = self._last_spawn.get(entity_name, -1e9)
            if current_time - last_spawn_time < cooldown_duration:
                continue
            weighted_choices.append((weight, entity_name, spawn_function))
        if not weighted_choices:
            return
        total_weight: float = sum(weight for weight, _, _ in weighted_choices)
        random_value: float = random.uniform(0.0, total_weight)
        weight_accumulator: float = 0.0
        chosen_name: str = weighted_choices[-1][1]
        spawner: Any = weighted_choices[-1][2]
        for weight, entity_name, spawn_function in weighted_choices:
            weight_accumulator += weight
            if random_value <= weight_accumulator:
                spawner = spawn_function
                chosen_name = entity_name
                break
        new_specials = spawner(screen, self)
        if not new_specials:
            # Spawner declined (e.g., screen too small); do not consume cooldowns
            return
        self.specials.extend(new_specials)
        # register cooldowns
        self._last_spawn[chosen_name] = current_time
        if self.settings.spawn_cooldown_global > 0:
            self._global_cooldown_until = current_time + float(self.settings.spawn_cooldown_global)

    def _palette(self, screen: Screen) -> List[int]:
        """Get color palette appropriate for current color mode.

        Args:
            screen: Screen interface for color capability detection

        Returns:
            List of color codes available for fish rendering
        """
        if self.settings.color == "mono":
            return [Screen.COLOUR_WHITE]
        return [
            Screen.COLOUR_CYAN,
            Screen.COLOUR_YELLOW,
            Screen.COLOUR_GREEN,
            Screen.COLOUR_RED,
            Screen.COLOUR_MAGENTA,
            Screen.COLOUR_BLUE,
            Screen.COLOUR_WHITE,
        ]

    def _draw_help(self, screen: Screen) -> None:
        """Draw help overlay with controls and current settings.

        Args:
            screen: Screen interface for rendering operations
        """
        lines: List[str] = [
            "Asciiquarium Redux",
            f"fps: {self.settings.fps}  density: {self.settings.density}  speed: {self.settings.speed}  color: {self.settings.color}",
            f"seed: {self.settings.seed if self.settings.seed is not None else 'random'}",
            "",
            "Controls:",
            "  q: quit    p: pause/resume    r: rebuild    f: feed fish",
            "  Left-click: drop fishhook to clicked spot",
            "  h/?: toggle this help",
        ]
        help_x: int = 2
        help_y: int = 1
        help_width: int = max(len(line) for line in lines) + 4
        help_height: int = len(lines) + 2
        screen.print_at("+" + "-" * (help_width - 2) + "+", help_x, help_y, colour=Screen.COLOUR_WHITE)
        for line_index, row in enumerate(lines, start=1):
            screen.print_at("|" + row.ljust(help_width - 2) + "|", help_x, help_y + line_index, colour=Screen.COLOUR_WHITE)
        screen.print_at("+" + "-" * (help_width - 2) + "+", help_x, help_y + help_height - 1, colour=Screen.COLOUR_WHITE)

    # --- Live population management helpers ---
    def _compute_target_counts(self, screen: Screen) -> tuple[int, int]:
        """Return (fish_count, seaweed_count) desired for current settings and screen size."""
        # Seaweed
        if self.settings.seaweed_count_base is not None and self.settings.seaweed_count_per_80_cols is not None:
            screen_units = max(1.0, screen.width / SCREEN_WIDTH_UNIT_DIVISOR)
            base_count = self.settings.seaweed_count_base
            per_unit_count = self.settings.seaweed_count_per_80_cols
            seaweed_count = max(1, int((base_count + per_unit_count * screen_units) * self.settings.density * self.settings.seaweed_scale))
        else:
            seaweed_count = max(1, int((screen.width // SEAWEED_DENSITY_WIDTH_DIVISOR) * self.settings.density * self.settings.seaweed_scale))

        # Fish
        water_top = self.settings.waterline_top
        water_area = max(1, (screen.height - (water_top + 4)) * screen.width)
        if self.settings.fish_count_base is not None and self.settings.fish_count_per_80_cols is not None:
            screen_units = max(1.0, screen.width / SCREEN_WIDTH_UNIT_DIVISOR)
            base_count = int(self.settings.fish_count_base)
            per_unit_count = float(self.settings.fish_count_per_80_cols)
            fish_count = max(FISH_MINIMUM_COUNT, int((base_count + per_unit_count * screen_units) * self.settings.density * self.settings.fish_scale))
        else:
            fish_count = max(FISH_MINIMUM_COUNT, int(water_area // FISH_DENSITY_AREA_DIVISOR * self.settings.density * self.settings.fish_scale))
        return fish_count, seaweed_count

    def _make_one_fish(self, screen: Screen, palette: List[int] | None = None) -> Fish:
        """Create a new fish with randomized properties and behavior.

        This method handles the complex fish initialization process including
        direction selection, frame/mask matching, positioning, and behavior
        configuration.

        Args:
            screen: Screen interface for positioning calculations
            palette: Optional color palette, defaults to screen-appropriate colors

        Returns:
            Fully configured Fish entity ready for animation
        """
        direction = self._determine_fish_direction()
        frames, colour_mask = self._select_fish_frames_and_mask(direction, palette or self._palette(screen))
        x, y, vx = self._calculate_fish_positioning(direction, frames, screen)

        fish = self._create_fish_entity(frames, x, y, vx, colour_mask, screen)
        self._configure_fish_behavior(fish)

        return fish

    def _determine_fish_direction(self) -> int:
        """Determine fish swimming direction based on configured bias.

        Returns:
            1 for rightward movement, -1 for leftward movement
        """
        return 1 if random.random() < float(self.settings.fish_direction_bias) else -1

    def _select_fish_frames_and_mask(self, direction: int, colours: List[int], frames: List[str] | None = None) -> tuple[List[str], List[str] | None]:
        """Select fish frames and create matching color mask.

        Args:
            direction: Fish swimming direction (1 for right, -1 for left)
            colours: Available color palette for fish

        Returns:
            Tuple of (frames, colour_mask) where colour_mask may be None
        """
        if frames is None:
            frames = random_fish_frames(direction)
        colour = random.choice(colours)

        # Build initial colour mask consistent with frames
        from .entities.core import (
            FISH_RIGHT, FISH_LEFT, FISH_RIGHT_MASKS, FISH_LEFT_MASKS,
        )

        if direction > 0:
            pairs = list(zip(FISH_RIGHT, FISH_RIGHT_MASKS))
        else:
            pairs = list(zip(FISH_LEFT, FISH_LEFT_MASKS))

        # Find matching mask for chosen frames
        mask = self._find_matching_mask(frames, pairs, direction)

        colour_mask = None
        if mask is not None and self.settings.color != "mono":
            from .util import randomize_colour_mask
            colour_mask = randomize_colour_mask(mask)

        return frames, colour_mask

    def _find_matching_mask(self, frames: List[str], pairs: List[tuple], direction: int) -> List[str] | None:
        """Find the color mask that matches the selected fish frames.

        Args:
            frames: Selected fish animation frames
            pairs: List of (frame_set, mask_set) tuples
            direction: Fish swimming direction for fallback logic

        Returns:
            Matching mask or None if no match found
        """
        # Try direct identity match first
        for fset, mset in pairs:
            if fset is frames:
                return mset

        # If identity didn't match (due to equality semantics), fallback by index
        from .entities.core import FISH_RIGHT, FISH_LEFT, FISH_RIGHT_MASKS, FISH_LEFT_MASKS

        try:
            frame_index = (FISH_RIGHT if direction > 0 else FISH_LEFT).index(frames)
            return (FISH_RIGHT_MASKS if direction > 0 else FISH_LEFT_MASKS)[frame_index]
        except ValueError:
            return None

    def _calculate_fish_positioning(self, direction: int, frames: List[str], screen: Screen) -> tuple[float, float, float]:
        """Calculate initial fish position and velocity.

        Args:
            direction: Fish swimming direction
            frames: Fish animation frames for size calculation
            screen: Screen interface for boundary calculations

        Returns:
            Tuple of (x, y, vx) representing position and velocity
        """
        fish_width, fish_height = sprite_size(frames)
        water_top = self.settings.waterline_top

        # initial y will be refined by Fish.respawn; use temp fallback
        fish_y = random.randint(max(water_top + 3, 1), max(water_top + 3, screen.height - fish_height - 2))
        fish_x = (-fish_width if direction > 0 else screen.width)
        speed_scale = self._speed_scale_for_height(fish_height)
        velocity_x = random.uniform(self.settings.fish_speed_min, self.settings.fish_speed_max) * speed_scale * direction

        return fish_x, fish_y, velocity_x

    def _create_fish_entity(self, frames: List[str], x: float, y: float, vx: float, colour_mask: List[str] | None, screen: Screen) -> Fish:
        """Create the Fish entity with all required parameters.

        Args:
            frames: Fish animation frames
            x, y: Initial position coordinates
            vx: Initial velocity
            colour_mask: Optional color mask for multi-color fish
            screen: Screen interface for palette generation

        Returns:
            Configured Fish entity
        """
        colours = self._palette(screen)
        colour = random.choice(colours)

        # Scale per-fish speed range based on its height so small fish are faster
        _, fish_height = sprite_size(frames)
        speed_scale = self._speed_scale_for_height(fish_height)
        return Fish(
            frames=frames,
            x=x,
            y=y,
            vx=vx,
            colour=colour,
            colour_mask=colour_mask,
            speed_min=self.settings.fish_speed_min * speed_scale,
            speed_max=self.settings.fish_speed_max * speed_scale,
            bubble_min=self.settings.fish_bubble_min,
            bubble_max=self.settings.fish_bubble_max,
            band_low_frac=(self.settings.fish_y_band[0] if self.settings.fish_y_band else 0.0),
            band_high_frac=(self.settings.fish_y_band[1] if self.settings.fish_y_band else 1.0),
            waterline_top=self.settings.waterline_top,
            water_rows=len(WATER_SEGMENTS),
        )

    def _configure_fish_behavior(self, fish: Fish) -> None:
        """Configure fish behavior parameters and timers.

        Args:
            fish: Fish entity to configure
        """
        # Initialize bubble timer from configured range
        fish.next_bubble = random.uniform(self.settings.fish_bubble_min, self.settings.fish_bubble_max)

        # Pass turning behavior config
        fish.turn_enabled = bool(getattr(self.settings, "fish_turn_enabled", True))
        fish.turn_chance_per_second = float(getattr(self.settings, "fish_turn_chance_per_second", 0.01))
        fish.turn_min_interval = float(getattr(self.settings, "fish_turn_min_interval", 6.0))
        fish.turn_shrink_seconds = float(getattr(self.settings, "fish_turn_shrink_seconds", 0.35))
        fish.turn_expand_seconds = float(getattr(self.settings, "fish_turn_expand_seconds", 0.35))

    def _choose_fish_frames_biased(self, direction: int) -> List[str]:
        """Choose fish frames with a bias toward smaller (shorter) fish.

        Weights are inversely proportional to height, so shorter fish are more likely.
        """
        from .entities.core import FISH_RIGHT, FISH_LEFT
        choices = FISH_RIGHT if direction > 0 else FISH_LEFT
        heights = [len(fr) for fr in choices]
        # Avoid division by zero and cap extremes
        weights = [1.0 / max(1, h) for h in heights]
        # random.choices expects a population and weights of same length
        return random.choices(choices, weights=weights, k=1)[0]

    def _speed_scale_for_height(self, height: int) -> float:
        """Compute a speed scale where smaller fish are faster and larger are slower.

        Uses a nominal base height of 4 rows; clamps to a reasonable range.
        """
        base_height = 4.0
        raw = base_height / max(1.0, float(height))
        # Clamp to avoid extremes
        return max(0.6, min(1.5, raw))

    def _make_one_seaweed(self, screen: Screen) -> Seaweed:
        seaweed_height = random.randint(SEAWEED_HEIGHT_MIN, SEAWEED_HEIGHT_MAX)
        seaweed_x = random.randint(1, max(1, screen.width - 3))
        base_y = screen.height - 2
        seaweed = Seaweed(x=seaweed_x, base_y=base_y, height=seaweed_height, phase=random.randint(0, SEAWEED_PHASE_MAX))
        # Apply configured lifecycle ranges (and initialize current params within those ranges)
        seaweed.sway_min = self.settings.seaweed_sway_min
        seaweed.sway_max = self.settings.seaweed_sway_max
        seaweed.lifetime_min_cfg = self.settings.seaweed_lifetime_min
        seaweed.lifetime_max_cfg = self.settings.seaweed_lifetime_max
        seaweed.regrow_delay_min_cfg = self.settings.seaweed_regrow_delay_min
        seaweed.regrow_delay_max_cfg = self.settings.seaweed_regrow_delay_max
        seaweed.growth_rate_min_cfg = self.settings.seaweed_growth_rate_min
        seaweed.growth_rate_max_cfg = self.settings.seaweed_growth_rate_max
        seaweed.shrink_rate_min_cfg = self.settings.seaweed_shrink_rate_min
        seaweed.shrink_rate_max_cfg = self.settings.seaweed_shrink_rate_max
        # initialize current dynamics based on configured ranges
        seaweed.sway_speed = random.uniform(seaweed.sway_min, seaweed.sway_max)
        seaweed.lifetime_max = random.uniform(seaweed.lifetime_min_cfg, seaweed.lifetime_max_cfg)
        seaweed.regrow_delay_max = random.uniform(seaweed.regrow_delay_min_cfg, seaweed.regrow_delay_max_cfg)
        seaweed.growth_rate = random.uniform(seaweed.growth_rate_min_cfg, seaweed.growth_rate_max_cfg)
        seaweed.shrink_rate = random.uniform(seaweed.shrink_rate_min_cfg, seaweed.shrink_rate_max_cfg)
        return seaweed

    def adjust_populations(self, screen: Screen):
        """Incrementally add/remove fish and seaweed to match target counts without a full rebuild."""
        target_fish_count, target_seaweed_count = self._compute_target_counts(screen)
        # Adjust seaweed first (background)
        current_seaweed_count = len(self.seaweed)
        if target_seaweed_count > current_seaweed_count:
            for _ in range(target_seaweed_count - current_seaweed_count):
                self.seaweed.append(self._make_one_seaweed(screen))
        elif target_seaweed_count < current_seaweed_count:
            # Remove from end for predictability
            del self.seaweed[target_seaweed_count:]
        # Adjust fish
        current_fish_count = len(self.fish)
        if target_fish_count > current_fish_count:
            palette = self._palette(screen)
            for _ in range(target_fish_count - current_fish_count):
                self.fish.append(self._make_one_fish(screen, palette))
        elif target_fish_count < current_fish_count:
            del self.fish[target_fish_count:]


def run(screen: Screen, settings: Settings):
    """Main game loop for the ASCII art aquarium simulation.

    This function manages the complete game execution including initialization,
    event processing, and frame-by-frame animation updates. It handles keyboard
    and mouse input, screen resizing, and maintains consistent frame rates.

    Args:
        screen: Screen interface for rendering and input
        settings: Configuration object with all simulation parameters
    """
    app, db, timing_state = _initialize_game_state(screen, settings)

    while True:
        timing_state = _update_frame_timing(timing_state, settings)

        # Process input events and handle special cases
        event = screen.get_event()
        if _handle_keyboard_events(event, app, screen):
            return  # User requested quit

        _handle_mouse_events(event, app, screen, settings, timing_state["now"])

        # Handle screen resize
        if screen.has_resized():
            from asciimatics.exceptions import ResizeScreenError  # type: ignore
            raise ResizeScreenError("Screen resized")

        # Render frame and manage timing
        _render_frame(app, db, timing_state)
        _manage_frame_rate(timing_state, settings)


def _initialize_game_state(screen: Screen, settings: Settings) -> tuple[AsciiQuarium, DoubleBufferedScreen, dict]:
    """Initialize the game application and screen buffers.

    Args:
        screen: Screen interface for rendering
        settings: Configuration object

    Returns:
        Tuple of (app, double_buffer, timing_state)
    """
    app = AsciiQuarium(settings)
    # Wrap the screen with a double buffer to reduce flicker
    db = DoubleBufferedScreen(screen)
    app.rebuild(screen)

    timing_state = {
        "last": time.time(),
        "frame_no": 0,
        "target_dt": 1.0 / max(1, settings.fps),
        "now": time.time(),
        "dt": 0.0
    }

    return app, db, timing_state


def _update_frame_timing(timing_state: dict, settings: Settings) -> dict:
    """Update timing calculations for the current frame.

    Args:
        timing_state: Dictionary containing timing information
        settings: Configuration object for FPS calculations

    Returns:
        Updated timing state dictionary
    """
    now = time.time()
    dt = min(MAX_DELTA_TIME, now - timing_state["last"])

    return {
        **timing_state,
        "now": now,
        "dt": dt,
        "last": now
    }


def _handle_keyboard_events(event, app: AsciiQuarium, screen: Screen) -> bool:
    """Process keyboard input events.

    Args:
        event: Input event from screen
        app: AsciiQuarium instance to control
        screen: Screen interface for operations

    Returns:
        True if quit was requested, False otherwise
    """
    from asciimatics.event import KeyboardEvent  # type: ignore

    key = event.key_code if isinstance(event, KeyboardEvent) else None
    if key is None:
        return False

    if key in (ord("q"), ord("Q")):
        return True

    if key in (ord("p"), ord("P")):
        app._paused = not app._paused
    elif key in (ord("r"), ord("R")):
        app.rebuild(screen)
    elif key in (ord("h"), ord("H"), ord("?")):
        app._show_help = not app._show_help
    elif key in (ord("t"), ord("T")):
        _handle_debug_fish_turn(app)
    elif key in (ord("f"), ord("F")):
        app.specials.extend(spawn_fish_food(screen, app))
    elif key == ord(" "):
        _handle_fishhook_toggle(app, screen)

    return False


def _handle_debug_fish_turn(app: AsciiQuarium) -> None:
    """Force a random fish to start turning (debug/verification feature).

    Args:
        app: AsciiQuarium instance containing fish
    """
    unhooked_fish = [fish for fish in app.fish if not getattr(fish, 'hooked', False)]
    if unhooked_fish:
        selected_fish = random.choice(unhooked_fish)
        try:
            selected_fish.start_turn()
        except Exception as e:
            # Log fish turning errors but continue operation
            logging.debug(f"Fish turn failed: {e}")


def _handle_fishhook_toggle(app: AsciiQuarium, screen: Screen) -> None:
    """Handle spacebar fishhook toggle (drop or retract).

    Args:
        app: AsciiQuarium instance to modify
        screen: Screen interface for spawning
    """
    active_hooks = [special for special in app.specials if isinstance(special, FishHook) and special.active]
    if active_hooks:
        # Retract existing hook on space
        for hook in active_hooks:
            if hasattr(hook, "retract_now"):
                hook.retract_now()
    else:
        app.specials.extend(spawn_fishhook(screen, app))


def _handle_mouse_events(event, app: AsciiQuarium, screen: Screen, settings: Settings, now: float) -> None:
    """Process mouse input events for fishhook interaction.

    Args:
        event: Input event from screen
        app: AsciiQuarium instance to modify
        screen: Screen interface for boundary checks
        settings: Configuration for water boundaries
        now: Current timestamp for debouncing
    """
    from asciimatics.event import MouseEvent  # type: ignore

    if isinstance(event, MouseEvent):
        # Spawn only on left button down transition (debounce)
        left_button_current = 1 if (event.buttons & 1) else 0
        left_button_previous = 1 if (app._mouse_buttons & 1) else 0

        if left_button_current and not left_button_previous:
            click_x = int(event.x)
            click_y = int(event.y)
            water_top = settings.waterline_top

            # Only accept clicks below waterline and above bottom-1
            if water_top + 1 <= click_y <= screen.height - 2:
                active_hooks = [special for special in app.specials if isinstance(special, FishHook) and special.active]
                if active_hooks:
                    # Retract existing hook on click
                    for hook in active_hooks:
                        if hasattr(hook, "retract_now"):
                            hook.retract_now()
                else:
                    app.specials.extend(spawn_fishhook_to(screen, app, click_x, click_y))

        app._mouse_buttons = event.buttons
        app._last_mouse_event_time = now
    else:
        # If we haven't seen a mouse event for a short while, assume release
        if app._mouse_buttons != 0 and (now - app._last_mouse_event_time) > 0.2:
            app._mouse_buttons = 0


def _render_frame(app: AsciiQuarium, db: DoubleBufferedScreen, timing_state: dict) -> None:
    """Render a single frame of the animation.

    Args:
        app: AsciiQuarium instance to render
        db: Double-buffered screen for smooth rendering
        timing_state: Timing information for the frame
    """
    db.clear()
    app.update(timing_state["dt"], cast(Screen, db), timing_state["frame_no"])
    db.flush()
    timing_state["frame_no"] += 1


def _manage_frame_rate(timing_state: dict, settings: Settings) -> None:
    """Manage frame rate by sleeping to maintain target FPS.

    Args:
        timing_state: Timing information for calculations
        settings: Configuration object for FPS target
    """
    elapsed = time.time() - timing_state["now"]
    sleep_for = max(0.0, timing_state["target_dt"] - elapsed)
    time.sleep(sleep_for)
