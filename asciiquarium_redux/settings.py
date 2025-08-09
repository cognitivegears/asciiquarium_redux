from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import tomllib


@dataclass
class Settings:
    fps: int = 20
    density: float = 1.0
    color: str = "auto"
    seed: Optional[int] = None
    speed: float = 0.75


def _find_config_paths() -> List[Path]:
    paths: List[Path] = []
    cwd = Path.cwd()
    paths.append(cwd / ".asciiquarium.toml")
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        paths.append(Path(xdg) / "asciiquarium-redux" / "config.toml")
    home = Path.home()
    paths.append(home / ".config" / "asciiquarium-redux" / "config.toml")
    return [p for p in paths if p.exists()]


def _load_toml(path: Path) -> dict:
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def load_settings_from_sources(argv: Optional[List[str]] = None) -> Settings:
    s = Settings()
    for p in _find_config_paths():
        data = _load_toml(p)
        render = data.get("render", {})
        scene = data.get("scene", {})
        if "fps" in render:
            s.fps = int(render.get("fps", s.fps))
        if "color" in render:
            s.color = str(render.get("color", s.color))
        if "density" in scene:
            try:
                s.density = float(scene.get("density", s.density))
            except Exception:
                pass
        if "seed" in scene:
            seed_val = scene.get("seed")
            if isinstance(seed_val, int):
                s.seed = seed_val
            elif isinstance(seed_val, str) and seed_val.lower() == "random":
                s.seed = None
        if "speed" in scene:
            try:
                s.speed = float(scene.get("speed", s.speed))
            except Exception:
                pass
        break
    parser = argparse.ArgumentParser(description="Asciiquarium Redux")
    parser.add_argument("--fps", type=int)
    parser.add_argument("--density", type=float)
    parser.add_argument("--color", choices=["auto", "mono", "16", "256"])
    parser.add_argument("--seed", type=int)
    parser.add_argument("--speed", type=float)
    args = parser.parse_args(argv)

    if args.fps is not None:
        s.fps = max(5, min(120, args.fps))
    if args.density is not None:
        s.density = max(0.1, min(5.0, args.density))
    if args.color is not None:
        s.color = args.color
    if args.seed is not None:
        s.seed = args.seed
    if args.speed is not None:
        s.speed = max(0.1, min(3.0, args.speed))
    return s
