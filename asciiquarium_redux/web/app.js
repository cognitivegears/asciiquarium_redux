// Pyodide is loaded via a classic <script> tag in index.html.
// Use the global window.loadPyodide to initialize.

const canvas = document.getElementById("aquarium");
const stage = document.querySelector(".stage");
const settingsDialog = document.getElementById("settingsDialog");
const settingsBtn = document.getElementById("settingsBtn");
const aboutBtn = document.getElementById("aboutBtn");
const aboutDialog = document.getElementById("aboutDialog");
const closeAbout = document.getElementById("closeAbout");
const aboutContent = document.getElementById("aboutContent");
const closeSettings = document.getElementById("closeSettings");
const ctx2d = canvas.getContext("2d", { alpha: false, desynchronized: true });
const state = { cols: 120, rows: 40, cellW: 12, cellH: 18, baseline: 4, fps: 24, running: false };
let lastFontSize = null;

function getAquariumFont() {
  // Get computed font-size for the canvas (may be set by media query)
  const style = window.getComputedStyle(canvas);
  return `${style.fontSize} Menlo, 'SF Mono', Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace`;
}
function measureCell(font) {
  ctx2d.setTransform(1, 0, 0, 1, 0, 0);
  ctx2d.font = font;
  const m = ctx2d.measureText("M");
  const w = Math.round(m.width);
  const ascent = Math.ceil(m.actualBoundingBoxAscent || 13);
  const descent = Math.ceil(m.actualBoundingBoxDescent || 3);
  const h = ascent + descent + 2;
  state.baseline = Math.ceil(descent + 1);
  return { w: Math.ceil(w), h: Math.ceil(h) };
}

function applyHiDPIScale() {
  const dpr = Math.max(1, Math.floor(window.devicePixelRatio || 1));
  ctx2d.setTransform(dpr, 0, 0, dpr, 0, 0);
}

let resizeTimer = null;
function resizeCanvasToGrid() {
  // Ensure measurement reflects container size, not prior fixed canvas pixels
  const prevInlineW = canvas.style.width;
  const prevInlineH = canvas.style.height;
  canvas.style.width = "100%";
  canvas.style.height = "100%";
  // Use client dimensions in CSS pixels
  const rect = stage.getBoundingClientRect();
  const st = window.getComputedStyle(stage);
  const padX = (parseFloat(st.paddingLeft) || 0) + (parseFloat(st.paddingRight) || 0);
  const padY = (parseFloat(st.paddingTop) || 0) + (parseFloat(st.paddingBottom) || 0);
  const cssW = Math.max(0, rect.width - padX);
  const cssH = Math.max(0, rect.height - padY);
  const cols = Math.max(40, Math.floor(cssW / state.cellW));
  const rows = Math.max(20, Math.floor(cssH / state.cellH));
  const prevCols = state.cols;
  const prevRows = state.rows;
  state.cols = cols; state.rows = rows;
  const dpr = Math.max(1, Math.floor(window.devicePixelRatio || 1));
  // Set CSS size
  const cssWidthPx = cols * state.cellW;
  const cssHeightPx = rows * state.cellH;
  if (canvas.style.width !== `${cssWidthPx}px`) canvas.style.width = `${cssWidthPx}px`;
  if (canvas.style.height !== `${cssHeightPx}px`) canvas.style.height = `${cssHeightPx}px`;
  // Set backing store size in device pixels
  const backingW = cssWidthPx * dpr;
  const backingH = cssHeightPx * dpr;
  if (canvas.width !== backingW) canvas.width = backingW;
  if (canvas.height !== backingH) canvas.height = backingH;
  applyHiDPIScale();
  // Only notify backend if grid size actually changed
  if ((cols !== prevCols || rows !== prevRows) && window.pyodide) {
    window.pyodide.runPython(`from asciiquarium_redux import web_backend; web_backend.web_app.resize(${cols}, ${rows})`);
  }
}
function scheduleResize() {
  if (resizeTimer) clearTimeout(resizeTimer);
  // Debounce to coalesce rapid layout changes
  resizeTimer = setTimeout(() => {
    resizeTimer = null;
    const r = stage.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) {
      resizeCanvasToGrid();
    }
  }, 100);
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
  // Measure cell metrics for a stable grid, but re-measure if font size changes (mobile)
  function updateCellMetrics() {
    const font = getAquariumFont();
    const style = window.getComputedStyle(canvas);
    const fontSize = style.fontSize;
    if (lastFontSize !== fontSize) {
      const m = measureCell(font);
      state.cellW = Math.round(m.w);
      state.cellH = Math.round(m.h);
      lastFontSize = fontSize;
    }
  }
  updateCellMetrics();
  // Apply initial layout
  resizeCanvasToGrid();

  // On resize/orientation change, re-measure font and grid
  window.addEventListener("resize", () => {
    updateCellMetrics();
    resizeCanvasToGrid();
  });
  window.addEventListener("orientationchange", () => {
    updateCellMetrics();
    resizeCanvasToGrid();
  });
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
  // Observe canvas box size and window resize; debounce like Tk runner
  const ro = new ResizeObserver(() => scheduleResize());
  ro.observe(stage);
  window.addEventListener("resize", scheduleResize);

  // Settings dialog open/close
  settingsBtn?.addEventListener("click", () => {
    if (!settingsDialog.open) {
      try { settingsDialog.showModal(); } catch { settingsDialog.show(); }
    } else {
      settingsDialog.close();
      settingsBtn.focus();
    }
  });
  // About dialog toggle + lazy load README on first open
  let aboutLoaded = false;
  async function ensureAboutLoaded() {
    if (aboutLoaded) return;
    try {
      // Try local paths first (dev server), then fallback to GitHub raw (Pages)
      const candidates = [
        './README.md', 'README.md', '../README.md', '../../README.md',
        'https://raw.githubusercontent.com/cognitivegears/asciiquarium_redux/main/README.md'
      ];
      let md = null;
      for (const url of candidates) {
        try {
          const r = await fetch(url, { cache: 'no-store' });
          if (r.ok) { md = await r.text(); break; }
        } catch {}
      }
      if (!md) throw new Error('README not found');
      // Minimal markdown to HTML converter for headings, lists, code blocks; keep it simple
      const html = renderMarkdownBasic(md);
      aboutContent.innerHTML = html;
      aboutLoaded = true;
    } catch (e) {
      aboutContent.textContent = 'Failed to load README.';
    }
  }
  aboutBtn?.addEventListener("click", async () => {
    if (!aboutDialog.open) {
      await ensureAboutLoaded();
      try { aboutDialog.showModal(); } catch { aboutDialog.show(); }
    } else {
      aboutDialog.close();
      aboutBtn.focus();
    }
  });
  closeAbout?.addEventListener("click", () => aboutDialog.close());
  closeSettings?.addEventListener("click", () => settingsDialog.close());
  requestAnimationFrame(loop);
}

function collectOptionsFromUI() {
  const byId = (id) => document.getElementById(id);
  const num = (id) => Number(byId(id).value);
  const val = (id) => byId(id).value;
  const chk = (id) => byId(id).checked;
  return {
    // Basics
    fps: num("fps"),
    speed: num("speed"),
    density: num("density"),
    color: val("color"),
    seed: val("seed") || null,
    chest: chk("chest"),
  castle: chk("castle"),
    turn: chk("turn"),
    // Fish
    fish_direction_bias: num("fish_direction_bias"),
    fish_speed_min: num("fish_speed_min"),
    fish_speed_max: num("fish_speed_max"),
    fish_scale: num("fish_scale"),
    // Seaweed
    seaweed_scale: num("seaweed_scale"),
  seaweed_sway_min: num("seaweed_sway_min"),
  seaweed_sway_max: num("seaweed_sway_max"),
    // Scene & spawn
    waterline_top: num("waterline_top"),
    chest_burst_seconds: num("chest_burst_seconds"),
    spawn_start_delay_min: num("spawn_start_delay_min"),
    spawn_start_delay_max: num("spawn_start_delay_max"),
    spawn_interval_min: num("spawn_interval_min"),
    spawn_interval_max: num("spawn_interval_max"),
    spawn_max_concurrent: num("spawn_max_concurrent"),
    spawn_cooldown_global: num("spawn_cooldown_global"),
    w_shark: num("w_shark"),
    w_fishhook: num("w_fishhook"),
    w_whale: num("w_whale"),
    w_ship: num("w_ship"),
    w_ducks: num("w_ducks"),
    w_dolphins: num("w_dolphins"),
    w_swan: num("w_swan"),
    w_monster: num("w_monster"),
    w_big_fish: num("w_big_fish"),
  // Fishhook
  fishhook_dwell_seconds: num("fishhook_dwell_seconds")
  };
}

  [
    // basics
  "fps","speed","density","color","chest","castle","turn","seed",
    // fish
  "fish_direction_bias","fish_speed_min","fish_speed_max","fish_scale",
    // seaweed
  "seaweed_scale","seaweed_sway_min","seaweed_sway_max",
    // scene & spawn
    "waterline_top","chest_burst_seconds","spawn_start_delay_min","spawn_start_delay_max","spawn_interval_min","spawn_interval_max",
    "spawn_max_concurrent","spawn_cooldown_global","w_shark","w_fishhook","w_whale","w_ship","w_ducks","w_dolphins","w_swan","w_monster","w_big_fish",
    // fishhook
    "fishhook_dwell_seconds"
  ].forEach(id => {
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

// Accordion: only one details group open at a time
document.querySelectorAll('.controls details.group').forEach((d) => {
  d.addEventListener('toggle', () => {
    if (d.open) {
      document.querySelectorAll('.controls details.group').forEach((other) => {
        if (other !== d) other.open = false;
      });
    }
  });
});

boot();

// Very small markdown renderer (headings, code blocks, inline code, paragraphs, links, lists)
function renderMarkdownBasic(md) {
  // Strip top badges row if present to keep dialog compact
  md = md.replace(/^\s*\[!\[.*\n/, '');
  const lines = md.split(/\r?\n/);
  const out = [];
  let inCode = false;
  let listOpen = false;
  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];
    if (line.startsWith('```')) {
      if (!inCode) { out.push('<pre><code>'); inCode = true; }
      else { out.push('</code></pre>'); inCode = false; }
      continue;
    }
    if (inCode) { out.push(escapeHtml(line) + '\n'); continue; }
    if (/^\s*#\s+/.test(line)) { out.push(`<h1>${escapeHtml(line.replace(/^\s*#\s+/, ''))}</h1>`); continue; }
    if (/^\s*##\s+/.test(line)) { out.push(`<h2>${escapeHtml(line.replace(/^\s*##\s+/, ''))}</h2>`); continue; }
    if (/^\s*###\s+/.test(line)) { out.push(`<h3>${escapeHtml(line.replace(/^\s*###\s+/, ''))}</h3>`); continue; }
    if (/^\s*[-*]\s+/.test(line)) {
      if (!listOpen) { out.push('<ul>'); listOpen = true; }
      out.push(`<li>${inlineMd(line.replace(/^\s*[-*]\s+/, ''))}</li>`);
      // If next line isn’t a list item, close
      const next = lines[i+1] || '';
      if (!/^\s*[-*]\s+/.test(next)) { out.push('</ul>'); listOpen = false; }
      continue;
    }
    if (/^\s*$/.test(line)) { out.push(''); continue; }
    out.push(`<p>${inlineMd(line)}</p>`);
  }
  return out.join('\n');
}
function inlineMd(s) {
  // links [text](url)
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1<\/a>');
  // inline code
  s = s.replace(/`([^`]+)`/g, '<code>$1<\/code>');
  return escapeHtmlPreserveTags(s);
}
function escapeHtml(s) {
  return s.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
}
function escapeHtmlPreserveTags(s) {
  return s.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])).replace(/&lt;(\/?)(a|code|pre|h1|h2|h3|ul|li)&gt;/g, '<$1$2>');
}
