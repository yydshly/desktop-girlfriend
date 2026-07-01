"""Persist Live2D desktop window runtime settings."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SETTINGS_FILE_NAME = "live2d-desktop-settings.json"
_MIN_SCALE = 0.65
_MAX_SCALE = 1.35
_MIN_OPACITY = 0.45
_MAX_OPACITY = 1.0


@dataclass(frozen=True)
class Live2DDesktopSettings:
    """User-facing runtime settings for the Live2D desktop companion."""

    scale: float = 1.0
    opacity: float = 1.0
    visible: bool = True
    always_on_top: bool = True


def default_live2d_desktop_settings_path() -> Path:
    """Return the default local path for Live2D desktop runtime settings."""

    return Path(".tmp") / _SETTINGS_FILE_NAME


def load_live2d_desktop_settings(path: Path) -> Live2DDesktopSettings:
    """Load persisted Live2D desktop settings, falling back to product defaults."""

    if not path.exists():
        return Live2DDesktopSettings()
    try:
        data: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return Live2DDesktopSettings()
    if not isinstance(data, dict):
        return Live2DDesktopSettings()

    scale = data.get("scale")
    opacity = data.get("opacity")
    visible = data.get("visible")
    always_on_top = data.get("always_on_top", True)
    if not isinstance(scale, int | float) or not isinstance(opacity, int | float):
        return Live2DDesktopSettings()
    if not isinstance(visible, bool):
        return Live2DDesktopSettings()
    if not isinstance(always_on_top, bool):
        return Live2DDesktopSettings()

    return Live2DDesktopSettings(
        scale=_clamp(float(scale), _MIN_SCALE, _MAX_SCALE),
        opacity=_clamp(float(opacity), _MIN_OPACITY, _MAX_OPACITY),
        visible=visible,
        always_on_top=always_on_top,
    )


def save_live2d_desktop_settings(
    path: Path,
    settings: Live2DDesktopSettings,
) -> None:
    """Persist Live2D desktop runtime settings."""

    path.parent.mkdir(parents=True, exist_ok=True)
    safe_settings = Live2DDesktopSettings(
        scale=_clamp(settings.scale, _MIN_SCALE, _MAX_SCALE),
        opacity=_clamp(settings.opacity, _MIN_OPACITY, _MAX_OPACITY),
        visible=settings.visible,
        always_on_top=settings.always_on_top,
    )
    path.write_text(
        json.dumps(
            {
                "scale": safe_settings.scale,
                "opacity": safe_settings.opacity,
                "visible": safe_settings.visible,
                "always_on_top": safe_settings.always_on_top,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def update_live2d_desktop_settings(
    path: Path,
    *,
    scale: float | None = None,
    opacity: float | None = None,
    visible: bool | None = None,
    always_on_top: bool | None = None,
) -> Live2DDesktopSettings:
    """Update selected Live2D desktop settings while preserving the rest."""

    current = load_live2d_desktop_settings(path)
    next_settings = Live2DDesktopSettings(
        scale=current.scale if scale is None else scale,
        opacity=current.opacity if opacity is None else opacity,
        visible=current.visible if visible is None else visible,
        always_on_top=current.always_on_top
        if always_on_top is None
        else always_on_top,
    )
    save_live2d_desktop_settings(path, next_settings)
    return load_live2d_desktop_settings(path)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, float(value)))
