"""Desktop presence shell types and helpers (Phase 2-D)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Compact mode window dimensions (width x height)
COMPACT_MODE_WIDTH = 340
COMPACT_MODE_HEIGHT = 320

# Live2D desktop shell defaults. These values describe the target desktop
# presentation before the GUI layer binds them to Qt window flags.
LIVE2D_DESKTOP_WIDTH = 520
LIVE2D_DESKTOP_HEIGHT = 760
LIVE2D_PROTOTYPE_ROUTE = "showcase-demo/live2d-prototype/index.html"
LIVE2D_DESKTOP_QUERY = "desktop=1"


@dataclass
class DesktopPresenceState:
    """UI-only state for desktop presence features.

    Does not affect avatar_action, chat_messages, product_status_visible,
    or memory panel state.
    """

    always_on_top: bool = False
    compact_mode: bool = False


@dataclass(frozen=True)
class Live2DDesktopShellSpec:
    """Desktop shell contract for hosting the Live2D runtime page."""

    source_url: str
    width: int = LIVE2D_DESKTOP_WIDTH
    height: int = LIVE2D_DESKTOP_HEIGHT
    transparent_background: bool = True
    frameless: bool = True
    always_on_top: bool = True
    click_through: bool = False
    devtools_enabled: bool = False


def build_live2d_desktop_shell_spec(
    workspace_root: Path,
    *,
    devtools_enabled: bool = False,
    click_through: bool = False,
) -> Live2DDesktopShellSpec:
    """Build the desktop shell spec that points at the local Live2D runtime."""

    route = workspace_root / LIVE2D_PROTOTYPE_ROUTE
    source_url = f"{route.resolve().as_uri()}?{LIVE2D_DESKTOP_QUERY}"
    return Live2DDesktopShellSpec(
        source_url=source_url,
        click_through=click_through,
        devtools_enabled=devtools_enabled,
    )


def render_live2d_shell_summary(spec: Live2DDesktopShellSpec) -> str:
    """Render a compact diagnostic summary for the desktop shell."""

    flags = [
        "transparent" if spec.transparent_background else "opaque",
        "frameless" if spec.frameless else "framed",
        "top" if spec.always_on_top else "normal-z",
        "click-through" if spec.click_through else "interactive",
    ]
    return f"Live2D desktop shell {spec.width}x{spec.height}: {', '.join(flags)}"


def render_pin_button_text(always_on_top: bool) -> str:
    """Return the pin toggle button label.

    Args:
        always_on_top: Whether the window is currently set to stay on top.

    Returns:
        "取消置顶" when already on top, "置顶" when not.
    """
    return "取消置顶" if always_on_top else "置顶"


def render_compact_button_text(compact_mode: bool) -> str:
    """Return the compact mode toggle button label.

    Args:
        compact_mode: Whether the window is currently in compact mode.

    Returns:
        "展开" when in compact mode, "小窗" when in normal mode.
    """
    return "展开" if compact_mode else "小窗"
