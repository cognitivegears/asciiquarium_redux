from __future__ import annotations

import random
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
from .settings import load_settings_from_sources
from .app import run


def main(argv: list[str] | None = None) -> None:
    settings = load_settings_from_sources(argv)
    if settings.seed is not None:
        random.seed(settings.seed)
    while True:
        try:
            Screen.wrapper(lambda scr: run(scr, settings))
            break
        except ResizeScreenError:
            continue


if __name__ == "__main__":
    main()
