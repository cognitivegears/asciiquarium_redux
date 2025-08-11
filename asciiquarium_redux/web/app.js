// Pyodide is loaded via a classic <script> tag in index.html.
// Use the global window.loadPyodide to initialize.

const canvas = document.getElementById("aquarium");
const ctx2d = canvas.getContext("2d", { alpha: false, desynchronized: true });
const state = { cols: 120, rows: 40, cellW: 12, cellH: 18, baseline: 4, fps: 24, running: false };

function measureCell(font = "16px Menlo, 'SF Mono', Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace") {
  // Ensure metrics are in CSS pixels (identity transform)
  ctx2d.setTransform(1, 0, 0, 1, 0, 0);
  ctx2d.font = font;
  const m = ctx2d.measureText("M");
  const w = Math.round(m.width);
  const ascent = Math.ceil(m.actualBoundingBoxAscent || 13);
  const descent = Math.ceil(m.actualBoundingBoxDescent || 3);
  const h = ascent + descent + 2; // small padding for descenders
  state.baseline = Math.ceil(descent + 1);
  return { w: Math.ceil(w), h: Math.ceil(h) };
}

function applyHiDPIScale() {
  const dpr = Math.max(1, Math.floor(window.devicePixelRatio || 1));
  ctx2d.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function resizeCanvasToGrid() {
  const { w, h } = measureCell();
  state.cellW = Math.round(w); state.cellH = Math.round(h);
  const rect = canvas.getBoundingClientRect();
  const cols = Math.max(40, Math.floor(rect.width / state.cellW));
  const rows = Math.max(20, Math.floor(rect.height / state.cellH));
  state.cols = cols; state.rows = rows;
  const dpr = Math.max(1, Math.floor(window.devicePixelRatio || 1));
  // Set CSS size
  canvas.style.width = `${cols * state.cellW}px`;
  canvas.style.height = `${rows * state.cellH}px`;
  // Set backing store size in device pixels
  canvas.width = cols * state.cellW * dpr;
  canvas.height = rows * state.cellH * dpr;
  applyHiDPIScale();
  if (window.pyodide) window.pyodide.runPython(`import importlib; web_backend = importlib.import_module('asciiquarium_redux.web_backend'); web_backend.web_app.resize(${cols}, ${rows})`);
}

function jsFlushHook(batches) {
  // Clear
  ctx2d.fillStyle = "#000";
  ctx2d.fillRect(0, 0, canvas.width, canvas.height);
  // Draw runs
  ctx2d.textBaseline = "alphabetic";
  ctx2d.textAlign = "left";
  ctx2d.font = "16px Menlo, 'SF Mono', Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace";
  // Convert Pyodide PyProxy (Python list[dict]) to plain JS if needed
  const items = batches && typeof batches.toJs === "function"
    ? batches.toJs({ dict_converter: Object.fromEntries, create_proxies: false })
    : batches;
  for (const b of items) {
    ctx2d.fillStyle = b.colour;
    const baseX = Math.round(b.x * state.cellW);
    const baseY = Math.round((b.y + 1) * state.cellH - state.baseline);
    const text = b.text || "";
    // Draw per character to enforce exact monospaced column width regardless of font metrics
    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      if (ch !== " ") {
        const px = baseX + i * state.cellW;
        ctx2d.fillText(ch, px, baseY);
      }
    }
  }
}

let last = performance.now();
function loop(now) {
  const dt = now - last;
  const frameInterval = 1000 / state.fps;
  if (dt >= frameInterval && state.running) {
    window.pyodide.runPython(`from asciiquarium_redux import web_backend; web_backend.web_app.tick(${dt})`);
    last = now;
  }
  requestAnimationFrame(loop);
}

async function boot() {
  const pyodide = await window.loadPyodide({ indexURL: "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/" });
  window.pyodide = pyodide;
  await pyodide.loadPackage("micropip");
  // Try to install from local wheel path (served alongside the page). Fallback to PyPI if needed.
  try {
  // Purge any previously installed copy to force reinstall of the latest local wheel
  await pyodide.runPythonAsync(`
import sys, shutil, pathlib
for p in list(sys.modules):
  if p.startswith('asciiquarium_redux'):
    del sys.modules[p]
site_pkgs = [path for path in sys.path if 'site-packages' in path]
for sp in site_pkgs:
  d = pathlib.Path(sp)
  pkg = d / 'asciiquarium_redux'
  if pkg.exists():
    shutil.rmtree(pkg, ignore_errors=True)
  for info in d.glob('asciiquarium_redux-*.dist-info'):
    shutil.rmtree(info, ignore_errors=True)
`);
  // Prefer the exact wheel name from manifest to satisfy micropip filename parsing
  // Add a cache-busting parameter so the browser/micropip won’t reuse an old wheel
  const nonce = Date.now();
  let wheelUrl = new URL(`./wheels/asciiquarium_redux-latest.whl?t=${nonce}` , window.location.href).toString();
    try {
      const m = await fetch(new URL("./wheels/manifest.json", window.location.href).toString(), { cache: "no-store" });
      if (m.ok) {
  const { wheel } = await m.json();
  if (wheel) wheelUrl = new URL(`./wheels/${wheel}?t=${nonce}` , window.location.href).toString();
      }
    } catch {}
    // Fetch wheel to avoid any Content-Type/CORS issues and install via file:// URI
    let installed = false;
  try {
      const resp = await fetch(wheelUrl, { cache: "no-store" });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const buf = new Uint8Array(await resp.arrayBuffer());
  const wheelName = decodeURIComponent(new URL(wheelUrl).pathname.split('/').pop() || 'asciiquarium_redux.whl');
  const wheelPath = `/tmp/${wheelName}`;
            pyodide.FS.writeFile(wheelPath, buf);
            await pyodide.runPythonAsync(`import micropip; await micropip.install('${wheelUrl}')`);
      installed = true;
  console.log('Installed local wheel');
    } catch (e) {
      console.warn("Local wheel install failed, falling back to PyPI:", e);
    }
    if (!installed) {
      await pyodide.runPythonAsync(`import micropip; await micropip.install('asciiquarium-redux')`);
      console.log('Installed from PyPI');
    }
    await pyodide.runPythonAsync(`import importlib; web_backend = importlib.import_module('asciiquarium_redux.web_backend')`);
  } catch (e) {
    console.error("Failed to install package:", e);
    return;
  }
  try {
    const version = await pyodide.runPythonAsync(`
import importlib.metadata as md
v = 'unknown'
try:
    v = md.version('asciiquarium-redux')
except Exception:
    pass
v
`);
    console.log("asciiquarium-redux version:", version);
  } catch (e) {
    console.warn("Could not determine installed version:", e);
  }
  // Provide the flush hook
  // Ensure module is in globals and then set js hook via pyimport
  // Workaround: set via pyodide.globals
  const mod = pyodide.pyimport("asciiquarium_redux.web_backend");
  mod.set_js_flush_hook(jsFlushHook);

  resizeCanvasToGrid();
  const opts = collectOptionsFromUI();
  // Convert JS object to a real Python dict to avoid JSON true/false/null issues
  const pyOpts = pyodide.toPy(opts);
  try {
    pyodide.globals.set("W_OPTS", pyOpts);
  } finally {
    pyOpts.destroy();
  }
  pyodide.runPython(`web_backend.web_app.start(${state.cols}, ${state.rows}, W_OPTS)`);
  state.running = true;

  canvas.addEventListener("click", ev => {
    const x = Math.floor(ev.offsetX / state.cellW);
    const y = Math.floor(ev.offsetY / state.cellH);
  pyodide.runPython(`web_backend.web_app.on_mouse(${x}, ${y}, 1)`);
  });
  window.addEventListener("keydown", ev => {
  pyodide.runPython(`web_backend.web_app.on_key("${ev.key}")`);
  });
  new ResizeObserver(resizeCanvasToGrid).observe(canvas);
  requestAnimationFrame(loop);
}

function collectOptionsFromUI() {
  return {
    fps: Number(document.getElementById("fps").value),
    speed: Number(document.getElementById("speed").value),
    density: Number(document.getElementById("density").value),
    color: document.getElementById("color").value,
    chest: document.getElementById("chest").checked,
    turn: document.getElementById("turn").checked,
    seed: document.getElementById("seed").value || null
  };
}

  ["fps","speed","density","color","chest","turn","seed"].forEach(id => {
  const el = document.getElementById(id);
  el.addEventListener("input", () => {
    const opts = collectOptionsFromUI();
      const pyOpts = pyodide.toPy(opts);
      try {
        pyodide.globals.set("W_OPTS", pyOpts);
      } finally {
        pyOpts.destroy();
      }
      window.pyodide?.runPython(`web_backend.web_app.set_options(W_OPTS)`);
  });
});

document.getElementById("reset").addEventListener("click", () => location.reload());

boot();
