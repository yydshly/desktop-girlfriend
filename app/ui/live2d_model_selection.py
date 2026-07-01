"""Persist the user's current Live2D model selection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SELECTION_FILE_NAME = "live2d-model-selection.json"


def default_live2d_model_selection_path() -> Path:
    """Return the default local path for the selected Live2D model id."""

    return Path(".tmp") / _SELECTION_FILE_NAME


def load_selected_live2d_model_id(path: Path) -> str:
    """Load the selected Live2D model id, returning empty string when unavailable."""

    if not path.exists():
        return ""
    try:
        data: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    if not isinstance(data, dict):
        return ""
    model_id = data.get("model_id")
    if not isinstance(model_id, str):
        return ""
    return model_id.strip()


def save_selected_live2d_model_id(path: Path, model_id: str) -> None:
    """Save the selected Live2D model id for the next app launch."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"model_id": model_id.strip()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
