from __future__ import annotations

import signal
import sys
import time
import tkinter as tk
from tkinter import font as tkfont
from typing import Any, cast

from ...screen_compat import Screen
from ...app import AsciiQuarium
from ...util import sprite_size
from ...entities.environment import CASTLE, WATER_SEGMENTS
from ..term import TkRenderContext, TkEventStream


class ScreenShim:
    """Minimal Screen-like adapter that exposes width, height and print_at.

    We import asciimatics.Screen only for colour constants; this shim never refreshes,
    TkRenderContext handles buffer flushing.
    """

    def __init__(self, ctx: TkRenderContext):
        self._ctx = ctx

    @property
    def width(self) -> int:
        return self._ctx.size()[0]

    @property
    def height(self) -> int:
        return self._ctx.size()[1]

    def print_at(self, text: str, x: int, y: int, colour: int | None = None, *args: Any, **kwargs: Any) -> None:
        """Print text at specific coordinates."""
        self._ctx.print_at(text, x, y, colour)


def run_tk(settings) -> None:
    # Window setup
    root = tk.Tk()
    root.title("Asciiquarium Redux")
    MIN_CELL_H = 7  # Allow smaller fonts on very short windows
    # Determine cell size from font; optionally auto-scale font to fit minimum rows
    family = getattr(settings, "ui_font_family", "Menlo")
    req_size = int(getattr(settings, "ui_font_size", 14))
    fnt = tkfont.Font(family=family, size=req_size)
    cell_w = max(8, int(fnt.measure("W")))
    cell_h = max(MIN_CELL_H, int(fnt.metrics("linespace")))
    cols = int(getattr(settings, "ui_cols", 120))
    rows = int(getattr(settings, "ui_rows", 40))

    # Compute a dynamic minimum rows requirement so all key elements fit.
    # total_needed = air (waterline_top) + water rows + tallest decor/special + bottom margin
    castle_h = sprite_size(CASTLE)[1]
    tallest_special_h = castle_h  # currently castle is the tallest element we must fit
    min_rows_required = int(getattr(settings, "waterline_top", 5)) + len(WATER_SEGMENTS) + tallest_special_h + 2
    target_rows = max(rows, min_rows_required)

    # If auto font is enabled, try to ensure at least target rows based on current screen height
    if getattr(settings, "ui_font_auto", True):
        try:
            # Use the monitor's available height for the initial window if not fullscreen
            screen_h_px = root.winfo_screenheight()
            # Reserve a bit of margin for window chrome (titlebar etc.)
            chrome_px = 64
            max_cell_h = max(10, (screen_h_px - chrome_px) // target_rows)
            # Binary search a font size that gives cell_h <= max_cell_h
            lo, hi = 4, max(10, req_size * 2)
            best = req_size
            while lo <= hi:
                mid = (lo + hi) // 2
                test = tkfont.Font(family=family, size=mid)
                th = max(MIN_CELL_H, int(test.metrics("linespace")))
                if th <= max_cell_h:
                    best = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
            if best != req_size:
                fnt = tkfont.Font(family=family, size=best)
                cell_w = max(8, int(fnt.measure("W")))
                cell_h = max(MIN_CELL_H, int(fnt.metrics("linespace")))
        except Exception:
            pass
    canvas = tk.Canvas(root, width=cols * cell_w, height=rows * cell_h, bg="black", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Expose cell size for event conversion
    root._cell_w = cell_w  # type: ignore[attr-defined]
    root._cell_h = cell_h  # type: ignore[attr-defined]

    if getattr(settings, "ui_fullscreen", False):
        root.attributes("-fullscreen", True)

    ctx = TkRenderContext(root, canvas, cols, rows, cell_w, cell_h, font=fnt)
    screen = ScreenShim(ctx)
    events = TkEventStream(root)
    app = AsciiQuarium(settings)
    app.rebuild(screen)  # type: ignore[arg-type]

    # SIGINT (Ctrl-C) handling: set a flag and let the tick loop exit cleanly.
    stop_requested = False

    def _on_sigint(_signum: int, _frame: Any) -> None:  # type: ignore[override]
        nonlocal stop_requested
        stop_requested = True

    def _install_signal(sig: int) -> None:
        try:
            signal.signal(sig, _on_sigint)
        except Exception:
            pass

    _install_signal(getattr(signal, "SIGINT", None) or signal.SIGINT)
    if hasattr(signal, "SIGTERM"):
        _install_signal(signal.SIGTERM)
    if hasattr(signal, "SIGHUP"):
        _install_signal(signal.SIGHUP)

    # Suppress noisy tracebacks from Tk callbacks on KeyboardInterrupt
    def _report_callback_exception(exc, val, tb):  # type: ignore[no-redef]
        if exc is KeyboardInterrupt or isinstance(val, KeyboardInterrupt):
            try:
                root.destroy()
            except Exception:
                pass
            return
        # Defer to default excepthook for other exceptions
        sys.__excepthook__(exc, val, tb)

    try:
        root.report_callback_exception = _report_callback_exception  # type: ignore[attr-defined]
    except Exception:
        pass

    last = time.time()
    frame_no = 0
    target_dt = 1.0 / max(1, settings.fps)

    resize_job: str | None = None

    def _schedule_resize() -> None:
        nonlocal resize_job
        if resize_job is not None:
            try:
                root.after_cancel(resize_job)
            except Exception:
                pass
        resize_job = root.after(120, _do_resize)

    def _do_resize() -> None:
        nonlocal resize_job, fnt, cell_w, cell_h
        resize_job = None
        # Use current canvas size in pixels
        w = max(1, int(canvas.winfo_width()))
        h = max(1, int(canvas.winfo_height()))
        # If auto font is enabled, reduce font size if needed so target_rows fit vertically
        if getattr(settings, "ui_font_auto", True):
            # Recompute target rows in case settings changed at runtime
            _castle_h = sprite_size(CASTLE)[1]
            _target_rows = max(int(getattr(settings, "ui_rows", 40)), int(getattr(settings, "waterline_top", 5)) + len(WATER_SEGMENTS) + _castle_h + 2)
            max_cell_h_now = max(6, h // max(1, _target_rows))
            if cell_h > max_cell_h_now:
                # Find the largest font size whose measured height <= max_cell_h_now
                lo, hi = 4, int(fnt.cget("size"))
                best_size = int(fnt.cget("size"))
                while lo <= hi:
                    mid = (lo + hi) // 2
                    test = tkfont.Font(family=family, size=mid)
                    th = max(MIN_CELL_H, int(test.metrics("linespace")))
                    if th <= max_cell_h_now:
                        best_size = mid
                        lo = mid + 1
                    else:
                        hi = mid - 1
                if best_size != int(fnt.cget("size")):
                    # Apply new font metrics
                    new_font = tkfont.Font(family=family, size=best_size)
                    new_cell_w = max(8, int(new_font.measure("W")))
                    new_cell_h = max(MIN_CELL_H, int(new_font.metrics("linespace")))
                    # Update globals and context
                    root._cell_w = new_cell_w  # type: ignore[attr-defined]
                    root._cell_h = new_cell_h  # type: ignore[attr-defined]
                    ctx.cell_w = new_cell_w
                    ctx.cell_h = new_cell_h
                    ctx.font = new_font
                    # Clear all existing text items to avoid mixed-font artifacts
                    try:
                        canvas.delete("all")
                        ctx._text_ids.clear()  # type: ignore[attr-defined]
                    except Exception:
                        pass
                    # Overwrite captured variables for subsequent calculations
                    fnt = new_font
                    cell_w = new_cell_w
                    cell_h = new_cell_h
        new_cols = max(1, w // cell_w)
        new_rows = max(1, h // cell_h)
        if new_cols != ctx.cols or new_rows != ctx.rows:
            ctx.resize(new_cols, new_rows)
            # Snap canvas to exact grid size to keep alignment crisp
            cw = new_cols * cell_w
            ch = new_rows * cell_h
            if cw != w or ch != h:
                canvas.config(width=cw, height=ch)
            app.rebuild(screen)  # type: ignore[arg-type]

    # Listen to canvas size changes (layout or user resize)
    canvas.bind("<Configure>", lambda _e: _schedule_resize())
    # Kick an immediate resize pass so we reflect the current window size ASAP
    root.after(0, _schedule_resize)

    def tick() -> None:
        nonlocal last, frame_no
        now = time.time()
        dt = min(0.1, now - last)
        last = now

        # Respect Ctrl-C requests
        if stop_requested:
            try:
                root.destroy()
            finally:
                return

        # Handle events
        for ev in events.poll():
            from ..term import KeyEvent as KEv, MouseEvent as MEv
            if isinstance(ev, KEv):
                k = ev.key
                if k in ("q", "Q"):
                    root.destroy()
                    return
                if k in ("p", "P"):
                    app._paused = not app._paused
                if k in ("r", "R"):
                    app.rebuild(screen)  # type: ignore[arg-type]
                if k in ("h", "H", "?"):
                    app._show_help = not app._show_help
                if k in ("s", "S"):
                    # Save a screenshot of the canvas area into the current directory
                    import os
                    def _next_png_name() -> str:
                        i = 1
                        while True:
                            name = f"asciiquarium_{i}.png"
                            if not os.path.exists(name):
                                return name
                            i += 1
                    out_png = _next_png_name()
                    try:
                        from PIL import ImageGrab  # type: ignore
                        x0 = canvas.winfo_rootx()
                        y0 = canvas.winfo_rooty()
                        x1 = x0 + canvas.winfo_width()
                        y1 = y0 + canvas.winfo_height()
                        img = ImageGrab.grab(bbox=(x0, y0, x1, y1))
                        img.save(out_png)
                        print(f"Saved screenshot to {out_png}")
                    except Exception as e:
                        # Fallback: PostScript dump (requires external conversion)
                        base = os.path.splitext(out_png)[0]
                        out_ps = f"{base}.ps"
                        try:
                            canvas.postscript(file=out_ps, colormode='color')
                            print(f"Saved PostScript screenshot to {out_ps} (convert to PNG with Ghostscript)")
                        except Exception as e2:
                            print(f"Screenshot failed: {e} / {e2}")
                if k == " ":
                    from ...entities.specials import FishHook, spawn_fishhook
                    hooks = [a for a in app.specials if isinstance(a, FishHook) and a.active]
                    if hooks:
                        for h in hooks:
                            if hasattr(h, "retract_now"):
                                h.retract_now()
                    else:
                        app.specials.extend(spawn_fishhook(screen, app))  # type: ignore[arg-type]
            elif isinstance(ev, MEv):
                # Mouse event
                if ev.button == 1:
                    click_x = int(getattr(ev, "x", 0))
                    click_y = int(getattr(ev, "y", 0))
                    water_top = settings.waterline_top
                    if water_top + 1 <= click_y <= screen.height - 2:
                        from ...entities.specials import FishHook, spawn_fishhook_to
                        hooks = [a for a in app.specials if isinstance(a, FishHook) and a.active]
                        if hooks:
                            for h in hooks:
                                if hasattr(h, "retract_now"):
                                    h.retract_now()
                        else:
                            app.specials.extend(spawn_fishhook_to(screen, app, click_x, click_y))  # type: ignore[arg-type]
        try:
            ctx.clear()
            app.update(dt, cast(Screen, screen), frame_no)
            ctx.flush()
        except KeyboardInterrupt:
            # Graceful shutdown on Ctrl-C during a frame
            try:
                root.destroy()
            finally:
                return
        frame_no += 1

        # Schedule next frame
        elapsed = time.time() - now
        delay_ms = max(0, int((target_dt - elapsed) * 1000))
        root.after(delay_ms, tick)

    def _activate() -> None:
        try:
            root.deiconify()
            root.lift()
            root.focus_force()
            # Briefly set always-on-top so the window comes to front, then disable
            root.attributes("-topmost", True)
            root.after(300, lambda: root.attributes("-topmost", False))
        except Exception:
            pass

    root.after(0, _activate)
    root.after(0, tick)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        # If SIGINT arrives outside our tick, exit quietly.
        pass
