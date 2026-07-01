"""Tests for local Live2D model package discovery and diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

from app.ui.live2d_model_catalog import (
    Live2DModelPackageStatus,
    build_live2d_model_options,
    inspect_live2d_model_package,
    render_live2d_model_catalog_details,
    render_live2d_model_catalog_summary,
    render_live2d_model_import_guide,
    scan_live2d_model_catalog,
)


def _write_model(
    path: Path,
    *,
    moc: str = "model.moc3",
    textures: list[str] | None = None,
    motions: dict | None = None,
    expressions: list[dict] | None = None,
    physics: str = "model.physics3.json",
    create_assets: bool = True,
) -> None:
    texture_refs = textures if textures is not None else ["texture_00.png"]
    motion_refs = motions if motions is not None else {
        "Idle": [{"File": "motions/idle.motion3.json"}]
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "Version": 3,
                "FileReferences": {
                    "Moc": moc,
                    "Textures": texture_refs,
                    "Physics": physics,
                    "Motions": motion_refs,
                    "Expressions": expressions or [],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    if not create_assets:
        return
    expression_refs = [
        item["File"]
        for item in expressions or []
        if isinstance(item, dict) and isinstance(item.get("File"), str)
    ]
    for asset in [moc, physics, *texture_refs, *_motion_files(motion_refs), *expression_refs]:
        if asset:
            asset_path = path.parent / asset
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            asset_path.write_text("asset", encoding="utf-8")


def _motion_files(motions: dict) -> list[str]:
    files: list[str] = []
    for entries in motions.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("File"), str):
                files.append(entry["File"])
    return files


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


def test_inspect_live2d_model_package_reports_visual_capabilities(
    tmp_path: Path,
) -> None:
    """Model diagnostics include motion groups and expression capacity."""
    model_path = tmp_path / "custom" / "Expressive" / "Expressive.model3.json"
    _write_model(
        model_path,
        motions={
            "Idle": [{"File": "motions/idle.motion3.json"}],
            "TapBody": [{"File": "motions/tap.motion3.json"}],
        },
        expressions=[
            {"Name": "smile", "File": "expressions/smile.exp3.json"},
            {"Name": "sad", "File": "expressions/sad.exp3.json"},
        ],
    )

    package = inspect_live2d_model_package(model_path, catalog_root=tmp_path)

    assert package.expression_count == 2
    assert package.expression_names == ("smile", "sad")


def test_inspect_live2d_model_package_reports_missing_required_parts(
    tmp_path: Path,
) -> None:
    """Missing moc or textures produce an actionable diagnostic."""
    model_path = tmp_path / "broken" / "Broken.model3.json"
    _write_model(model_path, moc="", textures=[])

    package = inspect_live2d_model_package(model_path, catalog_root=tmp_path)

    assert package.status == Live2DModelPackageStatus.BROKEN
    assert package.missing == ("Moc", "Textures")


def test_inspect_live2d_model_package_reports_missing_referenced_files(
    tmp_path: Path,
) -> None:
    """Referenced assets must exist next to the model package."""
    model_path = tmp_path / "broken" / "Broken.model3.json"
    _write_model(
        model_path,
        textures=["texture_00.png"],
        motions={"Idle": [{"File": "motions/idle.motion3.json"}]},
        create_assets=False,
    )

    package = inspect_live2d_model_package(model_path, catalog_root=tmp_path)

    assert package.status == Live2DModelPackageStatus.BROKEN
    assert package.missing == (
        "Moc file: model.moc3",
        "Texture file: texture_00.png",
        "Motion file: motions/idle.motion3.json",
        "Physics file: model.physics3.json",
    )


def test_inspect_live2d_model_package_reports_missing_expression_files(
    tmp_path: Path,
) -> None:
    """Expression files referenced by model3.json are validated."""
    model_path = tmp_path / "broken" / "Broken.model3.json"
    _write_model(
        model_path,
        expressions=[{"Name": "smile", "File": "expressions/smile.exp3.json"}],
        create_assets=False,
    )

    package = inspect_live2d_model_package(model_path, catalog_root=tmp_path)

    assert "Expression file: expressions/smile.exp3.json" in package.missing


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


def test_render_live2d_model_catalog_summary_follows_selected_model(
    tmp_path: Path,
) -> None:
    """Catalog summary can report the currently selected model package."""
    _write_model(tmp_path / "custom" / "Xiaoyun" / "Xiaoyun.model3.json")
    _write_model(
        tmp_path / "sample" / "Hiyori" / "Hiyori.model3.json",
        textures=["texture_00.png", "texture_01.png"],
        motions={
            "Idle": [{"File": "motions/idle.motion3.json"}],
            "TapBody": [{"File": "motions/tap.motion3.json"}],
        },
    )
    packages = scan_live2d_model_catalog(tmp_path)

    assert render_live2d_model_catalog_summary(
        packages,
        selected_model_id="sample/Hiyori",
    ) == "Model: Hiyori · ready · motions 2 · textures 2"


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


def test_render_live2d_model_catalog_details_reports_each_package(
    tmp_path: Path,
) -> None:
    """Catalog details explain where models live and why a package is broken."""
    _write_model(tmp_path / "sample" / "Hiyori" / "Hiyori.model3.json")
    _write_model(tmp_path / "broken" / "Broken.model3.json", moc="", textures=[])
    packages = scan_live2d_model_catalog(tmp_path)

    details = render_live2d_model_catalog_details(tmp_path, packages)

    assert f"Models folder: {tmp_path}" in details
    assert "Ready: 1, broken: 1" in details
    assert "broken/Broken: broken, missing Moc, Textures" in details
    assert (
        "sample/Hiyori: ready, motions 1, groups Idle, expressions 0, textures 1"
        in details
    )


def test_render_live2d_model_import_guide_reports_model_suitability(
    tmp_path: Path,
) -> None:
    """Import guide explains where models go and whether the active model is rich."""
    _write_model(tmp_path / "sample" / "Hiyori" / "Hiyori.model3.json")
    packages = scan_live2d_model_catalog(tmp_path)

    guide = render_live2d_model_import_guide(
        tmp_path,
        packages,
        selected_model_id="sample/Hiyori",
    )

    assert "Put custom models under" in guide
    assert "custom/<Name>/<Name>.model3.json" in guide
    assert "limited: add more motion groups or expressions" in guide
