"""Tests for the Live2D desktop WebView shell."""

from __future__ import annotations

from app.ui.live2d_desktop_window import (
    Live2DDesktopContextMenuAction,
    Live2DDesktopDependencyStatus,
    Live2DDesktopWindowPosition,
    build_live2d_context_menu_actions,
    calculate_dragged_position,
    load_live2d_window_position,
    probe_live2d_desktop_dependencies,
    reset_live2d_window_position,
    save_live2d_window_position,
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


def test_window_position_round_trips(tmp_path) -> None:
    """Live2D desktop window position can be persisted and restored."""
    path = tmp_path / "window.json"

    save_live2d_window_position(path, Live2DDesktopWindowPosition(x=120, y=240))

    assert load_live2d_window_position(path) == Live2DDesktopWindowPosition(
        x=120,
        y=240,
    )


def test_reset_window_position_writes_default_position(tmp_path) -> None:
    """Resetting the desktop companion position persists a predictable default."""
    path = tmp_path / "window.json"
    save_live2d_window_position(path, Live2DDesktopWindowPosition(x=120, y=240))

    reset_live2d_window_position(path)

    assert load_live2d_window_position(path) == Live2DDesktopWindowPosition(
        x=80,
        y=80,
    )


def test_missing_or_invalid_window_position_returns_none(tmp_path) -> None:
    """Invalid window position files are ignored instead of crashing launch."""
    missing = tmp_path / "missing.json"
    invalid = tmp_path / "invalid.json"
    invalid.write_text('{"x": "bad", "y": 3}', encoding="utf-8")

    assert load_live2d_window_position(missing) is None
    assert load_live2d_window_position(invalid) is None


def test_calculate_dragged_position_uses_global_delta() -> None:
    """Dragging moves the window by the global pointer delta."""
    assert calculate_dragged_position(
        window_x=100,
        window_y=200,
        press_global_x=10,
        press_global_y=20,
        move_global_x=40,
        move_global_y=55,
    ) == Live2DDesktopWindowPosition(x=130, y=235)


def test_context_menu_actions_describe_desktop_controls() -> None:
    """Right-click menu exposes the most useful desktop companion controls."""
    assert build_live2d_context_menu_actions(always_on_top=True) == (
        Live2DDesktopContextMenuAction("reset_position", "重置位置"),
        Live2DDesktopContextMenuAction("opacity_down", "淡一点"),
        Live2DDesktopContextMenuAction("opacity_up", "实一点"),
        Live2DDesktopContextMenuAction("toggle_top", "取消置顶"),
        Live2DDesktopContextMenuAction("close", "隐藏人物"),
    )


def test_context_menu_top_label_reflects_current_window_flag() -> None:
    """Pin label changes when the desktop companion is not currently on top."""
    actions = build_live2d_context_menu_actions(always_on_top=False)

    assert actions[3] == Live2DDesktopContextMenuAction("toggle_top", "置顶")
