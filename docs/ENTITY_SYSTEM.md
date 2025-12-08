# Asciiquarium Redux - Entity System
## Documentation Navigation

📋 **[Overview](../README.md)** | 🏗️ **[Architecture](ARCHITECTURE.md)** | 🚀 **[Getting Started](DEVELOPER_GUIDE.md)** | 📚 **[API Reference](API_REFERENCE.md)**

🎯 **Entity System** | ⚙️ **[Configuration](CONFIGURATION.md)** | 🖥️ **[Backends](BACKENDS.md)** | 🌐 **[Web Deployment](WEB_DEPLOYMENT.md)**

---


## Overview

The Asciiquarium Redux entity system provides a flexible framework for managing all dynamic elements in the aquarium simulation. The system is built around a simple [`Actor`](../asciiquarium_redux/entities/base.py:6) protocol that all entities implement, enabling consistent lifecycle management and rendering.

## Entity Architecture

### Actor Protocol

**Location**: [`asciiquarium_redux/entities/base.py`](../asciiquarium_redux/entities/base.py:6)

All entities must implement the [`Actor`](../asciiquarium_redux/entities/base.py:6) protocol:

```python
class Actor(Protocol):
    def update(self, dt: float, screen: Screen, app: Any) -> None:
        """Update entity state - physics, AI, lifecycle logic."""
        ...

    def draw(self, screen: Screen, mono: bool = False) -> None:
        """Render entity to screen buffer."""
        ...

    @property
    def active(self) -> bool:
        """Whether entity should remain in simulation."""
        ...
```

### Entity Categories

The system organizes entities into two main categories:

**Core Entities** (`entities/core/`):
- **Persistent**: Always present in the aquarium (fish, seaweed)
- **Ephemeral**: Short-lived effects (bubbles, splats)
- **Environmental**: Background elements (waterline, castle)

**Special Entities** (`entities/specials/`):
- **Interactive**: Player-triggered elements (fishhook)
- **Dramatic**: Rare spectacular events (whale, monster)
- **Atmospheric**: Mood-setting elements (ship, ducks, crab, scuba diver)
- **Decorative**: Persistent scenery (treasure chest)

## Entity Lifecycle

### Standard Lifecycle Flow

```
Entity Creation (Spawn) → Active State → Update Loop → Draw → Cleanup
                                      ↑         ↓
                                      └─────────┘
                                    (Continues while active=True)
```

### Update-Draw Pattern

The main game loop follows a consistent pattern:

1. **Input Processing**: Handle user events
2. **Entity Updates**: Call `update(dt, screen, app)` on all entities
3. **Collision Detection**: Check entity interactions
4. **Cleanup**: Remove inactive entities
5. **Rendering**: Call `draw(screen, mono)` in layered order
6. **Buffer Swap**: Display completed frame

### Active State Management

Entities control their own lifecycle through the `active` property:

```python
# Simple lifetime-based cleanup
class TimedEntity:
    def __init__(self, max_age: float = 10.0):
        self.age = 0.0
        self.max_age = max_age

    @property
    def active(self) -> bool:
        return self.age < self.max_age

    def update(self, dt: float, screen: Screen, app: Any) -> None:
        self.age += dt
        # Entity automatically removed when active becomes False
```

## Core Entities

### Fish Entity

**Location**: [`asciiquarium_redux/entities/core/fish.py`](../asciiquarium_redux/entities/core/fish.py:32)

Swimming entities with complex behavior patterns.

#### Behavior Systems

**Movement Pattern**:
```python
# Horizontal movement with screen wrapping
def update(self, dt: float, screen: Screen, app: Any) -> None:
    self.x += self.vx * dt

    # Screen boundary handling
    if self.x > screen.width:
        self.respawn(screen, app)  # Wrap to opposite side
    elif self.x + sprite_width < 0:
        self.respawn(screen, app)
```

**Turning Behavior**:
- Probabilistic turning based on `turn_chance_per_second`
- Shrink → pause → expand animation sequence
- Directional frame swapping (left ↔ right sprites)
- Cooldown period between turns

**Bubble Generation**:
```python
# Periodic bubble spawning
self.next_bubble -= dt
if self.next_bubble <= 0:
    app.bubbles.append(Bubble(x=self.x, y=self.y))
    self.next_bubble = random.uniform(self.bubble_min, self.bubble_max)
```

**Evasion Response** (when shark is present):
```python
# Fish flee from nearby sharks
for shark in app.specials:
    if isinstance(shark, Shark):
        distance = abs(self.x - shark.x) + abs(self.y - shark.y)
        if distance < shark.evasion_radius:
            self.vx = -self.vx  # Reverse direction
            break
```

#### Configuration Integration

Fish behavior adapts to [`Settings`](../asciiquarium_redux/util/settings.py:12):

```python
# Speed and movement
speed_min: float = settings.fish_speed_min
speed_max: float = settings.fish_speed_max
direction_bias: float = settings.fish_direction_bias

# Turning behavior
turn_enabled: bool = settings.fish_turn_enabled
turn_chance_per_second: float = settings.fish_turn_chance_per_second

# Bubble generation
bubble_min: float = settings.fish_bubble_min
bubble_max: float = settings.fish_bubble_max
```

### Seaweed Entity

**Location**: [`asciiquarium_redux/entities/core/seaweed.py`](../asciiquarium_redux/entities/core/seaweed.py:27)

Stationary entities with complex lifecycle state machines.

#### Lifecycle States

**State Machine**:
```
growing → alive → dying → dormant → growing (cycle repeats)
   ↑                                     ↓
   └─────────────────────────────────────┘
```

**State Behaviors**:

1. **Growing State**:
   ```python
   # Gradual height increase from 0 to full height
   self.visible_height = min(self.height,
                           self.visible_height + self.growth_rate * dt)
   if self.visible_height >= self.height:
       self.state = "alive"
   ```

2. **Alive State**:
   ```python
   # Normal swaying animation with aging
   self.lifetime_t += dt
   if self.lifetime_t >= self.lifetime_max:
       self.state = "dying"
   ```

3. **Dying State**:
   ```python
   # Gradual shrinking to zero height
   self.visible_height = max(0.0,
                           self.visible_height - self.shrink_rate * dt)
   if self.visible_height <= 0.0:
       self.state = "dormant"
   ```

4. **Dormant State**:
   ```python
   # Waiting period before regrowth
   self.regrow_delay_t += dt
   if self.regrow_delay_t >= self.regrow_delay_max:
       self.state = "growing"
       # Randomize new growth parameters
   ```

#### Animation System

**Swaying Animation**:
```python
# Per-entity sway timing
self.sway_t += dt
step = int(self.sway_t / self.sway_speed)
sway_frame = (step + self.phase) % 2

# Two-frame animation: ( → )
frames = [
    ["(", " ", "(", " "],  # Frame 0
    [" ", ")", " ", ")"]   # Frame 1
]
```

**Height-Based Rendering**:
```python
# Draw from bottom up to current visible height
visible_rows = int(self.visible_height)
for i in range(max_height - visible_rows, max_height):
    y = self.base_y - (max_height - 1 - i)
    screen.print_at(frame_data[i], self.x, y, colour=GREEN)
```

### Bubble Entity

**Location**: [`asciiquarium_redux/entities/core/bubble.py`](../asciiquarium_redux/entities/core/bubble.py:13)

Simple rising particles with collision detection.

#### Behavior Pattern

**Upward Movement**:
```python
def update(self, dt: float, screen: Screen, app: Any) -> None:
    self.lifetime += dt
    self.y -= max(1, int(10 * dt))  # Rise at ~10 pixels/second
```

**Waterline Collision**:
```python
# In AsciiQuarium.update()
if app._bubble_hits_waterline(bubble.x, bubble.y, screen):
    bubble.active = False  # Remove bubble on surface hit
```

**Lifetime Management**:
```python
@property
def active(self) -> bool:
    return self.lifetime < MAX_BUBBLE_LIFETIME  # Prevent memory leaks
```

**Rendering Variety**:
```python
def draw(self, screen: Screen) -> None:
    # Random bubble character for visual variety
    ch = random.choice([".", "o", "O"])
    screen.print_at(ch, self.x, self.y, colour=Screen.COLOUR_CYAN)
```

## Special Entities

### Shark Entity

**Location**: [`asciiquarium_redux/entities/specials/shark.py`](../asciiquarium_redux/entities/specials/shark.py:19)

Predator entity that influences fish behavior.

#### Predator Mechanics

**Directional Movement**:
```python
def __init__(self, screen: Screen, app):
    self.dir = random.choice([-1, 1])  # Random direction
    self.speed = SHARK_SPEED * self.dir
    self.y = random.randint(9, screen.height - 10)  # Mid-water spawn
```

**Fish Evasion Trigger**:
```python
# Fish check shark proximity and flee
evasion_radius: float = 8.0  # Distance threshold
for fish in app.fish:
    distance = abs(fish.x - shark.x) + abs(fish.y - shark.y)
    if distance < evasion_radius:
        fish.start_evasion(shark)
```

**Sprite System**:
```python
# Direction-specific artwork
if self.dir > 0:  # Moving right
    self.current_sprite = self.img_right
    self.current_mask = self.mask_right
else:  # Moving left
    self.current_sprite = self.img_left
    self.current_mask = self.mask_left
```

### Whale Entity

Large entity with breach animation sequence.

#### Animation States

**Breach Sequence**:
```
submerged → rising → breaching → surfaced → diving → submerged
```

**State Transitions**:
```python
if self.state == "submerged":
    # Move horizontally underwater
    if should_breach():
        self.state = "rising"
        self.breach_y = self.y

elif self.state == "rising":
    self.y -= BREACH_SPEED * dt
    if self.y <= SURFACE_LEVEL:
        self.state = "surfaced"
        self.surface_timer = SURFACE_DURATION

elif self.state == "surfaced":
    self.surface_timer -= dt
    # Splash effects, water displacement
    if self.surface_timer <= 0:
        self.state = "diving"
```

### Interactive Entities

#### FishHook Entity

Player-controlled entity for interactive gameplay.

**Mouse Integration**:
```python
# In main event loop
if isinstance(event, MouseEvent) and event.buttons & LEFT_CLICK:
    hook = spawn_fishhook_to(event.x, event.y)
    app.specials.extend(hook)
```

**Fish Interaction**:
```python
# Hook attracts nearby fish
for fish in app.fish:
    if collision_detected(fish, hook):
        fish.hooked = True
        fish.hook_target = (hook.x, hook.y)
```

## Spawn System

### Spawn Functions

All spawn functions follow a consistent signature:

```python
def spawn_entity_name(screen: Screen, app: AsciiQuarium) -> List[Actor]
```

### Weighted Random Selection

**Configuration-Driven Spawning**:
```python
# In AsciiQuarium.spawn_random()
choices = [
    ("shark", spawn_shark),
    ("whale", spawn_whale),
    ("ship", spawn_ship),
    # ... more entities
]

weighted_choices = []
for name, spawn_func in choices:
    weight = app.settings.specials_weights.get(name, 1.0)
    cooldown = app.settings.specials_cooldowns.get(name, 0.0)

    if weight > 0 and time_since_last_spawn(name) >= cooldown:
        weighted_choices.append((weight, name, spawn_func))
```

**Selection Algorithm**:
```python
# Weighted random selection
total_weight = sum(weight for weight, _, _ in weighted_choices)
r = random.uniform(0.0, total_weight)

cumulative = 0.0
for weight, name, spawn_func in weighted_choices:
    cumulative += weight
    if r <= cumulative:
        entities = spawn_func(screen, app)
        app.specials.extend(entities)
        break
```

### Population Management

#### Dynamic Scaling

**Screen Size Adaptation**:
```python
def compute_fish_count(screen: Screen, settings: Settings) -> int:
    if settings.fish_count_base is not None:
        # Explicit formula-based scaling
        units = screen.width / SCREEN_WIDTH_UNIT_DIVISOR
        base = settings.fish_count_base
        per_unit = settings.fish_count_per_80_cols
        return int((base + per_unit * units) * settings.density)
    else:
        # Area-based scaling (fallback)
        area = screen.width * (screen.height - waterline_offset)
        return int(area / FISH_DENSITY_DIVISOR * settings.density)
```

**Live Population Adjustment**:
```python
def adjust_populations(self, screen: Screen) -> None:
    """Adapt entity counts without full rebuild."""
    target_fish, target_seaweed = self._compute_target_counts(screen)

    # Add entities if below target
    current_fish = len(self.fish)
    if target_fish > current_fish:
        for _ in range(target_fish - current_fish):
            self.fish.append(self._make_one_fish(screen))

    # Remove excess entities
    elif target_fish < current_fish:
        del self.fish[target_fish:]
```

## Performance Considerations

### Memory Management

**Entity Cleanup**:
```python
# Automatic cleanup of inactive entities
self.bubbles = [b for b in self.bubbles if b.active]
self.splats = [s for s in self.splats if s.active]
self.specials = [e for e in self.specials if getattr(e, 'active', True)]
```

**Object Pooling** (future enhancement):
```python
# Reuse bubble instances to reduce allocation overhead
class BubblePool:
    def __init__(self, initial_size: int = 50):
        self.available = [Bubble(0, 0) for _ in range(initial_size)]
        self.active = []

    def spawn(self, x: int, y: int) -> Bubble:
        if self.available:
            bubble = self.available.pop()
            bubble.reset(x, y)
        else:
            bubble = Bubble(x, y)
        self.active.append(bubble)
        return bubble
```

### Rendering Optimization

**Z-Order Rendering**:
```python
# Draw entities back-to-front for proper layering
fish_sorted = sorted(self.fish, key=lambda f: f.z)
for fish in fish_sorted:
    fish.draw(screen, mono)
```

**Culling Optimizations**:
```python
# Skip rendering for off-screen entities
def draw(self, screen: Screen, mono: bool = False) -> None:
    if not (0 <= self.x < screen.width and 0 <= self.y < screen.height):
        return  # Skip off-screen entities

    # Normal rendering...
```

## Entity Development

### Creating New Entities

**1. Implement Actor Protocol**:
```python
class MyCustomEntity:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.active = True
        self.age = 0.0

    def update(self, dt: float, screen: Screen, app: Any) -> None:
        self.age += dt
        # Custom behavior logic

    def draw(self, screen: Screen, mono: bool = False) -> None:
        # Custom rendering logic

    @property
    def active(self) -> bool:
        return self.age < MAX_LIFETIME
```

**2. Create Spawn Function**:
```python
def spawn_my_entity(screen: Screen, app: AsciiQuarium) -> List[MyCustomEntity]:
    """Spawn MyCustomEntity with appropriate positioning."""
    x = random.uniform(0, screen.width)
    y = random.uniform(app.settings.waterline_top, screen.height - 2)
    entity = MyCustomEntity(x, y)
    return [entity]
```

**3. Register in Spawn System**:
```python
# In AsciiQuarium.spawn_random()
choices = [
    # ... existing entities
    ("my_entity", spawn_my_entity),
]
```

**4. Add Configuration**:
```python
# In Settings dataclass
my_entity_spawn_weight: float = 1.0
my_entity_cooldown: float = 10.0

# In specials_weights default factory
"my_entity": 1.0,
```

### Best Practices

**State Management**:
- Use clear state enums or constants
- Implement state transition validation
- Add debug logging for state changes

**Error Handling**:
```python
def update(self, dt: float, screen: Screen, app: Any) -> None:
    try:
        # Entity logic here
        pass
    except Exception as e:
        # Log error and deactivate problematic entity
        logging.warning(f"Entity update failed: {e}")
        self.active = False
```

**Configuration Integration**:
```python
# Accept configuration in constructor
class ConfigurableEntity:
    def __init__(self, x: float, y: float, settings: Settings):
        self.x = x
        self.y = y
        self.speed = settings.my_entity_speed
        self.lifetime = settings.my_entity_lifetime
```

## Debugging and Testing

### Entity State Inspection

**Debug Overlays**:
```python
# Optional debug rendering
def draw_debug_info(self, screen: Screen) -> None:
    if DEBUG_MODE:
        info = f"State: {self.state}, Age: {self.age:.1f}"
        screen.print_at(info, self.x, self.y - 1, Screen.COLOUR_WHITE)
```

**State Logging**:
```python
def change_state(self, new_state: str) -> None:
    if DEBUG_ENTITIES:
        logger.debug(f"{self.__class__.__name__} {id(self)}: {self.state} → {new_state}")
    self.state = new_state
```

### Testing Strategies

**Entity Lifecycle Testing**:
```python
def test_seaweed_lifecycle():
    seaweed = Seaweed(x=10, base_y=20, height=5, phase=0)

    # Test growing state
    seaweed.state = "growing"
    seaweed.visible_height = 0.0
    seaweed.update(1.0, mock_screen, mock_app)
    assert seaweed.visible_height > 0.0

    # Test state transitions
    seaweed.lifetime_t = seaweed.lifetime_max + 1.0
    seaweed.update(0.1, mock_screen, mock_app)
    assert seaweed.state == "dying"
```

**Spawn Function Testing**:
```python
def test_spawn_shark():
    entities = spawn_shark(mock_screen, mock_app)
    assert len(entities) == 1
    assert isinstance(entities[0], Shark)
    assert entities[0].active
```

## Cross-References

- **Main Controller**: [`ARCHITECTURE.md`](ARCHITECTURE.md) - System integration
- **Configuration**: [`CONFIGURATION.md`](CONFIGURATION.md) - Entity behavior settings
- **API Details**: [`API_REFERENCE.md`](API_REFERENCE.md) - Technical interfaces
- **Development**: [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) - Implementation guidance
- **Backend Integration**: [`BACKENDS.md`](BACKENDS.md) - Platform-specific rendering
