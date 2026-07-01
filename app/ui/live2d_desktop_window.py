"""Live2D desktop WebView window entrypoint."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

from app.ui.desktop_presence import Live2DDesktopShellSpec

_REQUIRED_QT_MODULES = (
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
)

_POSITION_FILE_NAME = "live2d-desktop-window.json"


@dataclass(frozen=True)
class Live2DDesktopDependencyStatus:
    """Dependency status for the Live2D desktop shell."""

    missing_modules: tuple[str, ...]

    @property
    def ready(self) -> bool:
        """Return True when all Qt desktop shell dependencies are importable."""

        return not self.missing_modules

    @property
    def detail(self) -> str:
        """Return a readable dependency diagnostic."""

        if self.ready:
            return "Live2D desktop dependencies ready"
        missing = ", ".join(self.missing_modules)
        return f"Missing Live2D desktop dependencies: {missing}"


def probe_live2d_desktop_dependencies(
    module_importer: Callable[[str], object] = import_module,
) -> Live2DDesktopDependencyStatus:
    """Probe whether the local Python runtime can host the Live2D WebView."""

    missing: list[str] = []
    for module_name in _REQUIRED_QT_MODULES:
        try:
            module_importer(module_name)
        except ImportError:
            missing.append(module_name)
    return Live2DDesktopDependencyStatus(missing_modules=tuple(missing))


def require_live2d_desktop_dependencies() -> None:
    """Raise a clear error when the Live2D desktop shell cannot run."""

    status = probe_live2d_desktop_dependencies()
    if not status.ready:
        raise RuntimeError(status.detail)


@dataclass(frozen=True)
class Live2DDesktopWindowPosition:
    """Persisted Live2D desktop window position."""

    x: int
    y: int


@dataclass(frozen=True)
class Live2DDesktopContextMenuAction:
    """Right-click action exposed by the Live2D desktop companion window."""

    key: str
    label: str


def default_live2d_position_path() -> Path:
    """Return the default local path for Live2D desktop window state."""

    return Path(".tmp") / _POSITION_FILE_NAME


def load_live2d_window_position(path: Path) -> Live2DDesktopWindowPosition | None:
    """Load a saved window position from disk."""

    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    x = data.get("x")
    y = data.get("y")
    if type(x) is not int or type(y) is not int:
        return None
    return Live2DDesktopWindowPosition(x=x, y=y)


def save_live2d_window_position(
    path: Path,
    position: Live2DDesktopWindowPosition,
) -> None:
    """Save the Live2D desktop window position to disk."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"x": position.x, "y": position.y}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_live2d_context_menu_actions(
    *,
    always_on_top: bool,
) -> tuple[Live2DDesktopContextMenuAction, ...]:
    """Return the right-click menu actions for the Live2D desktop companion."""

    return (
        Live2DDesktopContextMenuAction("reset_position", "重置位置"),
        Live2DDesktopContextMenuAction("opacity_down", "淡一点"),
        Live2DDesktopContextMenuAction("opacity_up", "实一点"),
        Live2DDesktopContextMenuAction("toggle_top", "取消置顶" if always_on_top else "置顶"),
        Live2DDesktopContextMenuAction("close", "隐藏人物"),
    )


def calculate_dragged_position(
    window_x: int,
    window_y: int,
    press_global_x: int,
    press_global_y: int,
    move_global_x: int,
    move_global_y: int,
) -> Live2DDesktopWindowPosition:
    """Calculate window position after dragging from a global press point."""

    return Live2DDesktopWindowPosition(
        x=window_x + move_global_x - press_global_x,
        y=window_y + move_global_y - press_global_y,
    )


def run_live2d_desktop_window(spec: Live2DDesktopShellSpec) -> int:
    """Run a transparent always-on-top WebView hosting the Live2D runtime."""

    require_live2d_desktop_dependencies()

    qt_core = import_module("PySide6.QtCore")
    qt_gui = import_module("PySide6.QtGui")
    qt_widgets = import_module("PySide6.QtWidgets")
    qt_webengine_core = import_module("PySide6.QtWebEngineCore")
    qt_webengine_widgets = import_module("PySide6.QtWebEngineWidgets")

    q_application = qt_widgets.QApplication
    q_web_engine_view = qt_webengine_widgets.QWebEngineView
    q_menu = qt_widgets.QMenu
    qt = qt_core.Qt
    q_url = qt_core.QUrl
    q_color = qt_gui.QColor
    q_web_engine_settings = qt_webengine_core.QWebEngineSettings
    position_path = default_live2d_position_path()

    class Live2DDesktopWebView(q_web_engine_view):
        def __init__(self) -> None:
            super().__init__()
            self._drag_origin = None
            self._window_origin = None

        def install_drag_event_filters(self) -> None:
            self.installEventFilter(self)
            focus_proxy = self.focusProxy()
            if focus_proxy is not None:
                focus_proxy.installEventFilter(self)
            for child in self.findChildren(qt_core.QObject):
                child.installEventFilter(self)

        def eventFilter(self, watched, event) -> bool:  # noqa: N802
            if self._handle_context_menu_event(event):
                return True
            if self._handle_drag_event(event):
                return True
            return super().eventFilter(watched, event)

        def contextMenuEvent(self, event) -> None:  # noqa: N802
            if self._show_context_menu(_event_global_position(event)):
                event.accept()
                return
            super().contextMenuEvent(event)

        def mousePressEvent(self, event) -> None:  # noqa: N802
            if self._handle_drag_event(event):
                return
            super().mousePressEvent(event)

        def mouseMoveEvent(self, event) -> None:  # noqa: N802
            if self._handle_drag_event(event):
                return
            super().mouseMoveEvent(event)

        def mouseReleaseEvent(self, event) -> None:  # noqa: N802
            if self._handle_drag_event(event):
                return
            super().mouseReleaseEvent(event)

        def _handle_drag_event(self, event) -> bool:
            event_type = event.type()
            if (
                event_type == qt_core.QEvent.Type.MouseButtonPress
                and event.button() == qt.MouseButton.LeftButton
            ):
                self._drag_origin = _event_global_position(event)
                self._window_origin = self.pos()
                event.accept()
                return True
            if (
                event_type == qt_core.QEvent.Type.MouseMove
                and self._drag_origin is not None
                and self._window_origin is not None
            ):
                current = _event_global_position(event)
                next_position = calculate_dragged_position(
                    self._window_origin.x(),
                    self._window_origin.y(),
                    self._drag_origin.x(),
                    self._drag_origin.y(),
                    current.x(),
                    current.y(),
                )
                self.move(next_position.x, next_position.y)
                event.accept()
                return True
            if (
                event_type == qt_core.QEvent.Type.MouseButtonRelease
                and event.button() == qt.MouseButton.LeftButton
            ):
                self._drag_origin = None
                self._window_origin = None
                save_live2d_window_position(
                    position_path,
                    Live2DDesktopWindowPosition(x=self.x(), y=self.y()),
                )
                event.accept()
                return True
            return False

        def _handle_context_menu_event(self, event) -> bool:
            if event.type() != qt_core.QEvent.Type.ContextMenu:
                return False
            self._show_context_menu(_event_global_position(event))
            event.accept()
            return True

        def _show_context_menu(self, global_position) -> bool:
            menu = q_menu(self)
            action_by_key = {}
            for menu_action in build_live2d_context_menu_actions(
                always_on_top=bool(self.windowFlags() & qt.WindowType.WindowStaysOnTopHint)
            ):
                action = menu.addAction(menu_action.label)
                action_by_key[action] = menu_action.key
            selected = menu.exec(global_position)
            selected_key = action_by_key.get(selected)
            if selected_key is None:
                return False
            self._apply_context_menu_action(selected_key)
            return True

        def _apply_context_menu_action(self, key: str) -> None:
            if key == "reset_position":
                try:
                    position_path.unlink(missing_ok=True)
                except OSError:
                    pass
                self.move(80, 80)
                return
            if key == "opacity_down":
                self.setWindowOpacity(max(0.45, round(self.windowOpacity() - 0.1, 2)))
                return
            if key == "opacity_up":
                self.setWindowOpacity(min(1.0, round(self.windowOpacity() + 0.1, 2)))
                return
            if key == "toggle_top":
                currently_top = bool(
                    self.windowFlags() & qt.WindowType.WindowStaysOnTopHint
                )
                self.setWindowFlag(
                    qt.WindowType.WindowStaysOnTopHint,
                    not currently_top,
                )
                self.show()
                return
            if key == "close":
                self.close()

    app = q_application.instance() or q_application([])
    view = Live2DDesktopWebView()
    view.setWindowTitle("Live2D Desktop Girlfriend")
    view.resize(spec.width, spec.height)
    view.setWindowOpacity(spec.opacity)
    saved_position = load_live2d_window_position(position_path)
    if saved_position is not None:
        view.move(saved_position.x, saved_position.y)

    flags = qt.WindowType.Window
    if spec.frameless:
        flags |= qt.WindowType.FramelessWindowHint
    if spec.always_on_top:
        flags |= qt.WindowType.WindowStaysOnTopHint
    view.setWindowFlags(flags)

    if spec.transparent_background:
        view.setAttribute(qt.WidgetAttribute.WA_TranslucentBackground, True)
        view.page().setBackgroundColor(q_color(0, 0, 0, 0))

    settings = view.settings()
    settings.setAttribute(q_web_engine_settings.WebAttribute.JavascriptEnabled, True)
    settings.setAttribute(
        q_web_engine_settings.WebAttribute.LocalContentCanAccessFileUrls,
        True,
    )
    settings.setAttribute(
        q_web_engine_settings.WebAttribute.LocalContentCanAccessRemoteUrls,
        True,
    )

    if spec.devtools_enabled:
        settings.setAttribute(q_web_engine_settings.WebAttribute.WebGLEnabled, True)

    if spec.click_through:
        view.setAttribute(qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    view.page().loadFinished.connect(lambda _ok: view.install_drag_event_filters())
    view.setUrl(q_url(spec.source_url))
    view.show()
    view.install_drag_event_filters()
    return app.exec()


def _event_global_position(event: object) -> object:
    if hasattr(event, "globalPosition"):
        return event.globalPosition().toPoint()
    return event.globalPos()
