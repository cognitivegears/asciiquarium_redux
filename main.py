from __future__ import annotations

# Thin shim delegating to the packaged app to avoid divergence.
# Keep this for local runs: `python main.py`.

import random
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
from asciiquarium_redux.settings import load_settings_from_sources
from asciiquarium_redux.app import run


def main(argv: list[str] | None = None) -> None:
    settings = load_settings_from_sources(argv)
    if settings.seed is not None:
        random.seed(settings.seed)
    # Restart on terminal resize so we can rebuild with new dimensions
    while True:
        try:
            Screen.wrapper(lambda scr: run(scr, settings))
            break
        except ResizeScreenError:
            # Loop and re-run with a fresh Screen
            continue


if __name__ == "__main__":
    main()
