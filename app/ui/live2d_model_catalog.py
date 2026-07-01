"""Local Live2D model package discovery and diagnostics."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class Live2DModelPackageStatus(StrEnum):
    """Health status for a discovered Live2D model package."""

    READY = "ready"
    BROKEN = "broken"


@dataclass(frozen=True)
class Live2DModelPackage:
    """Metadata extracted from one `.model3.json` package."""

    model_id: str
    display_name: str
    model_json: Path
    relative_model_json: str
    status: Live2DModelPackageStatus
    missing: tuple[str, ...]
    texture_count: int
    motion_count: int
    motion_groups: tuple[str, ...]
    moc: str = ""
    physics: str = ""


def inspect_live2d_model_package(
    model_json: Path,
    *,
    catalog_root: Path,
) -> Live2DModelPackage:
    """Inspect one model3 package without loading the native Live2D runtime."""
    model_json = model_json.resolve()
    catalog_root = catalog_root.resolve()

    data = _read_model_json(model_json)
    references = data.get("FileReferences", {})
    if not isinstance(references, dict):
        references = {}

    moc = _string_value(references.get("Moc"))
    physics = _string_value(references.get("Physics"))
    textures = _string_list(references.get("Textures"))
    motions = references.get("Motions", {})
    if not isinstance(motions, dict):
        motions = {}

    missing: list[str] = []
    if not moc:
        missing.append("Moc")
    if not textures:
        missing.append("Textures")

    return Live2DModelPackage(
        model_id=_model_id(model_json, catalog_root),
        display_name=_display_name(model_json),
        model_json=model_json,
        relative_model_json=_relative_path(model_json, catalog_root),
        status=Live2DModelPackageStatus.BROKEN
        if missing
        else Live2DModelPackageStatus.READY,
        missing=tuple(missing),
        texture_count=len(textures),
        motion_count=_motion_count(motions),
        motion_groups=tuple(str(group) for group in motions.keys()),
        moc=moc,
        physics=physics,
    )


def scan_live2d_model_catalog(catalog_root: Path) -> tuple[Live2DModelPackage, ...]:
    """Find model3 packages under a catalog root in stable order."""
    catalog_root = catalog_root.resolve()
    if not catalog_root.exists():
        return ()

    model_paths = sorted(
        catalog_root.rglob("*.model3.json"),
        key=lambda path: _relative_path(path, catalog_root),
    )
    return tuple(
        inspect_live2d_model_package(model_path, catalog_root=catalog_root)
        for model_path in model_paths
    )


def render_live2d_model_catalog_summary(
    packages: tuple[Live2DModelPackage, ...],
) -> str:
    """Render a compact model package status for the desktop control surface."""
    if not packages:
        return "Model: no local Live2D model packages found"

    primary = packages[0]
    if primary.status == Live2DModelPackageStatus.BROKEN:
        missing = ", ".join(primary.missing) if primary.missing else "unknown parts"
        return f"Model: {primary.display_name} · broken · missing {missing}"

    return (
        f"Model: {primary.display_name} · ready · "
        f"motions {primary.motion_count} · textures {primary.texture_count}"
    )


def build_live2d_model_options(
    packages: tuple[Live2DModelPackage, ...],
) -> tuple[tuple[str, str], ...]:
    """Build `(model_id, label)` pairs for the desktop model selector."""
    return tuple((package.model_id, package.display_name) for package in packages)


def render_live2d_model_catalog_details(
    catalog_root: Path,
    packages: tuple[Live2DModelPackage, ...],
) -> str:
    """Render detailed diagnostics for local Live2D model packages."""
    ready_count = sum(
        1 for package in packages if package.status == Live2DModelPackageStatus.READY
    )
    broken_count = len(packages) - ready_count
    lines = [
        f"Models folder: {catalog_root}",
        f"Ready: {ready_count}, broken: {broken_count}",
    ]
    if not packages:
        lines.append("Put model folders under custom/<Name>/<Name>.model3.json")
        return "\n".join(lines)

    for package in packages:
        if package.status == Live2DModelPackageStatus.BROKEN:
            missing = ", ".join(package.missing) if package.missing else "unknown parts"
            lines.append(f"{package.model_id}: broken, missing {missing}")
            continue
        lines.append(
            f"{package.model_id}: ready, motions {package.motion_count}, "
            f"textures {package.texture_count}"
        )
    return "\n".join(lines)


def _read_model_json(model_json: Path) -> dict[str, Any]:
    try:
        data = json.loads(model_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _string_value(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _string_list(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def _motion_count(motions: dict[Any, Any]) -> int:
    total = 0
    for entries in motions.values():
        if isinstance(entries, list):
            total += len(entries)
    return total


def _model_id(model_json: Path, catalog_root: Path) -> str:
    try:
        relative_parent = model_json.parent.relative_to(catalog_root)
    except ValueError:
        return model_json.parent.name or model_json.stem

    model_id = relative_parent.as_posix()
    if model_id == ".":
        return _display_name(model_json)
    display_name = _display_name(model_json)
    if relative_parent.name != display_name:
        return f"{model_id}/{display_name}"
    return model_id


def _display_name(model_json: Path) -> str:
    return model_json.name.removesuffix(".model3.json") or model_json.parent.name


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
