"""Tests for the Live2D desktop WebView shell."""

from __future__ import annotations

from app.ui.live2d_desktop_window import (
    Live2DDesktopDependencyStatus,
    probe_live2d_desktop_dependencies,
)


def test_dependency_status_ready_when_no_modules_missing() -> None:
    """Dependency status is ready when every required module is available."""
    status = Live2DDesktopDependencyStatus(missing_modules=())

    assert status.ready is True
    assert status.detail == "Live2D desktop dependencies ready"


def test_dependency_status_reports_missing_modules() -> None:
    """Dependency status explains which modules prevent desktop launch."""
    status = Live2DDesktopDependencyStatus(
        missing_modules=("PySide6.QtWebEngineWidgets",)
    )

    assert status.ready is False
    assert status.detail == (
        "Missing Live2D desktop dependencies: PySide6.QtWebEngineWidgets"
    )


def test_probe_dependencies_collects_missing_qt_modules() -> None:
    """Probe reports every Qt module that the importer cannot load."""

    def fake_importer(module_name: str) -> object:
        if module_name == "PySide6.QtWebEngineWidgets":
            raise ImportError(module_name)
        return object()

    status = probe_live2d_desktop_dependencies(fake_importer)

    assert status.ready is False
    assert status.missing_modules == ("PySide6.QtWebEngineWidgets",)


def test_probe_dependencies_ready_with_all_modules() -> None:
    """Probe succeeds when all desktop WebView modules are importable."""

    def fake_importer(module_name: str) -> object:
        return object()

    status = probe_live2d_desktop_dependencies(fake_importer)

    assert status.ready is True
    assert status.missing_modules == ()


def test_current_environment_probe_is_explicit() -> None:
    """Current environment probe returns a deterministic diagnostic shape."""
    status = probe_live2d_desktop_dependencies()

    assert isinstance(status.ready, bool)
    assert isinstance(status.missing_modules, tuple)
    if not status.ready:
        assert status.detail.startswith("Missing Live2D desktop dependencies:")
    else:
        assert status.detail == "Live2D desktop dependencies ready"
