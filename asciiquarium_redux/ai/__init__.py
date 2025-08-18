"""AI package for Asciiquarium Redux.

This package implements a tiny, dependency-free Utility AI and steering
behaviors used to provide more lifelike fish movement. It is entirely
optional and enabled via configuration/CLI flags. All randomness flows
through Python's built-in random module so runs are reproducible when a
seed is provided.

Public modules:
 - vector: Minimal 2D vector operations
 - noise: Leaky integrator noise used for smooth wander
 - steering: Seek/flee/align/cohere/separate/avoid/wander primitives
 - utility: Softmax-based action selection
 - brain: FishBrain that orchestrates sensing → action → steering
"""

from .vector import Vec2
from .brain import FishBrain

__all__ = ["Vec2", "FishBrain"]
