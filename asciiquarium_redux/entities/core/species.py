from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .fish_assets import FISH_RIGHT, FISH_LEFT


@dataclass(frozen=True)
class Species:
    id: int
    name: str
    height: int


def all_species() -> List[Species]:
    # One species per sprite index; height derived from right-facing sprite rows
    out: List[Species] = []
    for i, spr in enumerate(FISH_RIGHT):
        out.append(Species(id=i, name=f"Fish{i+1}", height=len(spr)))
    return out


def species_count() -> int:
    return len(FISH_RIGHT)


def species_frames(species_id: int, direction: int) -> List[str]:
    lst = FISH_RIGHT if direction > 0 else FISH_LEFT
    sid = max(0, min(species_count() - 1, species_id))
    return lst[sid]
