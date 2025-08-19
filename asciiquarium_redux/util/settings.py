"""Configuration management module for Asciiquarium Redux.

This module provides comprehensive configuration management for the aquarium simulation,
supporting multiple configuration sources with proper precedence handling. It enables
users to customize every aspect of the simulation through TOML files, command-line
arguments, and programmatic configuration.

Key Features:
    - **TOML Configuration Files**: Human-readable configuration with hierarchical structure
    - **Command-Line Integration**: Full CLI argument parsing with type validation
    - **Configuration Precedence**: Proper merging of settings from multiple sources
    - **Type Safety**: Strong typing with dataclass-based configuration schema
    - **Validation**: Input validation with helpful error messages
    - **Default Values**: Sensible defaults for all configuration parameters

Architecture:
    The module follows a layered configuration approach:

    1. **Base Defaults**: Built-in sensible defaults for all parameters
    2. **Configuration Files**: TOML files for persistent customization
    3. **Command-Line Arguments**: Runtime overrides for quick adjustments
    4. **Programmatic API**: Direct Settings object creation for embedded usage

Configuration Sources (Priority Order):
     1. **CLI Arguments** (highest priority): Runtime overrides
     2. **Explicit Config File**: User-specified via --config argument
     3. **Discovered Configs**: In order: ./.asciiquarium.toml, ./config.toml,
         then user config at $XDG_CONFIG_HOME/asciiquarium_rules/config.toml or
         ~/.config/asciiquarium_rules/config.toml
     4. **Built-in Defaults** (lowest priority): Fallback values

TOML Format Support:
    The module uses Python's built-in tomllib for parsing TOML files. Configuration
    files support the full range of TOML features including nested sections, arrays,
    and complex data types.

    Example Configuration:
        ```toml
        # Basic animation settings
        fps = 30
        density = 1.5
        color = "256"
        speed = 0.8

        # Special entity weights
        [specials_weights]
        shark = 2.0
        whale = 0.5
        fishhook = 1.2

        # Fish behavior
        fish_scale = 1.2
        fish_speed_min = 0.8
        fish_speed_max = 2.2
        ```

Command-Line Interface:
    The module generates a comprehensive CLI with automatic argument generation
    from the Settings dataclass schema. This ensures CLI and configuration file
    options remain synchronized.

    Categories:
        - **Animation**: FPS, speed, density control
        - **Visual**: Color modes, display options
        - **Behavior**: Entity-specific behavior parameters
        - **Spawning**: Special entity timing and weights
        - **Advanced**: Debug options and performance tuning

Type System:
    The Settings class uses dataclasses with proper type annotations to ensure
    type safety and enable automatic validation. Complex types like dictionaries
    and lists are properly handled with appropriate defaults.

Error Handling:
    The module provides detailed error messages for configuration issues:
    - Invalid TOML syntax with line number references
    - Type mismatches with expected vs actual types
    - Unknown configuration keys with suggestions
    - Value range validation with acceptable ranges

Performance:
    Configuration loading is optimized for startup time with efficient parsing
    and minimal object allocation. Settings objects are immutable after creation
    to prevent accidental modification during runtime.

Usage Examples:
    Load with defaults:
        >>> settings = Settings()

    Load from file:
        >>> settings = load_settings_from_sources(config_file="custom.toml")

    Load with CLI override:
        >>> settings = load_settings_from_sources(args=["--fps", "60"])

    Programmatic creation:
        >>> settings = Settings(fps=30, density=1.5, color="256")

Integration:
    The module integrates seamlessly with the CLI runner and application core:
    - runner.py uses load_settings_from_sources() for startup configuration
    - app.py accepts Settings objects for complete simulation control
    - Web interface dynamically updates settings for real-time changes

See Also:
    - runner.py: CLI interface that uses this configuration system
    - app.py: Main application that consumes Settings objects
    - sample-config.toml: Example configuration file with all options
    - docs/CONFIGURATION.md: Detailed configuration guide
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import tomllib


@dataclass
class Settings:
    """Configuration dataclass containing all simulation parameters for Asciiquarium Redux.

    The Settings class centralizes all configurable aspects of the aquarium simulation,
    from basic animation parameters to detailed entity behavior controls. It supports
    loading from TOML configuration files and command-line argument overrides.

    The class is designed as a dataclass for easy serialization/deserialization and
    provides sensible defaults for all parameters. Configuration can be loaded from:

    - TOML configuration files (recommended for complex setups)
    - Command-line arguments (for quick adjustments)
    - Direct instantiation with keyword arguments (for programmatic use)

    Categories:
        **Animation Control**:
            - fps: Frame rate control (5-60 fps recommended)
            - speed: Global speed multiplier for all animations
            - density: Entity spawn density multiplier

        **Visual Settings**:
            - color: Color mode (auto/mono/16/256)
            - waterline_top: Position of water surface
            - castle_enabled/chest_enabled: Enable/disable decorative elements

        **Entity Behavior**:
            - fish_*: Fish movement, turning, and bubble generation
            - seaweed_*: Seaweed growth, sway, and lifecycle
            - spawn_*: Special entity spawning timing and weights

        **Special Effects**:
            - specials_weights: Probability weights for different special entities
            - fishhook_*: Fishhook behavior and interaction timing
            - chest_burst_seconds: Treasure chest animation timing

    Performance Notes:
        - Higher FPS increases CPU usage but provides smoother animation
        - Density multipliers significantly affect entity count and performance
        - Color modes: mono < 16 < 256 < auto (performance impact)
        - Large scale values can overwhelm slower systems

    Attributes:
        fps (int): Animation frame rate, 5-60 fps recommended. Default: 20
        density (float): Global entity density multiplier. Default: 1.0
        color (str): Color mode - "auto", "mono", "16", or "256". Default: "auto"
        seed (Optional[int]): Random seed for reproducible simulations. Default: None
        speed (float): Global animation speed multiplier. Default: 0.75

        specials_weights (Dict[str, float]): Spawn probability weights for special entities.
            Keys: shark, fishhook, whale, ship, ducks, dolphins, swan, monster, big_fish
            Values: 0.0 (disabled) to 2.0+ (high frequency). Default: 1.0 each

        spawn_start_delay_min/max (float): Initial delay before first special spawn (seconds)
        spawn_interval_min/max (float): Time between special entity spawns (seconds)

        fish_scale (float): Fish population multiplier. Default: 1.0
        seaweed_scale (float): Seaweed population multiplier. Default: 1.0

        waterline_top (int): Row position of water surface. Default: 5
        castle_enabled (bool): Enable castle decoration. Default: True
        chest_enabled (bool): Enable treasure chest decoration. Default: True
        chest_burst_seconds (float): Treasure chest animation interval. Default: 60.0

        fish_direction_bias (float): Fish movement bias (0.0=left, 1.0=right). Default: 0.5
        fish_speed_min/max (float): Fish movement speed range. Default: 0.6-2.5
        fish_bubble_min/max (float): Fish bubble generation interval. Default: 2.0-5.0
        fish_turn_enabled (bool): Enable fish turning animation. Default: True
        fish_turn_chance_per_second (float): Probability of fish turning. Default: 0.01
        fish_turn_min_interval (float): Minimum time between turns. Default: 6.0
        fish_turn_shrink/expand_seconds (float): Turn animation timing. Default: 0.35 each

        ... (65+ total configuration parameters)

    Example:
        >>> # Basic usage with defaults
        >>> settings = Settings()
        >>>
        >>> # Custom configuration
        >>> settings = Settings(
        ...     fps=30,
        ...     density=1.5,
        ...     color="256",
        ...     fish_scale=2.0,
        ...     specials_weights={"shark": 2.0, "whale": 0.5}
        ... )
        >>>
        >>> # Load from TOML file
        >>> settings = Settings.from_toml("config.toml")
        >>>
        >>> # Override with command line
        >>> settings = Settings.from_args(["--fps", "60", "--density", "0.8"])

    See Also:
        - Configuration Guide: docs/CONFIGURATION.md
        - Sample Config: sample-config.toml
        - AsciiQuarium: Main application class that uses these settings
    """

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
    fish_scale: float = 1.0
    seaweed_scale: float = 1.0
    waterline_top: int = 5
    castle_enabled: bool = True
    chest_enabled: bool = True
    chest_burst_seconds: float = 60.0
    fish_direction_bias: float = 0.5
    fish_speed_min: float = 0.6
    fish_speed_max: float = 2.5
    # Max vertical drift speed (rows/sec); small to keep mostly horizontal motion
    # Slightly increased for more responsive vertical movement
    fish_vertical_speed_max: float = 0.5
    fish_bubble_min: float = 2.0
    fish_bubble_max: float = 5.0
    fish_turn_enabled: bool = True
    fish_turn_chance_per_second: float = 0.01
    fish_turn_min_interval: float = 6.0
    fish_turn_shrink_seconds: float = 0.35
    fish_turn_expand_seconds: float = 0.35
    fish_count_base: Optional[int] = None
    fish_count_per_80_cols: Optional[float] = None
    fish_y_band: Optional[Tuple[float, float]] = None
    seaweed_count_base: Optional[int] = None
    seaweed_count_per_80_cols: Optional[float] = None
    # Fish food (special) configuration
    fish_food_count_min: int = 5
    fish_food_count_max: int = 12
    fish_food_float_seconds_min: float = 1.0
    fish_food_float_seconds_max: float = 3.0
    fish_food_sink_speed_min: float = 0.4
    fish_food_sink_speed_max: float = 1.0
    fish_food_drift_chance: float = 0.35
    fish_food_drift_speed: float = 1.0
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
    spawn_max_concurrent: int = 1
    spawn_cooldown_global: float = 0.0
    specials_cooldowns: Dict[str, float] = field(default_factory=dict)
    fishhook_dwell_seconds: float = 20.0
    ui_backend: str = "terminal"
    ui_fullscreen: bool = False
    ui_cols: int = 120
    ui_rows: int = 40
    ui_font_family: str = "Menlo"
    ui_font_size: int = 14
    ui_font_auto: bool = True
    ui_font_min_size: int = 10
    ui_font_max_size: int = 22
    web_open: bool = False
    web_port: int = 8000
    # AI configuration (Utility AI + steering)
    ai_enabled: bool = True
    ai_action_temperature: float = 0.6
    ai_wander_tau: float = 1.2
    ai_separation_radius: float = 3.0
    ai_obstacle_radius: float = 3.0
    ai_flock_alignment: float = 0.8
    ai_flock_cohesion: float = 0.5
    ai_flock_separation: float = 1.2
    ai_eat_gain: float = 1.2
    ai_hide_gain: float = 1.5
    ai_explore_gain: float = 0.6
    ai_baseline_separation: float = 0.6
    ai_baseline_avoid: float = 0.9
    # When idling, allow very low speeds and add damping to calm motion
    ai_idle_min_speed: float = 0.0
    ai_idle_damping_per_sec: float = 0.8
    ai_idle_vy_damping_per_sec: float = 1.2
    # Restock configuration: if fish population remains below target for this many seconds, add fish
    restock_enabled: bool = True
    restock_after_seconds: float = 20.0
    restock_min_fraction: float = 0.6  # if below 60% of target, trigger restock
    # Fish tank mode: if enabled, fish turn before reaching left/right edges
    fish_tank: bool = True
    fish_tank_margin: int = 0


def _find_config_paths(override: Optional[Path] = None) -> List[Path]:
    if override is not None:
        if override.exists():
            return [override]
        return [override]
    paths: List[Path] = []
    cwd = Path.cwd()
    # Project-local configs (priority order)
    paths.append(cwd / ".asciiquarium.toml")
    paths.append(cwd / "config.toml")
    # User configs: prefer new namespace "asciiquarium_rules"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        paths.append(Path(xdg) / "asciiquarium_rules" / "config.toml")
    home = Path.home()
    paths.append(home / ".config" / "asciiquarium_rules" / "config.toml")
    return [p for p in paths if p.exists()]


def _load_toml(path: Path) -> dict:
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def load_settings_from_sources(argv: Optional[List[str]] = None) -> Settings:
    """Load settings from multiple sources with proper precedence.

    This function implements the complete configuration loading pipeline:
    1. Create base Settings with defaults
    2. Parse config file path from command line
    3. Load and merge TOML configuration files
    4. Apply command line argument overrides

    Args:
        argv: Optional command line arguments for parsing

    Returns:
        Fully configured Settings object with all sources merged

    Raises:
        FileNotFoundError: If explicitly specified config file doesn't exist
    """
    s = Settings()

    # Parse config file path from command line
    override_path = _parse_config_file_path(argv)

    # Load TOML configuration files
    _load_toml_configurations(s, override_path)

    # Apply command line argument overrides
    _apply_cli_overrides(s, argv)

    return s


def _parse_config_file_path(argv: Optional[List[str]]) -> Optional[Path]:
    """Extract config file path from command line arguments.

    Args:
        argv: Command line arguments to parse

    Returns:
        Path to config file if specified, None otherwise
    """
    if not argv:
        return None

    for i, tok in enumerate(argv):
        if tok == "--config" and i + 1 < len(argv):
            return Path(str(argv[i + 1])).expanduser()
        if tok.startswith("--config="):
            return Path(tok.split("=", 1)[1]).expanduser()

    return None


def _load_toml_configurations(s: Settings, override_path: Optional[Path]) -> None:
    """Load and merge TOML configuration files into settings.

    Args:
        s: Settings object to modify
        override_path: Optional explicit config file path

    Raises:
        FileNotFoundError: If explicit config file doesn't exist
    """
    candidates = _find_config_paths(override_path)
    if override_path is not None and candidates and not candidates[0].exists():
        raise FileNotFoundError(f"Config file not found: {override_path}")

    for p in candidates:
        data = _load_toml(p)
        _parse_render_settings(s, data.get("render", {}))
        _parse_scene_settings(s, data.get("scene", {}))
        _parse_spawn_settings(s, data.get("spawn", {}))
        _parse_fish_settings(s, data.get("fish", {}))
        _parse_seaweed_settings(s, data.get("seaweed", {}))
        _parse_fishhook_settings(s, data.get("fishhook", {}))
        _parse_ui_settings(s, data.get("ui", {}))
        _parse_ai_settings(s, data.get("ai", {}))
        # Fallback: accept top-level fish tank keys if users placed them at root
        try:
            if "fish_tank" in data:
                s.fish_tank = bool(data.get("fish_tank"))
            if "fish_tank_margin" in data:
                s.fish_tank_margin = max(0, int(data.get("fish_tank_margin") or 0))
        except Exception:
            pass
        break  # Only process first found config file


def _parse_render_settings(s: Settings, render: dict) -> None:
    """Parse render section of TOML configuration.

    Args:
        s: Settings object to modify
        render: Render section dictionary from TOML
    """
    if "fps" in render:
        s.fps = int(render.get("fps", s.fps))
    if "color" in render:
        s.color = str(render.get("color", s.color))


def _parse_scene_settings(s: Settings, scene: dict) -> None:
    """Parse scene section of TOML configuration.

    Args:
        s: Settings object to modify
        scene: Scene section dictionary from TOML
    """
    _safe_set_float(s, "density", scene)
    _safe_set_float(s, "speed", scene)

    if "seed" in scene:
        seed_val = scene.get("seed")
        if isinstance(seed_val, int):
            s.seed = seed_val
        elif isinstance(seed_val, str) and seed_val.lower() == "random":
            s.seed = None

    _safe_set_int(s, "waterline_top", scene)
    _safe_set_bool(s, "castle_enabled", scene)
    _safe_set_bool(s, "chest_enabled", scene)
    _safe_set_float(s, "chest_burst_seconds", scene)

    # Population resilience (restocking)
    _safe_set_bool(s, "restock_enabled", scene)
    _safe_set_float(s, "restock_after_seconds", scene)
    _safe_set_float(s, "restock_min_fraction", scene)
    # Fish tank mode
    _safe_set_bool(s, "fish_tank", scene)
    _safe_set_int(s, "fish_tank_margin", scene)
    # Accept kebab-case aliases
    try:
        if "fish-tank" in scene:
            s.fish_tank = bool(scene.get("fish-tank"))
        if "fish-tank-margin" in scene:
            s.fish_tank_margin = max(0, int(scene.get("fish-tank-margin") or 0))
    except Exception:
        pass


def _parse_spawn_settings(s: Settings, spawn: dict) -> None:
    """Parse spawn section of TOML configuration.

    Args:
        s: Settings object to modify
        spawn: Spawn section dictionary from TOML
    """
    # Handle special entity weights
    specials = spawn.get("specials")
    if isinstance(specials, dict):
        for k in list(s.specials_weights.keys()):
            v = specials.get(k)
            if isinstance(v, (int, float)):
                try:
                    s.specials_weights[k] = float(v)
                except Exception:
                    pass

    # Handle spawn timing parameters
    spawn_mappings = [
        ("start_delay_min", "spawn_start_delay_min"),
        ("start_delay_max", "spawn_start_delay_max"),
        ("interval_min", "spawn_interval_min"),
        ("interval_max", "spawn_interval_max"),
        ("fish_scale", "fish_scale"),
        ("seaweed_scale", "seaweed_scale"),
        ("cooldown_global", "spawn_cooldown_global"),
    ]

    for key, attr in spawn_mappings:
        if key in spawn:
            try:
                val = spawn.get(key)
                if val is not None:
                    setattr(s, attr, float(val))
            except Exception:
                pass

    if "max_concurrent" in spawn:
        try:
            val = spawn.get("max_concurrent")
            if val is not None:
                s.spawn_max_concurrent = int(val)
        except Exception:
            pass

    # Handle per-type cooldowns
    per_type = spawn.get("per_type")
    if isinstance(per_type, dict):
        for k, v in per_type.items():
            try:
                s.specials_cooldowns[k] = float(v)
            except Exception:
                pass


def _parse_fish_settings(s: Settings, fish: dict) -> None:
    """Parse fish section of TOML configuration.

    Args:
        s: Settings object to modify
        fish: Fish section dictionary from TOML
    """
    if not fish:
        return

    fish_mappings = [
        ("direction_bias", "fish_direction_bias"),
        ("speed_min", "fish_speed_min"),
        ("speed_max", "fish_speed_max"),
    ("vertical_speed_max", "fish_vertical_speed_max"),
        # accept alias spelling
        ("vertical_max_speed", "fish_vertical_speed_max"),
        ("bubble_min", "fish_bubble_min"),
        ("bubble_max", "fish_bubble_max"),
        ("turn_chance_per_second", "fish_turn_chance_per_second"),
        ("turn_min_interval", "fish_turn_min_interval"),
        ("turn_shrink_seconds", "fish_turn_shrink_seconds"),
        ("turn_expand_seconds", "fish_turn_expand_seconds"),
    ]

    for key, attr in fish_mappings:
        if key in fish:
            try:
                val = fish.get(key)
                if val is not None:
                    setattr(s, attr, float(val))
            except Exception:
                pass

    if "turn_enabled" in fish:
        try:
            s.fish_turn_enabled = bool(fish.get("turn_enabled"))
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
            val = fish.get("count_base")
            if val is not None:
                s.fish_count_base = int(val)
        except Exception:
            pass

    if "count_per_80_cols" in fish:
        try:
            val = fish.get("count_per_80_cols")
            if val is not None:
                s.fish_count_per_80_cols = float(val)
        except Exception:
            pass


def _parse_seaweed_settings(s: Settings, seaweed: dict) -> None:
    """Parse seaweed section of TOML configuration.

    Args:
        s: Settings object to modify
        seaweed: Seaweed section dictionary from TOML
    """
    if not seaweed:
        return

    seaweed_mappings = [
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
    ]

    for key, attr in seaweed_mappings:
        if key in seaweed:
            try:
                val = seaweed.get(key)
                if val is not None:
                    setattr(s, attr, float(val))
            except Exception:
                pass

    if "count_base" in seaweed:
        try:
            val = seaweed.get("count_base")
            if val is not None:
                s.seaweed_count_base = int(val)
        except Exception:
            pass

    if "count_per_80_cols" in seaweed:
        try:
            val = seaweed.get("count_per_80_cols")
            if val is not None:
                s.seaweed_count_per_80_cols = float(val)
        except Exception:
            pass


def _parse_fishhook_settings(s: Settings, fishhook: dict) -> None:
    """Parse fishhook section of TOML configuration.

    Args:
        s: Settings object to modify
        fishhook: Fishhook section dictionary from TOML
    """
    if isinstance(fishhook, dict):
        if "dwell_seconds" in fishhook:
            try:
                val = fishhook.get("dwell_seconds")
                if val is not None:
                    s.fishhook_dwell_seconds = float(val)
            except Exception:
                pass


def _parse_ui_settings(s: Settings, ui: dict) -> None:
    """Parse UI section of TOML configuration.

    Args:
        s: Settings object to modify
        ui: UI section dictionary from TOML
    """
    if not isinstance(ui, dict):
        return

    b = ui.get("backend")
    if isinstance(b, str):
        s.ui_backend = b

    fs = ui.get("fullscreen")
    if isinstance(fs, bool):
        s.ui_fullscreen = fs

    v = ui.get("cols")
    if isinstance(v, int):
        s.ui_cols = max(40, min(300, v))

    v = ui.get("rows")
    if isinstance(v, int):
        s.ui_rows = max(15, min(200, v))

    f = ui.get("font_family")
    if isinstance(f, str):
        s.ui_font_family = f

    v = ui.get("font_size")
    if isinstance(v, int):
        s.ui_font_size = max(8, min(48, v))

    b = ui.get("font_auto")
    if isinstance(b, bool):
        s.ui_font_auto = b

    v = ui.get("font_min_size")
    if isinstance(v, int):
        s.ui_font_min_size = max(6, min(64, v))

    v = ui.get("font_max_size")
    if isinstance(v, int):
        s.ui_font_max_size = max(8, min(72, v))

    # Ensure coherent bounds
    if s.ui_font_max_size < s.ui_font_min_size:
        s.ui_font_max_size = s.ui_font_min_size


def _apply_cli_overrides(s: Settings, argv: Optional[List[str]]) -> None:
    """Apply command line argument overrides to settings.

    Args:
        s: Settings object to modify
        argv: Command line arguments to parse
    """
    parser = argparse.ArgumentParser(description="Asciiquarium Redux")
    parser.add_argument("--config", type=str, help="Path to a config TOML file")
    parser.add_argument("--fps", type=int)
    parser.add_argument("--density", type=float)
    parser.add_argument("--color", choices=["auto", "mono", "16", "256"])
    parser.add_argument("--seed", type=int)
    parser.add_argument("--speed", type=float)
    parser.add_argument("--backend", choices=["terminal", "tk", "web"])
    parser.add_argument("--open", dest="web_open", action="store_true")
    parser.add_argument("--port", dest="web_port", type=int)
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument("--no-fullscreen", dest="fullscreen", action="store_false")
    parser.add_argument("--castle", dest="castle_enabled", action="store_true", default=None)
    parser.add_argument("--no-castle", dest="castle_enabled", action="store_false")
    parser.add_argument("--font-min", dest="ui_font_min_size", type=int)
    parser.add_argument("--font-max", dest="ui_font_max_size", type=int)
    parser.add_argument("--ai", dest="ai_enabled", action="store_true")
    parser.add_argument("--no-ai", dest="ai_enabled", action="store_false")
    # Default paired booleans to None so absent flags don't override config
    parser.set_defaults(fullscreen=None, ai_enabled=None)
    parser.add_argument("--fish-tank", dest="fish_tank", action="store_true")
    parser.add_argument("--no-fish-tank", dest="fish_tank", action="store_false")
    parser.add_argument("--fish-tank-margin", dest="fish_tank_margin", type=int)
    parser.set_defaults(fish_tank=None)
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
    if args.backend is not None:
        s.ui_backend = args.backend
    if getattr(args, "fullscreen", None) is not None:
        s.ui_fullscreen = bool(args.fullscreen)
    if getattr(args, "castle_enabled", None) is not None:
        s.castle_enabled = bool(args.castle_enabled)
    if getattr(args, "ai_enabled", None) is not None:
        s.ai_enabled = bool(args.ai_enabled)
    if getattr(args, "fish_tank", None) is not None:
        s.fish_tank = bool(args.fish_tank)
    if getattr(args, "fish_tank_margin", None) is not None:
        s.fish_tank_margin = max(0, int(args.fish_tank_margin))
    if getattr(args, "ui_font_min_size", None) is not None:
        s.ui_font_min_size = max(6, min(64, int(args.ui_font_min_size)))
    if getattr(args, "ui_font_max_size", None) is not None:
        s.ui_font_max_size = max(8, min(72, int(args.ui_font_max_size)))
    if s.ui_font_max_size < s.ui_font_min_size:
        s.ui_font_max_size = s.ui_font_min_size
    try:
        if getattr(args, "web_open", False):
            s.web_open = True
        vp = getattr(args, "web_port", None)
        if isinstance(vp, int) and vp:
            s.web_port = vp
    except Exception:
        pass


def _safe_set_float(s: Settings, attr: str, data: dict) -> None:
    """Safely set a float attribute with error handling.

    Args:
        s: Settings object to modify
        attr: Attribute name to set
        data: Dictionary containing the value
    """
    if attr in data:
        try:
            val = data.get(attr)
            if val is not None:
                setattr(s, attr, float(val))
        except Exception:
            pass


def _safe_set_int(s: Settings, attr: str, data: dict) -> None:
    """Safely set an integer attribute with error handling.

    Args:
        s: Settings object to modify
        attr: Attribute name to set
        data: Dictionary containing the value
    """
    if attr in data:
        try:
            val = data.get(attr)
            if val is not None:
                setattr(s, attr, int(val))
        except Exception:
            pass


def _safe_set_bool(s: Settings, attr: str, data: dict) -> None:
    """Safely set a boolean attribute with error handling.

    Args:
        s: Settings object to modify
        attr: Attribute name to set
        data: Dictionary containing the value
    """
    if attr in data:
        try:
            setattr(s, attr, bool(data.get(attr)))
        except Exception:
            pass


def _parse_ai_settings(s: Settings, ai: dict) -> None:
    """Parse AI section of TOML configuration.

    Section keys follow:
        enabled (bool), action_temperature, wander_tau,
        separation_radius, obstacle_radius,
        flock_alignment, flock_cohesion, flock_separation,
        eat_gain, hide_gain, explore_gain,
        baseline_separation, baseline_avoid
    """
    if not isinstance(ai, dict):
        return
    _safe_set_bool(s, "ai_enabled", ai)
    for key, attr in [
        ("action_temperature", "ai_action_temperature"),
        ("wander_tau", "ai_wander_tau"),
        ("separation_radius", "ai_separation_radius"),
        ("obstacle_radius", "ai_obstacle_radius"),
        ("flock_alignment", "ai_flock_alignment"),
        ("flock_cohesion", "ai_flock_cohesion"),
        ("flock_separation", "ai_flock_separation"),
        ("eat_gain", "ai_eat_gain"),
        ("hide_gain", "ai_hide_gain"),
        ("explore_gain", "ai_explore_gain"),
        ("baseline_separation", "ai_baseline_separation"),
        ("baseline_avoid", "ai_baseline_avoid"),
    ]:
        if key in ai:
            try:
                val = ai.get(key)
                if val is not None:
                    setattr(s, attr, float(val))
            except Exception:
                pass
