"""Environment readiness checks for release candidate setup."""

from __future__ import annotations

import ast
import builtins
import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _read_repo_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_readme_does_not_use_requirements_install() -> None:
    content = _read_repo_text("README.md")
    assert "pip install -r requirements.txt" not in content


def test_readme_uses_pyproject_dev_install() -> None:
    content = _read_repo_text("README.md")
    assert 'pip install -e ".[dev]"' in content


def test_readme_uses_python_311_launcher_for_venv() -> None:
    content = _read_repo_text("README.md")
    # Windows PowerShell launcher approach
    assert "py -3.11 -m venv .venv" in content
    # Linux/macOS python approach is also acceptable
    # (README may contain both; the important thing is py launcher is present)
    assert "python -m venv .venv" in content or "py -3.11" in content


def test_run_desktop_does_not_use_requirements_install() -> None:
    content = _read_repo_text("scripts/run_desktop.ps1")
    assert "pip install -r requirements.txt" not in content


def test_run_desktop_uses_pyproject_dev_install() -> None:
    content = _read_repo_text("scripts/run_desktop.ps1")
    assert 'pip install -e ".[dev]"' in content


def test_run_desktop_checks_python_311() -> None:
    content = _read_repo_text("scripts/run_desktop.ps1")
    assert "sys.version_info >= (3, 11)" in content
    assert "py -3.11 -c" in content
    assert "Python >= 3.11 is required." in content


def test_pyproject_requires_python_311_or_newer() -> None:
    content = _read_repo_text("pyproject.toml")
    assert 'requires-python = ">=3.11"' in content


def _block_sounddevice_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import = builtins.__import__

    def guarded_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> ModuleType:
        if name == "sounddevice" or name.startswith("sounddevice."):
            raise ModuleNotFoundError("No module named 'sounddevice'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)


def test_importing_audio_package_does_not_require_sounddevice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_sounddevice_import(monkeypatch)
    import app.input.audio.recorder as recorder_module

    importlib.reload(recorder_module)
    importlib.import_module("app.input.audio")


def test_importing_asr_controller_does_not_require_sounddevice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_sounddevice_import(monkeypatch)
    sys.modules.pop("app.input.asr.controller", None)
    importlib.import_module("app.input.asr.controller")


def test_recorder_has_no_top_level_sounddevice_import() -> None:
    source = _read_repo_text("app/input/audio/recorder.py")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Import):
            assert all(alias.name != "sounddevice" for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "sounddevice"
