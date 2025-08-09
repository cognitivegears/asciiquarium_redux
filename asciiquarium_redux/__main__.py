from __future__ import annotations

import random
from asciimatics.screen import Screen
from .app import load_settings_from_sources, run


def main(argv: list[str] | None = None) -> None:
    settings = load_settings_from_sources(argv)
    if settings.seed is not None:
        random.seed(settings.seed)
    Screen.wrapper(lambda scr: run(scr, settings))


if __name__ == "__main__":
    main()
