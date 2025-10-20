from __future__ import annotations

from typing import TYPE_CHECKING

from ..screen_compat import Screen
from ..util import draw_sprite, draw_sprite_masked_with_bg, draw_sprite_masked

if TYPE_CHECKING:
    from ..protocols import ScreenProtocol, AsciiQuariumProtocol

class Actor:
    """Base protocol defining the interface for all animated entities in the aquarium.

    The Actor protocol establishes a common interface that all entities must implement
    to participate in the aquarium's update/render cycle. This protocol enables
    polymorphic entity management and ensures consistent behavior across different
    entity types.

    Design Philosophy:
        The Actor protocol follows the "composition over inheritance" principle,
        allowing entities to implement the required interface without forcing
        a specific inheritance hierarchy. This design provides flexibility for
        diverse entity implementations while maintaining system consistency.

    Protocol Methods:
        All implementing classes must provide these three core methods to integrate
        with the entity management system. The protocol ensures type safety and
        consistent interfaces across the entire entity hierarchy.

    Performance:
        The protocol interface is designed for high-frequency calls (20-60 FPS)
        with minimal overhead. Method signatures are optimized for common use
        cases while providing necessary flexibility for diverse entity behaviors.

    Implementation Examples:
        - Fish: Complex movement, bubble generation, and interaction behaviors
        - Seaweed: Lifecycle management with growth/death animations
        - Bubble: Simple upward movement with automatic cleanup
        - Special Entities: Sharks, whales, ships with unique behaviors
        - Environmental: Static decorations like treasure chests and castles

    Usage Pattern:
        ```python
        # Entity collections use the common Actor interface
        entities: List[Actor] = [fish1, seaweed1, bubble1, shark1]

        # Polymorphic updates and rendering
        for entity in entities:
            entity.update(dt, screen, app)
            if entity.active:
                entity.draw(screen, mono=color_mode == "mono")
            else:
                entities.remove(entity)  # Cleanup inactive entities
        ```

    See Also:
        - Fish, Seaweed, Bubble: Core entity implementations
        - AsciiQuarium: Main class that manages Actor collections
        - Entity System Documentation: docs/ENTITY_SYSTEM.md
    """

    @property
    def scene_x(self) -> float:
        """Scene X coordinate (leftmost in scene = 0)."""
        ...

    @property
    def scene_y(self) -> float:
        """Scene Y coordinate (topmost in scene = 0)."""
        ...

    def update(self, dt: float, screen: "ScreenProtocol", app: "AsciiQuariumProtocol") -> None:
        """Update entity state for the current frame.

        Called once per frame to advance entity animations, handle physics,
        process interactions, and manage entity-specific state changes.

        Args:
            dt: Time elapsed since last update (in seconds)
            screen: Screen abstraction for dimension and rendering context
            app: Reference to main AsciiQuarium instance for global state access

        Implementation Notes:
            - Must handle variable dt for frame-rate independence
            - Should update position, animation timers, and internal state
            - May spawn new entities (bubbles, effects) via app reference
            - Should handle edge cases like screen boundary conditions
        """
        ...

    def draw(self, screen: "ScreenProtocol", mono: bool = False) -> None:
        """Render entity visual representation to the screen.

        Called once per frame after update() to draw the entity's current
        visual state. Must handle different color modes and screen constraints.

        Args:
            screen: Screen abstraction for rendering operations
            mono: Whether to use monochrome rendering (no colors)

        Implementation Notes:
            - Must respect screen boundaries and handle clipping
            - Should support both color and monochrome rendering modes
            - May use screen.print_at() for text or draw_sprite() for graphics
            - Should handle transparency and layering appropriately
        """
        ...

    def draw_sprite(
            self,
            app: "AsciiQuariumProtocol",
            screen: "ScreenProtocol",
            img: list[str],
            img_mask: list[str],
            px: int,
            py: int,
            primary_colour: int,
            background_colour: int = Screen.COLOUR_BLACK,
    ):
        """Identify the proper render method and draw sprite.

        This is a helper method to abstract away the difference between
        `draw_sprite`, `draw_sprite_masked` and `draw_sprite_masked_with_bg`.

        Args:
            app: Reference to main AsciiQuarium instance for global state access
            screen: Screen abstraction for rendering operations
            img: String representation of the sprite image
            img_mask: String representation of the sprite mask image
            px: X coordinate for the top-left corner of the sprite
            py: Y coordinate for the top-left corner of the sprite
            primary_colour: Primary colour of the sprite
            background_colour: Background colour for masked sprites

        Implementation Notes:
            - Should be called from draw() on the child class after appropriate
                variables have been set up
        """
        if app.settings.color == "mono":
            draw_sprite(screen, img, px, py, Screen.COLOUR_WHITE)
        else:
            if app.settings.solid_fish:
                draw_sprite_masked_with_bg(
                    screen,
                    img,
                    img_mask,
                    px,
                    py,
                    primary_colour,
                    background_colour
                )
            else:
                draw_sprite_masked(
                    screen,
                    img,
                    img_mask,
                    px,
                    py,
                    primary_colour
                )

    @property
    def active(self) -> bool:
        """Check if entity should remain in the simulation.

        Returns True if the entity should continue updating and rendering,
        False if it should be removed from entity collections for cleanup.

        Returns:
            bool: True to keep entity active, False to mark for removal

        Implementation Notes:
            - Used by entity management system for automatic cleanup
            - Should return False when entity is off-screen, expired, or destroyed
            - Enables automatic memory management without manual tracking
        """
        ...
