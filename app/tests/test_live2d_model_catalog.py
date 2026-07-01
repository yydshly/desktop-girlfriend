"""Tests for local Live2D model package discovery and diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

from app.ui.live2d_model_catalog import (
    Live2DModelPackageStatus,
    build_live2d_model_options,
    inspect_live2d_model_package,
    render_live2d_model_catalog_summary,
    scan_live2d_model_catalog,
)


def _write_model(
    path: Path,
    *,
    moc: str = "model.moc3",
    textures: list[str] | None = None,
    motions: dict | None = None,
    physics: str = "model.physics3.json",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "Version": 3,
                "FileReferences": {
                    "Moc": moc,
                    "Textures": textures if textures is not None else ["texture_00.png"],
                    "Physics": physics,
                    "Motions": motions
                    if motions is not None
                    else {"Idle": [{"File": "motions/idle.motion3.json"}]},
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_inspect_live2d_model_package_reports_ready_package(tmp_path: Path) -> None:
    """A complete model3 package reports counts and ready status."""
    model_path = tmp_path / "custom" / "Xiaoyun" / "Xiaoyun.model3.json"
    _write_model(
        model_path,
        textures=["texture_00.png", "texture_01.png"],
        motions={
            "Idle": [{"File": "motions/idle.motion3.json"}],
            "TapBody": [{"File": "motions/tap.motion3.json"}],
        },
    )

    package = inspect_live2d_model_package(model_path, catalog_root=tmp_path)

    assert package.status == Live2DModelPackageStatus.READY
    assert package.model_id == "custom/Xiaoyun"
    assert package.display_name == "Xiaoyun"
    assert package.relative_model_json == "custom/Xiaoyun/Xiaoyun.model3.json"
    assert package.texture_count == 2
    assert package.motion_count == 2
    assert package.motion_groups == ("Idle", "TapBody")
    assert package.missing == ()


def test_inspect_live2d_model_package_reports_missing_required_parts(
    tmp_path: Path,
) -> None:
    """Missing moc or textures produce an actionable diagnostic."""
    model_path = tmp_path / "broken" / "Broken.model3.json"
    _write_model(model_path, moc="", textures=[])

    package = inspect_live2d_model_package(model_path, catalog_root=tmp_path)

    assert package.status == Live2DModelPackageStatus.BROKEN
    assert package.missing == ("Moc", "Textures")


def test_scan_live2d_model_catalog_sorts_model_packages(tmp_path: Path) -> None:
    """Catalog scanning finds model3 packages recursively in stable order."""
    _write_model(tmp_path / "sample" / "Hiyori" / "Hiyori.model3.json")
    _write_model(tmp_path / "custom" / "Xiaoyun" / "Xiaoyun.model3.json")

    packages = scan_live2d_model_catalog(tmp_path)

    assert [package.model_id for package in packages] == [
        "custom/Xiaoyun",
        "sample/Hiyori",
    ]


def test_render_live2d_model_catalog_summary_reports_ready_primary_model(
    tmp_path: Path,
) -> None:
    """Catalog summary makes the selected model health visible in the UI."""
    model_path = tmp_path / "custom" / "Xiaoyun" / "Xiaoyun.model3.json"
    _write_model(
        model_path,
        textures=["texture_00.png", "texture_01.png"],
        motions={
            "Idle": [{"File": "motions/idle.motion3.json"}],
            "TapBody": [{"File": "motions/tap.motion3.json"}],
        },
    )
    package = inspect_live2d_model_package(model_path, catalog_root=tmp_path)

    assert render_live2d_model_catalog_summary((package,)) == (
        "Model: Xiaoyun · ready · motions 2 · textures 2"
    )


def test_render_live2d_model_catalog_summary_reports_broken_primary_model(
    tmp_path: Path,
) -> None:
    """Broken model packages include actionable missing-part diagnostics."""
    model_path = tmp_path / "broken" / "Broken.model3.json"
    _write_model(model_path, moc="", textures=[])
    package = inspect_live2d_model_package(model_path, catalog_root=tmp_path)

    assert render_live2d_model_catalog_summary((package,)) == (
        "Model: Broken · broken · missing Moc, Textures"
    )


def test_render_live2d_model_catalog_summary_reports_empty_catalog() -> None:
    """Empty model directories produce a clear status instead of a blank label."""
    assert render_live2d_model_catalog_summary(()) == (
        "Model: no local Live2D model packages found"
    )


def test_build_live2d_model_options_uses_model_ids_and_display_names(
    tmp_path: Path,
) -> None:
    """Catalog packages become stable model selector options."""
    _write_model(tmp_path / "sample" / "Hiyori" / "Hiyori.model3.json")
    _write_model(tmp_path / "custom" / "Xiaoyun" / "Xiaoyun.model3.json")
    packages = scan_live2d_model_catalog(tmp_path)

    assert build_live2d_model_options(packages) == (
        ("custom/Xiaoyun", "Xiaoyun"),
        ("sample/Hiyori", "Hiyori"),
    )
