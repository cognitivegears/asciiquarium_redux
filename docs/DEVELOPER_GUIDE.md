# Asciiquarium Redux - Developer Guide
## Documentation Navigation

📋 **[Overview](../README.md)** | 🏗️ **[Architecture](ARCHITECTURE.md)** | 🚀 **Getting Started** | 📚 **[API Reference](API_REFERENCE.md)**

🎯 **[Entity System](ENTITY_SYSTEM.md)** | ⚙️ **[Configuration](CONFIGURATION.md)** | 🖥️ **[Backends](BACKENDS.md)** | 🌐 **[Web Deployment](WEB_DEPLOYMENT.md)**

---


## Quick Start

### Prerequisites

- **Python 3.11+** (required for `tomllib` support)
- **Terminal with ANSI color support** (for best experience)
- **Git** (for version control)

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/cognitivegears/asciiquarium_redux.git
   cd asciiquarium_redux
   ```

2. **Install with uv (Recommended)**:
   ```bash
   # Install uv if you don't have it
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install project with dependencies
   uv sync
   ```

3. **Alternative: pip/venv setup**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

4. **Verify installation**:
   ```bash
   uv run asciiquarium --help
   # or with pip: asciiquarium --help
   ```

### Running the Application

**Basic usage**:
```bash
# Default terminal mode
uv run asciiquarium

# With configuration
uv run asciiquarium --config sample-config.toml

# Web mode (browser interface)
uv run asciiquarium --backend web --open

# Quick testing mode
uv run asciiquarium --fps 30 --density 2.0 --speed 1.5
```

**Development shortcuts**:
```bash
# Run from source without installation
uv run python -m asciiquarium_redux

# Debug mode with verbose output
uv run python -m asciiquarium_redux --verbose
```

## Project Structure

```
asciiquarium_redux/
├── __init__.py              # Package initialization
├── __main__.py              # Entry point (python -m asciiquarium_redux)
├── app.py                   # AsciiQuarium main controller
├── constants.py             # Extracted magic numbers and constants
├── runner.py                # CLI runner and backend selection
├── screen_compat.py         # Screen interface abstraction
├── web_server.py            # Standalone web server
├── backend/                 # Platform-specific rendering
│   ├── term/                # Terminal backend (Asciimatics)
│   ├── web/                 # Web backend (WebSocket)
│   └── tk/                  # TkInter backend (GUI)
├── entities/                # Entity system
│   ├── base.py              # Actor protocol
│   ├── core/                # Core entities (Fish, Seaweed, Bubble)
│   ├── specials/            # Special entities (Shark, Whale, etc.)
│   └── environment.py       # Environmental assets (castle, waterline)
├── util/                    # Utility modules
│   ├── buffer.py            # Double-buffered screen wrapper
│   ├── settings.py          # Configuration management
│   └── types.py             # Type definitions
└── web/                     # Web frontend assets
    ├── index.html           # HTML interface
    ├── app.js               # JavaScript client
    └── styles.css           # CSS styling
```

## Development Workflow

### Code Style and Standards

The project follows **PEP 8** with these conventions:

**Imports**:
```python
from __future__ import annotations  # Always first

import standard_library
import third_party
from .relative import local_module
```

**Type Hints**:
```python
# Use modern typing syntax (Python 3.11+)
def process_entities(entities: list[Entity]) -> dict[str, Any]:
    ...

# Prefer protocols over inheritance
class Drawable(Protocol):
    def draw(self, screen: Screen) -> None: ...
```

**Docstrings** (Google style):
```python
def spawn_entity(screen: Screen, entity_type: str) -> list[Actor]:
    """Spawn a new entity on the screen.

    Args:
        screen: The screen to spawn on
        entity_type: Type of entity to spawn ("fish", "shark", etc.)

    Returns:
        List of spawned actor instances

    Raises:
        ValueError: If entity_type is not recognized
    """
```

### Configuration Management

**Settings Priority** (highest to lowest):
1. Command-line arguments (`--fps 30`)
2. Local config (`.asciiquarium.toml`)
3. User config (`~/.config/asciiquarium-redux/config.toml`)
4. Defaults in [`Settings`](../asciiquarium_redux/util/settings.py:12) dataclass

**Adding New Settings**:
1. Add field to [`Settings`](../asciiquarium_redux/util/settings.py:12) dataclass
2. Update [`load_settings_from_sources()`](../asciiquarium_redux/util/settings.py) parsing
3. Add command-line argument in [`runner.py`](../asciiquarium_redux/runner.py)
4. Document in [`CONFIGURATION.md`](CONFIGURATION.md)

### Entity Development

**Creating New Entities**:

1. **Implement the [`Actor`](../asciiquarium_redux/entities/base.py:6) protocol**:
   ```python
   from asciiquarium_redux.entities.base import Actor

   class MyEntity:
       def __init__(self, x: float, y: float):
           self.x = x
           self.y = y
           self.active = True

       def update(self, dt: float, screen: Screen, app: Any) -> None:
           # Physics and behavior logic
           self.x += dt * 10  # Move right

           # Deactivate when off-screen
           if self.x > screen.width:
               self.active = False

       def draw(self, screen: Screen, mono: bool = False) -> None:
           # Rendering logic
           if 0 <= self.x < screen.width and 0 <= self.y < screen.height:
               color = Screen.COLOUR_WHITE if mono else Screen.COLOUR_CYAN
               screen.print_at("@", int(self.x), int(self.y), colour=color)
   ```

2. **Create spawn function**:
   ```python
   def spawn_my_entity(screen: Screen, app: Any) -> list[MyEntity]:
       """Spawn MyEntity at random location."""
       x = random.uniform(0, screen.width)
       y = random.uniform(app.settings.waterline_top, screen.height - 2)
       return [MyEntity(x, y)]
   ```

3. **Register in spawn system**:
   ```python
   # In AsciiQuarium.spawn_random()
   choices = [
       # ... existing choices
       ("my_entity", spawn_my_entity),
   ]
   ```

### Backend Development

**Adding New Backends**:

1. **Implement [`Screen`](../asciiquarium_redux/screen_compat.py) interface**:
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

2. **Create backend runner**:
   ```python
   def run_my_backend(settings: Settings) -> None:
       screen = MyBackendScreen(settings.ui_cols, settings.ui_rows)
       app = AsciiQuarium(settings)
       app.rebuild(screen)

       # Main loop
       while True:
           # ... game loop logic
   ```

3. **Register in [`runner.py`](../asciiquarium_redux/runner.py)**:
   ```python
   backend_map = {
       # ... existing backends
       "my_backend": run_my_backend,
   }
   ```

## Testing

### Manual Testing

**Basic functionality**:
```bash
# Test different backends
uv run asciiquarium --backend terminal
uv run asciiquarium --backend web --port 8080
uv run asciiquarium --backend tk

# Test configuration loading
uv run asciiquarium --config sample-config.toml
uv run asciiquarium --config big.toml

# Test entity spawning
uv run asciiquarium --spawn-weights '{"shark": 10.0}'

# Performance testing
uv run asciiquarium --fps 60 --density 3.0
```

**Interactive testing controls**:
- `h` or `?`: Toggle help display
- `p`: Pause/resume simulation
- `r`: Rebuild (respawn all entities)
- `q`: Quit
- `t`: Force fish turning (debug)
- `Left-click`: Drop fishhook at cursor

### Unit Testing (Future)

**Recommended test structure**:
```
tests/
├── test_entities.py         # Entity behavior testing
├── test_settings.py         # Configuration parsing
├── test_spawn.py            # Entity spawning logic
├── test_backends.py         # Backend compatibility
└── fixtures/                # Test data and configs
```

**Testing patterns**:
```python
def test_fish_movement():
    screen = MockScreen(80, 24)
    fish = Fish(frames=["<°)))><"], x=10, y=12, vx=1.0, colour=1)

    fish.update(1.0, screen, None)
    assert fish.x == 11.0  # Moved right

def test_entity_lifecycle():
    entity = SomeEntity()
    assert entity.active

    entity.destroy()
    assert not entity.active
```

## Performance Optimization

### Profiling

**Python profiling**:
```bash
# Profile main execution
uv run python -m cProfile -o profile.stats -m asciiquarium_redux --fps 60

# Analyze results
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

**Memory usage**:
```bash
# Monitor memory consumption
uv run python -m memory_profiler -m asciiquarium_redux
```

### Optimization Guidelines

**Entity Management**:
- Use `active` property for lifecycle management
- Implement object pooling for frequently created/destroyed entities
- Avoid allocations in hot paths (update loops)

**Rendering**:
- Use double buffering: [`DoubleBufferedScreen`](../asciiquarium_redux/util/buffer.py)
- Minimize string concatenation in draw methods
- Cache color calculations

**Configuration**:
- Prefer integer math over floating-point when possible
- Use appropriate data structures (`list` vs `set` vs `dict`)

## Debugging

### Common Issues

**Import Errors**:
```bash
# Ensure proper installation
uv sync
# or
pip install -e .
```

**Terminal Display Issues**:
```bash
# Test terminal compatibility
uv run asciiquarium --color mono
uv run asciiquarium --fps 10  # Slower refresh
```

**Configuration Problems**:
```bash
# Validate TOML syntax
python -c "import tomllib; tomllib.load(open('config.toml', 'rb'))"

# Debug configuration loading
uv run asciiquarium --verbose --config your-config.toml
```

### Debug Tools

**Built-in debugging**:
- Use `--verbose` flag for detailed output
- Press `t` key to trigger fish turning behavior
- Monitor FPS display with `h` key

**Code debugging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints in development
logger = logging.getLogger(__name__)
logger.debug(f"Entity count: {len(self.entities)}")
```

## Contributing Guidelines

### Pull Request Process

1. **Fork and branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make focused changes**:
   - One feature/fix per PR
   - Follow existing code style
   - Add appropriate documentation

3. **Test thoroughly**:
   - Test all backends (terminal, web, tk)
   - Verify configuration loading
   - Check performance impact

4. **Update documentation**:
   - Add/update docstrings
   - Update relevant documentation files
   - Include usage examples

### Code Review Checklist

**Functionality**:
- [ ] Does it work as intended?
- [ ] Are edge cases handled?
- [ ] Is error handling appropriate?

**Code Quality**:
- [ ] Follows PEP 8 and project conventions
- [ ] Has appropriate type hints
- [ ] Includes docstrings for public APIs
- [ ] No obvious performance issues

**Architecture**:
- [ ] Fits well with existing design patterns
- [ ] Doesn't break backend abstraction
- [ ] Maintains entity system consistency

**Documentation**:
- [ ] Public APIs are documented
- [ ] Complex algorithms explained
- [ ] Configuration options documented

## Resources

### Key Files for Contributors

- **Main Controller**: [`asciiquarium_redux/app.py`](../asciiquarium_redux/app.py) - Core game logic
- **Configuration**: [`asciiquarium_redux/util/settings.py`](../asciiquarium_redux/util/settings.py) - Settings management
- **Entity Base**: [`asciiquarium_redux/entities/base.py`](../asciiquarium_redux/entities/base.py) - Entity protocol
- **Examples**: [`sample-config.toml`](../sample-config.toml) - Configuration examples

### Related Documentation

- **Architecture**: [`ARCHITECTURE.md`](ARCHITECTURE.md) - System design overview
- **Entity System**: [`ENTITY_SYSTEM.md`](ENTITY_SYSTEM.md) - Entity behavior details
- **Configuration**: [`CONFIGURATION.md`](CONFIGURATION.md) - Settings reference
- **Backends**: [`BACKENDS.md`](BACKENDS.md) - Platform-specific details
- **Web Deployment**: [`WEB_DEPLOYMENT.md`](WEB_DEPLOYMENT.md) - Web backend setup

### External Resources

- **Asciimatics Documentation**: https://asciimatics.readthedocs.io/
- **Python Type Hints**: https://docs.python.org/3/library/typing.html
- **TOML Specification**: https://toml.io/en/
- **Original Asciiquarium**: https://github.com/cmatsuoka/asciiquarium

## Getting Help

**Issues and Discussion**:
- GitHub Issues: https://github.com/cognitivegears/asciiquarium_redux/issues
- Documentation: All files in [`docs/`](.) directory

**Development Questions**:
- Check existing issues for similar problems
- Provide minimal reproduction steps
- Include system information (OS, Python version, terminal)

**Feature Requests**:
- Describe the use case and expected behavior
- Consider implementation complexity
- Discuss with maintainers before major changes
