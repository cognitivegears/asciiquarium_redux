# Asciiquarium Redux - Architecture Documentation
## Documentation Navigation

📋 **[Overview](../README.md)** | 🏗️ **Architecture** | 🚀 **[Getting Started](DEVELOPER_GUIDE.md)** | 📚 **[API Reference](API_REFERENCE.md)**

🎯 **[Entity System](ENTITY_SYSTEM.md)** | ⚙️ **[Configuration](CONFIGURATION.md)** | 🖥️ **[Backends](BACKENDS.md)** | 🌐 **[Web Deployment](WEB_DEPLOYMENT.md)**

---


## Overview

Asciiquarium Redux is a multi-platform ASCII art aquarium simulation built with Python. The architecture follows a modular design with clear separation between rendering backends, entity management, and configuration systems.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  AsciiQuarium (Main Controller)                             │
│  - Entity lifecycle management                              │
│  - Game loop and update logic                               │
│  - Rendering coordination                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Entity System                            │
├─────────────────────────────────────────────────────────────┤
│  Core Entities:        Special Entities:                    │
│  • Fish (swimming)     • Shark (predator)                   │
│  • Seaweed (static)    • Whale (large)                      │
│  • Bubble (floating)   • Ship (surface)                     │
│  • Splat (effects)     • Dolphins (group)                   │
│                        • Monster (rare)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend Abstraction                        │
├─────────────────────────────────────────────────────────────┤
│  Screen Interface (Rendering Contract)                      │
│  - Color management                                         │
│  - Character positioning                                    │
│  - Input event handling                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Platform Backends                          │
├─────────────────────────────────────────────────────────────┤
│  Terminal Backend     Web Backend      TkInter Backend      │
│  - Asciimatics        - WebSocket      - Tkinter Canvas     │
│  - Native terminal    - Browser        - Desktop GUI        │
│  - Full color         - Full color     - Limited color      │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. AsciiQuarium Class (Main Controller)

**Location**: [`asciiquarium_redux/app.py`](../asciiquarium_redux/app.py)

The [`AsciiQuarium`](../asciiquarium_redux/app.py:44) class is the central orchestrator that manages:

- **Entity Collections**: Fish, seaweed, bubbles, splats, and special entities
- **Game Loop**: [`update()`](../asciiquarium_redux/app.py:170) method coordinates all entity updates
- **Rendering Pipeline**: Manages layered drawing (seaweed → decor → fish → castle → bubbles → specials → splats)
- **Spawn Management**: Random spawning of special entities with cooldowns and weights
- **Population Control**: Dynamic adjustment of fish and seaweed counts based on screen size

**Key Methods**:
- [`rebuild(screen)`](../asciiquarium_redux/app.py:69): Initialize/reset all entities for screen size
- [`update(dt, screen, frame_no)`](../asciiquarium_redux/app.py:170): Main game loop iteration
- [`spawn_random(screen)`](../asciiquarium_redux/app.py:252): Weighted random special entity spawning
- [`adjust_populations(screen)`](../asciiquarium_redux/app.py:443): Live population management without rebuild

### 2. Settings System

**Location**: [`asciiquarium_redux/util/settings.py`](../asciiquarium_redux/util/settings.py)

The [`Settings`](../asciiquarium_redux/util/settings.py:12) dataclass provides comprehensive configuration:

- **Performance**: FPS, density scaling, speed multipliers
- **Entity Behavior**: Fish movement, turning, bubble generation
- **Spawning Control**: Weights, cooldowns, concurrent limits
- **Visual Appearance**: Colors, scaling factors, enabled features
- **Backend Selection**: Terminal, web, or TkInter interface

**Configuration Sources** (in priority order):
1. Command-line arguments
2. `~/.asciiquarium.toml`
3. `$XDG_CONFIG_HOME/asciiquarium-redux/config.toml`
4. `~/.config/asciiquarium-redux/config.toml`

### 3. Entity System

**Base Interface**: [`asciiquarium_redux/entities/base.py`](../asciiquarium_redux/entities/base.py)

All entities implement the [`Actor`](../asciiquarium_redux/entities/base.py:6) protocol:
- [`update(dt, screen, app)`](../asciiquarium_redux/entities/base.py:7): Physics and behavior updates
- [`draw(screen, mono=False)`](../asciiquarium_redux/entities/base.py:8): Rendering logic
- [`active`](../asciiquarium_redux/entities/base.py:10) property: Lifecycle management

**Entity Categories**:

**Core Entities** (`entities/core/`):
- **Fish**: Swimming with directional movement, turning behavior, bubble generation
- **Seaweed**: Swaying animation with lifecycle (grow → live → shrink → regrow)
- **Bubble**: Rising with collision detection against waterline
- **Splat**: Short-lived visual effects

**Special Entities** (`entities/specials/`):
- **Shark**: Predator that causes fish evasion behavior
- **Whale**: Large entity with breach animation
- **Ship**: Surface entity with wake effects
- **Dolphins**: Group behavior with synchronized movement
- **Monster**: Rare dramatic entity with special effects

### 4. Backend Architecture

**Strategy Pattern Implementation**: Each backend provides platform-specific rendering while maintaining a consistent [`Screen`](../asciiquarium_redux/screen_compat.py) interface.

**Terminal Backend** (`backend/term/`):
- Uses Asciimatics library for terminal control
- Full color support with RGB palette
- Keyboard and mouse input handling
- Cross-platform terminal compatibility

**Web Backend** (`backend/web/`):
- WebSocket-based real-time communication
- HTML5 Canvas rendering with JavaScript
- Browser-based interface with responsive design
- Mobile-friendly touch controls

**TkInter Backend** (`backend/tk/`):
- Native desktop GUI using Python's built-in Tkinter
- Canvas-based rendering with limited color support
- Desktop application experience

## Design Patterns

### 1. Strategy Pattern
Backend selection allows runtime switching between terminal, web, and GUI rendering without changing core logic.

### 2. Template Method Pattern
All entities follow the same [`update()`](../asciiquarium_redux/entities/base.py:7) → [`draw()`](../asciiquarium_redux/entities/base.py:8) lifecycle with entity-specific implementations.

### 3. Factory Pattern
Entity spawn functions create configured instances with appropriate settings and initial states.

### 4. Observer Pattern (Implicit)
Entities react to app state changes (e.g., fish evasion when shark is present) through direct app reference.

## Data Flow

```
Configuration Loading → Settings Validation → Backend Selection
                                    ↓
                    AsciiQuarium Initialization
                                    ↓
                        Entity Population
                                    ↓
        ┌─────────────────────────────────────────────────┐
        │                Game Loop                        │
        ├─────────────────────────────────────────────────┤
        │  1. Input Processing (events, keys)             │
        │  2. Entity Updates (physics, AI, lifecycle)     │
        │  3. Collision Detection (bubbles, hooks)        │
        │  4. Spawn Management (special entities)         │
        │  5. Rendering Pipeline (layered drawing)        │
        │  6. Screen Buffer Swap                          │
        └─────────────────────────────────────────────────┘
                                    ↓
                            Platform-Specific Output
```

## Performance Considerations

### Entity Management
- **Lazy Cleanup**: Inactive entities are filtered out rather than immediately removed
- **Population Scaling**: Entity counts scale with screen size using configurable formulas
- **Z-Order Optimization**: Fish are depth-sorted only when necessary for layered rendering

### Rendering Optimization
- **Double Buffering**: Reduces screen flicker using [`DoubleBufferedScreen`](../asciiquarium_redux/util/buffer.py)
- **Dirty Region Tracking**: Only redraw changed screen areas (backend-dependent)
- **Color Mode Support**: Monochrome mode for better performance on limited terminals

### Memory Management
- **Entity Pooling**: Reuse bubble and splat objects to reduce allocation overhead
- **Bounded Collections**: Maximum concurrent special entities prevent memory growth
- **Lifecycle Management**: Automatic cleanup of expired entities

## Extension Points

### Adding New Entities
1. Implement [`Actor`](../asciiquarium_redux/entities/base.py:6) protocol
2. Add spawn function to [`entities/specials/`](../asciiquarium_redux/entities/specials/)
3. Register in [`spawn_random()`](../asciiquarium_redux/app.py:252) weighted selection
4. Add configuration options to [`Settings`](../asciiquarium_redux/util/settings.py:12)

### Adding New Backends
1. Implement [`Screen`](../asciiquarium_redux/screen_compat.py) interface
2. Create backend module in [`backend/`](../asciiquarium_redux/backend/)
3. Add backend selection logic to runner
4. Handle platform-specific input events

### Configuration Extensions
1. Add fields to [`Settings`](../asciiquarium_redux/util/settings.py:12) dataclass
2. Update TOML parsing in [`load_settings_from_sources()`](../asciiquarium_redux/util/settings.py)
3. Add command-line argument handling
4. Document in [`CONFIGURATION.md`](CONFIGURATION.md)

## Dependencies

**Core Dependencies**:
- `asciimatics`: Terminal rendering and input handling
- `tomllib`: TOML configuration file parsing (Python 3.11+)

**Web Backend Dependencies**:
- `websockets`: Real-time browser communication
- `uvloop`: High-performance asyncio event loop (optional)

**Development Dependencies**:
- `pytest`: Unit testing framework
- `mypy`: Static type checking
- `black`: Code formatting

## Cross-References

- **Entity Details**: See [`ENTITY_SYSTEM.md`](ENTITY_SYSTEM.md)
- **Configuration Guide**: See [`CONFIGURATION.md`](CONFIGURATION.md)
- **Backend Specifics**: See [`BACKENDS.md`](BACKENDS.md)
- **API Reference**: See [`API_REFERENCE.md`](API_REFERENCE.md)
- **Development Setup**: See [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md)
