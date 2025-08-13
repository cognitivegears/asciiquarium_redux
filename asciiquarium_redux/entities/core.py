"""Core entity compatibility module for Asciiquarium Redux.

This module serves as a compatibility shim that re-exports the core entity
classes and functions from their new locations in the entities/core/ directory.
It maintains backward compatibility for existing code while supporting the
new modularized entity system architecture.

Purpose:
    When the entity system was refactored for better organization, the core
    entities (Fish, Seaweed, Bubble, Splat) were moved from a single file
    into separate modules under entities/core/. This compatibility layer
    ensures existing imports continue to work without modification.

Architecture:
    The module uses Python's import system to transparently redirect imports
    to the new locations. This approach provides:

    - **Backward Compatibility**: Existing code continues to work unchanged
    - **Gradual Migration**: Users can migrate to new imports at their own pace
    - **Clean API**: The public interface remains stable and predictable
    - **Future Flexibility**: New organization enables better modularity

Re-exported Components:
    **Fish Assets**:
        - FISH_RIGHT: Right-facing fish sprite frames
        - FISH_LEFT: Left-facing fish sprite frames
        - FISH_RIGHT_MASKS: Color masks for right-facing fish
        - FISH_LEFT_MASKS: Color masks for left-facing fish
        - random_fish_frames(): Factory function for random fish sprites

    **Core Entity Classes**:
        - Fish: Main fish entity with movement and bubble generation
        - Seaweed: Animated background seaweed with lifecycle management
        - Bubble: Simple upward-floating bubble effects
        - Splat: Temporary splash effects for collisions

Migration Guide:
    **Current (Compatibility) Imports**:
        ```python
        from asciiquarium_redux.entities.core import Fish, Seaweed, Bubble
        from asciiquarium_redux.entities.core import random_fish_frames
        ```

    **New (Recommended) Imports**:
        ```python
        from asciiquarium_redux.entities.core.fish import Fish
        from asciiquarium_redux.entities.core.seaweed import Seaweed
        from asciiquarium_redux.entities.core.bubble import Bubble
        from asciiquarium_redux.entities.core.fish_assets import random_fish_frames
        ```

Implementation:
    The compatibility layer uses relative imports to access the actual
    implementations in the entities/core/ subdirectory. This approach
    has minimal performance overhead while maintaining clean separation.

Future Plans:
    This compatibility module will be maintained for the foreseeable future
    to ensure existing code continues to work. However, new code is encouraged
    to use the direct imports from the specific modules for better clarity
    and IDE support.

Performance:
    The re-export mechanism has negligible performance impact. Import time
    is essentially the same as direct imports, and runtime performance is
    identical since the same objects are being used.

See Also:
    - entities/core/fish.py: Fish entity implementation
    - entities/core/seaweed.py: Seaweed entity implementation
    - entities/core/bubble.py: Bubble entity implementation
    - entities/core/fish_assets.py: Fish sprite definitions
    - docs/ENTITY_SYSTEM.md: Complete entity system documentation
"""

from .core import (  # type: ignore[F401]
    FISH_RIGHT,
    FISH_LEFT,
    FISH_RIGHT_MASKS,
    FISH_LEFT_MASKS,
    random_fish_frames,
    Seaweed,
    Bubble,
    Splat,
    Fish,
)

__all__ = [
    "FISH_RIGHT",
    "FISH_LEFT",
    "FISH_RIGHT_MASKS",
    "FISH_LEFT_MASKS",
    "random_fish_frames",
    "Seaweed",
    "Bubble",
    "Splat",
    "Fish",
]
