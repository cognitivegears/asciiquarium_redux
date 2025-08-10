from __future__ import annotations

import time
import tkinter as tk
from tkinter import font as tkfont
from typing import Any, cast

from asciimatics.screen import Screen

from .app import AsciiQuarium
from .backends import TkRenderContext, TkEventStream


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
        self._ctx.print_at(x, y, text, colour)


def run_tk(settings) -> None:
    # Window setup
    root = tk.Tk()
    root.title("Asciiquarium Redux")
    # Determine cell size from font
    family = getattr(settings, "ui_font_family", "Menlo")
    size = getattr(settings, "ui_font_size", 14)
    fnt = tkfont.Font(family=family, size=size)
    cell_w = max(8, int(fnt.measure("W")))
    cell_h = max(12, int(fnt.metrics("linespace")))
    cols = getattr(settings, "ui_cols", 120)
    rows = getattr(settings, "ui_rows", 40)
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
        nonlocal resize_job
        resize_job = None
        # Use current canvas size in pixels
        w = max(1, int(canvas.winfo_width()))
        h = max(1, int(canvas.winfo_height()))
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
    root.after(0, _schedule_resize)

    def tick() -> None:
        nonlocal last, frame_no
        now = time.time()
        dt = min(0.1, now - last)
        last = now

        # Handle events
        for ev in events.poll():
            from .backends import KeyEvent as KEv, MouseEvent as MEv
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
                    from .entities.specials import FishHook, spawn_fishhook
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
                        from .entities.specials import FishHook, spawn_fishhook_to
                        hooks = [a for a in app.specials if isinstance(a, FishHook) and a.active]
                        if hooks:
                            for h in hooks:
                                if hasattr(h, "retract_now"):
                                    h.retract_now()
                        else:
                            app.specials.extend(spawn_fishhook_to(screen, app, click_x, click_y))  # type: ignore[arg-type]
        ctx.clear()
        app.update(dt, cast(Screen, screen), frame_no)
        ctx.flush()
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
    root.mainloop()
