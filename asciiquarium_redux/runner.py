from __future__ import annotations

import random
import sys
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError

from .settings import load_settings_from_sources
from .app import run as _run


def run_with_resize(settings) -> None:
    """Run the app, restarting the Screen on terminal resize.

    This wraps Screen.wrapper and catches ResizeScreenError to recreate
    the screen, without changing application behavior.
    """
    while True:
        try:
            Screen.wrapper(lambda scr: _run(scr, settings))
            break
        except ResizeScreenError:
            continue


def main(argv: list[str] | None = None) -> None:
    # Ensure we forward the actual CLI argv to settings so --config pre-scan works.
    if argv is None:
        argv = sys.argv[1:]
    try:
        settings = load_settings_from_sources(argv)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
    if settings.seed is not None:
        random.seed(settings.seed)
    run_with_resize(settings)
