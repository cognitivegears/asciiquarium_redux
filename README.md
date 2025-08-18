# Asciiquarium Redux 🐠

[![PyPI version](https://img.shields.io/pypi/v/asciiquarium-redux.svg)](https://pypi.org/project/asciiquarium-redux/) [![Live demo](https://img.shields.io/badge/web%20demo-open-0aaac0?logo=githubpages&logoColor=white)](https://cognitivegears.github.io/asciiquarium_redux/) [![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/) [![CI](https://github.com/cognitivegears/asciiquarium_redux/actions/workflows/ci.yml/badge.svg)](https://github.com/cognitivegears/asciiquarium_redux/actions/workflows/ci.yml) [![License](https://img.shields.io/github/license/cognitivegears/asciiquarium_redux.svg)](LICENSE)

A joyful, colorful Python reimagining of the classic terminal aquarium. Watch fish swim, seaweed sway, hooks drop, sharks prowl, and bubbles pop—right in your terminal or a windowed Tk screen.

Original Asciiquarium by Kirk Baucom (Perl): [robobunny.com/projects/asciiquarium](https://robobunny.com/projects/asciiquarium/html/)

Status: Playable, configurable, and window-ready (Tk). Bring your own snacks (for the ducks).

👉 Try it in your browser (no install): [Live web version](https://cognitivegears.github.io/asciiquarium_redux/)

![Preview – Asciiquarium Redux](docs/screenshot.png)

## Why a Redux?

- Keep the whimsical aquarium alive on modern terminals and platforms
- Offer configurable FPS, colors, sizes, and deterministic playback (seeded RNG)
- Ship as an installable Python package for easy use (e.g., `pipx install`)

## Features

- Faithful animations: fish (with color masks), seaweed lifecycle/sway, waterline, castle, bubbles, and many specials (shark, whale, ship, ducks, swan, dolphins, monster, big fish)
- Decor: treasure chest that sits on the seabed, occasionally bubbles, and periodically opens to release a stream of bubbles (drawn behind fish)
- Fishhook gameplay: one hook at a time, impact pause, configurable dwell time, collisions while lowering/dwelling/retracting
- Smooth rendering: double-buffered terminal drawing to reduce flicker
- Backends: terminal (asciimatics) and windowed Tk canvas (resizable, color)
- Configurable everything: FPS, speed, density, spawn timings/weights, fish bands, colors; TOML-based config
- Deterministic playback (seed) for captures and demos
- Fish turning: fish can occasionally turn around with a smooth shrink/flip/expand animation (configurable)

## 📚 Documentation

### Quick Start

- **[Getting Started Guide](docs/DEVELOPER_GUIDE.md)** - Setup, installation, and first steps
- **[Configuration Guide](docs/CONFIGURATION.md)** - Complete settings reference and customization
- **[Backend Comparison](docs/BACKENDS.md)** - Terminal vs Web vs TkInter backends

### Technical Reference

- **[Architecture Overview](docs/ARCHITECTURE.md)** - System design and component relationships
- **[API Reference](docs/API_REFERENCE.md)** - Public interfaces and usage examples
- **[Entity System](docs/ENTITY_SYSTEM.md)** - Fish, seaweed, bubbles, and special entity details

### Deployment & Advanced

- **[Web Deployment](docs/WEB_DEPLOYMENT.md)** - Browser setup and GitHub Pages deployment
- **[Sample Configuration](sample-config.toml)** - Example TOML configuration file

## Quick start

From source using uv (already configured in this repo):

```sh
# macOS/Linux
uv run python main.py  # terminal backend

# Or use the repo venv directly
source .venv/bin/activate
python main.py
```

Install-free run from PyPI with uvx:

```sh
# Latest published version
uvx asciiquarium-redux

# Pass CLI flags to the app directly
uvx asciiquarium-redux --fps 30 --density 1.2 --seed 123

# Windowed Tk backend
uvx asciiquarium-redux --backend tk

# Refresh cached app to the newest release
uvx --refresh asciiquarium-redux
```

Run with pipx:

```sh
pipx install asciiquarium-redux

# Run
asciiquarium-redux

# Tk backend
asciiquarium-redux --backend tk

# Upgrade later
pipx upgrade asciiquarium-redux
```

Windowed Tk backend:

```sh
uv run python main.py --backend tk
```

## Web mode (run in your browser)

You can run Asciiquarium Redux fully in the browser using Pyodide. The app starts a tiny local web server that serves a static page and installs the package into the browser runtime.

Local run (opens your default browser):

```sh
# From a clone
uv run python main.py --backend web --open

# Or via the installed CLI
asciiquarium-redux --backend web --open

# Choose a port (default 8000) and open manually if you prefer
asciiquarium-redux --backend web --port 9000
# Then visit http://127.0.0.1:9000/
```

Notes

- The web page provides simple controls (FPS, speed, density, color, chest, turn, seed). Changes apply live.
- Keyboard/mouse controls mirror the terminal/Tk versions: q, p, r, h, space, t; click to drop/retract the hook.
- If you update Python code, the server copies the latest wheel into `web/wheels`. Hard refresh the page to pick up changes.
- The browser installs the local wheel first; if not present, it falls back to PyPI.

### Deploy to GitHub Pages

You can publish the web UI as a static site. The browser will install the package from PyPI at load time.

Option A — one-click from VS Code

1) Use the provided task: “Deploy web to GitHub Pages”. It creates (or overwrites) a `gh-pages` branch with the contents of `asciiquarium_redux/web/` and pushes it to `origin`.
2) In your GitHub repo Settings → Pages, choose “Branch: gh-pages / root”.
3) Visit <https://USERNAME.github.io/REPO/>

Option B — manual commands (equivalent)

```sh
# From the repo root
set -euo pipefail
tmp=$(mktemp -d)
rsync -a --delete asciiquarium_redux/web/ "$tmp/"
cp -f "$tmp/index.html" "$tmp/404.html" || true
origin=$(git remote get-url origin)
git -C "$tmp" init
git -C "$tmp" checkout -b gh-pages
git -C "$tmp" add .
git -C "$tmp" -c user.name='gh-pages' -c user.email='gh-pages@local' commit -m 'Deploy web to GitHub Pages'
git -C "$tmp" remote add origin "$origin"
git -C "$tmp" push --force origin gh-pages
```

Tips

- Paths in `index.html` are relative, so project pages (`/your-repo/`) work without changes.
- If the page can’t install the package in the browser, ensure the latest version on PyPI includes the web backend.
- For custom forks, publishing your own release to PyPI ensures the web UI can install cleanly from Pages.

Controls:

- q: quit
- p: pause/resume
- r: rebuild scene (useful after resize)
- h or ?: toggle help overlay
- space: drop/retract fishhook (random position in terminal)
- mouse: left-click to drop a hook at the cursor (or retract if one is active)
- s (Tk): save a screenshot as ./asciiquarium_#.png (auto-incrementing)
- t: force a random fish to turn (useful to preview the turning animation)
- f: feed fish (spawns floating flakes fish will seek and eat)

CLI examples:

```sh
uv run python main.py --fps 30 --density 1.5 --color mono --seed 123 --speed 0.7
# Use a specific config file
uv run python main.py --config ./sample-config.toml
uv run python main.py --backend tk --fullscreen
```

Common flags:

- --fps (int): target frames per second (default 24, clamp 5–120)
- --density (float): density multiplier (default 1.0, clamp 0.1–5.0)
- --color <auto|mono|16|256>: color mode (mono forces white)
- --seed (int): deterministic RNG seed; omit for random
- --speed (float): global speed multiplier (default 0.75)
- --backend <terminal|tk>: choose backend
- --fullscreen: make Tk window fullscreen
- --font-min (int): minimum Tk font size bound for auto-resize
- --font-max (int): maximum Tk font size bound for auto-resize
- --ai / --no-ai: enable or disable Utility AI behaviors
- --port (int): web server port for web backend

## Notes

- Terminal uses `asciimatics`; Tk backend renders to a Canvas with per-cell text.
- Tk resizes by adjusting the character grid to the window size; the scene rebuilds when size stabilizes.
- When Tk font_auto is enabled, font size auto-fits within [font_min_size, font_max_size] so the castle fits; sliders clamp min<=max.
- Ensure a UTF-8 locale and a monospaced font for best results.

Behavior highlights

- Fish can drift vertically (bounded by fish.vertical_speed_max; default 2.0 rows/sec) while keeping mostly horizontal motion.
- Utility AI (when enabled) prioritizes eating fish food; when very hungry and no food is available, larger fish may prey on strictly smaller fish.
- Predation creates a brief splat effect; prey are immediately respawned to maintain population.
- If fish counts remain low for a while, restocking gently replenishes the population.

## Tk backend requirements (Tkinter)

This is only needed if you want to use the Tk backend (`--backend tk`). If tk is not available, the app will fall back to the terminal backend.

The Tk backend needs Python built with tkinter and the system Tk libraries. If Tk isn’t available, the app automatically falls back to the terminal backend.

Quick test:

```sh
python -c "import tkinter as tk; print('tk', tk.TkVersion)"
```

macOS

- Recommended: Install Python from python.org (bundles a compatible Tcl/Tk).
- Homebrew (brew):

```sh
brew install python tcl-tk
python3 -c "import tkinter as tk; print('tk', tk.TkVersion)"
```

- If multiple Pythons are installed, ensure uv/venv uses the one with tkinter available.

Linux

- Debian/Ubuntu:

```sh
sudo apt install python3-tk tk
```

- Fedora/RHEL:

```sh
sudo dnf install python3-tkinter tk
```

- Arch:

```sh
sudo pacman -S tk
```

- Some distros package tkinter separately; install both Python and the tkinter/Tk packages.

Windows

- The official Python installer from python.org includes tkinter by default.
- If you see "ModuleNotFoundError: _tkinter", re-run the installer and ensure “tcl/tk and IDLE” is selected.
- Using MSYS2: install tk and Python via pacman to get tkinter support.

Notes

- Tkinter is not installed via pip; it’s part of the Python build and OS packages.

## Configuration

Default locations checked (first wins):

- `./.asciiquarium.toml`
- `~/.config/asciiquarium-redux/config.toml`
- `$XDG_CONFIG_HOME/asciiquarium-redux/config.toml`

Example `config.toml`:

```toml
[render]
fps = 24
color = "mono"   # auto|mono|16|256

[scene]
density = 1.2     # 0.1..5.0
seed = 42         # or "random" (string) for non-deterministic
speed = 0.75      # 0.1..3.0 (lower = slower)
waterline_top = 5 # top row of waterline
chest_enabled = true         # show treasure chest decor
chest_burst_seconds = 60.0   # seconds between lid bursts

[spawn]
# Initial delay range before the first special appears (seconds):
start_delay_min = 3.0
start_delay_max = 8.0
# Interval range between specials (seconds):
interval_min = 8.0
interval_max = 20.0
# Relative weights for random special spawns (0 disables a type):
[spawn.per_type]  # optional per-type cooldowns in seconds
shark = 0.0
fishhook = 0.0
whale = 0.0
ship = 0.0
ducks = 0.0
dolphins = 0.0
swan = 0.0
monster = 0.0
big_fish = 0.0
[spawn]
max_concurrent = 1
cooldown_global = 0.0
[spawn.specials]
shark = 1.0
fishhook = 1.0
whale = 1.0
ship = 1.0
ducks = 1.0
dolphins = 1.0
swan = 1.0
monster = 1.0
big_fish = 1.0
# Optional extra scaling beyond density for counts
fish_scale = 1.0
seaweed_scale = 1.0

[fishhook]
dwell_seconds = 20.0

[fish]
direction_bias = 0.5   # 0..1 probability of rightward motion
speed_min = 0.6
speed_max = 2.5
bubble_min = 2.0
bubble_max = 5.0
# Turning behavior
turn_enabled = true
turn_chance_per_second = 0.01   # per-second chance (scaled by dt)
turn_min_interval = 6.0         # cooldown between turns (seconds)
turn_shrink_seconds = 0.35      # time to shrink to center
turn_expand_seconds = 0.35      # time to expand after flip
# y_band = [0.2, 0.9]   # optional band (fractions of height)
# count_base = 6        # optional count override
# count_per_80_cols = 3.0

[seaweed]
sway_min = 0.18
sway_max = 0.5
lifetime_min = 25.0
lifetime_max = 60.0
regrow_delay_min = 4.0
regrow_delay_max = 12.0
growth_rate_min = 6.0
growth_rate_max = 12.0
shrink_rate_min = 8.0
shrink_rate_max = 16.0
# count_base = 4        # optional count override
# count_per_80_cols = 3.0

[ui]
backend = "terminal"   # terminal|tk
fullscreen = false
cols = 120
rows = 40
font_family = "Menlo"
font_size = 14
font_min_size = 10   # lower bound for Tk auto font sizing
font_max_size = 22   # upper bound for Tk auto font sizing
font_auto = true     # auto-resize font to fit scene; bounded by min/max

Tk auto font sizing notes

- When using the Tk backend with font_auto = true, the app adjusts the font size so that the minimal scene (waterline + water + castle + margin) fits vertically.
- The font size is recalculated on window resize and can grow or shrink, but it is always clamped between font_min_size and font_max_size to avoid unreadably small or comically large text.
- Very small windows: the app will shrink the font no smaller than font_min_size; if things still don’t fit, some tall specials (e.g., big_fish) will be skipped until there’s enough space.
```

Run with uvx without cloning the repo:

```sh
uvx asciiquarium-redux
```

Place a user config at one of the default paths above (e.g., `~/.config/asciiquarium-redux/config.toml`) to change spawn weights, timing, or scaling without modifying code.

You can also point to a specific config with `--config` (absolute or relative path). See `sample-config.toml` in the repo for a ready-to-edit template.

## Treasure chest (decor)

- Behavior
  - Sits near the seabed (like the castle). Drawn in front of seaweed and behind fish, so fish swim in front of it.
  - Emits occasional small bubbles while closed.
  - On a periodic timer, the lid opens briefly and a stream of bubbles pops out, then it closes again.
- Configuration
  - `scene.chest_enabled` (bool, default `true`): toggle the treasure chest on/off.
  - `scene.chest_burst_seconds` (float, default `60.0`): seconds between lid openings.

## Fish turning

- Behavior
  - Occasionally, a fish slows down while its body visually “collapses” to a single center column, flips to the opposite direction, then expands back out and accelerates the other way.
  - The center stays visually anchored during the animation to avoid popping.
- Controls
  - Press `t` to force a random fish to turn immediately (handy to preview the effect).
- Configuration (under `[fish]`)
  - `turn_enabled` (bool, default `true`)
  - `turn_chance_per_second` (float, default `0.01`): random chance per second (scaled by frame time).
  - `turn_min_interval` (float, default `6.0`): minimum seconds between turns per fish.
  - `turn_shrink_seconds` (float, default `0.35`): time to shrink to the middle.
  - `turn_expand_seconds` (float, default `0.35`): time to expand after flipping.

## Differences from the original

- Python 3 implementation
- Config file support and richer CLI options
- Deterministic mode for reproducible animations
- Terminal capability detection and graceful fallbacks

The goal remains fidelity to the original look-and-feel first, with extras opt-in.

## Development

Prereqs

- Python 3.11+ (3.13 recommended)
- [uv](https://github.com/astral-sh/uv) for env + builds (fast, zero-hassle)
- No Node required (web UI is static)

Setup

```sh
# Clone and enter the repo
git clone https://github.com/cognitivegears/asciiquarium_redux.git
cd asciiquarium_redux

# Create a local venv and install deps
uv sync
```

Run (terminal/Tk)

```sh
# Terminal backend
uv run python main.py

# Tk backend (windowed)
uv run python main.py --backend tk
```

Web development

```sh
# 1) Build a wheel (the browser installs the wheel)
uv build

# 2) Start the local web server (auto-copies latest wheel to web/wheels/)
uv run python -c "from asciiquarium_redux.web_server import serve_web; serve_web(port=8000, open_browser=True)"
# or
uv run python main.py --backend web --open
```

Dev loop tips (web)

- Changing Python code: `uv build`, then restart the web server so it refreshes `web/wheels/`. Hard-refresh the page to reinstall the wheel.
- Changing HTML/CSS/JS: just refresh the browser.
- The browser first tries the local wheel (when served locally); on GitHub Pages it installs from PyPI.

Config and CLI

```sh
# Example CLI flags
uv run python main.py --fps 30 --density 1.5 --seed 123

# Use a config file (see sample-config.toml)
uv run python main.py --config ./sample-config.toml
```

Deploy the web UI

- VS Code task: “Deploy web to GitHub Pages” (publishes `asciiquarium_redux/web/` to `gh-pages`).
- Or follow the manual commands in “Deploy to GitHub Pages” above.

Misc

- Key dep: `asciimatics`
- Entry points: `main.py` (CLI), `asciiquarium_redux/web_server.py` (local web serving)
- Optional sanity check:

```sh
uv run python devtools/verify_shark_evasion.py
```

## Recording a demo GIF (tips)

- macOS: `brew install ffmpeg` then use `asciinema` + `agg` or `ttygif`
- Keep background dark and font mono; target 20–30 FPS; limit palette if needed

## Troubleshooting

- Colors look wrong: try `--color mono` or use a 256-color/truecolor-capable terminal
- Misaligned art: ensure a monospaced font and disable ligatures
- High CPU: lower `--fps` or reduce density; try `ncurses` terminfo with fewer color changes
- Unicode issues: set `LANG`/`LC_ALL` to UTF-8 (e.g., `en_US.UTF-8`)

## Acknowledgements

- Original Asciiquarium by Kirk Baucom (Perl): [robobunny.com/projects/asciiquarium](https://robobunny.com/projects/asciiquarium/html/)
- Community contributors and testers who keep terminal art alive

## License

GPL-2.0-or-later to match the original Asciiquarium’s license. See [LICENSE](LICENSE).
