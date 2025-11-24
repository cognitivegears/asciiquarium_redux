# Asciiquarium Redux - API Reference
## Documentation Navigation

📋 **[Overview](../README.md)** | 🏗️ **[Architecture](ARCHITECTURE.md)** | 🚀 **[Getting Started](DEVELOPER_GUIDE.md)** | 📚 **API Reference**

🎯 **[Entity System](ENTITY_SYSTEM.md)** | ⚙️ **[Configuration](CONFIGURATION.md)** | 🖥️ **[Backends](BACKENDS.md)** | 🌐 **[Web Deployment](WEB_DEPLOYMENT.md)**

---


## Core Classes

### AsciiQuarium Class

**Location**: [`asciiquarium_redux/app.py`](../asciiquarium_redux/app.py:44)

The main application controller that manages the aquarium simulation.

#### Constructor

```python
def __init__(self, settings: Settings)
```

**Parameters**:
- `settings`: [`Settings`](#settings-class) instance containing configuration

**Example**:
```python
from asciiquarium_redux.util.settings import Settings
from asciiquarium_redux.app import AsciiQuarium

settings = Settings(fps=30, density=1.5)
app = AsciiQuarium(settings)
```

#### Public Methods

##### [`rebuild(screen)`](../asciiquarium_redux/app.py:69)
Initialize or reset all entities for a specific screen size.

```python
def rebuild(self, screen: Screen) -> None
```

**Parameters**:
- `screen`: [`Screen`](#screen-interface) instance for rendering

**Use Case**: Called when screen size changes or when resetting the simulation.

**Example**:
```python
app.rebuild(screen)  # Respawn all entities
```

##### [`update(dt, screen, frame_no)`](../asciiquarium_redux/app.py:170)
Main game loop iteration - updates all entities and renders the scene.

```python
def update(self, dt: float, screen: Screen, frame_no: int) -> None
```

**Parameters**:
- `dt`: Delta time in seconds since last update
- `screen`: [`Screen`](#screen-interface) instance for rendering
- `frame_no`: Current frame number (for debugging)

**Example**:
```python
import time

last_time = time.time()
frame = 0
while True:
    now = time.time()
    dt = now - last_time
    last_time = now

    app.update(dt, screen, frame)
    frame += 1
```

##### [`spawn_random(screen)`](../asciiquarium_redux/app.py:252)
Spawn a random special entity based on configured weights and cooldowns.

```python
def spawn_random(self, screen: Screen) -> None
```

**Parameters**:
- `screen`: [`Screen`](#screen-interface) instance for positioning

**Example**:
```python
# Manually trigger special entity spawning
app.spawn_random(screen)
```

##### [`adjust_populations(screen)`](../asciiquarium_redux/app.py:443)
Dynamically adjust fish and seaweed counts without full rebuild.

```python
def adjust_populations(self, screen: Screen) -> None
```

**Use Case**: Adapt to screen size changes or setting updates without disrupting existing entities.

#### Public Properties

- `seaweed: List[Seaweed]` - Active seaweed entities
- `fish: List[Fish]` - Active fish entities
- `bubbles: List[Bubble]` - Active bubble entities
- `splats: List[Splat]` - Active splat effects
- `specials: List[Actor]` - Active special entities (sharks, whales, etc.)
- `decor: List[Actor]` - Persistent decoration entities (treasure chest)

#### Drawing Methods

##### [`draw_waterline(screen)`](../asciiquarium_redux/app.py:133)
Render the water surface line.

##### [`draw_castle(screen)`](../asciiquarium_redux/app.py:158)
Render the castle decoration.

### Settings Class

**Location**: [`asciiquarium_redux/util/settings.py`](../asciiquarium_redux/util/settings.py:12)

Configuration dataclass with 65+ settings controlling all aspects of the simulation.

#### Performance Settings

```python
fps: int = 20                    # Target frames per second
density: float = 1.0             # Entity density multiplier
speed: float = 0.75              # Global speed multiplier
```

#### Entity Behavior

```python
# Fish behavior
fish_direction_bias: float = 0.5        # Probability of rightward movement
fish_speed_min: float = 0.6             # Minimum fish speed
fish_speed_max: float = 2.5             # Maximum fish speed
fish_turn_enabled: bool = True          # Enable fish turning behavior
fish_turn_chance_per_second: float = 0.01  # Turning probability

# Seaweed dynamics
seaweed_sway_min: float = 0.18          # Minimum sway speed
seaweed_sway_max: float = 0.5           # Maximum sway speed
seaweed_lifetime_min: float = 25.0      # Minimum lifecycle duration
seaweed_lifetime_max: float = 60.0      # Maximum lifecycle duration
```

#### Spawning Configuration

```python
spawn_start_delay_min: float = 3.0      # Initial spawn delay range
spawn_start_delay_max: float = 8.0
spawn_interval_min: float = 8.0         # Ongoing spawn intervals
spawn_interval_max: float = 20.0
spawn_max_concurrent: int = 1           # Maximum concurrent specials

# Entity weights for random spawning
specials_weights: Dict[str, float] = {
    "shark": 1.0,
    "whale": 1.0,
    "ship": 1.0,
    # ... more entities
}

# Per-entity cooldowns (seconds)
specials_cooldowns: Dict[str, float] = {
    "shark": 10.0,
    "whale": 15.0,
    # ... per-entity settings
}
```

#### UI Configuration
```python
ui_backend: str = "terminal"           # Backend: "terminal", "web", "tk"
ui_cols: int = 120                     # Screen width
ui_rows: int = 40                      # Screen height
color: str = "auto"                    # Color mode: "auto", "mono", "16", "256"
solid_fish: bool = False               # CLI: --solid-fish (opaque fish silhouettes)
start_screen: bool = False             # CLI: --start-screen (centered title/controls overlay)
# Optional post-overlay animation (played after start_screen shrinks away)
start_overlay_after_frames: List[str] = []
start_overlay_after_frame_seconds: float = 0.08
```

#### Example Usage

```python
from asciiquarium_redux.util.settings import Settings

# Create custom settings
settings = Settings(
    fps=60,
    density=2.0,
    fish_speed_max=5.0,
    specials_weights={"shark": 5.0, "whale": 0.1}
)

# Load from TOML file
from asciiquarium_redux.util.settings import load_settings_from_sources
settings = load_settings_from_sources(config_path="my-config.toml")
```

## Entity System

### Actor Protocol

**Location**: [`asciiquarium_redux/entities/base.py`](../asciiquarium_redux/entities/base.py:6)

Base protocol that all entities must implement.

```python
class Actor(Protocol):
    def update(self, dt: float, screen: Screen, app: Any) -> None:
        """Update entity state (physics, AI, lifecycle)."""
        ...

    def draw(self, screen: Screen, mono: bool = False) -> None:
        """Render entity to screen."""
        ...

    @property
    def active(self) -> bool:
        """Whether entity should remain in simulation."""
        ...
```

### Core Entities

#### Fish Class

**Location**: [`asciiquarium_redux/entities/core/fish.py`](../asciiquarium_redux/entities/core/fish.py:32)

Swimming fish with directional movement and bubble generation.

```python
@dataclass
class Fish:
    frames: List[str]           # ASCII art frames
    x: float                    # X position
    y: float                    # Y position
    vx: float                   # X velocity
    colour: int                 # Base color
    z: int = 10                 # Z-depth for layering
    colour_mask: List[str] | None = None  # Color mask for multi-color fish

    # Behavior configuration
    speed_min: float = 0.6
    speed_max: float = 2.5
    bubble_min: float = 2.0     # Bubble generation interval
    bubble_max: float = 5.0

    # Turning behavior
    turn_enabled: bool = True
    turn_chance_per_second: float = 0.01
```

**Methods**:
- `update(dt, screen, app)` - Movement, boundary checking, bubble generation
- `draw(screen)` - Render with color mask support
- `start_turn()` - Initiate turning animation
- `respawn(screen, app)` - Reset position and state

#### Seaweed Class

**Location**: [`asciiquarium_redux/entities/core/seaweed.py`](../asciiquarium_redux/entities/core/seaweed.py)

Swaying seaweed with growth/decay lifecycle.

```python
@dataclass
class Seaweed:
    x: int                      # X position
    base_y: int                 # Base Y position (sea floor)
    height: int                 # Current height
    phase: int                  # Animation phase

    # Lifecycle state
    state: str = "growing"      # "growing", "living", "shrinking", "regrowing"
    age: float = 0.0           # Current age in state

    # Dynamic behavior ranges
    sway_speed: float = 0.3
    lifetime_max: float = 45.0
    regrow_delay_max: float = 8.0
```

#### Bubble Class

**Location**: [`asciiquarium_redux/entities/core/bubble.py`](../asciiquarium_redux/entities/core/bubble.py)

Rising bubbles with waterline collision detection.

```python
@dataclass
class Bubble:
    x: int                      # X position
    y: float                    # Y position (float for smooth movement)
    vy: float = -1.0           # Y velocity (upward)
    age: float = 0.0           # Age for lifetime management
    max_age: float = 30.0      # Maximum lifetime
```

### Special Entities

All special entities are located in [`asciiquarium_redux/entities/specials/`](../asciiquarium_redux/entities/specials/).

#### Shark

Predator entity that causes fish evasion behavior.

```python
class Shark:
    def __init__(self, frames: List[str], x: float, y: float, direction: int)

    # Key properties
    direction: int              # Movement direction (-1 left, 1 right)
    evasion_radius: float = 8.0 # Fish evasion trigger distance
```

#### Whale

Large entity with breach animation sequence.

```python
class Whale:
    def __init__(self, screen: Screen, direction: int = 1)

    # Animation states
    state: str                  # "submerged", "breaching", "surfaced", "diving"
    surface_time: float         # Time spent at surface
```

#### Ship

Surface entity with wake effects.

```python
class Ship:
    def __init__(self, frames: List[str], x: float, y: float, direction: int)

    wake_trail: List[Tuple[int, int]]  # Wake effect positions
```

## Spawn Functions

All spawn functions follow the same signature and are located in [`asciiquarium_redux/entities/specials/`](../asciiquarium_redux/entities/specials/).

### Signature

```python
def spawn_entity_name(screen: Screen, app: AsciiQuarium) -> List[Actor]
```

**Parameters**:
- `screen`: [`Screen`](#screen-interface) for positioning and bounds
- `app`: [`AsciiQuarium`](#asciiquarium-class) instance for settings access

**Returns**: List of spawned actor instances (usually single item)

### Available Spawn Functions

```python
from asciiquarium_redux.entities.specials import (
    spawn_shark,           # Predator fish
    spawn_whale,           # Large breaching whale
    spawn_ship,            # Surface vessel with wake
    spawn_ducks,           # Group of swimming ducks
    spawn_dolphins,        # Pod of jumping dolphins
    spawn_swan,            # Elegant surface swimmer
    spawn_monster,         # Rare dramatic entity
    spawn_big_fish,        # Large decorative fish
    spawn_fishhook,        # Interactive fishing hook
    spawn_treasure_chest,  # Persistent decoration
    spawn_crab,            # Crab on the Sea floor 
)
```

### Example Usage

```python
# Manual spawning
sharks = spawn_shark(screen, app)
app.specials.extend(sharks)

# Weighted random spawning (internal)
def custom_spawn_system(screen, app):
    import random

    choices = [
        (0.3, spawn_shark),
        (0.2, spawn_whale),
        (0.5, spawn_ship),
    ]

    # Weighted selection
    r = random.random()
    cumulative = 0.0
    for weight, spawn_func in choices:
        cumulative += weight
        if r <= cumulative:
            return spawn_func(screen, app)

    return []
```

## Utility Functions

### Sprite Rendering

**Location**: [`asciiquarium_redux/util/__init__.py`](../asciiquarium_redux/util/__init__.py)

#### [`sprite_size(lines)`](../asciiquarium_redux/util/__init__.py:16)
Calculate sprite dimensions.

```python
def sprite_size(lines: List[str]) -> Tuple[int, int]
```

**Returns**: `(width, height)` tuple

#### [`draw_sprite(screen, lines, x, y, colour)`](../asciiquarium_redux/util/__init__.py:22)
Draw ASCII sprite treating spaces as transparent.

```python
def draw_sprite(screen: Screen, lines: List[str], x: int, y: int, colour: int) -> None
```

**Example**:
```python
fish_frames = ["<°)))><", " <°)))><"]
draw_sprite(screen, fish_frames, 10, 5, Screen.COLOUR_CYAN)
```

#### [`draw_sprite_masked(screen, lines, mask, x, y, default_colour)`](../asciiquarium_redux/util/__init__.py:77)
Draw sprite with per-character color mask.

```python
def draw_sprite_masked(
    screen: Screen,
    lines: List[str],
    mask: List[str],
    x: int,
    y: int,
    default_colour: int
) -> None
```

**Color Mask Characters**:
- `r/R`: Red
- `g/G`: Green
- `b/B`: Blue
- `c/C`: Cyan
- `m/M`: Magenta
- `y/Y`: Yellow
- `w/W`: White
- `k/K`: Black
- ` ` (space): Use default color

**Example**:
```python
sprite = ["<°)))><"]
mask   = ["rwwwwwr"]  # Red ends, white middle
draw_sprite_masked(screen, sprite, mask, x, y, Screen.COLOUR_CYAN)
```

#### [`randomize_colour_mask(mask)`](../asciiquarium_redux/util/__init__.py:208)
Replace digit placeholders with random colors.

```python
def randomize_colour_mask(mask: List[str]) -> List[str]
```

**Placeholder System**:
- `1-3`, `5-9`: Random color selection
- `4`: Always white (eyes)

**Example**:
```python
template = ["<1)))2>"]  # 1 and 2 will be random colors
colored_mask = randomize_colour_mask(template)
# Result: ["<r)))g>"] (random example)
```

### Collision Detection

#### [`aabb_overlap(ax, ay, aw, ah, bx, by, bw, bh)`](../asciiquarium_redux/util/__init__.py:238)
Axis-aligned bounding box overlap test.

```python
def aabb_overlap(ax: int, ay: int, aw: int, ah: int,
                 bx: int, by: int, bw: int, bh: int) -> bool
```

**Parameters**: Two rectangles defined by (x, y, width, height)

**Returns**: `True` if rectangles overlap

**Example**:
```python
# Check if fish collides with shark
fish_w, fish_h = sprite_size(fish.frames)
shark_w, shark_h = sprite_size(shark.frames)

if aabb_overlap(fish.x, fish.y, fish_w, fish_h,
                shark.x, shark.y, shark_w, shark_h):
    # Collision detected
    trigger_fish_evasion(fish, shark)
```

## Screen Interface

**Location**: [`asciiquarium_redux/screen_compat.py`](../asciiquarium_redux/screen_compat.py)

Abstract interface for platform-specific rendering backends.

### Core Methods

```python
class Screen(Protocol):
    width: int                  # Screen width in characters
    height: int                 # Screen height in characters

    def print_at(self, text: str, x: int, y: int, colour: int) -> None:
        """Print text at specific screen coordinates."""
        ...

    def get_event(self) -> Event | None:
        """Get next input event (keyboard/mouse)."""
        ...
```

### Color Constants

```python
# Standard color constants (platform-agnostic)
Screen.COLOUR_BLACK = 0
Screen.COLOUR_RED = 1
Screen.COLOUR_GREEN = 2
Screen.COLOUR_YELLOW = 3
Screen.COLOUR_BLUE = 4
Screen.COLOUR_MAGENTA = 5
Screen.COLOUR_CYAN = 6
Screen.COLOUR_WHITE = 7
```

### Example Usage

```python
# Basic text rendering
screen.print_at("Hello", 10, 5, Screen.COLOUR_CYAN)

# Check screen bounds
if 0 <= x < screen.width and 0 <= y < screen.height:
    screen.print_at("Safe", x, y, Screen.COLOUR_WHITE)

# Handle input
event = screen.get_event()
if event and hasattr(event, 'key_code'):
    if event.key_code == ord('q'):
        quit_application()
```

## Configuration Management

### Loading Settings

```python
from asciiquarium_redux.util.settings import load_settings_from_sources
from pathlib import Path

# Load with default search paths
settings = load_settings_from_sources()

# Load specific config file
settings = load_settings_from_sources(config_path=Path("custom.toml"))

# Load with command-line overrides
import argparse
parser = argparse.ArgumentParser()
# ... add arguments
args = parser.parse_args()
settings = load_settings_from_sources(args=args)
```

### TOML Configuration Format

```toml
# Basic settings
fps = 30
density = 1.5
speed = 1.0
color = "auto"

# Entity behavior
[fish]
direction_bias = 0.7
speed_min = 0.8
speed_max = 3.0
turn_enabled = true

[seaweed]
sway_min = 0.2
sway_max = 0.8
lifetime_min = 30.0
lifetime_max = 90.0

# Spawning configuration
[spawn]
start_delay_min = 2.0
start_delay_max = 5.0
interval_min = 5.0
interval_max = 15.0
max_concurrent = 2

[spawn.weights]
shark = 2.0
whale = 1.0
ship = 0.5

[spawn.cooldowns]
shark = 15.0
whale = 30.0

# UI settings
[ui]
backend = "terminal"
cols = 120
rows = 40
```

## Backend Development

### Implementing New Backends

To create a new rendering backend:

1. **Implement Screen Protocol**:
```python
class MyBackendScreen:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    def print_at(self, text: str, x: int, y: int, colour: int) -> None:
        # Platform-specific character rendering
        pass

    def get_event(self) -> Event | None:
        # Platform-specific input handling
        return None
```

2. **Create Runner Function**:
```python
def run_my_backend(settings: Settings) -> None:
    screen = MyBackendScreen(settings.ui_cols, settings.ui_rows)
    app = AsciiQuarium(settings)
    app.rebuild(screen)

    # Main game loop
    while True:
        # Update and render
        app.update(dt, screen, frame_no)

        # Handle input
        event = screen.get_event()
        if should_quit(event):
            break
```

3. **Register Backend**:
```python
# In runner.py
backend_map = {
    "my_backend": run_my_backend,
    # ... existing backends
}
```

## Event Handling

### Input Events

Different backends provide different event types:

**Terminal Backend** (Asciimatics):
```python
from asciimatics.event import KeyboardEvent, MouseEvent

if isinstance(event, KeyboardEvent):
    key = event.key_code
    if key == ord('q'):
        quit()
    elif key == ord('p'):
        toggle_pause()

elif isinstance(event, MouseEvent):
    if event.buttons & MouseEvent.LEFT_CLICK:
        spawn_fishhook_to(event.x, event.y)
```

**Web Backend**:
```python
# Events come as JSON messages via WebSocket
{
    "type": "keydown",
    "key": "q"
}
{
    "type": "click",
    "x": 45,
    "y": 12
}
```

## Error Handling

### Common Patterns

**Entity Error Isolation**:
```python
# In AsciiQuarium.update()
for entity in entities:
    try:
        entity.update(dt, screen, self)
    except Exception as e:
        logging.warning(f"Entity update failed: {e}")
        entity.active = False  # Remove problematic entity
```

**Configuration Validation**:
```python
# In settings loading
def validate_settings(settings: Settings) -> Settings:
    if settings.fps <= 0:
        settings.fps = 20
    if settings.density <= 0:
        settings.density = 1.0
    return settings
```

**Spawn Function Safety**:
```python
def safe_spawn(spawn_func, screen, app):
    try:
        return spawn_func(screen, app)
    except Exception as e:
        logging.error(f"Spawn failed: {e}")
        return []  # Return empty list on failure
```

## Cross-References

- **Architecture Overview**: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- **Development Setup**: [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md)
- **Entity Details**: [`ENTITY_SYSTEM.md`](ENTITY_SYSTEM.md)
- **Configuration Guide**: [`CONFIGURATION.md`](CONFIGURATION.md)
- **Backend Specifics**: [`BACKENDS.md`](BACKENDS.md)
- **Web Deployment**: [`WEB_DEPLOYMENT.md`](WEB_DEPLOYMENT.md)
