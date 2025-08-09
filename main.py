from __future__ import annotations

# Thin shim delegating to the packaged app to avoid divergence.
# Keep this for local runs: `python main.py`.

import random
import sys
from asciimatics.screen import Screen
from asciiquarium_redux.settings import load_settings_from_sources
from asciiquarium_redux.app import run


def main(argv: list[str] | None = None) -> None:
    # If argv not provided, pass the process args so --config and flags are honored.
    if argv is None:
        argv = sys.argv[1:]
    settings = load_settings_from_sources(argv)
    if settings.seed is not None:
        random.seed(settings.seed)
    Screen.wrapper(lambda scr: run(scr, settings))


if __name__ == "__main__":
    main()
