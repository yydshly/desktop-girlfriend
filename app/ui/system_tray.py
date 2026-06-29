"""System tray controller for desktop presence."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from app.ui.tray_view import TrayView, build_tray_view


class DesktopSystemTrayController:
    """Controller for system tray integration.

    Provides hide-to-tray and restore-from-tray functionality with a simple
    menu containing show/hide/quit actions.
    """

    def __init__(
        self,
        window: Any,
        on_quit: Callable[[], None],
        tray_view: TrayView | None = None,
    ) -> None:
        """Initialize the system tray controller.

        Args:
            window: The main application window to show/hide.
            on_quit: Callback invoked when the user selects quit from tray menu.
            tray_view: Optional TrayView for menu text; defaults to build_tray_view().
        """
        self._window = window
        self._on_quit = on_quit
        self._tray_view = tray_view or build_tray_view()
        self._tray: QSystemTrayIcon | None = None
        self._menu: QMenu | None = None
        self._show_action: QAction | None = None
        self._hide_action: QAction | None = None
        self._quit_action: QAction | None = None
        self._available = QSystemTrayIcon.isSystemTrayAvailable()

        if self._available:
            self._setup_tray()

    def _setup_tray(self) -> None:
        """Set up the system tray icon and menu."""
        self._tray = QSystemTrayIcon()

        # Try to use a standard icon; fall back to empty icon if unavailable
        app_instance = QApplication.instance()
        style = None
        if isinstance(app_instance, QApplication):
            style = app_instance.style()
        if style is not None:
            # SP_DesktopIcon is universally available
            icon = style.standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
            self._tray.setIcon(icon)
        else:
            self._tray.setIcon(QIcon())

        self._tray.setToolTip(self._tray_view.tooltip)

        # Build context menu
        self._menu = QMenu()
        self._show_action = QAction(self._tray_view.show_text)
        self._show_action.triggered.connect(self.restore_window)
        self._menu.addAction(self._show_action)

        self._hide_action = QAction(self._tray_view.hide_text)
        self._hide_action.triggered.connect(self.hide_to_tray)
        self._menu.addAction(self._hide_action)

        self._menu.addSeparator()

        self._quit_action = QAction(self._tray_view.quit_text)
        self._quit_action.triggered.connect(self._handle_quit)
        self._menu.addAction(self._quit_action)

        self._tray.setContextMenu(self._menu)

        # Double-click on tray icon restores window
        self._tray.activated.connect(self._on_tray_activated)

        self._tray.setVisible(True)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation (e.g., double-click).

        Args:
            reason: The activation reason.
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.restore_window()

    @property
    def available(self) -> bool:
        """Return whether the system tray is available on this platform."""
        return self._available

    def show_tray(self) -> None:
        """Make the tray icon visible."""
        if self._tray is not None:
            self._tray.setVisible(True)

    def hide_to_tray(self) -> None:
        """Hide the main window to system tray."""
        if self._window is not None:
            self._window.hide()

    def restore_window(self) -> None:
        """Restore (show and activate) the main window from tray."""
        if self._window is not None:
            self._window.show()
            self._window.raise_()
            self._window.activateWindow()

    def _handle_quit(self) -> None:
        """Handle quit action from tray menu."""
        self._on_quit()

    def dispose(self) -> None:
        """Clean up tray resources."""
        if self._tray is not None:
            self._tray.setVisible(False)
            self._tray.deleteLater()
            self._tray = None
        self._menu = None
        self._show_action = None
        self._hide_action = None
        self._quit_action = None
