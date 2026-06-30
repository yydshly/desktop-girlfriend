"""Probe the Live2D desktop shell launch readiness."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.ui.desktop_presence import (
    build_live2d_desktop_shell_spec,
    render_live2d_shell_summary,
)
from app.ui.live2d_desktop_window import probe_live2d_desktop_dependencies


def main() -> int:
    """Print launch readiness for the Live2D desktop shell."""

    spec = build_live2d_desktop_shell_spec(PROJECT_ROOT, devtools_enabled=True)
    status = probe_live2d_desktop_dependencies()

    print(render_live2d_shell_summary(spec))
    print(f"source: {spec.source_url}")
    print(f"dependencies: {status.detail}")
    print("launch: python -m app.live2d_desktop")

    return 0 if status.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
