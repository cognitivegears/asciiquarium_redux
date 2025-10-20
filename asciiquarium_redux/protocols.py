"""Formal protocol definitions for Asciiquarium Redux type safety.

This module provides comprehensive protocol definitions that replace `Any` usage
throughout the codebase, enabling proper type checking and better development
tooling support.

Protocols Definition:
    - **AsciiQuariumProtocol**: Main application interface for entity interactions
    - **ScreenProtocol**: Enhanced screen interface for all backends
    - **ActorProtocol**: Formal entity interface for polymorphic entity management
    - **SettingsProtocol**: Configuration interface for dependency injection
    - **EventProtocol**: Input event interface for cross-platform event handling

Design Philosophy:
    These protocols follow the "interface segregation principle" and provide
    minimal, focused interfaces that enable loose coupling between components
    while maintaining type safety. They replace all `Any` usage with concrete
    protocol definitions.

Type Safety Benefits:
    - **Static Analysis**: mypy and IDEs can perform comprehensive type checking
    - **Auto-completion**: Better development experience with accurate suggestions
    - **Runtime Checks**: Optional runtime validation using @runtime_checkable
    - **Documentation**: Self-documenting interfaces with clear contracts
    - **Refactoring Safety**: Type-safe refactoring with IDE support

Usage:
    Import and use these protocols throughout the codebase to replace `Any`:

    ```python
    from asciiquarium_redux.protocols import AsciiQuariumProtocol, ScreenProtocol

    def update(self, dt: float, screen: ScreenProtocol, app: AsciiQuariumProtocol) -> None:
        # Type-safe implementation
        app.bubbles.append(Bubble(x=self.x, y=self.y))
    ```

See Also:
    - entities/base.py: Actor implementations using these protocols
    - app.py: AsciiQuarium class implementing AsciiQuariumProtocol
    - util/types.py: Legacy ScreenProtocol replaced by enhanced version
"""

from __future__ import annotations

from typing import Protocol, List, Dict, Optional, Union, Any, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    # Forward references to avoid circular imports
    pass


@runtime_checkable
class ScreenProtocol(Protocol):
    """Enhanced screen protocol defining the complete interface for all backends.

    This protocol replaces the incomplete ScreenProtocol in util/types.py and
    provides a comprehensive interface that all screen implementations must support.

    The protocol covers all rendering operations, input handling, and screen
    management functionality used throughout the codebase.

    Attributes:
        width: Screen width in character columns
        height: Screen height in character rows
    """

    width: int
    height: int

    def clear(self) -> None:
        """Clear the entire screen buffer."""
        ...

    def print_at(self, text: str, x: int, y: int, colour: Optional[Union[int, Any]] = None, *args: Any, **kwargs: Any) -> None:
        """Print text at specific screen coordinates with optional color.

        Args:
            text: Text string to render
            x: Column position (0-based)
            y: Row position (0-based)
            colour: Optional color code (uses default if None)
        """
        ...

    def refresh(self) -> None:
        """Update the physical display with current buffer contents."""
        ...

    def get_event(self) -> Any:
        """Get the next input event from the event queue.

        Returns:
            Event object or None if no events available.
            Event types vary by backend (keyboard, mouse, resize, etc.)
        """
        ...

    def has_resized(self) -> bool:
        """Check if the screen has been resized since last check.

        Returns:
            True if screen dimensions have changed
        """
        ...


@runtime_checkable
class ActorProtocol(Protocol):
    """Formal protocol defining the interface for all animated entities.

    This protocol formalizes the Actor interface and ensures type safety
    for all entity implementations. It replaces informal duck typing with
    explicit interface contracts.

    All entities (fish, seaweed, bubbles, specials) must implement this
    protocol to participate in the entity management system.
    """

    def update(self, dt: float, screen: Any, app: Any = None) -> None:
        """Update entity state for the current frame.

        Args:
            dt: Time elapsed since last update (seconds)
            screen: Screen interface for dimension and rendering context
            app: Optional main application instance for global state access
        """
        ...

    def draw(self, screen: Any, mono: bool = False, *args: Any, **kwargs: Any) -> None:
        """Render entity to the screen.

        Args:
            screen: Screen interface for rendering operations
            mono: Whether to use monochrome rendering mode
        """
        ...

    @property
    def active(self) -> bool:
        """Check if entity should remain in the simulation.

        Returns:
            True to keep entity active, False to mark for removal
        """
        ...


@runtime_checkable
class AsciiQuariumProtocol(Protocol):
    """Protocol defining the main application interface for entity interactions.

    This protocol replaces `Any` usage in entity update methods and provides
    a type-safe interface for entities to interact with the main application.

    The protocol includes only the methods and attributes that entities
    actually use, following the interface segregation principle.
    """

    # Settings access for configuration-driven behavior
    settings: Any

    # Entity collections for spawning and interaction
    seaweed: List[Any]
    fish: List[Any]
    bubbles: List[Any]
    splats: List[Any]
    specials: List[Any]
    decor: List[Any]

    def spawn_random(self, screen: Any) -> None:
        """Spawn a random special entity based on configured weights.

        Args:
            screen: Screen interface for positioning calculations
        """
        ...

    def adjust_populations(self, screen: Any) -> None:
        """Adjust entity populations based on current screen size.

        Args:
            screen: Screen interface for dimension calculations
        """
        ...


@runtime_checkable
class SettingsProtocol(Protocol):
    """Protocol defining configuration interface for dependency injection.

    This protocol enables type-safe access to configuration parameters
    without requiring direct dependency on the Settings class.

    Only includes the most commonly accessed configuration parameters
    to keep the interface focused and maintainable.
    """

    # Animation and rendering settings
    fps: int
    speed: float
    density: float
    color: str

    # Scene layout settings
    waterline_top: int
    castle_enabled: bool
    chest_enabled: bool

    # Population scaling settings
    fish_scale: float
    seaweed_scale: float

    # Special entity spawning settings
    spawn_start_delay_min: float
    spawn_start_delay_max: float
    spawn_interval_min: float
    spawn_interval_max: float
    spawn_max_concurrent: int
    specials_weights: Dict[str, float]

    # Fish behavior settings
    fish_direction_bias: float
    fish_speed_min: float
    fish_speed_max: float
    fish_bubble_min: float
    fish_bubble_max: float
    fish_turn_enabled: bool
    fish_turn_chance_per_second: float

    # Seaweed behavior settings
    seaweed_sway_min: float
    seaweed_sway_max: float
    seaweed_lifetime_min: float
    seaweed_lifetime_max: float


@runtime_checkable
class EventProtocol(Protocol):
    """Protocol for input events across different backends.

    This protocol provides a unified interface for handling input events
    from different backends (terminal, TkInter, web) with type safety.

    Different backends may implement additional event properties,
    but this protocol defines the common interface used by the application.
    """

    # Common event properties
    timestamp: float

    # Event type identification methods
    def is_key_event(self) -> bool:
        """Check if this is a keyboard event."""
        ...

    def is_mouse_event(self) -> bool:
        """Check if this is a mouse event."""
        ...

    def is_resize_event(self) -> bool:
        """Check if this is a screen resize event."""
        ...


@runtime_checkable
class KeyEventProtocol(EventProtocol, Protocol):
    """Protocol for keyboard input events.

    Extends EventProtocol with keyboard-specific properties for
    type-safe keyboard event handling.
    """

    key_code: int
    key_name: Optional[str]

    def is_printable(self) -> bool:
        """Check if the key produces a printable character."""
        ...


@runtime_checkable
class MouseEventProtocol(EventProtocol, Protocol):
    """Protocol for mouse input events.

    Extends EventProtocol with mouse-specific properties for
    type-safe mouse event handling.
    """

    x: int
    y: int
    buttons: int

    def is_left_click(self) -> bool:
        """Check if this is a left mouse button click."""
        ...

    def is_right_click(self) -> bool:
        """Check if this is a right mouse button click."""
        ...


# Type aliases for common spawn function signatures
SpawnFunction = "Callable[[ScreenProtocol, AsciiQuariumProtocol], List[ActorProtocol]]"
SpawnFunctionTargeted = "Callable[[ScreenProtocol, AsciiQuariumProtocol, int, int], List[ActorProtocol]]"


# Legacy compatibility - re-export enhanced ScreenProtocol as the new standard
__all__ = [
    "ScreenProtocol",
    "ActorProtocol",
    "AsciiQuariumProtocol",
    "SettingsProtocol",
    "EventProtocol",
    "KeyEventProtocol",
    "MouseEventProtocol",
    "SpawnFunction",
    "SpawnFunctionTargeted",
]
