"""Command entrypoint for the Live2D desktop companion shell."""

from __future__ import annotations

from pathlib import Path

from app.ui.desktop_presence import build_live2d_desktop_shell_spec
from app.ui.live2d_desktop_window import run_live2d_desktop_window


def main() -> int:
    """Run the local Live2D prototype as a desktop companion window."""

    workspace_root = Path(__file__).resolve().parents[1]
    spec = build_live2d_desktop_shell_spec(workspace_root)
    return run_live2d_desktop_window(spec)


if __name__ == "__main__":
    raise SystemExit(main())
