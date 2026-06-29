"""Environment readiness probe for release candidate setup.

No Qt, no network, no LLM/TTS/ASR calls, no memory access, no .env reads,
and no file writes.
"""

from __future__ import annotations

import ast
import builtins
import importlib
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _check_pyproject() -> bool:
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.is_file():
        return False
    content = pyproject.read_text(encoding="utf-8")
    return 'requires-python = ">=3.11"' in content


def _check_install_docs() -> bool:
    readme = _read_text("README.md")
    return (
        "pip install -r requirements.txt" not in readme
        and 'pip install -e ".[dev]"' in readme
        and "py -3.11 -m venv .venv" in readme
    )


def _check_run_script() -> bool:
    script = _read_text("scripts/run_desktop.ps1")
    return (
        "pip install -r requirements.txt" not in script
        and 'pip install -e ".[dev]"' in script
        and "sys.version_info >= (3, 11)" in script
        and "py -3.11 -c" in script
        and "Python >= 3.11 is required." in script
    )


def _with_sounddevice_blocked(check: Callable[[], bool]) -> bool:
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

    builtins.__import__ = guarded_import
    try:
        return check()
    finally:
        builtins.__import__ = real_import


def _recorder_has_no_top_level_sounddevice_import() -> bool:
    source = _read_text("app/input/audio/recorder.py")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Import):
            if any(alias.name == "sounddevice" for alias in node.names):
                return False
        if isinstance(node, ast.ImportFrom) and node.module == "sounddevice":
            return False
    return True


def _check_audio_import_boundary() -> bool:
    def check_imports() -> bool:
        import app.input.audio.recorder as recorder_module

        importlib.reload(recorder_module)
        importlib.import_module("app.input.audio")
        sys.modules.pop("app.input.asr.controller", None)
        importlib.import_module("app.input.asr.controller")
        return True

    try:
        return _recorder_has_no_top_level_sounddevice_import() and _with_sounddevice_blocked(
            check_imports
        )
    except Exception:
        return False


def main() -> int:
    print("Environment Readiness Probe\n")

    checks = {
        "pyproject": _check_pyproject(),
        "install docs": _check_install_docs(),
        "run script": _check_run_script(),
        "audio import boundary": _check_audio_import_boundary(),
    }

    for name, ok in checks.items():
        print(f"{name}: {'OK' if ok else 'FAIL'}")

    print()
    if all(checks.values()):
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
