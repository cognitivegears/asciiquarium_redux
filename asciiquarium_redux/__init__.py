"""Asciiquarium Redux - Cross-platform ASCII art aquarium simulator.

This package provides a modern, cross-platform implementation of the classic
ASCII art aquarium simulation. It features animated fish, seaweed, bubbles,
and special entities in a terminal-based underwater scene.

Key Features:
    - **Multi-backend Support**: Terminal (Asciimatics), web (WebAssembly), and TkInter
    - **Rich Entity System**: Fish, seaweed, bubbles, sharks, whales, ships, and more
    - **Comprehensive Configuration**: 65+ settings for complete customization
    - **Interactive Elements**: Fishhook deployment, pause/resume, help system
    - **Performance Optimized**: Smooth animations at 20-60 FPS across platforms
    - **Modern Architecture**: Clean separation of concerns with protocol-based design

Architecture Overview:
    The package follows a layered architecture with clear separation between:

    - **Application Layer** (AsciiQuarium): Main controller and game loop
    - **Entity System** (entities/): Polymorphic actors with update/render lifecycle
    - **Backend Abstraction** (Screen): Platform-specific rendering implementations
    - **Configuration Management** (Settings): TOML-based parameter control
    - **Utilities** (util/): Sprite rendering, buffer management, helper functions

Backends:
    - **Terminal Backend**: Rich console experience using Asciimatics library
    - **Web Backend**: Browser-based simulation using Pyodide/WebAssembly
    - **TkInter Backend**: Desktop GUI using Python's built-in UI toolkit

Usage Examples:
    Command Line Interface:
        $ asciiquarium-redux                    # Launch with default settings
        $ asciiquarium-redux --fps 30 --density 1.5
        $ asciiquarium-redux web --port 8080    # Web interface
        $ asciiquarium-redux --config custom.toml

    Programmatic API:
        >>> from asciiquarium_redux import AsciiQuarium
        >>> from asciiquarium_redux.util.settings import Settings
        >>> from asciiquarium_redux.backends.terminal import TerminalScreen
        >>>
        >>> settings = Settings(fps=30, density=1.5, color="256")
        >>> aquarium = AsciiQuarium(settings)
        >>> screen = TerminalScreen()
        >>> aquarium.run(screen)

Package Structure:
    asciiquarium_redux/
    ├── app.py                  # Main AsciiQuarium controller class
    ├── runner.py              # CLI interface and backend selection
    ├── web_server.py          # Local development server for web backend
    ├── constants.py           # Centralized magic number definitions
    ├── screen_compat.py       # Screen abstraction protocol
    ├── backends/              # Platform-specific screen implementations
    ├── entities/              # Entity system with core and special entities
    ├── util/                  # Utilities for rendering, settings, and helpers
    └── web/                   # Static web assets for browser deployment

Documentation:
    - Architecture Guide: docs/ARCHITECTURE.md
    - Developer Guide: docs/DEVELOPER_GUIDE.md
    - API Reference: docs/API_REFERENCE.md
    - Entity System: docs/ENTITY_SYSTEM.md
    - Configuration: docs/CONFIGURATION.md
    - Backend Comparison: docs/BACKENDS.md
    - Web Deployment: docs/WEB_DEPLOYMENT.md

Dependencies:
    Core: Python 3.9+, tomllib (built-in), dataclasses
    Terminal: asciimatics
    Web: Pyodide runtime (automatically loaded in browser)
    TkInter: Built-in Python module (usually pre-installed)

License:
    Open source under MIT license. See LICENSE.md for details.

Author:
    Modernized implementation of Kirk Baucom's original Asciiquarium (1999).
    Redux version by [Project Contributors] (2024).

See Also:
    - Original Asciiquarium: https://robobunny.com/projects/asciiquarium/
    - GitHub Repository: https://github.com/cognitivegears/asciiquarium_redux
    - Live site: https://ascifi.sh/
    - Documentation: https://cognitivegears.github.io/asciiquarium_redux/
"""

__all__ = []
