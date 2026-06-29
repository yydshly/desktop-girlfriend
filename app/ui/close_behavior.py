"""Close behavior decision logic for desktop presence.

Provides pure functions for deciding whether a window close event should
hide to tray or accept the close, and rendering hint text.
No Qt, no file I/O, no LLM/TTS/ASR.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CloseBehaviorDecision:
    """Result of a close behavior decision."""

    should_hide_to_tray: bool
    should_accept_close: bool
    reason: str


def decide_close_behavior(
    tray_available: bool,
    force_quit: bool,
) -> CloseBehaviorDecision:
    """Decide what to do when the user tries to close the window.

    Args:
        tray_available: Whether the system tray is available on this platform.
        force_quit: Whether a force-quit has been requested (e.g., from tray menu).

    Returns:
        A CloseBehaviorDecision indicating whether to hide to tray or accept close.
    """
    if force_quit:
        return CloseBehaviorDecision(
            should_hide_to_tray=False,
            should_accept_close=True,
            reason="force quit requested",
        )

    if tray_available:
        return CloseBehaviorDecision(
            should_hide_to_tray=True,
            should_accept_close=False,
            reason="tray available; hide to tray",
        )

    return CloseBehaviorDecision(
        should_hide_to_tray=False,
        should_accept_close=True,
        reason="tray unavailable; accept close",
    )


def render_close_to_tray_hint(tray_available: bool) -> str:
    """Render a user-facing hint about close behavior.

    Args:
        tray_available: Whether the system tray is available on this platform.

    Returns:
        A Chinese hint string describing what happens when the window is closed.
    """
    if tray_available:
        return "关闭窗口时，小云会隐藏到托盘。"
    return "托盘不可用，关闭窗口将退出应用。"
