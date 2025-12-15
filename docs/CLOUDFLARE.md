# Cloudflare setup for asciifi.sh

This repo is deployed to GitHub Pages (gh-pages branch) and served at a custom domain via Cloudflare.

## DNS

- Nameservers: Point your registrar to Cloudflare’s nameservers for asciifi.sh.
- Records in Cloudflare DNS:
  - CNAME: Name=@ (apex), Target=cognitivegears.github.io, Proxy=Proxied (orange cloud)
  - Optional: CNAME Name=www, Target=cognitivegears.github.io, Proxy=Proxied

Cloudflare will apply CNAME Flattening at the apex automatically.

## GitHub Pages

- Repository → Settings → Pages:
  - Source: Deploy from branch → gh-pages / root
  - Custom domain: asciifi.sh (Save)
  - Enforce HTTPS: On
- repo contains `asciiquarium_redux/web/CNAME` with the domain `asciifi.sh` to keep the domain pinned on deploy.

## Cache and Rules

You can use Cloudflare Cache Rules (or legacy Page Rules) for a simple setup:

- Rule 1: Bypass cache for HTML (so index.html always refreshes quickly)
  - If URL path matches: `/*`
  - AND Response content type contains: `text/html`
  - Then: Cache: Bypass
- Rule 2: Cache Everything for static assets (CSS, JS, icons, wheels, wasm)
  - If URL path matches: `/*.css`, `/*.js`, `/icons/*`, `/wheels/*`
  - Then: Cache: Eligible for cache; Edge TTL: a week or longer

Notes

- The service worker handles runtime caching and uses a versioned cache name derived from `/wheels/manifest.json`.
- We register the service worker with a `?v=wheelname` suffix so proxy/CDN layers see a new URL when you push a new wheel.

## Optional: Redirect www → apex

- Redirect Rule: If hostname equals `www.asciifi.sh`, then redirect to `https://asciifi.sh/$1` (Status 301).

## Optional: Worker (not required)

If you later want to implement custom proxy logic, a Cloudflare Worker can fetch from `https://cognitivegears.github.io/asciiquarium_redux/` and rewrite paths. For now, DNS+CNAME is sufficient.
