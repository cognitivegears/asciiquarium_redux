from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import tomllib


@dataclass
class Settings:
    fps: int = 20
    density: float = 1.0
    color: str = "auto"
    seed: Optional[int] = None
    speed: float = 0.75
    # Spawn/scaling configuration
    specials_weights: Dict[str, float] = field(default_factory=lambda: {
        "shark": 1.0,
        "fishhook": 1.0,
        "whale": 1.0,
        "ship": 1.0,
        "ducks": 1.0,
        "dolphins": 1.0,
        "swan": 1.0,
        "monster": 1.0,
        "big_fish": 1.0,
    })
    spawn_start_delay_min: float = 3.0
    spawn_start_delay_max: float = 8.0
    spawn_interval_min: float = 8.0
    spawn_interval_max: float = 20.0
    fish_scale: float = 1.0     # additional multiplier for fish count
    seaweed_scale: float = 1.0  # additional multiplier for seaweed count
    # Waterline
    waterline_top: int = 5
    # Fish controls
    fish_direction_bias: float = 0.5  # 0..1; probability of rightward motion
    fish_speed_min: float = 0.6
    fish_speed_max: float = 2.5
    fish_bubble_min: float = 2.0
    fish_bubble_max: float = 5.0
    fish_count_base: Optional[int] = None
    fish_count_per_80_cols: Optional[float] = None
    fish_y_band: Optional[Tuple[float, float]] = None  # fractions of screen height [0..1]
    # Seaweed controls
    seaweed_count_base: Optional[int] = None
    seaweed_count_per_80_cols: Optional[float] = None
    seaweed_sway_min: float = 0.18
    seaweed_sway_max: float = 0.5
    seaweed_lifetime_min: float = 25.0
    seaweed_lifetime_max: float = 60.0
    seaweed_regrow_delay_min: float = 4.0
    seaweed_regrow_delay_max: float = 12.0
    seaweed_growth_rate_min: float = 6.0
    seaweed_growth_rate_max: float = 12.0
    seaweed_shrink_rate_min: float = 8.0
    seaweed_shrink_rate_max: float = 16.0
    # Spawn concurrency/cooldowns
    spawn_max_concurrent: int = 1
    spawn_cooldown_global: float = 0.0
    specials_cooldowns: Dict[str, float] = field(default_factory=dict)


def _find_config_paths(override: Optional[Path] = None) -> List[Path]:
    if override is not None and override.exists():
        return [override]
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
    # Pre-scan argv for a --config path to prefer that file first
    override_path: Optional[Path] = None
    if argv:
        # support --config /path and --config=/path
        for i, tok in enumerate(argv):
            if tok == "--config" and i + 1 < len(argv):
                override_path = Path(str(argv[i + 1])).expanduser()
                break
            if tok.startswith("--config="):
                override_path = Path(tok.split("=", 1)[1]).expanduser()
                break

    for p in _find_config_paths(override_path):
        data = _load_toml(p)
        render = data.get("render", {})
        scene = data.get("scene", {})
        spawn = data.get("spawn", {})
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
        # Spawn/scaling config
        specials = spawn.get("specials")
        if isinstance(specials, dict):
            # copy known keys; ignore unknown
            for k in list(s.specials_weights.keys()):
                v = specials.get(k)
                if isinstance(v, (int, float)):
                    try:
                        s.specials_weights[k] = float(v)
                    except Exception:
                        pass
        for key, attr in [
            ("start_delay_min", "spawn_start_delay_min"),
            ("start_delay_max", "spawn_start_delay_max"),
            ("interval_min", "spawn_interval_min"),
            ("interval_max", "spawn_interval_max"),
            ("fish_scale", "fish_scale"),
            ("seaweed_scale", "seaweed_scale"),
            ("cooldown_global", "spawn_cooldown_global"),
        ]:
            if key in spawn:
                try:
                    setattr(s, attr, float(spawn.get(key)))
                except Exception:
                    pass
        # max_concurrent is an int
        if "max_concurrent" in spawn:
            try:
                s.spawn_max_concurrent = int(spawn.get("max_concurrent"))
            except Exception:
                pass
        # per-type cooldowns
        per_type = spawn.get("per_type")
        if isinstance(per_type, dict):
            for k, v in per_type.items():
                try:
                    s.specials_cooldowns[k] = float(v)
                except Exception:
                    pass

        # waterline
        if "waterline_top" in scene:
            try:
                s.waterline_top = int(scene.get("waterline_top", s.waterline_top))
            except Exception:
                pass
        # fish section
        fish = data.get("fish", {})
        if fish:
            for key, attr in [
                ("direction_bias", "fish_direction_bias"),
                ("speed_min", "fish_speed_min"),
                ("speed_max", "fish_speed_max"),
                ("bubble_min", "fish_bubble_min"),
                ("bubble_max", "fish_bubble_max"),
            ]:
                if key in fish:
                    try:
                        setattr(s, attr, float(fish.get(key)))
                    except Exception:
                        pass
            if "y_band" in fish and isinstance(fish.get("y_band"), (list, tuple)):
                try:
                    band = tuple(float(x) for x in fish.get("y_band"))  # type: ignore[arg-type]
                    if len(band) == 2:
                        s.fish_y_band = (band[0], band[1])
                except Exception:
                    pass
            if "count_base" in fish:
                try:
                    s.fish_count_base = int(fish.get("count_base"))
                except Exception:
                    pass
            if "count_per_80_cols" in fish:
                try:
                    s.fish_count_per_80_cols = float(fish.get("count_per_80_cols"))
                except Exception:
                    pass
        # seaweed section
        seaweed = data.get("seaweed", {})
        if seaweed:
            for key, attr in [
                ("sway_min", "seaweed_sway_min"),
                ("sway_max", "seaweed_sway_max"),
                ("lifetime_min", "seaweed_lifetime_min"),
                ("lifetime_max", "seaweed_lifetime_max"),
                ("regrow_delay_min", "seaweed_regrow_delay_min"),
                ("regrow_delay_max", "seaweed_regrow_delay_max"),
                ("growth_rate_min", "seaweed_growth_rate_min"),
                ("growth_rate_max", "seaweed_growth_rate_max"),
                ("shrink_rate_min", "seaweed_shrink_rate_min"),
                ("shrink_rate_max", "seaweed_shrink_rate_max"),
            ]:
                if key in seaweed:
                    try:
                        setattr(s, attr, float(seaweed.get(key)))
                    except Exception:
                        pass
            if "count_base" in seaweed:
                try:
                    s.seaweed_count_base = int(seaweed.get("count_base"))
                except Exception:
                    pass
            if "count_per_80_cols" in seaweed:
                try:
                    s.seaweed_count_per_80_cols = float(seaweed.get("count_per_80_cols"))
                except Exception:
                    pass
        # use the first found config file only
        break
    parser = argparse.ArgumentParser(description="Asciiquarium Redux")
    parser.add_argument("--config", type=str, help="Path to a config TOML file")
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
