"""System tray view definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrayView:
    """Immutable view model for system tray UI text."""

    tooltip: str
    show_text: str
    hide_text: str
    quit_text: str
    hide_button_text: str


def build_tray_view(
    app_name: str = "Desktop Girlfriend", companion_name: str = "小云"
) -> TrayView:
    """Build the tray view with localized strings.

    Args:
        app_name: The application name.
        companion_name: The companion character name.

    Returns:
        A TrayView instance with tray UI strings.
    """
    return TrayView(
        tooltip=f"{companion_name}正在桌面陪你",
        show_text="显示小云",
        hide_text="隐藏小云",
        quit_text="退出",
        hide_button_text="隐藏",
    )


def render_tray_availability_text(available: bool) -> str:
    """Render human-readable tray availability text.

    Args:
        available: Whether the system tray is available.

    Returns:
        Localized availability text.
    """
    return "托盘可用" if available else "托盘不可用"
