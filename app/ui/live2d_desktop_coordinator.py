"""Coordinate Live2D bridge, model catalog, and desktop process lifecycle."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from app.contracts.events import BaseEvent
from app.ui.live2d_bridge import Live2DBridgeEventDispatcher
from app.ui.live2d_bridge_server import Live2DBridgeServer
from app.ui.live2d_desktop_process import Live2DDesktopProcess
from app.ui.live2d_desktop_settings import (
    Live2DDesktopSettings,
    default_live2d_desktop_settings_path,
    load_live2d_desktop_settings,
    save_live2d_desktop_settings,
)
from app.ui.live2d_desktop_window import (
    default_live2d_position_path,
    reset_live2d_window_position,
)
from app.ui.live2d_model_catalog import (
    Live2DModelPackage,
    build_live2d_model_options,
    render_live2d_model_catalog_details,
    render_live2d_model_catalog_summary,
    render_live2d_model_import_guide,
    scan_live2d_model_catalog,
)
from app.ui.live2d_model_selection import (
    default_live2d_model_selection_path,
    load_selected_live2d_model_id,
    save_selected_live2d_model_id,
)

logger = logging.getLogger(__name__)


class _ViewModel(Protocol):
    selected_live2d_model_id: str

    def set_live2d_runtime_status(self, status: dict[str, object]) -> None:
        """Update compact runtime status text."""

    def set_live2d_model_options(
        self,
        options: tuple[tuple[str, str], ...],
        *,
        selected_model_id: str | None = None,
    ) -> None:
        """Set selectable model options."""

    def select_live2d_model(self, model_id: str) -> bool:
        """Select a model id."""

    def set_live2d_model_catalog_summary(self, text: str) -> None:
        """Set compact model catalog text."""

    def set_live2d_model_catalog_details(self, text: str) -> None:
        """Set detailed model catalog text."""

    def set_live2d_model_import_guide(self, text: str) -> None:
        """Set model import guidance text."""


class _BridgeServer(Protocol):
    def set_runtime_status_callback(
        self,
        callback: Callable[[dict[str, Any]], None] | None,
    ) -> None:
        """Register runtime status callback."""

    def start(self) -> None:
        """Start server."""

    def stop(self) -> None:
        """Stop server."""

    def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message."""


class _LifecycleComponent(Protocol):
    def start(self) -> None:
        """Start component."""

    def stop(self) -> None:
        """Stop component."""


class _DesktopProcess(_LifecycleComponent, Protocol):
    scale: float
    opacity: float
    model_id: str


def default_live2d_model_root() -> Path:
    """Return the app-local Live2D model catalog root."""

    return (
        Path(__file__).resolve().parents[2]
        / "showcase-demo"
        / "live2d-prototype"
        / "assets"
        / "models"
    )


def build_live2d_control_log_context(
    *,
    action: str,
    scale: float,
    opacity: float,
    visible: bool,
) -> str:
    """Build a compact diagnostic context for Live2D desktop control actions."""

    return (
        f"action={action} "
        f"scale={scale:g} "
        f"opacity={opacity:g} "
        f"visible={visible}"
    )


class Live2DDesktopCoordinator:
    """Own Live2D desktop runtime lifecycle outside the application entry point."""

    def __init__(
        self,
        *,
        view_model: _ViewModel,
        subscribe: Callable[[str, Callable[[BaseEvent], None]], None],
        unsubscribe: Callable[[str, Callable[[BaseEvent], None]], None],
        auto_launch: bool,
        bridge_server: _BridgeServer | None = None,
        bridge_dispatcher: _LifecycleComponent | None = None,
        desktop_process: _DesktopProcess | None = None,
        model_root: Path | None = None,
        model_selection_path: Path | None = None,
        desktop_settings_path: Path | None = None,
        position_path: Path | None = None,
        open_models_folder: Callable[[Path], bool] | None = None,
        schedule_ui_update: Callable[[Callable[[], None]], None] | None = None,
    ) -> None:
        self.view_model = view_model
        self.model_root = model_root or default_live2d_model_root()
        self.model_selection_path = (
            model_selection_path or default_live2d_model_selection_path()
        )
        self.desktop_settings_path = (
            desktop_settings_path or default_live2d_desktop_settings_path()
        )
        self.position_path = position_path or default_live2d_position_path()
        self.bridge_server = bridge_server or Live2DBridgeServer()
        self.bridge_dispatcher = bridge_dispatcher or Live2DBridgeEventDispatcher(
            subscribe=subscribe,
            unsubscribe=unsubscribe,
            broadcast=self.bridge_server.broadcast,
        )
        self.desktop_process = (
            desktop_process
            if desktop_process is not None
            else Live2DDesktopProcess()
            if auto_launch
            else None
        )
        self._open_models_folder = open_models_folder or _open_folder_with_desktop
        self._schedule_ui_update = schedule_ui_update or _schedule_qt_ui_update
        self._view_refresher: Callable[[], None] | None = None

        self._model_packages: tuple[Live2DModelPackage, ...] = ()
        self._desktop_settings = load_live2d_desktop_settings(
            self.desktop_settings_path
        )
        self._scale = self._desktop_settings.scale
        self._opacity = self._desktop_settings.opacity
        self._visible = self.desktop_process is not None and self._desktop_settings.visible
        self._model_id = ""

        self.bridge_server.set_runtime_status_callback(self._on_runtime_status)
        self.refresh_model_catalog(restart_desktop=False, update_view=False)
        self._model_id = self.view_model.selected_live2d_model_id
        self._sync_desktop_process_settings()

    @property
    def visible(self) -> bool:
        """Return whether the desktop companion should be visible."""

        return self._visible

    @property
    def model_packages(self) -> tuple[Live2DModelPackage, ...]:
        """Return the last scanned model packages."""

        return self._model_packages

    def set_view_refresher(self, callback: Callable[[], None]) -> None:
        """Register a UI refresh callback once the main window exists."""

        self._view_refresher = callback

    def start(self) -> None:
        """Start bridge server, bridge dispatcher, and optional desktop process."""

        self.bridge_server.start()
        self.bridge_dispatcher.start()
        if self.desktop_process is not None and self._visible:
            self.desktop_process.start()

    def stop(self) -> None:
        """Stop desktop process and bridge components."""

        if self.desktop_process is not None:
            self.desktop_process.stop()
        self.bridge_dispatcher.stop()
        self.bridge_server.stop()

    def on_scale_up_requested(self) -> None:
        """Handle UI request to enlarge the Live2D desktop companion."""

        self._scale = min(1.35, round(self._scale + 0.1, 2))
        self._log_control("scale_up")
        self._save_settings()
        self._restart_desktop()

    def on_scale_down_requested(self) -> None:
        """Handle UI request to shrink the Live2D desktop companion."""

        self._scale = max(0.65, round(self._scale - 0.1, 2))
        self._log_control("scale_down")
        self._save_settings()
        self._restart_desktop()

    def on_opacity_down_requested(self) -> None:
        """Handle UI request to make the Live2D companion more transparent."""

        self._opacity = max(0.45, round(self._opacity - 0.1, 2))
        self._log_control("opacity_down")
        self._save_settings()
        self._restart_desktop()

    def on_opacity_up_requested(self) -> None:
        """Handle UI request to make the Live2D companion more opaque."""

        self._opacity = min(1.0, round(self._opacity + 0.1, 2))
        self._log_control("opacity_up")
        self._save_settings()
        self._restart_desktop()

    def on_visibility_toggled(self) -> None:
        """Handle UI request to show or hide the Live2D desktop companion."""

        if self.desktop_process is None:
            return
        self._visible = not self._visible
        self._log_control("toggle_visibility")
        self._save_settings()
        if self._visible:
            self._sync_desktop_process_settings()
            self.desktop_process.start()
            return
        self.desktop_process.stop()

    def on_position_reset_requested(self) -> None:
        """Handle UI request to reset the Live2D desktop companion position."""

        reset_live2d_window_position(self.position_path)
        logger.info(
            "Live2D desktop control requested %s position_path=%s",
            build_live2d_control_log_context(
                action="reset_position",
                scale=self._scale,
                opacity=self._opacity,
                visible=self._visible,
            ),
            self.position_path,
        )
        self._restart_desktop()

    def on_model_selected(self, model_id: str) -> None:
        """Handle UI request to switch the active Live2D model."""

        if not self.view_model.select_live2d_model(model_id):
            logger.warning("Ignored unknown Live2D model selection model_id=%s", model_id)
            return
        save_selected_live2d_model_id(self.model_selection_path, model_id)
        self._model_id = model_id
        self.view_model.set_live2d_model_catalog_summary(
            render_live2d_model_catalog_summary(
                self._model_packages,
                selected_model_id=model_id,
            )
        )
        logger.info(
            "Live2D desktop control requested %s model_id=%s",
            build_live2d_control_log_context(
                action="select_model",
                scale=self._scale,
                opacity=self._opacity,
                visible=self._visible,
            ),
            model_id,
        )
        self._restart_desktop()

    def on_models_refresh_requested(self) -> None:
        """Handle UI request to rescan the Live2D model catalog."""

        self.refresh_model_catalog(restart_desktop=True, update_view=True)

    def on_models_folder_requested(self) -> None:
        """Handle UI request to open the Live2D model folder."""

        self.model_root.mkdir(parents=True, exist_ok=True)
        opened = self._open_models_folder(self.model_root)
        logger.info(
            "Live2D models folder open requested root=%s opened=%s",
            self.model_root,
            opened,
        )

    def refresh_model_catalog(
        self,
        *,
        restart_desktop: bool,
        update_view: bool,
    ) -> None:
        """Scan model catalog and update ViewModel diagnostics."""

        preferred_model_id = self.view_model.selected_live2d_model_id or (
            load_selected_live2d_model_id(self.model_selection_path)
        )
        packages = scan_live2d_model_catalog(self.model_root)
        self._model_packages = packages
        self.view_model.set_live2d_model_catalog_details(
            render_live2d_model_catalog_details(self.model_root, packages)
        )
        self.view_model.set_live2d_model_options(
            build_live2d_model_options(packages),
            selected_model_id=preferred_model_id,
        )
        selected_model_id = self.view_model.selected_live2d_model_id
        summary = render_live2d_model_catalog_summary(
            packages,
            selected_model_id=selected_model_id,
        )
        self.view_model.set_live2d_model_catalog_summary(summary)
        self.view_model.set_live2d_model_import_guide(
            render_live2d_model_import_guide(
                self.model_root,
                packages,
                selected_model_id=selected_model_id,
            )
        )
        self._model_id = selected_model_id
        if selected_model_id:
            save_selected_live2d_model_id(
                self.model_selection_path,
                selected_model_id,
            )
        logger.info(
            "Live2D model catalog refreshed root=%s packages=%d selected_model_id=%s summary=%s",
            self.model_root,
            len(packages),
            selected_model_id,
            summary,
        )
        if restart_desktop:
            self._restart_desktop()
        if update_view:
            self._refresh_view()

    def _on_runtime_status(self, status: dict[str, object]) -> None:
        logger.info("Live2D runtime status updated type=%s", status.get("type"))
        self.view_model.set_live2d_runtime_status(status)
        self._schedule_ui_update(self._refresh_view)

    def _save_settings(self) -> None:
        save_live2d_desktop_settings(
            self.desktop_settings_path,
            Live2DDesktopSettings(
                scale=self._scale,
                opacity=self._opacity,
                visible=self._visible,
                always_on_top=load_live2d_desktop_settings(
                    self.desktop_settings_path
                ).always_on_top,
            ),
        )

    def _restart_desktop(self) -> None:
        if self.desktop_process is None:
            return
        self.desktop_process.stop()
        self._sync_desktop_process_settings()
        if self._visible:
            self.desktop_process.start()

    def _sync_desktop_process_settings(self) -> None:
        if self.desktop_process is None:
            return
        self.desktop_process.scale = self._scale
        self.desktop_process.opacity = self._opacity
        self.desktop_process.model_id = self._model_id

    def _log_control(self, action: str) -> None:
        logger.info(
            "Live2D desktop control requested %s",
            build_live2d_control_log_context(
                action=action,
                scale=self._scale,
                opacity=self._opacity,
                visible=self._visible,
            ),
        )

    def _refresh_view(self) -> None:
        if self._view_refresher is not None:
            self._view_refresher()


def _open_folder_with_desktop(path: Path) -> bool:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices

    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


def _schedule_qt_ui_update(callback: Callable[[], None]) -> None:
    from PySide6.QtCore import QTimer

    QTimer.singleShot(0, callback)
