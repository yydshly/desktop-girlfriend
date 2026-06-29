"""Desktop presence shell types and helpers (Phase 2-D)."""

from __future__ import annotations

from dataclasses import dataclass

# Compact mode window dimensions (width x height)
COMPACT_MODE_WIDTH = 340
COMPACT_MODE_HEIGHT = 320


@dataclass
class DesktopPresenceState:
    """UI-only state for desktop presence features.

    Does not affect avatar_action, chat_messages, product_status_visible,
    or memory panel state.
    """

    always_on_top: bool = False
    compact_mode: bool = False


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
