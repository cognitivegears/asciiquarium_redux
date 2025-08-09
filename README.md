# Asciiquarium Redux (Python)

A Python-based port of the classic terminal animation “Asciiquarium,” implemented with the asciimatics library. It renders a waterline, castle, seaweed sway, fish with occasional bubbles, and basic controls.

Original Asciiquarium by Kirk Baucom (Perl): [robobunny.com/projects/asciiquarium](https://robobunny.com/projects/asciiquarium/html/)

Status: Playable port with CLI options, help overlay, and config support.


## Why a Redux?

- Keep the whimsical aquarium alive on modern terminals and platforms
- Offer configurable FPS, colors, sizes, and deterministic playback (seeded RNG)
- Provide a cleaner architecture with tests and a small CLI
- Ship as an installable Python package for easy use (e.g., `pipx install`)


## Feature goals

- Faithful animations: fish, sharks, whales, submarines, jellyfish, bubbles, treasure chests
- Color output with sensible fallbacks (auto-detect 16/256/truecolor)
- Adaptive to window resizes and various terminal fonts
- Configurable parameters (speed/FPS, density, palette, RNG seed, scene length)
- Controls at runtime (pause, speed up/down, quit, reset)
- Deterministic mode for demos/recordings
- Cross-platform: macOS, Linux; Windows via `windows-curses` (planned)


## Quick start

From source using uv (already configured in this repo):

```sh
# macOS/Linux
uv run python main.py

# Or use the repo venv directly
source .venv/bin/activate
python main.py
```

Controls:

- q: quit
- p: pause/resume
- r: rebuild scene (useful after resize)
- h or ?: toggle help overlay

CLI examples:

```sh
uv run python main.py --fps 30 --density 1.5 --color mono --seed 123 --speed 0.7
```

- --fps (int): target frames per second (default 20, clamp 5–120)
- --density (float): density multiplier (default 1.0, clamp 0.1–5.0)
- --color <auto|mono|16|256>: color mode (mono forces white)
- --seed (int): deterministic RNG seed; omit for random
- --speed (float): global speed multiplier (default 0.75; 1.0 = baseline)


## Notes

- Uses `asciimatics` for portable terminal rendering and input.
- Targets ~20 FPS. Performance depends on terminal.
- Ensure a UTF-8 locale and a monospaced font for best results.


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
```


## Differences from the original

- Python 3 implementation with tests and packaging
- Config file support and richer CLI options
- Deterministic mode for reproducible animations
- Terminal capability detection and graceful fallbacks
- Structured codebase for easier contribution and extensions

The goal remains fidelity to the original look-and-feel first, with extras opt-in.


## Development

- Python 3.13 (repo venv managed by uv)
- Key dep: `asciimatics`
- Entry point: `main.py` using `Screen.wrapper`


## Recording a demo GIF (tips)

- macOS: `brew install ffmpeg` then use `asciinema` + `agg` or `ttygif`
- Keep background dark and font mono; target 20–30 FPS; limit palette if needed


## Troubleshooting

- Colors look wrong: try `--color mono` or use a 256-color/truecolor-capable terminal
- Misaligned art: ensure a monospaced font and disable ligatures
- High CPU: lower `--fps` or reduce density; try `ncurses` terminfo with fewer color changes
- Unicode issues: set `LANG`/`LC_ALL` to UTF-8 (e.g., `en_US.UTF-8`)


## Roadmap

- [ ] M1: Minimal port with core sprites and motion parity
- [ ] M2: Config + CLI + runtime controls
- [ ] M3: Packaging (`uv tool`), docs, and demo assets
- [ ] M4: Windows support via `windows-curses`
- [ ] M5: Extended creatures, events, and themes


## Acknowledgements

- Original Asciiquarium by Kirk Baucom (Perl): [robobunny.com/projects/asciiquarium](https://robobunny.com/projects/asciiquarium/html/)
- Community contributors and testers who keep terminal art alive


## License

TBD. See `LICENSE` once added. The original Asciiquarium license and assets remain credited to their respective authors.
