# Asciiquarium Redux - Backend System
## Documentation Navigation

📋 **[Overview](../README.md)** | 🏗️ **[Architecture](ARCHITECTURE.md)** | 🚀 **[Getting Started](DEVELOPER_GUIDE.md)** | 📚 **[API Reference](API_REFERENCE.md)**

🎯 **[Entity System](ENTITY_SYSTEM.md)** | ⚙️ **[Configuration](CONFIGURATION.md)** | 🖥️ **Backends** | 🌐 **[Web Deployment](WEB_DEPLOYMENT.md)**

---


## Overview

Asciiquarium Redux implements a multi-backend architecture using the Strategy Pattern to provide consistent aquarium simulation across different platforms and environments. The system abstracts rendering and input handling through a common [`Screen`](../asciiquarium_redux/screen_compat.py) interface while enabling platform-specific optimizations.

## Architecture Design

### Backend Abstraction Layer

```
┌─────────────────────────────────────────────────────────────┐
│                  AsciiQuarium Core                          │
│  - Entity management and game logic                         │
│  - Platform-agnostic simulation                             │
└─────────────────────┬───────────────────────────────────────┘
                      │ Screen Interface
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Screen Abstraction                           │
│  - print_at(text, x, y, colour)                             │
│  - get_event() → KeyboardEvent | MouseEvent                 │
│  - width, height properties                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │ Strategy Pattern
                      ▼
┌──────────────┬──────────────┬──────────────┬──────────────┐
│   Terminal   │     Web      │   TkInter    │   Future     │
│   Backend    │   Backend    │   Backend    │  Backends    │
│              │              │              │              │
│ Asciimatics  │ WebSocket +  │ Tkinter +    │     ...      │
│ + Terminal   │ HTML Canvas  │ Canvas       │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### Common Interface

All backends implement a consistent interface:

```python
class Screen(Protocol):
    width: int
    height: int

    def print_at(self, text: str, x: int, y: int, colour: int) -> None:
        """Print text at screen coordinates with specified color."""
        ...

    def get_event(self) -> Event | None:
        """Get next input event (keyboard/mouse) or None."""
        ...
```

## Terminal Backend

**Location**: [`asciiquarium_redux/backend/term/`](../asciiquarium_redux/backend/term/)

The terminal backend provides native terminal rendering using the Asciimatics library.

### Features

- **Full ANSI Color Support**: 16-color, 256-color, and true-color modes
- **Cross-Platform**: Works on Windows, macOS, Linux terminals
- **Performance Optimized**: Direct terminal control with minimal overhead
- **Rich Input**: Keyboard and mouse event handling
- **Terminal Detection**: Automatic capability detection and fallback

### Architecture

**Components**:
- [`TerminalRenderContext`](../asciiquarium_redux/backend/term/term_backends.py:38): Manages screen rendering and double buffering
- [`TerminalEventStream`](../asciiquarium_redux/backend/term/term_backends.py): Handles keyboard and mouse input
- Screen size auto-detection from terminal dimensions

**Rendering Pipeline**:
```
App entities → Screen.print_at() → DoubleBufferedScreen → Asciimatics → Terminal
```

### Configuration

```toml
[ui]
backend = "terminal"
# cols/rows ignored - uses actual terminal size
```

**Command Line**:
```bash
# Default backend (explicit)
asciiquarium --backend terminal

# Color mode override
asciiquarium --backend terminal --color mono
asciiquarium --backend terminal --color 256
```

### Terminal Compatibility

| Terminal             | Color Support | Mouse Support | Performance |
|----------------------|---------------|---------------|-------------|
| **Modern Terminals** |               |               |             |
| iTerm2 (macOS)       | True-color    | Full          | Excellent   |
| Terminal.app (macOS) | 256-color     | Full          | Excellent   |
| Windows Terminal     | True-color    | Full          | Excellent   |
| GNOME Terminal       | True-color    | Full          | Excellent   |
| **Legacy Terminals** |               |               |             |
| cmd.exe              | 16-color      | Limited       | Good        |
| PuTTY                | 256-color     | Full          | Good        |
| **Remote/SSH**       |               |               |             |
| tmux                 | 256-color     | Full          | Excellent   |
| screen               | 256-color     | Limited       | Good        |
| SSH terminals        | Varies        | Varies        | Good        |

### Best Use Cases

- **SSH Sessions**: Remote server administration
- **Development**: Local development and testing
- **Production**: Server environments without GUI
- **Scripting**: Automated environments
- **Low Resource**: Minimal memory and CPU usage

### Example Usage

```python
# Direct terminal backend usage
from asciiquarium_redux.util.settings import Settings
from asciiquarium_redux.app import run

settings = Settings(ui_backend="terminal")
run(screen, settings)  # Uses terminal automatically
```

## Web Backend

**Location**: [`asciiquarium_redux/backend/web/`](../asciiquarium_redux/backend/web/)

The web backend provides browser-based rendering using WebSocket communication and HTML5 Canvas.

### Features

- **Browser-Based**: Runs in any modern web browser
- **Real-Time Updates**: WebSocket for low-latency communication
- **Mobile Friendly**: Responsive design with touch controls
- **Remote Access**: Network accessibility for multiple users
- **Cross-Platform**: Works on any device with a web browser

### Architecture

**Components**:
- [`WebApp`](../asciiquarium_redux/backend/web/web_backend.py:28): Main application controller for web environment
- [`WebScreen`](../asciiquarium_redux/backend/web/web_screen.py): Canvas-based screen abstraction
- [`web_server.py`](../asciiquarium_redux/web_server.py): Standalone web server for hosting

**Technology Stack**:
- **Backend**: Python WebSocket server using `websockets` library
- **Frontend**: HTML5 Canvas with JavaScript client
- **Protocol**: JSON message passing over WebSocket
- **Deployment**: Can run in Pyodide (WebAssembly) for client-side execution

**Communication Flow**:
```
Browser ←→ WebSocket ←→ Python App ←→ AsciiQuarium Core
   ↑           ↑            ↑              ↑
Canvas ← JavaScript ← JSON Messages ← WebScreen
```

### Configuration

```toml
[ui]
backend = "web"
cols = 120              # Canvas width in characters
rows = 40               # Canvas height in characters

[web]
port = 8000             # Server port
host = "localhost"      # Bind address
open = true             # Auto-open browser
```

**Command Line**:
```bash
# Basic web backend
asciiquarium --backend web

# Custom port and auto-open
asciiquarium --backend web --port 8080 --open

# Network accessible
asciiquarium --backend web --host 0.0.0.0 --port 8000
```

### Web Interface Features

**Browser Controls**:
- **Mouse Interaction**: Click to drop fishhook
- **Keyboard Shortcuts**: Same as terminal (q, p, r, h)
- **Responsive Layout**: Adapts to browser window size
- **Mobile Support**: Touch-friendly interface

**JavaScript Client** ([`asciiquarium_redux/web/app.js`](../asciiquarium_redux/web/app.js)):
```javascript
// WebSocket communication
const ws = new WebSocket('ws://localhost:8000/ws');

// Canvas rendering
function renderFrame(updates) {
    updates.forEach(update => {
        drawText(update.x, update.y, update.text, update.color);
    });
}

// Input handling
canvas.addEventListener('click', (event) => {
    const x = Math.floor(event.offsetX / cellWidth);
    const y = Math.floor(event.offsetY / cellHeight);
    ws.send(JSON.stringify({type: 'click', x, y}));
});
```

### Deployment Options

**Local Development**:
```bash
# Run local web server
asciiquarium --backend web --port 8080 --open
# Open browser to http://localhost:8080
```

**Network Deployment**:
```bash
# Bind to all interfaces
asciiquarium --backend web --host 0.0.0.0 --port 8000
# Access from http://[server-ip]:8000
```

**WebAssembly/Pyodide** (Future):
```javascript
// Client-side Python execution in browser
import { loadPyodide } from "pyodide";
const pyodide = await loadPyodide();
await pyodide.loadPackage("asciiquarium-redux");
```

### Best Use Cases

- **Remote Monitoring**: Server dashboards accessible via browser
- **Demonstrations**: Easy sharing and presentation
- **Mobile Access**: Touch-friendly interface on tablets/phones
- **Education**: Classroom demonstrations without installation
- **Development**: Quick testing across different devices

## TkInter Backend

**Location**: [`asciiquarium_redux/backend/tk/`](../asciiquarium_redux/backend/tk/)

The TkInter backend provides a native desktop GUI application using Python's built-in Tkinter library.

### Features

- **Native Desktop**: Platform-native window management
- **No Dependencies**: Uses Python's built-in Tkinter (included in most Python installations)
- **Font Customization**: Configurable fonts and sizes
- **Fullscreen Support**: Dedicated fullscreen mode
- **Window Controls**: Standard minimize, maximize, close buttons

### Architecture

**Components**:
- [`run_tk()`](../asciiquarium_redux/backend/tk/runner.py:35): Main TkInter application runner
- [`ScreenShim`](../asciiquarium_redux/backend/tk/runner.py:13): Adapter to common Screen interface
- [`TkRenderContext`](../asciiquarium_redux/backend/term/term_backends.py): Canvas-based rendering context
- [`TkEventStream`](../asciiquarium_redux/backend/term/term_backends.py): Tkinter event handling

**Rendering Architecture**:
```
App → ScreenShim → TkRenderContext → Tkinter Canvas → Desktop Window
```

### Configuration

```toml
[ui]
backend = "tk"
fullscreen = false      # Window or fullscreen mode
cols = 100              # Canvas width in characters
rows = 30               # Canvas height in characters
font_family = "Menlo"   # Font name
font_size = 14          # Font size in points
```

**Command Line**:
```bash
# Basic TkInter backend
asciiquarium --backend tk

# Fullscreen mode
asciiquarium --backend tk --fullscreen

# Custom window size
asciiquarium --backend tk --cols 80 --rows 24
```

### Font Configuration

**Built-in Font Selection**:
```toml
[ui]
font_family = "Courier New"    # Windows-friendly
font_family = "Monaco"         # macOS monospace
font_family = "Ubuntu Mono"    # Linux
font_family = "Source Code Pro" # Modern programming font
```

**Font Requirements**:
- Must be monospace (fixed-width) for proper character alignment
- Should support ASCII characters used in entity sprites
- Recommended sizes: 10-18 points for optimal visibility

### Window Management

**Window Modes**:
```python
# Windowed mode (default)
settings.ui_fullscreen = False

# Fullscreen mode
settings.ui_fullscreen = True
```

**Size Calculation**:
```python
# Automatic sizing based on font metrics
cell_width = font.measure("W")
cell_height = font.metrics("linespace")
window_width = cols * cell_width
window_height = rows * cell_height
```

### Platform Behavior

| Platform    | Native Look         | Performance | Font Rendering |
|-------------|---------------------|-------------|----------------|
| **Windows** | Windows 10/11 style | Good        | ClearType      |
| **macOS**   | Aqua/System style   | Excellent   | Retina-aware   |
| **Linux**   | GTK/Qt themed       | Good        | Fontconfig     |

### Best Use Cases

- **Desktop Applications**: Standalone aquarium screensaver or application
- **Kiosk Mode**: Fullscreen display for exhibitions or demonstrations
- **Offline Use**: No network requirements, fully self-contained
- **Font Customization**: Users can adjust fonts for accessibility
- **Window Integration**: Works with desktop window managers and virtual desktops

### Limitations

- **Limited Color Support**: Reduced color palette compared to terminal/web backends
- **Platform Dependency**: Requires Tkinter (usually included with Python)
- **Performance**: Canvas rendering slower than terminal for large screens
- **Threading**: Tkinter's single-threaded nature can limit some optimizations

## Backend Comparison

### Feature Matrix

| Feature          | Terminal    | Web        | TkInter  |
|------------------|-------------|------------|----------|
| **Installation** |             |            |          ||
| Dependencies     | Asciimatics | websockets | Built-in |
| Platform Support | All         | All        | All      |
| Setup Complexity | Medium      | High       | Low      |
| **Performance**  |             |            |          ||
| Rendering Speed  | Excellent   | Good       | Fair     |
| Memory Usage     | Low         | Medium     | Medium   |
| CPU Usage        | Low         | Medium     | Medium   |
| **Display**      |             |            |          ||
| Color Support    | Full        | Full       | Limited  |
| Font Control     | Terminal    | Browser    | Full     |
| Fullscreen       | Terminal    | Browser    | Native   |
| **Input**        |             |            |          ||
| Keyboard         | Full        | Full       | Full     |
| Mouse            | Full        | Full       | Full     |
| Touch            | No          | Yes        | No       |
| **Deployment**   |             |            |          ||
| Remote Access    | SSH         | Network    | No       |
| Mobile Support   | Limited     | Full       | No       |
| Offline Use      | Yes         | No         | Yes      |

### Performance Characteristics

**Rendering Throughput** (characters/second):
- **Terminal**: ~50,000 chars/sec (direct terminal control)
- **Web**: ~30,000 chars/sec (WebSocket + Canvas)
- **TkInter**: ~15,000 chars/sec (Canvas drawing operations)

**Memory Usage** (typical 120x40 screen):
- **Terminal**: ~5MB (Asciimatics + double buffer)
- **Web**: ~15MB (WebSocket server + client state)
- **TkInter**: ~12MB (Tkinter widgets + Canvas buffer)

**Startup Time**:
- **Terminal**: <100ms (immediate terminal access)
- **Web**: ~500ms (server startup + browser connection)
- **TkInter**: ~300ms (GUI initialization + window creation)

### Backend Selection Guidelines

**Choose Terminal Backend When**:
- Running on servers or in SSH sessions
- Maximum performance and minimal resource usage required
- Working in terminal-based environments (tmux, screen)
- Need full ANSI color support
- Integrating with command-line tools

**Choose Web Backend When**:
- Need remote access from multiple devices
- Mobile or tablet support required
- Sharing demonstrations or presentations
- Running in environments without GUI
- Want responsive, browser-based interface

**Choose TkInter Backend When**:
- Building standalone desktop application
- Need native window management and controls
- Want font customization and accessibility features
- Running in GUI environment without browser
- Distributing as desktop application

## Implementation Details

### Screen Interface Implementation

Each backend provides its own implementation of the core [`Screen`](../asciiquarium_redux/screen_compat.py) interface:

```python
# Terminal Backend
class AscimaticsScreen:
    def print_at(self, text: str, x: int, y: int, colour: int) -> None:
        # Direct Asciimatics screen.print_at() call
        self._screen.print_at(text, x, y, colour)

    def get_event(self) -> Event | None:
        # Asciimatics event polling
        return self._screen.get_event()

# Web Backend
class WebScreen:
    def print_at(self, text: str, x: int, y: int, colour: int) -> None:
        # Buffer update for WebSocket transmission
        self._buffer[y][x] = (text, colour)

    def get_event(self) -> Event | None:
        # WebSocket message parsing to events
        return self._parse_websocket_event()

# TkInter Backend
class TkScreen:
    def print_at(self, text: str, x: int, y: int, colour: int) -> None:
        # Tkinter Canvas text drawing
        self._canvas.create_text(x * cell_w, y * cell_h, text=text, fill=colour)

    def get_event(self) -> Event | None:
        # Tkinter event queue processing
        return self._process_tk_events()
```

### Event Handling Differences

**Terminal Backend** (Asciimatics events):
```python
from asciimatics.event import KeyboardEvent, MouseEvent

if isinstance(event, KeyboardEvent):
    key_code = event.key_code
elif isinstance(event, MouseEvent):
    x, y = event.x, event.y
    buttons = event.buttons
```

**Web Backend** (JSON messages):
```javascript
// Browser → Python
{
    "type": "keydown",
    "key": "q",
    "timestamp": 1234567890
}
{
    "type": "click",
    "x": 45,
    "y": 12,
    "button": 0
}
```

**TkInter Backend** (Tkinter events):
```python
def on_key_press(event):
    key_char = event.char
    key_code = event.keycode

def on_mouse_click(event):
    x = event.x // cell_width
    y = event.y // cell_height
```

### Color Management

**Terminal Backend**:
- Uses Asciimatics color constants (0-255)
- Automatic terminal capability detection
- Fallback to monochrome for limited terminals

**Web Backend**:
- Converts to CSS color values
- Supports full RGB color space
- Client-side color palette management

**TkInter Backend**:
- Maps to Tkinter color names/hex values
- Limited to standard GUI colors
- Platform-specific color rendering

## Adding New Backends

### Implementation Steps

1. **Create Backend Module**:
   ```
   asciiquarium_redux/backend/mybackend/
   ├── __init__.py
   ├── my_backend.py
   └── my_screen.py
   ```

2. **Implement Screen Interface**:
   ```python
   class MyScreen:
       def __init__(self, width: int, height: int):
           self.width = width
           self.height = height

       def print_at(self, text: str, x: int, y: int, colour: int) -> None:
           # Backend-specific rendering
           pass

       def get_event(self) -> Event | None:
           # Backend-specific input handling
           return None
   ```

3. **Create Runner Function**:
   ```python
   def run_mybackend(settings: Settings) -> None:
       screen = MyScreen(settings.ui_cols, settings.ui_rows)
       app = AsciiQuarium(settings)
       app.rebuild(screen)

       # Backend-specific main loop
       while True:
           app.update(dt, screen, frame_no)
           # Handle events, timing, etc.
   ```

4. **Register Backend**:
   ```python
   # In runner.py
   from .backend.mybackend import run_mybackend

   backend_map = {
       "terminal": run_terminal,
       "web": run_web,
       "tk": run_tk,
       "mybackend": run_mybackend,  # Add new backend
   }
   ```

5. **Add Configuration Support**:
   ```python
   # In settings.py
   parser.add_argument("--backend",
                      choices=["terminal", "web", "tk", "mybackend"])
   ```

### Backend Requirements

**Mandatory Features**:
- Character-based rendering via `print_at()`
- Keyboard input handling (q, p, r, h keys minimum)
- Screen size management
- Color support (at least monochrome)

**Recommended Features**:
- Mouse/touch input for fishhook interaction
- Configurable screen dimensions
- Performance optimization for target platform
- Graceful degradation for limited environments

**Optional Features**:
- Full-color support
- Font customization
- Fullscreen modes
- Audio support (future)

## Troubleshooting

### Common Issues

**Terminal Backend**:
```bash
# Color display issues
asciiquarium --backend terminal --color mono
asciiquarium --backend terminal --color 16

# Terminal size detection
export TERM=xterm-256color
asciiquarium --backend terminal
```

**Web Backend**:
```bash
# Port conflicts
asciiquarium --backend web --port 8080

# Network access issues
asciiquarium --backend web --host 0.0.0.0

# Browser compatibility
# Use modern browsers with WebSocket support
```

**TkInter Backend**:
```bash
# Font issues
asciiquarium --backend tk --font-family "Courier New"

# Display scaling
asciiquarium --backend tk --font-size 16

# Missing Tkinter (Linux)
sudo apt-get install python3-tk
```

### Performance Optimization

**All Backends**:
```toml
[render]
fps = 15           # Reduce frame rate
color = "mono"     # Simplify rendering

[scene]
density = 0.8      # Fewer entities
```

**Terminal-Specific**:
```bash
# Use fastest terminal
export TERM=xterm-256color
# Disable mouse if not needed
asciiquarium --no-mouse
```

**Web-Specific**:
```toml
[ui]
cols = 80          # Smaller canvas
rows = 24
```

## Cross-References

- **Architecture Overview**: [`ARCHITECTURE.md`](ARCHITECTURE.md) - Backend design patterns
- **Configuration**: [`CONFIGURATION.md`](CONFIGURATION.md) - Backend-specific settings
- **Web Deployment**: [`WEB_DEPLOYMENT.md`](WEB_DEPLOYMENT.md) - Web backend setup details
- **Development Guide**: [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) - Backend development
- **API Reference**: [`API_REFERENCE.md`](API_REFERENCE.md) - Screen interface details
