from __future__ import annotations

from typing import Callable, List, Protocol, TypedDict, runtime_checkable


class FlushBatch(TypedDict):
    y: int
    x: int
    text: str
    colour: str


FlushHook = Callable[[List[FlushBatch]], None]


@runtime_checkable
class ScreenProtocol(Protocol):
    width: int
    height: int

    def clear(self) -> None: ...

    def print_at(self, text: str, x: int, y: int, colour: int = 7) -> None: ...

    def flush_batches(self) -> List[FlushBatch]: ...
