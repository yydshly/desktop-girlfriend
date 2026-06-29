"""v0.2.0-alpha.1 Readiness Probe.

No Qt, no network, no real LLM/TTS/ASR, no memory access, no file writes.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _check_version() -> bool:
    version_file = REPO_ROOT / "VERSION"
    if not version_file.is_file():
        print("VERSION: missing")
        return False
    content = version_file.read_text(encoding="utf-8").strip()
    if content != "0.2.0-alpha.1":
        print(f"VERSION: unexpected '{content}'")
        return False
    print("VERSION: OK")
    return True


def _check_release_stage() -> bool:
    from app.core.version import get_app_version

    ver = get_app_version()
    if ver.release_stage != "alpha":
        print(f"release_stage: unexpected '{ver.release_stage}'")
        return False
    print("release stage: OK")
    return True


def _check_ui_modules() -> bool:
    ui_modules = [
        "app.ui.avatar_action",
        "app.ui.avatar_expression_view",
        "app.ui.companion_presence",
        "app.ui.desktop_presence",
        "app.ui.memory_record_view",
        "app.ui.memory_suggestion",
        "app.ui.product_status",
        "app.ui.product_status_builder",
        "app.ui.proactive_companion_view",
        "app.ui.settings_view",
        "app.ui.startup_diagnostics_view",
        "app.ui.system_tray",
        "app.ui.tray_view",
        "app.ui.conversation_view",
        "app.ui.window",
        "app.ui.window_style",
    ]
    missing = []
    for mod in ui_modules:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        print(f"ui modules: missing {missing}")
        return False
    print("ui modules: OK")
    return True


def _check_settings_safety() -> bool:
    from app.core.config import AppConfig
    from app.ui.settings_view import build_settings_view, render_settings_view_text

    cfg = AppConfig()
    cfg.minimax_api_key = "sk-abcdefghijk1234567890"
    cfg.mimo_api_key = "sk-xyz1234567890abcdefgh"
    view = build_settings_view(cfg)
    text = render_settings_view_text(view)
    if "sk-abcdefghijk1234567890" in text:
        print("settings safety: FAIL (API key leaked)")
        return False
    if "sk-xyz1234567890abcdefgh" in text:
        print("settings safety: FAIL (API key leaked)")
        return False
    print("settings safety: OK")
    return True


def main() -> int:
    print("v0.2.0-alpha.1 Readiness Probe\n")

    checks = {
        "version": _check_version(),
        "release stage": _check_release_stage(),
        "ui modules": _check_ui_modules(),
        "settings safety": _check_settings_safety(),
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
    sys.exit(main())
