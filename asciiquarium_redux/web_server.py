from __future__ import annotations

import http.server
import os
import json
import socketserver
import webbrowser
from pathlib import Path


from typing import Any


class _WasmHandler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path: Any):
        typ = super().guess_type(path)
        if str(path).endswith('.wasm'):
            return 'application/wasm'
        if str(path).endswith('.whl'):
            return 'application/octet-stream'
        return typ


def serve_web(port: int = 8000, open_browser: bool = True) -> None:
    root = Path(__file__).parent / 'web'
    # Best-effort: place latest local wheel at a stable path for the web app
    try:
        project_root = Path(__file__).resolve().parent.parent
        dist_dir = project_root / 'dist'
        wheels_dir = root / 'wheels'
        wheels_dir.mkdir(parents=True, exist_ok=True)
        if dist_dir.exists():
            wheels = sorted(dist_dir.glob('asciiquarium_redux-*.whl'))
            if wheels:
                latest = wheels[-1]
                target_alias = wheels_dir / 'asciiquarium_redux-latest.whl'
                target_named = wheels_dir / latest.name
                # Copy only if changed to avoid unnecessary I/O
                try:
                    need_copy = (not target_alias.exists()) or (latest.stat().st_mtime_ns != target_alias.stat().st_mtime_ns)
                    if need_copy:
                        data = latest.read_bytes()
                        target_alias.write_bytes(data)
                        target_named.write_bytes(data)
                        # Preserve mtime fingerprint for quick change checks
                        os.utime(str(target_alias), (latest.stat().st_atime, latest.stat().st_mtime))
                        os.utime(str(target_named), (latest.stat().st_atime, latest.stat().st_mtime))
                        # Write a simple manifest with the exact filename
                        manifest = {"wheel": latest.name}
                        (wheels_dir / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
                        print(f"[web] Updated local wheel: {latest.name} -> {target_alias}")
                    else:
                        print(f"[web] Local wheel up-to-date: {target_alias}")
                except Exception:
                    print("[web] Warning: failed to copy latest wheel to web/wheels")
            else:
                print("[web] No dist wheel found; run 'uv build' to enable local install in browser")
    except Exception:
        print("[web] Warning: exception while preparing local wheel; will continue without it")
    class Handler(_WasmHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

    with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
        url = f"http://127.0.0.1:{port}/"
        if open_browser:
            webbrowser.open(url)
        print(f"Serving {root} at {url} (Ctrl+C to stop)")
        httpd.serve_forever()
