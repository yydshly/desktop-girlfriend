"""Command entrypoint for the Live2D desktop companion shell."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.ui.desktop_presence import build_live2d_desktop_shell_spec
from app.ui.live2d_desktop_window import run_live2d_desktop_window
from app.ui.live2d_model_selection import (
    default_live2d_model_selection_path,
    load_selected_live2d_model_id,
)


def main(argv: list[str] | None = None) -> int:
    """Run the local Live2D prototype as a desktop companion window."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--opacity", type=float, default=1.0)
    parser.add_argument("--model-id", default="")
    args = parser.parse_args(argv)

    workspace_root = Path(__file__).resolve().parents[1]
    model_id = args.model_id.strip() or load_selected_live2d_model_id(
        default_live2d_model_selection_path()
    )
    spec = build_live2d_desktop_shell_spec(
        workspace_root,
        scale=args.scale,
        opacity=args.opacity,
        model_id=model_id,
    )
    return run_live2d_desktop_window(spec)


if __name__ == "__main__":
    raise SystemExit(main())
