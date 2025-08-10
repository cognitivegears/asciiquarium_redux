"""
Compatibility shim: specials moved into submodules under entities/specials/.
This module re-exports the public API so existing imports continue to work.
"""

from .specials import (  # type: ignore[F401]
    Shark,
    FishHook,
    Whale,
    Ducks,
    Dolphins,
    Swan,
    Monster,
    Ship,
    BigFish,
    spawn_shark,
    spawn_fishhook,
    spawn_whale,
    spawn_ducks,
    spawn_dolphins,
    spawn_swan,
    spawn_monster,
    spawn_ship,
    spawn_big_fish,
)

__all__ = [
    "Shark",
    "FishHook",
    "Whale",
    "Ducks",
    "Dolphins",
    "Swan",
    "Monster",
    "Ship",
    "BigFish",
    "spawn_shark",
    "spawn_fishhook",
    "spawn_whale",
    "spawn_ducks",
    "spawn_dolphins",
    "spawn_swan",
    "spawn_monster",
    "spawn_ship",
    "spawn_big_fish",
]
