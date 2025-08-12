"""Web (Pyodide/Canvas) backend package."""

from .web_backend import web_app, set_js_flush_hook, WebApp  # re-export convenience

__all__ = ["web_app", "set_js_flush_hook", "WebApp"]
