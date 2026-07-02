"""Tests for Live2D desktop lifecycle coordination."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.ui.live2d_desktop_coordinator import (
    Live2DDesktopCoordinator,
    build_live2d_control_log_context,
)
from app.ui.live2d_desktop_settings import (
    Live2DDesktopSettings,
    load_live2d_desktop_settings,
    save_live2d_desktop_settings,
)
from app.ui.live2d_model_selection import load_selected_live2d_model_id


class FakeViewModel:
    def __init__(self) -> None:
        self.selected_live2d_model_id = ""
        self.live2d_model_options: tuple[tuple[str, str], ...] = ()
        self.runtime_status: dict[str, object] = {}
        self.summary = ""
        self.details = ""
        self.import_guide = ""

    def set_live2d_runtime_status(self, status: dict[str, object]) -> None:
        self.runtime_status = dict(status)

    def set_live2d_model_options(
        self,
        options: tuple[tuple[str, str], ...],
        *,
        selected_model_id: str | None = None,
    ) -> None:
        self.live2d_model_options = tuple(options)
        valid_ids = {model_id for model_id, _label in options}
        if selected_model_id in valid_ids:
            self.selected_live2d_model_id = selected_model_id or ""
        elif self.selected_live2d_model_id not in valid_ids:
            self.selected_live2d_model_id = options[0][0] if options else ""

    def select_live2d_model(self, model_id: str) -> bool:
        valid_ids = {option_id for option_id, _label in self.live2d_model_options}
        if model_id not in valid_ids:
            return False
        self.selected_live2d_model_id = model_id
        return True

    def set_live2d_model_catalog_summary(self, text: str) -> None:
        self.summary = text

    def set_live2d_model_catalog_details(self, text: str) -> None:
        self.details = text

    def set_live2d_model_import_guide(self, text: str) -> None:
        self.import_guide = text


class FakeBridgeServer:
    def __init__(self) -> None:
        self.started = 0
        self.stopped = 0
        self.callback = None

    def set_runtime_status_callback(self, callback) -> None:
        self.callback = callback

    def start(self) -> None:
        self.started += 1

    def stop(self) -> None:
        self.stopped += 1

    def broadcast(self, message: dict[str, Any]) -> None:
        pass


class FakeDispatcher:
    def __init__(self) -> None:
        self.started = 0
        self.stopped = 0

    def start(self) -> None:
        self.started += 1

    def stop(self) -> None:
        self.stopped += 1


class FakeDesktopProcess:
    def __init__(self) -> None:
        self.scale = 1.0
        self.opacity = 1.0
        self.model_id = ""
        self.started = 0
        self.stopped = 0

    def start(self) -> None:
        self.started += 1

    def stop(self) -> None:
        self.stopped += 1


def test_build_live2d_control_log_context() -> None:
    assert build_live2d_control_log_context(
        action="scale_up",
        scale=1.2,
        opacity=0.8,
        visible=True,
    ) == "action=scale_up scale=1.2 opacity=0.8 visible=True"


def test_coordinator_starts_and_stops_lifecycle_components(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    save_live2d_desktop_settings(settings_path, Live2DDesktopSettings(visible=True))
    bridge_server = FakeBridgeServer()
    dispatcher = FakeDispatcher()
    process = FakeDesktopProcess()

    coordinator = Live2DDesktopCoordinator(
        view_model=FakeViewModel(),
        subscribe=lambda event_type, callback: None,
        unsubscribe=lambda event_type, callback: None,
        auto_launch=True,
        bridge_server=bridge_server,
        bridge_dispatcher=dispatcher,
        desktop_process=process,
        model_root=tmp_path / "models",
        model_selection_path=tmp_path / "selection.json",
        desktop_settings_path=settings_path,
        position_path=tmp_path / "position.json",
    )

    coordinator.start()
    coordinator.stop()

    assert bridge_server.started == 1
    assert dispatcher.started == 1
    assert process.started == 1
    assert process.stopped == 1
    assert dispatcher.stopped == 1
    assert bridge_server.stopped == 1


def test_runtime_status_updates_view_model_and_schedules_refresh(tmp_path: Path) -> None:
    bridge_server = FakeBridgeServer()
    view_model = FakeViewModel()
    refreshes: list[str] = []
    scheduled: list[str] = []

    coordinator = Live2DDesktopCoordinator(
        view_model=view_model,
        subscribe=lambda event_type, callback: None,
        unsubscribe=lambda event_type, callback: None,
        auto_launch=False,
        bridge_server=bridge_server,
        bridge_dispatcher=FakeDispatcher(),
        model_root=tmp_path / "models",
        model_selection_path=tmp_path / "selection.json",
        desktop_settings_path=tmp_path / "settings.json",
        position_path=tmp_path / "position.json",
        schedule_ui_update=lambda callback: (scheduled.append("scheduled"), callback()),
    )
    coordinator.set_view_refresher(lambda: refreshes.append("refresh"))

    assert bridge_server.callback is not None
    bridge_server.callback({"type": "live2d.model_loaded", "modelId": "sample/Hiyori"})

    assert view_model.runtime_status["type"] == "live2d.model_loaded"
    assert scheduled == ["scheduled"]
    assert refreshes == ["refresh"]


def test_scale_control_persists_settings_and_restarts_desktop_process(
    tmp_path: Path,
) -> None:
    settings_path = tmp_path / "settings.json"
    save_live2d_desktop_settings(settings_path, Live2DDesktopSettings(visible=True))
    process = FakeDesktopProcess()

    coordinator = Live2DDesktopCoordinator(
        view_model=FakeViewModel(),
        subscribe=lambda event_type, callback: None,
        unsubscribe=lambda event_type, callback: None,
        auto_launch=True,
        bridge_server=FakeBridgeServer(),
        bridge_dispatcher=FakeDispatcher(),
        desktop_process=process,
        model_root=tmp_path / "models",
        model_selection_path=tmp_path / "selection.json",
        desktop_settings_path=settings_path,
        position_path=tmp_path / "position.json",
    )

    coordinator.on_scale_up_requested()

    assert process.scale == 1.1
    assert process.stopped == 1
    assert process.started == 1
    assert load_live2d_desktop_settings(settings_path).scale == 1.1


def test_model_selection_persists_selected_model_and_restarts_process(
    tmp_path: Path,
) -> None:
    model_root = tmp_path / "models"
    model_root.mkdir()
    _write_minimal_model(model_root / "custom" / "A" / "A.model3.json")
    _write_minimal_model(model_root / "custom" / "B" / "B.model3.json")
    selection_path = tmp_path / "selection.json"
    process = FakeDesktopProcess()
    view_model = FakeViewModel()

    coordinator = Live2DDesktopCoordinator(
        view_model=view_model,
        subscribe=lambda event_type, callback: None,
        unsubscribe=lambda event_type, callback: None,
        auto_launch=True,
        bridge_server=FakeBridgeServer(),
        bridge_dispatcher=FakeDispatcher(),
        desktop_process=process,
        model_root=model_root,
        model_selection_path=selection_path,
        desktop_settings_path=tmp_path / "settings.json",
        position_path=tmp_path / "position.json",
    )

    coordinator.on_model_selected("custom/B")

    assert view_model.selected_live2d_model_id == "custom/B"
    assert load_selected_live2d_model_id(selection_path) == "custom/B"
    assert process.model_id == "custom/B"
    assert process.stopped == 1


def test_refresh_model_catalog_updates_view_and_desktop_model(tmp_path: Path) -> None:
    model_root = tmp_path / "models"
    model_root.mkdir()
    selection_path = tmp_path / "selection.json"
    view_model = FakeViewModel()
    process = FakeDesktopProcess()
    refreshes: list[str] = []

    coordinator = Live2DDesktopCoordinator(
        view_model=view_model,
        subscribe=lambda event_type, callback: None,
        unsubscribe=lambda event_type, callback: None,
        auto_launch=True,
        bridge_server=FakeBridgeServer(),
        bridge_dispatcher=FakeDispatcher(),
        desktop_process=process,
        model_root=model_root,
        model_selection_path=selection_path,
        desktop_settings_path=tmp_path / "settings.json",
        position_path=tmp_path / "position.json",
    )
    coordinator.set_view_refresher(lambda: refreshes.append("refresh"))

    _write_minimal_model(model_root / "custom" / "A" / "A.model3.json")
    coordinator.on_models_refresh_requested()

    assert view_model.selected_live2d_model_id == "custom/A"
    assert process.model_id == "custom/A"
    assert "custom/A" in view_model.details
    assert refreshes == ["refresh"]


def _write_minimal_model(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    (path.parent / "A.moc3").write_bytes(b"moc")
    (path.parent / "texture_00.png").write_bytes(b"png")
    path.write_text(
        """
{
  "Version": 3,
  "FileReferences": {
    "Moc": "A.moc3",
    "Textures": ["texture_00.png"],
    "Motions": {}
  }
}
""".strip(),
        encoding="utf-8",
    )
