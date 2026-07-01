from __future__ import annotations

from pathlib import Path

from app import live2d_desktop


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
