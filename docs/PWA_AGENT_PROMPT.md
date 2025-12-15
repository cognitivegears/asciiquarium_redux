# Agentic Prompt: Make the Web Backend an Installable Progressive Web App (PWA)

You are an expert full‑stack engineer. Convert the Asciiquarium Redux web frontend into a standards‑compliant Progressive Web App (PWA) that users can install via an explicit “Install App” button. Produce minimal, surgical diffs that preserve existing behavior and styles.

Context

- Web assets are in `asciiquarium_redux/web/` (`index.html`, `app.js`, `styles.css`, `wheels/`).
- Deployment is via GitHub Pages task, publishing `asciiquarium_redux/web/` to `gh-pages` (HTTPS; `.nojekyll` present).
- The app runs in-browser with Pyodide; local wheels are under `web/wheels/`, with PyPI fallback.

Authoritative reference to follow

- Read and use: [Build a PWA from scratch with HTML, CSS, and JavaScript](https://www.freecodecamp.org/news/build-a-pwa-from-scratch-with-html-css-and-javascript) for the manifest, service worker, offline caching, and installability flow.

## Mission

Ship a reliable, installable PWA with offline capability and a visible “Install App” button, with no regressions to the aquarium simulation.

## Deliverables

- New files:
  - `asciiquarium_redux/web/manifest.webmanifest`
  - `asciiquarium_redux/web/service-worker.js`
  - `asciiquarium_redux/web/icons/` (PNG: 192×192, 512×512, plus maskable 512×512)
- Modified files:
  - `asciiquarium_redux/web/index.html` (link manifest, theme meta, install button UI)
  - `asciiquarium_redux/web/app.js` (SW registration, install button logic)
  - `asciiquarium_redux/web/styles.css` (minimal styling for install UI, if needed)
- Docs: brief PWA notes added to `docs/WEB_DEPLOYMENT.md` (how to test, cache busting).

## Functional requirements

### 1. Web App Manifest

- Create `manifest.webmanifest`:
  - `name`, `short_name`, `description`
  - `start_url: "./"`, `scope: "./"`, `display: "standalone"`
  - `theme_color`, `background_color`, `orientation: "landscape"` (preferred)
  - `categories` (e.g., `entertainment`)
- Icons:
  - PNG 192×192 and 512×512, plus a `purpose: "maskable"` (512×512) icon
  - Place under `asciiquarium_redux/web/icons/` and reference with relative `./icons/...` paths
- In `index.html`:
  - `<link rel="manifest" href="./manifest.webmanifest">`
  - `<meta name="theme-color" content="#0b3d91">` (choose an appropriate project color)
- iOS support in `index.html`:
  - `<link rel="apple-touch-icon" href="./icons/icon-192.png">` (and 512 if desired)
  - `<meta name="apple-mobile-web-app-capable" content="yes">`
  - `<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">`

### 2. Service worker and offline

- Create `service-worker.js` at web root to control scope `./` on GitHub Pages.
- Precache on `install` at minimum:
  - `index.html`, `styles.css`, `app.js`, `manifest.webmanifest`, icons directory
  - Essential local wheel/WASM assets in `web/wheels/` (explicit list). Version the cache.
- Fetch strategy:
  - Navigation: network‑first with offline fallback to `index.html` (SPA behavior)
  - Static shell: cache‑first
  - Third‑party/network assets (e.g., PyPI/CDN): network‑first or stale‑while‑revalidate with graceful failures
- Lifecycle:
  - On `activate`, remove old caches
  - Use a `CACHE_VERSION` to bust caches per release
  - Optionally use `self.skipWaiting()` and `clients.claim()` and notify clients to reload when updated

### 3. Install button (A2HS)

- Add an “Install App” button to `index.html`, hidden by default and accessible (ARIA label, keyboard focusable).
- In `app.js`:
  - Handle `beforeinstallprompt`: `preventDefault()`, stash the event, reveal the button
  - On click: call `prompt()`; handle the user choice; hide the button afterward
  - Listen for `appinstalled` to log and hide the button
- iOS fallback:
  - If `beforeinstallprompt` is unavailable, show a small dismissible tip: “Use Share → Add to Home Screen” when not in standalone

### 4. Registration and scope

- Register `./service-worker.js` from `app.js` when supported and HTTPS/localhost.
- Ensure `start_url` and `scope` in the manifest match GH Pages root deployment.

### 5. UX and behavior

- In standalone display mode, optionally tweak UI with `(display-mode: standalone)` or `navigator.standalone`.
- The aquarium must load and run offline after the first successful visit.
- No changes to simulation logic or performance characteristics.

### 6. Build/deploy integration

- Ensure the GitHub Pages deploy task includes manifest, service worker, and icons.
- Keep `.nojekyll` in place.
- Only static assets; no server changes.

### 7. Testing and validation

- Validate installability in Chrome/Edge (desktop and mobile) and verify iOS A2HS flow.
- Run Lighthouse PWA audits and address issues until Installable and Offline pass.
- Manually test offline (disable network, reload) and confirm the app starts and renders.
- Verify SW update behavior and cache invalidation without breaking existing users.

### 8. Non‑goals

- Do not add push notifications, background sync, or periodic background fetch.
- Avoid extra tooling (e.g., Workbox) unless strictly necessary; prefer a small, readable SW.

## Constraints and conventions

- Keep diffs minimal; follow existing code style and structure.
- Do not break the Pyodide bootstrap; precache only essential local wheels and allow network fallback.
- Honor scene/fish‑tank settings; do not change simulation behavior.
- Respect the web backend conventions in `asciiquarium_redux/backend/web/` and documented UI flows.

## Implementation plan

1. Manifest and icons

- Create `manifest.webmanifest` with correct metadata and icon entries
- Add manifest `<link>` and theme color `<meta>` to `index.html`
- Add iOS apple‑touch‑icons and iOS display meta tags

2. Service worker

- Create `service-worker.js` with versioned cache names
- Precache shell, icons, manifest, and essential wheels (explicit list)
- Add fetch handler: nav fallback to `index.html`; cache‑first for shell; SWR or network‑first for dynamic
- Activate handler to clean old caches; consider `skipWaiting()` and `clients.claim()`

3. Install button

- Add hidden button in `index.html` (e.g., `id="install-btn"`)
- In `app.js`: wire `beforeinstallprompt`, `appinstalled`, and click flows; include iOS hint logic

4. Register SW

- In `app.js`, register `./service-worker.js` on HTTPS/localhost

5. Test and validate

- Run locally via `uv run python main.py --backend web --open`
- Inspect DevTools → Application → Service Workers
- Run Lighthouse PWA audits and fix issues

6. Deploy

- Use the existing “Deploy web to GitHub Pages” task
- Verify installability and offline behavior on the live site

## Edge cases

- First visit fully offline: show a friendly fallback (after first successful visit, cache `index.html`; optionally add `offline.html`).
- SW update loop: avoid aggressive page reloads; prompt once, then refresh.
- GH Pages pathing: use relative URLs (`./...`) for assets and SW registration.
- Cross‑origin failures (PyPI/CDN): handle gracefully without breaking the app shell.

## Acceptance criteria

- Lighthouse PWA “Installable” audit passes.
- The app installs and launches standalone with correct icon and theme color.
- Core features run offline after first successful visit.
- The install button appears when eligible, prompts install, and hides after outcome.
- No regressions in simulation behavior or performance.

## Output

- List of files created/modified with a short rationale for each.
- Lighthouse results summary and manual test notes (Chrome, Edge, iOS Safari).
- Short addition to `docs/WEB_DEPLOYMENT.md` on PWA testing and cache busting.
# Agent Prompt: Transform Asciiquarium Redux Web Backend into an Installable Progressive Web App (PWA)

You are an expert full‑stack engineer tasked with converting the Asciiquarium Redux web frontend into a standards‑compliant Progressive Web App (PWA) that users can install via an explicit “Install App” button. Deliver all functional requirements below with minimal, surgical diffs and keep styles, signatures, and existing behavior stable.

Repository context:

- Web assets live in `asciiquarium_redux/web/` (`index.html`, `app.js`, `styles.css`, `wheels/`).
- Deployed to GitHub Pages via the provided task, publishing `asciiquarium_redux/web/` to the repository root of the `gh-pages` branch (HTTPS served, `.nojekyll` present).
- The app runs in-browser via Pyodide; local wheels are in `web/wheels/`, with fallback to PyPI when needed.

Primary reference for PWA implementation:

- Read and follow: [Build a PWA from scratch with HTML, CSS, and JavaScript](https://www.freecodecamp.org/news/build-a-pwa-from-scratch-with-html-css-and-javascript) for concepts and step-by-step guidance (manifest, service worker, offline caching, installability).

## Mission

Ship a reliable, installable PWA experience for the web backend with offline capability, proper app metadata, and an install button, without regressing current features.

## Deliverables

- New files (at minimum):
- `asciiquarium_redux/web/manifest.webmanifest`
- `asciiquarium_redux/web/service-worker.js`
- `asciiquarium_redux/web/icons/` (PNG set including 192×192, 512×512, and a maskable 512×512)
- Modified files:
- `asciiquarium_redux/web/index.html` (link manifest, theme meta, install UI)
- `asciiquarium_redux/web/app.js` (service worker registration, install button logic)
- `asciiquarium_redux/web/styles.css` (minimal styles for install UI if needed)
- Updated docs: add a short section to `docs/WEB_DEPLOYMENT.md` describing PWA behavior, testing, and cache busting.

## Functional Requirements (must‑have)

### 1. Web App Manifest

- Create `manifest.webmanifest` with:
- `name`, `short_name`, `description`
- `start_url: "./"`, `scope: "./"`, `display: "standalone"`
- `theme_color`, `background_color`, `orientation: "landscape"` (preferred)
- `categories` (e.g., `entertainment`)
- Provide icons:
- 192×192 and 512×512 PNGs, plus a `purpose: "maskable"` variant (e.g., 512×512)
- Place under `asciiquarium_redux/web/icons/` and reference correct relative paths
- In `index.html` add:
- `<link rel="manifest" href="./manifest.webmanifest">`
- `<meta name="theme-color" content="#0b3d91">` (choose a project-appropriate color)
- Add iOS support in `index.html`:
- `<link rel="apple-touch-icon" href="./icons/icon-192.png">` (and 512 as needed)
- `<meta name="apple-mobile-web-app-capable" content="yes">`
- `<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">`

### 2. Service Worker: Offline and Performance

- Create `service-worker.js` at the web root to control scope `./` on GitHub Pages.
- Precache the app shell during `install`:
- `index.html`, `styles.css`, `app.js`, `manifest.webmanifest`, icons directory
- Include essential local WASM/wheel assets in `web/wheels/` (explicit list) for offline bootstrap; version the cache
- Fetch handling:
- Navigation requests: network-first with offline fallback to `index.html` (SPA)
- Static shell assets: cache-first
- Third-party/network requests (e.g., PyPI/CDN): network-first or stale-while-revalidate with graceful failure
- Lifecycle:
- On `activate`, clean up old caches
- Use a version string to bust caches on release
- Optionally use `self.skipWaiting()` and `clients.claim()` and notify pages to reload when updated

### 3. Install Button (A2HS)

- Add an “Install App” button in `index.html`, hidden by default and accessible (ARIA label, focusable).
- In `app.js`:
- Listen for `beforeinstallprompt`, `preventDefault()`, stash the event, reveal button
- On click, call `prompt()` on the saved event; handle outcome; hide button after
- Listen for `appinstalled` to record install and hide the button
- iOS Safari fallback:
- Detect lack of `beforeinstallprompt`; show a small, dismissible hint: “Use Share → Add to Home Screen” when not already in standalone

### 4. Registration and Scope

- Register the SW from `app.js` when supported and served over HTTPS/localhost.
- Registration path must be `./service-worker.js` so scope covers the site root on GH Pages.
- Ensure `start_url` and `scope` in manifest align with GH Pages deployment path (root).

### 5. UX and Behavior

- In standalone display mode, optionally apply minor UI tweaks using `(display-mode: standalone)` or `navigator.standalone`.
- App must work offline after first visit: the aquarium loads and runs without network.
- Maintain existing rendering and performance; do not alter simulation behavior.

### 6. Build/Deploy Integration

- Ensure the GitHub Pages deploy task publishes manifest, service worker, and icons.
- Keep `.nojekyll` to avoid path rewriting by GH Pages.
- No server-side changes; all PWA features must be static.

### 7. Testing and Validation

- Validate installability in Chrome/Edge (desktop and mobile) and iOS A2HS flow.
- Run Lighthouse PWA audits; resolve issues until Installable and Offline pass.
- Manually test offline: disable network and reload; app should start and render.
- Verify SW update behavior: cache invalidation without breaking current users.

### 8. Non‑Goals (for now)

- Do not add push notifications, background sync, or periodic background fetch.
- Avoid external build tooling (e.g., Workbox) unless strictly necessary; prefer a small handcrafted SW.

## Constraints and Project Conventions

- Keep diffs minimal and surgical; follow existing code style and structure.
- Do not break Pyodide bootstrap; precache essential local wheels and allow network fallback.
- Honor scene/fish‑tank settings; this change must not modify simulation logic.
- Respect the web backend conventions in `asciiquarium_redux/backend/web/` and documented UI flows.

## Implementation Plan (high level)

1. Manifest and Icons

- Create `manifest.webmanifest` with correct metadata and icon entries
- Add link tag and meta theme-color to `index.html`
- Add iOS apple-touch-icon(s) and iOS display meta tags

2. Service Worker

- Create `service-worker.js` with versioned cache names
- Precache shell, icons, manifest, and required local wheels (explicit list)
- Add fetch handler: nav fallback to `index.html`; cache-first for shell; SWR or network-first for dynamic
- Add activate handler to clean old caches; consider `skipWaiting()` and `clients.claim()`

3. Install Button

- Add hidden button in `index.html` (e.g., `id="install-btn"`)
- In `app.js`: wire `beforeinstallprompt`, `appinstalled`, and click flows; include iOS hint logic

4. Register SW

- In `app.js`, register `./service-worker.js` on HTTPS/localhost

5. Test and Validate

- Run locally via `uv run python main.py --backend web --open`
- Use DevTools → Application → Service Workers to inspect registration and caches
- Run Lighthouse PWA audits and address issues

6. Deploy

- Use the existing “Deploy web to GitHub Pages” task
- After deploy, verify installability and offline behavior on the live site

## Edge Cases to Handle

- First visit entirely offline: ensure a friendly fallback (cache `index.html` after first successful visit; optionally include a minimal `offline.html`).
- SW update loop: avoid aggressive reloads; prompt once and then refresh.
- GitHub Pages pathing: use relative URLs (`./...`) for assets and registration.
- Cross-origin fetches (PyPI/CDN): handle failures gracefully; don’t break the app shell.

## Acceptance Criteria

- Lighthouse PWA “Installable” audit passes.
- App can be installed (desktop/mobile) and launches standalone with correct icon and theme color.
- App loads and runs core features offline after first successful visit.
- Install button appears when eligible, triggers the prompt, and hides afterward or when unsupported.
- No regressions in simulation behavior or performance.

## Notes for Implementation

- Use the freeCodeCamp article above for manifest creation, SW registration, caching patterns, and install flow.
- Keep the SW small and readable; add `CACHE_VERSION` and explicit precache lists. Document what’s cached and why.
- Prefer explicit asset lists for precache; include essential `wheels/` artifacts for Pyodide offline use if feasible.
- Provide a small, non-blocking iOS A2HS hint when `beforeinstallprompt` is not available.

## Output Expectations

- Provide the list of files created/modified and a brief rationale for each.
- Summarize Lighthouse results and manual tests across Chrome, Edge, and iOS Safari.
- Add short guidance in `docs/WEB_DEPLOYMENT.md` on PWA testing and cache busting for future releases.
# Agent Prompt: Transform Asciiquarium Redux Web Backend into an Installable Progressive Web App (PWA)

You are an expert full‑stack engineer tasked with converting the Asciiquarium Redux web frontend into a standards‑compliant Progressive Web App (PWA) that users can install via an explicit “Install App” button. You must deliver all functional requirements below with minimal, surgical diffs and keep styles, signatures, and existing behavior stable.

Repository context:

- Web assets live in `asciiquarium_redux/web/` (`index.html`, `app.js`, `styles.css`, `wheels/`).
- Deployed to GitHub Pages via the provided task, publishing `asciiquarium_redux/web/` to the repository root of the `gh-pages` branch (HTTPS served, `.nojekyll` present).
- The app runs in-browser via Pyodide; local wheels are in `web/wheels/`, with fallback to PyPI when needed.

Primary references for PWA implementation:

- Read and follow: [Build a PWA from scratch with HTML, CSS, and JavaScript](https://www.freecodecamp.org/news/build-a-pwa-from-scratch-with-html-css-and-javascript) (overview of manifest, service worker, offline caching, and install flow)

## Mission
Ship a reliable, installable PWA experience for the web backend with offline capability, proper app metadata, and an install button, without regressing current features.

## Deliverables

- `asciiquarium_redux/web/manifest.webmanifest`
- `asciiquarium_redux/web/service-worker.js`
- `asciiquarium_redux/web/icons/` (PNG set including 192×192, 512×512, and maskable variants)
- `asciiquarium_redux/web/index.html` (link manifest, meta, install UI)
- `asciiquarium_redux/web/app.js` (service worker registration, install button logic)
- `asciiquarium_redux/web/styles.css` (minimal styles for install UI if needed)

## Functional Requirements (must‑have)

### 1. Web App Manifest

- 192×192 and 512×512 PNGs, plus a `purpose: maskable` variant (e.g., 512×512).
- Place under `asciiquarium_redux/web/icons/` and reference correct relative paths.

### 2. Service Worker: Offline and Performance

- `index.html`, `styles.css`, `app.js`, `manifest.webmanifest`, icons directory, and a small offline fallback `offline.html` (optional if `index.html` can serve as the fallback).
- Include essential WASM/wheel assets that are served locally under `web/wheels/` (cache by pattern or explicit list); ensure the cache is versioned.
- Serve cached shell assets offline (cache-first) and use network-first or stale-while-revalidate for dynamic/network requests (e.g., PyPI/CDN).
- Provide an offline fallback to `index.html` (SPA approach) if network is unavailable and the request is navigation.
- On activation, cleanup old caches.
- Use a version string to bust caches on release.
- Optionally call `self.skipWaiting()` and `clients.claim()` and notify the page to prompt a reload on updates.

### 3. Install Button (A2HS)

- Listen for `beforeinstallprompt`, prevent default, stash the event, and reveal the button.
- On button click, call `prompt()` on the saved event; handle user choice; hide the button after outcome.
- Listen for `appinstalled` to record install and hide the button.

### 4. Registration and Scope

### 5. UX and Behavior

### 6. Build/Deploy Integration

### 7. Testing and Validation


### 8. Non‑Goals (for now)

## Constraints and Project Conventions

## Implementation Plan (high level)

1. Manifest and Icons

- Create `manifest.webmanifest` with correct metadata and icon entries.
- Add link tag and meta theme-color to `index.html`.
- Add iOS apple-touch-icon(s) and iOS display meta tags.

2. Service Worker

- Create `service-worker.js` with versioned cache names.
- Precache shell, icons, manifest, local wheels (explicit list or glob during build; if static, provide explicit list now).
- Add fetch handler: navigation fallback to `index.html`, cache-first for shell, network-first or stale-while-revalidate for others.
- Add activate handler to cleanup old caches; consider `skipWaiting()` and `clients.claim()`.

3. Install Button

- Add hidden button in `index.html` (e.g., `id="install-btn"`).
- In `app.js`: wire `beforeinstallprompt`, `appinstalled`, and click flows; include iOS fallback tip logic.

4. Register SW

- In `app.js`, register `./service-worker.js` when supported and served over HTTPS/localhost.

5. Test and Validate

- Run locally via `uv run python main.py --backend web --open` (localhost qualifies for SW).
- Use DevTools → Application → Service Workers to inspect registration, caches, and offline behavior.
- Run Lighthouse PWA audits and address issues until “Installable” and “Offline” pass.

6. Deploy

- Use the existing “Deploy web to GitHub Pages” task.
- Post-deploy: verify installability and offline behavior on the live site.

## Edge Cases to Handle

## Acceptance Criteria

## Notes for Implementation

## Output Expectations

- Provide short guidance in `docs/WEB_DEPLOYMENT.md` on PWA testing and cache busting for future releases.
