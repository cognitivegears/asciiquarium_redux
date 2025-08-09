from __future__ import annotations

import random
import sys
from asciimatics.screen import Screen
from .settings import load_settings_from_sources
from .app import run


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    settings = load_settings_from_sources(argv)
    if settings.seed is not None:
        random.seed(settings.seed)
    Screen.wrapper(lambda scr: run(scr, settings))


if __name__ == "__main__":
    main()
