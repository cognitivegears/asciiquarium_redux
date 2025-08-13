"""Command-line interface and backend selection module for Asciiquarium Redux.

This module provides the primary entry point for the application, handling command-line
argument parsing, backend selection, and coordinating the startup sequence. It bridges
between user input and the core application logic.

Key Responsibilities:
    - CLI Argument Processing: Parse and validate command-line options
    - Backend Selection: Choose appropriate screen implementation based on user preferences
    - Settings Management: Load and merge configuration from files and CLI arguments
    - Application Bootstrapping: Initialize and start the aquarium simulation
    - Error Handling: Graceful degradation and user-friendly error messages

Architecture:
    The module follows a functional approach with clear separation between argument
    parsing, configuration loading, and application startup. This design enables
    easy testing and modification of startup behavior.

Backend Selection Logic:
    1. **Explicit Backend**: User specifies backend via command-line (--backend terminal/web/tkinter)
    2. **Web Subcommand**: Special handling for 'web' subcommand with server options
    3. **Auto Detection**: Fall back to terminal backend as default
    4. **Dependency Checking**: Verify required libraries are available

Command-Line Interface:
    The module supports a rich CLI with global options and subcommands:

    Global Options:
        --fps, --density, --color, --seed: Animation and visual settings
        --config: Load settings from TOML configuration file
        --backend: Force specific backend (terminal/web/tkinter)

    Subcommands:
        web: Launch web interface with server options (--port, --no-open-browser)

Configuration Precedence:
    1. Command-line arguments (highest priority)
    2. Configuration file specified via --config
    3. Default configuration file (./config.toml)
    4. Built-in defaults (lowest priority)

Error Handling:
    The module provides user-friendly error messages for common issues:
    - Missing dependencies for specific backends
    - Invalid configuration values or file formats
    - Port conflicts for web backend
    - Unsupported terminal configurations

Usage Examples:
    Basic Usage:
        $ asciiquarium-redux                     # Launch with defaults
        $ asciiquarium-redux --fps 30 --density 1.5

    Configuration Files:
        $ asciiquarium-redux --config aquarium.toml
        $ asciiquarium-redux --config custom.toml --fps 60

    Backend Selection:
        $ asciiquarium-redux --backend terminal  # Force terminal
        $ asciiquarium-redux --backend tkinter   # Force TkInter GUI
        $ asciiquarium-redux web                 # Web interface
        $ asciiquarium-redux web --port 3000     # Custom port

Entry Points:
    The module is registered as a console script in pyproject.toml:
    - asciiquarium-redux: Primary command-line interface

Performance:
    Startup time is optimized through lazy imports and efficient dependency checking.
    Backend-specific imports are deferred until backend selection is complete.

See Also:
    - app.py: Core application logic and AsciiQuarium class
    - util.settings: Configuration system and Settings class
    - backends/: Platform-specific screen implementations
    - web_server.py: Development server for web backend
    - docs/BACKENDS.md: Detailed backend comparison
"""

from __future__ import annotations

import random
import sys
from .screen_compat import Screen

from .util.settings import load_settings_from_sources
from .app import run as _run


def run_with_resize(settings) -> None:
    """Run the app, restarting the Screen on terminal resize.

    This wraps Screen.wrapper and catches ResizeScreenError to recreate
    the screen, without changing application behavior.
    """
    # Import terminal dependencies lazily to avoid import-time costs in other backends
    from asciimatics.screen import Screen as _RealScreen  # type: ignore
    from asciimatics.exceptions import ResizeScreenError  # type: ignore
    while True:
        try:
            _RealScreen.wrapper(lambda scr: _run(scr, settings))
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
    backend = getattr(settings, "ui_backend", "terminal")
    if backend == "web":
        # Simple local server to host the web assets
        from .web_server import serve_web
        serve_web(port=int(getattr(settings, 'web_port', 8000)), open_browser=bool(getattr(settings, 'web_open', False)))
        return
    if backend == "tk":
        try:
            # Preflight to provide a clearer error if Tk isn't present
            import tkinter  # type: ignore
            from .backend.tk import run_tk
            run_tk(settings)
            return
        except Exception as e:
            print(f"Tk backend unavailable ({e}); falling back to terminal.", file=sys.stderr)
    # Default: terminal backend
    run_with_resize(settings)
