# Web Deployment Guide
## Documentation Navigation

📋 **[Overview](../README.md)** | 🏗️ **[Architecture](ARCHITECTURE.md)** | 🚀 **[Getting Started](DEVELOPER_GUIDE.md)** | 📚 **[API Reference](API_REFERENCE.md)**

🎯 **[Entity System](ENTITY_SYSTEM.md)** | ⚙️ **[Configuration](CONFIGURATION.md)** | 🖥️ **[Backends](BACKENDS.md)** | 🌐 **Web Deployment**

---


This guide covers setting up, running, and deploying the Asciiquarium Redux web interface.

## Overview

The web backend allows running Asciiquarium Redux in a browser using WebAssembly (WASM) through Pyodide. The system supports both local development and GitHub Pages deployment.

## Architecture

```
Web System Components:
├── asciiquarium_redux/web_server.py    # Local development server
├── asciiquarium_redux/web/             # Static web assets
│   ├── index.html                      # Main web interface
│   ├── app.js                          # JavaScript application logic
│   ├── styles.css                      # Web interface styling
│   └── wheels/                         # Local wheel storage (auto-generated)
└── .github/workflows/deploy-web.yml    # GitHub Pages deployment
```

## Local Development

### Prerequisites

- Python 3.9+ with the project installed in development mode
- A built wheel package (for local testing)

### Building the Package

First, build a wheel package for local testing:

```bash
# Install build dependencies
uv sync --dev

# Build the wheel
uv build
```

This creates a wheel file in the `dist/` directory that the web server will automatically detect.

### Starting the Development Server

Run the web server using the CLI:

```bash
# Start server on default port 8000 and open browser
asciiquarium-redux web

# Specify custom port and disable auto-open
asciiquarium-redux web --port 3000 --no-open-browser
```

Or programmatically:

```python
from asciiquarium_redux.web_server import serve_web

# Start with default settings
serve_web()

# Custom configuration
serve_web(port=3000, open_browser=False)
```

### Web Server Features

The development server ([`web_server.py`](../asciiquarium_redux/web_server.py)) provides:

#### Automatic Wheel Management
- Detects the latest wheel in `dist/` directory
- Copies it to `web/wheels/asciiquarium_redux-latest.whl`
- Creates a manifest.json with the exact filename
- Only updates when the wheel file changes (based on mtime)

#### MIME Type Handling
- Serves `.wasm` files with correct `application/wasm` MIME type
- Handles `.whl` files as `application/octet-stream`
- Supports all standard web file types

#### Development Workflow
1. Make code changes
2. Run `uv build` to create a new wheel
3. Restart the web server (it will auto-detect the new wheel)
4. Refresh the browser to load the updated code

## Web Interface Features

### Interactive Settings Panel

The web interface ([`index.html`](../asciiquarium_redux/web/index.html)) includes:

- **Real-time configuration**: Modify settings without restarting
- **Organized controls**: Grouped by functionality (Basics, Fish, Seaweed, Scene, Spawn, Special Weights)
- **Validation**: Range limits and type checking for all parameters
- **Reset functionality**: Restore default settings

### Key Controls

| Control | Function |
|---------|----------|
| **FPS** | Animation frame rate (5-60 fps) |
| **Speed** | Global animation speed multiplier (0.1-3.0x) |
| **Density** | Entity spawn density (0.1-5.0x) |
| **Color** | Color mode (auto/mono/16/256) |
| **Seed** | Random seed for reproducible layouts |

### Keyboard Shortcuts

- `q` - Quit/close
- `p` - Pause/resume animation
- `Space` - Deploy fishhook
- `t` - Toggle fish turning
- `h` - Show help
- Click anywhere to deploy fishhook

## GitHub Pages Deployment

### Automatic Deployment

The project uses GitHub Actions for automatic deployment to GitHub Pages:

**Workflow**: [`.github/workflows/deploy-web.yml`](../.github/workflows/deploy-web.yml)

**Triggers**:
- Push to `main` branch affecting web files
- Manual workflow dispatch
- Changes to web directory, deployment config, or README

**Process**:
1. Checkout repository
2. Copy web assets to `out/` directory
3. Add `.nojekyll` file for GitHub Pages compatibility
4. Copy `index.html` to `404.html` for SPA routing
5. Deploy to `gh-pages` branch with force-orphan

### Manual Deployment

To deploy manually:

```bash
# 1. Build static directory
mkdir -p out
rsync -a --delete asciiquarium_redux/web/ out/

# 2. Add GitHub Pages optimizations
touch out/.nojekyll
cp out/index.html out/404.html

# 3. Deploy to gh-pages branch (requires git setup)
# This is typically handled by the GitHub Action
```

### Production vs Development Differences

| Aspect | Development | Production (GitHub Pages) |
|--------|-------------|---------------------------|
| **Package Source** | Local wheel from `dist/` | PyPI package via Pyodide |
| **Update Method** | Rebuild wheel + restart server | Push to main branch |
| **Installation** | [`app.js`](../asciiquarium_redux/web/app.js) loads local wheel | [`app.js`](../asciiquarium_redux/web/app.js) installs from PyPI |
| **Performance** | Faster (pre-built wheel) | Slower initial load |

## Configuration

### Web-Specific Settings

The web interface supports all configuration options from [`CONFIGURATION.md`](CONFIGURATION.md), exposed through the settings panel:

```javascript
// Settings are applied real-time via JavaScript
const config = {
  fps: 24,
  speed: 0.75,
  density: 1.0,
  color: 'auto',
  // ... all other settings
};
```

### Customizing the Interface

#### Modifying Styles

Edit [`styles.css`](../asciiquarium_redux/web/styles.css) for visual customization:

```css
/* Example: Change color scheme */
:root {
  --primary-color: #2563eb;
  --background-color: #0f172a;
  --text-color: #f1f5f9;
}
```

#### Adding Controls

Extend [`index.html`](../asciiquarium_redux/web/index.html) to add new settings:

```html
<!-- Add to settings dialog -->
<div class="field">
  <label for="new_setting">New Setting</label>
  <input class="opt" id="new_setting" type="range" min="0" max="100" value="50">
</div>
```

Update [`app.js`](../asciiquarium_redux/web/app.js) to handle the new control.

## Troubleshooting

### Common Issues

#### Web Server Won't Start

```bash
# Check if port is in use
lsof -i :8000

# Try different port
asciiquarium-redux web --port 8080
```

#### Package Not Loading in Browser

1. **Check wheel build**:
   ```bash
   ls -la dist/
   # Should show asciiquarium_redux-*.whl files
   ```

2. **Verify wheel copying**:
   ```bash
   ls -la asciiquarium_redux/web/wheels/
   # Should show asciiquarium_redux-latest.whl and manifest.json
   ```

3. **Check browser console** for Pyodide loading errors

#### GitHub Pages Deployment Failing

1. **Check workflow logs** in Actions tab
2. **Verify permissions**: Repository needs write access to deploy
3. **Check file paths**: Ensure web assets exist and are valid

#### Performance Issues

- **Reduce FPS**: Lower frame rate for slower devices
- **Decrease density**: Fewer entities for better performance
- **Use mono color**: Disable color rendering
- **Clear browser cache**: Force reload of updated assets

### Debug Mode

Enable verbose logging in the browser console:

```javascript
// In browser developer tools
localStorage.setItem('asciiquarium_debug', 'true');
location.reload();
```

## Security Considerations

### Local Development

- Server binds to `127.0.0.1` (localhost only)
- No authentication required for development
- Automatic file serving from web directory

### Production Deployment

- Static files served via GitHub Pages
- No server-side code execution
- All computation happens in browser via WASM
- No user data persistence or collection

## Performance Optimization

### Local Development

- **Wheel caching**: Server only updates wheels when file changes
- **Static serving**: Direct file serving with appropriate MIME types
- **No processing overhead**: Pure static file server

### Browser Performance

- **Pyodide caching**: Browser caches the Python runtime
- **Package caching**: Installed packages persist across sessions
- **Canvas optimization**: Efficient ASCII rendering
- **Memory management**: Proper cleanup of animation frames

## Integration with Other Backends

The web backend integrates with the broader Asciiquarium Redux architecture:

- **Shared core logic**: Same entity system and game logic as terminal/TkInter
- **Unified configuration**: Same settings schema across all backends
- **Cross-platform compatibility**: Write once, run everywhere approach

See [`BACKENDS.md`](BACKENDS.md) for detailed backend comparison and [`ARCHITECTURE.md`](ARCHITECTURE.md) for system design overview.

---

**Next Steps**: After setting up the web backend, see [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) for contributing guidelines and [`API_REFERENCE.md`](API_REFERENCE.md) for programmatic usage.
