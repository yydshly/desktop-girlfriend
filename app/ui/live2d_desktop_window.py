"""Live2D desktop WebView window entrypoint."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module

from app.ui.desktop_presence import Live2DDesktopShellSpec

_REQUIRED_QT_MODULES = (
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
)


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


def run_live2d_desktop_window(spec: Live2DDesktopShellSpec) -> int:
    """Run a transparent always-on-top WebView hosting the Live2D runtime."""

    require_live2d_desktop_dependencies()

    qt_core = import_module("PySide6.QtCore")
    qt_gui = import_module("PySide6.QtGui")
    qt_widgets = import_module("PySide6.QtWidgets")
    qt_webengine_core = import_module("PySide6.QtWebEngineCore")
    qt_webengine_widgets = import_module("PySide6.QtWebEngineWidgets")

    QApplication = qt_widgets.QApplication
    QWebEngineView = qt_webengine_widgets.QWebEngineView
    Qt = qt_core.Qt
    QUrl = qt_core.QUrl
    QColor = qt_gui.QColor
    QWebEngineSettings = qt_webengine_core.QWebEngineSettings

    app = QApplication.instance() or QApplication([])
    view = QWebEngineView()
    view.setWindowTitle("Live2D Desktop Girlfriend")
    view.resize(spec.width, spec.height)

    flags = Qt.WindowType.Window
    if spec.frameless:
        flags |= Qt.WindowType.FramelessWindowHint
    if spec.always_on_top:
        flags |= Qt.WindowType.WindowStaysOnTopHint
    view.setWindowFlags(flags)

    if spec.transparent_background:
        view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        view.page().setBackgroundColor(QColor(0, 0, 0, 0))

    if spec.devtools_enabled:
        settings = view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls,
            True,
        )

    if spec.click_through:
        view.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    view.setUrl(QUrl(spec.source_url))
    view.show()
    return app.exec()
