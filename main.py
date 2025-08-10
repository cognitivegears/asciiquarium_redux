from __future__ import annotations

# Thin shim delegating to the packaged runner to avoid divergence.
# Keep this for local runs: `python main.py`.

from asciiquarium_redux.runner import main


if __name__ == "__main__":
    main()
