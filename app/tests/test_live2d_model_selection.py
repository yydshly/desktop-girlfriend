from pathlib import Path

from app.ui.live2d_model_selection import (
    default_live2d_model_selection_path,
    load_selected_live2d_model_id,
    save_selected_live2d_model_id,
)


def test_default_live2d_model_selection_path_is_local_tmp() -> None:
    assert default_live2d_model_selection_path() == Path(
        ".tmp/live2d-model-selection.json"
    )


def test_live2d_model_selection_round_trips_selected_model_id(tmp_path: Path) -> None:
    path = tmp_path / "selection.json"

    save_selected_live2d_model_id(path, "sample/Natori")

    assert load_selected_live2d_model_id(path) == "sample/Natori"


def test_live2d_model_selection_ignores_missing_or_invalid_files(
    tmp_path: Path,
) -> None:
    missing_path = tmp_path / "missing.json"
    invalid_path = tmp_path / "invalid.json"
    empty_path = tmp_path / "empty.json"
    invalid_path.write_text("{", encoding="utf-8")
    empty_path.write_text('{"model_id": "   "}', encoding="utf-8")

    assert load_selected_live2d_model_id(missing_path) == ""
    assert load_selected_live2d_model_id(invalid_path) == ""
    assert load_selected_live2d_model_id(empty_path) == ""
