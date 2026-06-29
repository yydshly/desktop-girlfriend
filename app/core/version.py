from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppVersion:
    version: str
    release_name: str
    release_stage: str


_DEFAULT_VERSION = "0.3.0-alpha.1"
_RELEASE_NAME = "Desktop Girlfriend Alpha"
_RELEASE_STAGE = "alpha"


def read_version(version_file: Path | None = None) -> str:
    if version_file is None:
        version_file = Path(__file__).resolve().parents[2] / "VERSION"

    try:
        value = version_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return _DEFAULT_VERSION

    return value or _DEFAULT_VERSION


def get_app_version(version_file: Path | None = None) -> AppVersion:
    return AppVersion(
        version=read_version(version_file),
        release_name=_RELEASE_NAME,
        release_stage=_RELEASE_STAGE,
    )
