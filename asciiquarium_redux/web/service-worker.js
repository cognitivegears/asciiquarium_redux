/* Simple, versioned service worker for Asciiquarium Redux (GitHub Pages scope: ./) */
const CACHE_VERSION = 'v1';
const CACHE_NAME = `asciiquarium-cache-${CACHE_VERSION}`;
const APP_SHELL = [
  './',
  './index.html',
  './styles.css',
  './app.js',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  // Wheels manifest and a default wheel alias; individual wheels may be large, keep list small
  './wheels/manifest.json',
  './wheels/asciiquarium_redux-latest.whl'
];

// 1x1 transparent PNG (base64)
const PNG_1x1_BASE64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5nF9kAAAAASUVORK5CYII=';
function transparentPngResponse() {
  const bytes = Uint8Array.from(atob(PNG_1x1_BASE64), c => c.charCodeAt(0));
  return new Response(bytes, { headers: { 'Content-Type': 'image/png', 'Cache-Control': 'public, max-age=31536000, immutable' } });
}

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).catch(() => {})
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map((k) => (k !== CACHE_NAME ? caches.delete(k) : undefined)));
    await self.clients.claim();
  })());
});

function isNavigationRequest(request) {
  return request.mode === 'navigate' || (request.method === 'GET' && request.headers.get('accept')?.includes('text/html'));
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  // Special-case icons: serve embedded placeholders if not present on disk
  if (url.origin === location.origin && url.pathname.startsWith('/icons/') && url.pathname.match(/icon-(192|512|maskable-512)\.png$/)) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      const cached = await cache.match(request);
      if (cached) return cached;
      // Try network first (if actual files exist), else fallback to embedded
      try {
        const resp = await fetch(request);
        if (resp.ok) {
          cache.put(request, resp.clone());
          return resp;
        }
      } catch {}
      const resp = transparentPngResponse();
      cache.put(request, resp.clone());
      return resp;
    })());
    return;
  }

  // Handle jsDelivr Pyodide assets with stale-while-revalidate for offline resilience
  if (url.hostname.includes('cdn.jsdelivr.net') && url.pathname.includes('/pyodide/')) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      const cached = await cache.match(request);
      const fetchPromise = fetch(request).then((resp) => {
        cache.put(request, resp.clone());
        return resp;
      }).catch(() => undefined);
      return cached || fetchPromise || fetch(request);
    })());
    return;
  }

  // Only handle same-origin beyond this point
  if (url.origin !== location.origin) return;

  // Navigation: network-first, fallback to cached index.html
  if (isNavigationRequest(request)) {
    event.respondWith((async () => {
      try {
        const resp = await fetch(request);
        // Optionally, update cached index.html
        const cache = await caches.open(CACHE_NAME);
        cache.put('./index.html', resp.clone());
        return resp;
      } catch (e) {
        const cache = await caches.open(CACHE_NAME);
        const cached = await cache.match('./index.html');
        if (cached) return cached;
        return new Response('<h1>Offline</h1>', { headers: { 'Content-Type': 'text/html' }, status: 200 });
      }
    })());
    return;
  }

  // App shell static: cache-first
  if (APP_SHELL.some((p) => url.pathname.endsWith(p.replace('./', '/')))) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      const cached = await cache.match(request);
      if (cached) return cached;
      try {
        const resp = await fetch(request);
        cache.put(request, resp.clone());
        return resp;
      } catch (e) {
        return cached || Response.error();
      }
    })());
    return;
  }

  // Default strategy: stale-while-revalidate
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);
    const fetchPromise = fetch(request).then((resp) => {
      cache.put(request, resp.clone());
      return resp;
    }).catch(() => undefined);
    return cached || fetchPromise || fetch(request);
  })());
});
