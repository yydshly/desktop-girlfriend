"""Settings Runtime Controls Probe (Phase 2-E).

Uses QT_QPA_PLATFORM=offscreen to avoid display requirement.
No real LLM/TTS/ASR, no memory access, no file writes, no network.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.settings_view import build_settings_view, render_settings_view_text
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


def main() -> int:
    print("Settings Runtime Controls Probe\n")

    QApplication.instance() or QApplication(sys.argv)

    # Verify settings view content
    from app.core.config import AppConfig

    config = AppConfig()
    config.minimax_api_key = "sk-real-looking-key-1234567890abcdef"
    config.mimo_api_key = "sk-another-real-key-abcdef1234567890"

    view = build_settings_view(config)
    text = render_settings_view_text(view)

    checks_passed = True

    # Safety checks: no real API keys leaked
    if "sk-real-looking-key-1234567890abcdef" in text:
        print("safety: FAIL (real minimax key leaked)")
        checks_passed = False
    elif "sk-another-real-key-abcdef1234567890" in text:
        print("safety: FAIL (real mimo key leaked)")
        checks_passed = False
    else:
        print("safety: OK")

    if "0.1.0-rc.3" in text:
        print("settings view: OK (version present)")
    else:
        print("settings view: FAIL (version missing)")
        checks_passed = False

    if "release-candidate" in text:
        print("settings view: OK (release stage present)")
    else:
        print("settings view: FAIL (release stage missing)")
        checks_passed = False

    if "已配置" in text or "未配置" in text:
        print("settings view: OK (api key status shown)")
    else:
        print("settings view: FAIL (api key status missing)")
        checks_passed = False

    # Create window
    vm = DesktopViewModel()
    vm.set_settings_text(text)

    window = DesktopWindow(
        view_model=vm,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )

    try:
        window.show()
        window.update_from_view_model()
        print("window: OK")
    except Exception as e:
        print(f"window: FAIL ({e})")
        return 1

    # Verify settings button exists
    if hasattr(window, "_settings_button") and window._settings_button.text() == "设置":
        print("settings button: OK")
    else:
        label = getattr(window, "_settings_button", None).text() if hasattr(window, "_settings_button") else "MISSING"
        print(f"settings button: FAIL (label='{label}')")
        return 1

    # Test settings button click
    window._settings_button.clicked.emit()
    QApplication.instance().processEvents()

    if vm.settings_visible and window._settings_panel.isVisible():
        print("settings button: OK (opens panel)")
    else:
        print("settings button: FAIL (panel did not open)")
        return 1

    # Second click closes
    window._settings_button.clicked.emit()
    QApplication.instance().processEvents()

    if not vm.settings_visible and not window._settings_panel.isVisible():
        print("settings button: OK (closes panel)")
    else:
        print("settings button: FAIL (panel did not close)")
        return 1

    if not checks_passed:
        print("\nFAIL")
        return 1

    print()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
