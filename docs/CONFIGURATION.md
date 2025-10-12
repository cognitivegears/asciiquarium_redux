# Asciiquarium Redux - Configuration Guide
## Documentation Navigation

📋 **[Overview](../README.md)** | 🏗️ **[Architecture](ARCHITECTURE.md)** | 🚀 **[Getting Started](DEVELOPER_GUIDE.md)** | 📚 **[API Reference](API_REFERENCE.md)**

🎯 **[Entity System](ENTITY_SYSTEM.md)** | ⚙️ **Configuration** | 🖥️ **[Backends](BACKENDS.md)** | 🌐 **[Web Deployment](WEB_DEPLOYMENT.md)**

---


## Overview

Asciiquarium Redux uses TOML configuration files to customize all aspects of the aquarium simulation. The configuration system provides extensive control over entity behavior, spawn patterns, performance settings, and visual appearance.

## Configuration Sources

### Priority Order

Configuration is loaded with the following priority (highest to lowest):

1. **Command-line arguments** - Direct overrides
2. **Local config file** - `.asciiquarium.toml` in current directory
3. **User config file** - `~/.config/asciiquarium-redux/config.toml`
4. **XDG config** - `$XDG_CONFIG_HOME/asciiquarium-redux/config.toml`
5. **Default values** - Built-in [`Settings`](../asciiquarium_redux/util/settings.py:12) defaults

### Configuration File Locations

**Automatic Detection**:
```bash
# These files are automatically loaded if they exist
./asciiquarium.toml                                    # Project-specific
~/.config/asciiquarium-redux/config.toml              # User settings
$XDG_CONFIG_HOME/asciiquarium-redux/config.toml       # XDG standard
```

**Explicit Configuration**:
```bash
# Specify custom config file
asciiquarium --config my-settings.toml
asciiquarium --config=/path/to/config.toml
```

## Configuration Structure

### TOML File Format

Configuration files use [TOML](https://toml.io/) format with the following top-level sections:

```toml
[render]     # Display and performance settings
[scene]      # Global simulation parameters
[spawn]      # Entity spawning configuration
[fish]       # Fish behavior and population
[seaweed]    # Seaweed behavior and lifecycle
[fishhook]   # Interactive hook behavior
[ui]         # Backend and interface settings
```

## Render Settings

**Section**: `[render]`

Controls display performance and visual output.

```toml
[render]
fps = 24           # Target frames per second (5-120)
color = "auto"     # Color mode: "auto", "mono", "16", "256"
```

### Settings Reference

| Setting | Type    | Default  | Range     | Description                                                                     |
|---------|---------|----------|-----------|---------------------------------------------------------------------------------|
| `fps`   | integer | `20`     | `5-120`   | Target frames per second. Higher values = smoother animation but more CPU usage |
| `color` | string  | `"auto"` | See below | Color palette mode                                                              |

### Color Modes

- **`"auto"`**: Automatically detect terminal capabilities
- **`"mono"`**: Monochrome (white text only) - fastest performance
- **`"16"`**: 16-color ANSI palette - good compatibility
- **`"256"`**: 256-color palette - best visual quality

**Performance Impact**:
```toml
# High performance (older terminals)
[render]
fps = 15
color = "mono"

# Balanced (modern terminals)
[render]
fps = 24
color = "auto"

# High quality (powerful systems)
[render]
fps = 60
color = "256"
```

## Scene Settings

**Section**: `[scene]`

Global simulation parameters affecting the entire aquarium.

```toml
[scene]
density = 1.0              # Entity density multiplier (0.1-5.0)
seed = "random"            # Random seed: "random" or integer
speed = 0.75               # Global time multiplier (0.1-3.0)
waterline_top = 5          # Top row of waterline (0-based)
chest_enabled = true       # Show treasure chest decoration
chest_burst_seconds = 60.0 # Seconds between treasure chest bubbles
restock_enabled = true     # Replenish fish if counts stay low
restock_after_seconds = 20.0   # Time below threshold before restock
restock_min_fraction = 0.6     # Threshold: fraction of target count
fish_tank = true               # If true, fish turn before hitting left/right edges
fish_tank_margin = 0           # Columns from each side considered the glass margin
```

### Settings Reference

| Setting                 | Type       | Default    | Range        | Description                                                                                      |
|-------------------------|------------|------------|--------------|--------------------------------------------------------------------------------------------------|
| `density`               | float      | `1.0`      | `0.1-5.0`    | Scales all entity counts. Higher = more crowded aquarium                                         |
| `seed`                  | string/int | `"random"` | Any integer  | Random seed for deterministic playback                                                           |
| `speed`                 | float      | `0.75`     | `0.1-3.0`    | Global time multiplier. Higher = faster movement                                                 |
| `waterline_top`         | integer    | `5`        | `0-20`       | Top row of water surface (0 = very top of screen)                                                |
| `chest_enabled`         | boolean    | `true`     | -            | Whether to show treasure chest decoration                                                        |
| `chest_burst_seconds`   | float      | `60.0`     | `10.0-300.0` | Interval between treasure chest bubble bursts                                                    |
| `restock_enabled`       | boolean    | `true`     | -            | If true and fish population remains below threshold for `restock_after_seconds`, gently add fish |
| `restock_after_seconds` | float      | `20.0`     | `5.0-600.0`  | Duration below threshold before restock triggers                                                 |
| `restock_min_fraction`  | float      | `0.6`      | `0.1-1.0`    | Threshold fraction of target fish count that defines "low"                                       |
| `fish_tank`             | boolean    | `true`     | -            | Treat scene as a tank; fish turn before reaching side edges                                      |
| `fish_tank_margin`      | integer    | `0`        | `0-40`       | Margin (columns) from each side where fish will turn when `fish_tank` is true                    |

### Example Configurations

**Calm Aquarium**:
```toml
[scene]
density = 0.5     # Fewer entities
speed = 0.5       # Slower movement
waterline_top = 8 # Lower water level
```

**Busy Aquarium**:
```toml
[scene]
density = 2.5     # Many entities
speed = 1.5       # Fast movement
waterline_top = 3 # High water level
```

**Deterministic Playback**:
```toml
[scene]
seed = 12345      # Fixed seed for reproducible sessions
density = 1.0
speed = 1.0
```

## Spawn Settings

**Section**: `[spawn]`

Controls when and how special entities (sharks, whales, etc.) appear.

```toml
[spawn]
start_delay_min = 3.0      # Initial delay before first special (seconds)
start_delay_max = 8.0
interval_min = 8.0         # Time between specials (seconds)
interval_max = 20.0
fish_scale = 1.0           # Fish population multiplier
seaweed_scale = 1.0        # Seaweed population multiplier
max_concurrent = 1         # Maximum simultaneous specials
cooldown_global = 0.0      # Global cooldown after any special (seconds)

[spawn.specials]           # Relative spawn weights
shark = 1.0                # Equal probability
whale = 1.0
ship = 1.0
ducks = 1.0
dolphins = 1.0
swan = 1.0
monster = 1.0
big_fish = 1.0
fishhook = 1.0

[spawn.per_type]           # Per-entity cooldowns (seconds)
shark = 0.0                # No additional cooldown
whale = 0.0
ship = 0.0
# ... other entities
```

### Spawn Timing

| Setting               | Type    | Default    | Description                                              |
|-----------------------|---------|------------|----------------------------------------------------------|
| `start_delay_min/max` | float   | `3.0/8.0`  | Initial delay range before first special entity          |
| `interval_min/max`    | float   | `8.0/20.0` | Time range between subsequent special spawns             |
| `max_concurrent`      | integer | `1`        | Maximum number of special entities active simultaneously |
| `cooldown_global`     | float   | `0.0`      | Global cooldown after any special spawns                 |

### Spawn Weights

Control the relative probability of each special entity type:

```toml
[spawn.specials]
shark = 2.0      # Twice as likely as default
whale = 0.5      # Half as likely
ship = 0.0       # Disabled (never spawns)
monster = 10.0   # Very common
```

**Weight Calculation**:
- Weights are relative, not absolute percentages
- `shark=2.0, whale=1.0` means sharks are 2x more likely than whales
- `0.0` weight completely disables that entity type
- Weights can be fractional (e.g., `0.1`, `1.5`)

### Per-Type Cooldowns

Prevent specific entities from spawning too frequently:

```toml
[spawn.per_type]
shark = 15.0     # 15-second cooldown after shark spawns
whale = 30.0     # 30-second cooldown after whale spawns
monster = 60.0   # 1-minute cooldown after monster spawns
```

### Example Spawn Configurations

**Fast-Paced Action**:
```toml
[spawn]
start_delay_min = 1.0
start_delay_max = 3.0
interval_min = 3.0
interval_max = 8.0
max_concurrent = 3

[spawn.specials]
shark = 5.0
monster = 2.0
```

**Peaceful Environment**:
```toml
[spawn]
start_delay_min = 10.0
start_delay_max = 30.0
interval_min = 30.0
interval_max = 60.0
max_concurrent = 1

[spawn.specials]
shark = 0.0      # No predators
whale = 1.0
ducks = 2.0
swan = 2.0
```

**Shark-Heavy Theme**:
```toml
[spawn.specials]
shark = 10.0     # Very common
big_fish = 2.0   # Moderate
whale = 0.1      # Rare
ship = 0.0       # Disabled
ducks = 0.0      # Disabled
```

## Fish Settings

**Section**: `[fish]`

Controls fish behavior, movement, and population.

```toml
[fish]
direction_bias = 0.5       # Probability of rightward movement (0.0-1.0)
speed_min = 0.6            # Minimum fish speed (units/second)
speed_max = 2.5            # Maximum fish speed
bubble_min = 2.0           # Minimum seconds between bubbles
bubble_max = 5.0           # Maximum seconds between bubbles
vertical_speed_max = 0.5   # Max vertical drift speed (rows/sec); lower = calmer
turn_enabled = true        # Enable fish turning behavior
turn_chance_per_second = 0.01  # Probability of turning per second
turn_min_interval = 6.0    # Minimum time between turns (seconds)
turn_shrink_seconds = 0.35 # Duration of shrink animation
turn_expand_seconds = 0.35 # Duration of expand animation

# Optional: Override population calculation
# count_base = 6           # Base fish count
# count_per_80_cols = 3.0  # Additional fish per 80 columns of screen width

# Optional: Restrict fish to vertical band
# y_band = [0.2, 0.9]      # Fish stay between 20%-90% of screen height
```

### Behavior Settings

| Setting                  | Type    | Default   | Range      | Description                                                                                     |
|--------------------------|---------|-----------|------------|-------------------------------------------------------------------------------------------------|
| `direction_bias`         | float   | `0.5`     | `0.0-1.0`  | Probability fish spawn moving rightward                                                         |
| `speed_min/max`          | float   | `0.6/2.5` | `0.1-10.0` | Fish speed range (screen units/second)                                                          |
| `bubble_min/max`         | float   | `2.0/5.0` | `0.5-30.0` | Time range between bubble generation                                                            |
| `vertical_speed_max`     | float   | `0.5`     | `0.0-10.0` | Clamp on vertical drift speed (rows/sec). Smaller values produce calmer, more horizontal motion |
| `turn_enabled`           | boolean | `true`    | -          | Whether fish can turn around mid-swim                                                           |
| `turn_chance_per_second` | float   | `0.01`    | `0.0-1.0`  | Probability of initiating turn per second                                                       |

### Population Control

**Automatic Scaling** (default):
Fish count automatically scales with screen size using the formula:
```
count = (screen_area / density_divisor) * density * fish_scale
```

**Manual Override**:
```toml
[fish]
count_base = 8              # Base count regardless of screen size
count_per_80_cols = 4.0     # Additional fish per 80 columns of width
```

**Example**: For 120-column screen:
```
units = 120 / 80 = 1.5
total_fish = 8 + (4.0 * 1.5) = 14 fish
```

### Vertical Banding

Restrict fish to specific screen regions:

```toml
[fish]
y_band = [0.3, 0.8]    # Fish stay between 30%-80% of screen height
```

- `[0.0, 1.0]`: Full screen (default)
- `[0.2, 0.6]`: Upper-middle region only
- `[0.6, 1.0]`: Bottom region only

### Example Fish Configurations

**Slow, Peaceful Fish**:
```toml
[fish]
speed_min = 0.3
speed_max = 1.0
bubble_min = 5.0
bubble_max = 15.0
turn_chance_per_second = 0.005
```

**Fast, Active Fish**:
```toml
[fish]
speed_min = 1.5
speed_max = 4.0
bubble_min = 1.0
bubble_max = 3.0
turn_chance_per_second = 0.02
```

**Directional School**:
```toml
[fish]
direction_bias = 0.9    # Mostly rightward
turn_enabled = false    # No turning
speed_min = 1.0
speed_max = 1.5         # Consistent speed
```

## AI Settings (Utility AI)

These settings control the high-level AI behavior used when `ai_enabled` is true (default). They tune flocking, hiding, and exploration, and include idle-specific damping for calmer motion.

```toml
[ai]
idle_min_speed = 0.0               # Allow fish to fully stop while idling
idle_damping_per_sec = 0.8         # Horizontal velocity damping when idling (per second)
idle_vy_damping_per_sec = 1.2      # Vertical velocity damping when idling (per second)
wander_tau = 1.2                   # Smoothness of wander (higher = smoother)
eat_gain = 1.2
hide_gain = 1.5
explore_gain = 0.6
```

Notes:

- Damping applies only when the AI's current action is IDLE, helping big fish pause naturally.
- Lower `vertical_speed_max` in `[fish]` reinforces calmer, mostly horizontal motion.

## Seaweed Settings

**Section**: `[seaweed]`

Controls seaweed growth, lifecycle, and appearance.

```toml
[seaweed]
sway_min = 0.18           # Minimum sway speed (lower = faster)
sway_max = 0.5            # Maximum sway speed
lifetime_min = 25.0       # Minimum time alive (seconds)
lifetime_max = 60.0       # Maximum time alive
regrow_delay_min = 4.0    # Minimum dormant time (seconds)
regrow_delay_max = 12.0   # Maximum dormant time
growth_rate_min = 6.0     # Minimum growth speed (rows/second)
growth_rate_max = 12.0    # Maximum growth speed
shrink_rate_min = 8.0     # Minimum shrink speed (rows/second)
shrink_rate_max = 16.0    # Maximum shrink speed

# Optional: Override population calculation
# count_base = 4          # Base seaweed count
# count_per_80_cols = 3.0 # Additional seaweed per 80 columns
```

### Lifecycle Parameters

| Setting                | Type  | Default     | Range       | Description                                |
|------------------------|-------|-------------|-------------|--------------------------------------------|
| `sway_min/max`         | float | `0.18/0.5`  | `0.05-2.0`  | Sway animation speed (lower = faster sway) |
| `lifetime_min/max`     | float | `25.0/60.0` | `5.0-300.0` | How long seaweed stays alive (seconds)     |
| `regrow_delay_min/max` | float | `4.0/12.0`  | `1.0-60.0`  | Dormant period before regrowth (seconds)   |
| `growth_rate_min/max`  | float | `6.0/12.0`  | `1.0-50.0`  | Growing speed (screen rows/second)         |
| `shrink_rate_min/max`  | float | `8.0/16.0`  | `1.0-50.0`  | Dying speed (screen rows/second)           |

### Seaweed States

Each seaweed follows this lifecycle:

1. **Growing**: `0` → `full height` at `growth_rate`
2. **Alive**: Swaying for `lifetime` duration
3. **Dying**: `full height` → `0` at `shrink_rate`
4. **Dormant**: Invisible for `regrow_delay` duration
5. **Repeat**: Back to growing with new random parameters

### Example Seaweed Configurations

**Fast-Changing Garden**:
```toml
[seaweed]
lifetime_min = 10.0      # Short lives
lifetime_max = 20.0
regrow_delay_min = 2.0   # Quick regrowth
regrow_delay_max = 5.0
growth_rate_min = 15.0   # Fast growth
growth_rate_max = 20.0
```

**Stable Forest**:
```toml
[seaweed]
lifetime_min = 120.0     # Long lives
lifetime_max = 300.0
regrow_delay_min = 30.0  # Slow regrowth
regrow_delay_max = 60.0
growth_rate_min = 2.0    # Slow growth
growth_rate_max = 4.0
```

**Gentle Swaying**:
```toml
[seaweed]
sway_min = 0.8           # Very slow sway
sway_max = 1.2
lifetime_min = 60.0      # Moderate lifetime
lifetime_max = 90.0
```

## Fishhook Settings

**Section**: `[fishhook]`

Controls interactive fishing hook behavior.

```toml
[fishhook]
dwell_seconds = 20.0     # How long hook stays down (seconds)
```

| Setting         | Type  | Default | Range       | Description                                      |
|-----------------|-------|---------|-------------|--------------------------------------------------|
| `dwell_seconds` | float | `20.0`  | `5.0-120.0` | Duration hook remains deployed before retracting |

### Hook Interaction

**Mouse/Click Behavior**:
- Left-click anywhere on screen drops hook at that location
- Hook automatically retracts after `dwell_seconds`
- Nearby fish are attracted to the hook
- Only one hook can be active at a time

**Example Configurations**:
```toml
# Quick fishing
[fishhook]
dwell_seconds = 10.0

# Patient fishing
[fishhook]
dwell_seconds = 45.0
```

## UI Settings

**Section**: `[ui]`

Backend selection and display configuration.

```toml
[ui]
backend = "terminal"      # Backend: "terminal", "web", "tk"
fullscreen = false        # Fullscreen mode (tk backend only)
cols = 120               # Screen width in characters
rows = 40                # Screen height in characters
font_family = "Menlo"    # Font name (tk backend only)
font_size = 14           # Font size (tk backend only)
font_auto = true         # Auto-fit font so the castle fits under the waterline
font_min_size = 10       # Lower bound for auto font sizing
font_max_size = 22       # Upper bound for auto font sizing
```

When `font_auto` is enabled, the Tk backend adjusts font size on resize within `[font_min_size, font_max_size]` to keep the minimal scene (waterline + water + castle + margin) visible.

### Backend Selection

| Backend      | Description                               | Best For                       |
|--------------|-------------------------------------------|--------------------------------|
| `"terminal"` | Native terminal rendering via Asciimatics | SSH, tmux, standard terminals  |
| `"web"`      | Browser-based interface via WebSocket     | Remote access, mobile devices  |
| `"tk"`       | Desktop GUI window via Tkinter            | Standalone desktop application |

### Terminal Backend

```toml
[ui]
backend = "terminal"
cols = 120              # Ignored (uses terminal size)
rows = 40               # Ignored (uses terminal size)
```

**Features**:
- Full ANSI color support
- Automatic terminal size detection
- Keyboard and mouse input
- Best performance and compatibility

### Web Backend

```toml
[ui]
backend = "web"
cols = 120              # Canvas width in characters
rows = 40               # Canvas height in characters
```

**Additional CLI Options**:
```bash
asciiquarium --backend web --port 8080 --open
```

**Features**:
- Browser-based interface
- WebSocket real-time updates
- Mobile-friendly responsive design
- Remote access capability

### TkInter Backend

```toml
[ui]
backend = "tk"
fullscreen = false      # Window mode
cols = 100              # Canvas width in characters
rows = 30               # Canvas height in characters
font_family = "Consolas"
font_size = 12
```

**Features**:
- Native desktop window
- Font customization
- Fullscreen support
- Cross-platform GUI

### Example UI Configurations

**Large Terminal Display**:
```toml
[ui]
backend = "terminal"    # Uses actual terminal size
```

**Compact Web Interface**:
```toml
[ui]
backend = "web"
cols = 80
rows = 24
```

**Fullscreen Desktop**:
```toml
[ui]
backend = "tk"
fullscreen = true
font_family = "Source Code Pro"
font_size = 16
```

## AI Settings

Enable simple lifelike choices and steering for fish.

```toml
[ai]
enabled = true
action_temperature = 0.6
wander_tau = 1.2
separation_radius = 3.0
obstacle_radius = 3.0
flock_alignment = 0.8
flock_cohesion = 0.5
flock_separation = 1.2
eat_gain = 1.2
hide_gain = 1.5
explore_gain = 0.6
baseline_separation = 0.6
baseline_avoid = 0.9
```

Notes

- Fish prefer food flakes; when they are very hungry and no food is available, larger fish may eat strictly smaller fish. A brief splat effect appears and prey are respawned to keep populations healthy.

## Command-Line Overrides

Most configuration options can be overridden via command-line arguments:

### Basic Options

```bash
# Performance settings
asciiquarium --fps 30 --color mono

# Scene settings
asciiquarium --density 2.0 --speed 1.5 --seed 12345

# Backend selection
asciiquarium --backend web --port 8080
asciiquarium --backend tk --fullscreen
```

### Advanced Options

```bash
# Spawn configuration
asciiquarium --spawn-weights '{"shark": 5.0, "whale": 0.1}'
asciiquarium --spawn-max-concurrent 3

# Population scaling
asciiquarium --fish-scale 2.0 --seaweed-scale 0.5

# Fish behavior
asciiquarium --fish-speed-min 1.0 --fish-speed-max 3.0
```

### Configuration File Override

```bash
# Use specific config file
asciiquarium --config production.toml

# Combine config file with CLI overrides
asciiquarium --config base.toml --fps 60 --density 1.5
```

## Configuration Examples

### Performance Profiles

**Low-End Systems**:
```toml
[render]
fps = 12
color = "mono"

[scene]
density = 0.7
speed = 0.8

[spawn]
max_concurrent = 1
interval_min = 15.0
interval_max = 30.0
```

**High-End Systems**:
```toml
[render]
fps = 60
color = "256"

[scene]
density = 2.0
speed = 1.2

[spawn]
max_concurrent = 3
interval_min = 3.0
interval_max = 8.0
```

### Theme Configurations

**Peaceful Ocean**:
```toml
[scene]
density = 0.8
speed = 0.6

[spawn.specials]
shark = 0.0
monster = 0.0
whale = 2.0
ducks = 1.0
swan = 1.0

[fish]
speed_min = 0.4
speed_max = 1.2
bubble_min = 8.0
bubble_max = 15.0
```

**Predator Tank**:
```toml
[scene]
density = 1.5
speed = 1.3

[spawn.specials]
shark = 10.0
monster = 5.0
big_fish = 3.0
whale = 0.0
ducks = 0.0

[fish]
speed_min = 1.0
speed_max = 3.0
turn_chance_per_second = 0.02
```

**Zen Garden**:
```toml
[scene]
density = 0.5
speed = 0.4

[spawn]
max_concurrent = 1
interval_min = 60.0
interval_max = 120.0

[spawn.specials]
shark = 0.0
monster = 0.0
ship = 0.0
whale = 0.1
swan = 1.0

[seaweed]
sway_min = 1.0
sway_max = 2.0
lifetime_min = 180.0
lifetime_max = 300.0
```

## Validation and Error Handling

### Configuration Validation

The system validates configuration values and applies sensible defaults:

```toml
# Invalid values are corrected
[render]
fps = 500        # Clamped to maximum (120)
color = "invalid" # Falls back to "auto"

[scene]
density = -1.0   # Clamped to minimum (0.1)
speed = 0.0      # Clamped to minimum (0.1)
```

### Error Recovery

**Missing Files**: Non-existent config files are silently ignored, falling back to defaults.

**Malformed TOML**: Syntax errors in TOML files are logged but don't crash the application.

**Invalid Settings**: Out-of-range or wrong-type values are corrected with warnings.

### Debug Configuration

To troubleshoot configuration issues:

```bash
# Verbose mode shows config loading process
asciiquarium --verbose

# Test specific config file
asciiquarium --config test.toml --verbose
```

## Performance Tuning

### CPU Optimization

**Reduce Update Frequency**:
```toml
[render]
fps = 15           # Lower FPS = less CPU usage

[scene]
density = 0.8      # Fewer entities = less computation
```

**Simplify Behavior**:
```toml
[fish]
turn_enabled = false     # Disable complex turning animation
bubble_max = 10.0        # Longer bubble intervals

[spawn]
max_concurrent = 1       # Fewer special entities
interval_min = 20.0      # Less frequent spawning
```

### Memory Optimization

**Control Population Growth**:
```toml
[scene]
density = 1.0            # Reasonable entity count

[spawn]
max_concurrent = 2       # Limit simultaneous specials
interval_min = 10.0      # Prevent spawn floods

[fish]
bubble_max = 8.0         # Limit bubble generation
```

### Display Optimization

**Terminal Compatibility**:
```toml
[render]
color = "16"             # Better compatibility than "256"
fps = 20                 # Reasonable refresh rate

[ui]
backend = "terminal"     # Native terminal is fastest
```

## Cross-References

- **Architecture Overview**: [`ARCHITECTURE.md`](ARCHITECTURE.md) - System design context
- **Development Setup**: [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) - Development configuration
- **API Reference**: [`API_REFERENCE.md`](API_REFERENCE.md) - Settings class details
- **Entity Behavior**: [`ENTITY_SYSTEM.md`](ENTITY_SYSTEM.md) - How settings affect entities
- **Backend Selection**: [`BACKENDS.md`](BACKENDS.md) - Backend-specific options
- **Web Deployment**: [`WEB_DEPLOYMENT.md`](WEB_DEPLOYMENT.md) - Web backend configuration
