from pathlib import Path

from app.ui.live2d_desktop_settings import (
    Live2DDesktopSettings,
    default_live2d_desktop_settings_path,
    load_live2d_desktop_settings,
    save_live2d_desktop_settings,
)


def test_default_live2d_desktop_settings_path_is_local_tmp() -> None:
    assert default_live2d_desktop_settings_path() == Path(
        ".tmp/live2d-desktop-settings.json"
    )


def test_missing_live2d_desktop_settings_use_product_defaults(
    tmp_path: Path,
) -> None:
    settings = load_live2d_desktop_settings(tmp_path / "missing.json")

    assert settings == Live2DDesktopSettings(scale=1.0, opacity=1.0, visible=True)


def test_live2d_desktop_settings_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"

    save_live2d_desktop_settings(
        path,
        Live2DDesktopSettings(scale=1.2, opacity=0.75, visible=False),
    )

    assert load_live2d_desktop_settings(path) == Live2DDesktopSettings(
        scale=1.2,
        opacity=0.75,
        visible=False,
    )


def test_live2d_desktop_settings_ignore_invalid_files(tmp_path: Path) -> None:
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text('{"scale": "large", "opacity": null}', encoding="utf-8")

    assert load_live2d_desktop_settings(invalid_path) == Live2DDesktopSettings()


def test_live2d_desktop_settings_are_clamped(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        '{"scale": 9, "opacity": -1, "visible": true}',
        encoding="utf-8",
    )

    assert load_live2d_desktop_settings(path) == Live2DDesktopSettings(
        scale=1.35,
        opacity=0.45,
        visible=True,
    )
