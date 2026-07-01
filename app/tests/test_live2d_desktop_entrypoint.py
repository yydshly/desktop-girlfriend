from __future__ import annotations

from pathlib import Path

from app import live2d_desktop
from app.ui.live2d_desktop_settings import Live2DDesktopSettings


def _capture_spec(captured: dict):
    def run(spec):
        captured["spec"] = spec
        return 0

    return run


def test_live2d_desktop_entrypoint_uses_saved_model_when_cli_model_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured = {}
    selection_path = tmp_path / "selection.json"

    monkeypatch.setattr(
        live2d_desktop,
        "default_live2d_model_selection_path",
        lambda: selection_path,
        raising=False,
    )
    monkeypatch.setattr(
        live2d_desktop,
        "load_selected_live2d_model_id",
        lambda path: "sample/Natori" if path == selection_path else "",
        raising=False,
    )
    monkeypatch.setattr(
        live2d_desktop,
        "run_live2d_desktop_window",
        _capture_spec(captured),
    )

    assert live2d_desktop.main([]) == 0

    assert "model=sample%2FNatori" in captured["spec"].source_url


def test_live2d_desktop_entrypoint_prefers_cli_model_over_saved_model(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured = {}

    monkeypatch.setattr(
        live2d_desktop,
        "default_live2d_model_selection_path",
        lambda: tmp_path / "selection.json",
        raising=False,
    )
    monkeypatch.setattr(
        live2d_desktop,
        "load_selected_live2d_model_id",
        lambda path: "sample/Natori",
        raising=False,
    )
    monkeypatch.setattr(
        live2d_desktop,
        "run_live2d_desktop_window",
        _capture_spec(captured),
    )

    assert live2d_desktop.main(["--model-id", "custom/Xiaoyun"]) == 0

    assert "model=custom%2FXiaoyun" in captured["spec"].source_url


def test_live2d_desktop_entrypoint_uses_saved_window_settings(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured = {}

    monkeypatch.setattr(
        live2d_desktop,
        "default_live2d_desktop_settings_path",
        lambda: tmp_path / "settings.json",
        raising=False,
    )
    monkeypatch.setattr(
        live2d_desktop,
        "load_live2d_desktop_settings",
        lambda path: Live2DDesktopSettings(
            scale=1.2,
            opacity=0.72,
            visible=True,
            always_on_top=False,
        ),
        raising=False,
    )
    monkeypatch.setattr(
        live2d_desktop,
        "run_live2d_desktop_window",
        _capture_spec(captured),
    )

    assert live2d_desktop.main([]) == 0

    assert captured["spec"].opacity == 0.72
    assert captured["spec"].always_on_top is False


def test_live2d_desktop_entrypoint_prefers_cli_window_settings(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured = {}

    monkeypatch.setattr(
        live2d_desktop,
        "default_live2d_desktop_settings_path",
        lambda: tmp_path / "settings.json",
        raising=False,
    )
    monkeypatch.setattr(
        live2d_desktop,
        "load_live2d_desktop_settings",
        lambda path: Live2DDesktopSettings(
            scale=0.8,
            opacity=0.6,
            visible=True,
            always_on_top=False,
        ),
        raising=False,
    )
    monkeypatch.setattr(
        live2d_desktop,
        "run_live2d_desktop_window",
        _capture_spec(captured),
    )

    assert live2d_desktop.main(["--scale", "1.1", "--opacity", "0.9"]) == 0

    assert captured["spec"].opacity == 0.9
    assert captured["spec"].always_on_top is False
