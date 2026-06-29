"""Proactive Companion UX Probe (Phase 2-G).

Uses QT_QPA_PLATFORM=offscreen to avoid display requirement.
No real LLM/TTS/ASR, no memory access, no file writes, no network.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.proactive_companion_view import (
    build_proactive_companion_view,
    render_proactive_message_prefix,
    render_proactive_status_text,
)
from app.ui.settings_view import build_settings_view, render_settings_view_text
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


def main() -> int:
    print("Proactive Companion UX Probe\n")

    QApplication.instance() or QApplication(sys.argv)

    checks_passed = True

    # Verify proactive view functions
    proactive_view = build_proactive_companion_view(
        enabled=True,
        quiet_hours_enabled=False,
        cooldown_seconds=300,
    )
    if "小云" in proactive_view.subtitle:
        print("proactive view: OK (subtitle contains 小云)")
    else:
        print(f"proactive view: FAIL (subtitle='{proactive_view.subtitle}')")
        checks_passed = False

    if proactive_view.message_prefix == "小云主动来陪你：":
        print("proactive view: OK (message_prefix correct)")
    else:
        print(f"proactive view: FAIL (message_prefix='{proactive_view.message_prefix}')")
        checks_passed = False

    disabled_view = build_proactive_companion_view(
        enabled=False,
        quiet_hours_enabled=True,
        cooldown_seconds=300,
    )
    if "未启用" in disabled_view.subtitle:
        print("proactive view: OK (disabled subtitle correct)")
    else:
        print(f"proactive view: FAIL (disabled subtitle='{disabled_view.subtitle}')")
        checks_passed = False

    prefix = render_proactive_message_prefix()
    if prefix == "小云主动来陪你：":
        print("proactive view: OK (message prefix function correct)")
    else:
        print(f"proactive view: FAIL (prefix='{prefix}')")
        checks_passed = False

    status_text = render_proactive_status_text()
    if status_text and len(status_text) > 0:
        print("proactive view: OK (status text non-empty)")
    else:
        print("proactive view: FAIL (status text empty)")
        checks_passed = False

    # Verify settings view includes proactive explanation
    from app.core.config import AppConfig

    config = AppConfig()
    config.proactive_enabled = True
    view = build_settings_view(config)
    text = render_settings_view_text(view)

    if "小云会在你空闲" in text:
        print("settings copy: OK (proactive description present)")
    else:
        print("settings copy: FAIL (proactive description missing)")
        checks_passed = False

    if "冷却时间" in text:
        print("settings copy: OK (cooldown explanation present)")
    else:
        print("settings copy: FAIL (cooldown explanation missing)")
        checks_passed = False

    if "别打扰" in text or "安静" in text:
        print("settings copy: OK (user control hint present)")
    else:
        print("settings copy: FAIL (user control hint missing)")
        checks_passed = False

    # Verify no API key leakage
    config.minimax_api_key = "sk-abcdefghijk1234567890"
    config.mimo_api_key = "sk-xyz1234567890abcdefgh"
    view = build_settings_view(config)
    text = render_settings_view_text(view)
    if "sk-abcdefghijk1234567890" not in text:
        print("settings copy: OK (no API key leak)")
    else:
        print("settings copy: FAIL (API key leaked)")
        checks_passed = False

    # Create window
    vm = DesktopViewModel()
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

    # Verify status button works
    def on_status() -> None:
        vm.toggle_product_status_visible()
        window.update_from_view_model()

    window._on_product_status_requested = on_status
    window._product_status_button.pressed.emit()
    QApplication.instance().processEvents()

    if vm.product_status_visible:
        print("status button: OK (panel opens)")
    else:
        print("status button: FAIL (panel did not open)")
        checks_passed = False

    # Close status panel
    window._product_status_button.pressed.emit()
    QApplication.instance().processEvents()

    # Verify settings button works
    vm.set_settings_text("test settings")

    def on_settings_toggle() -> None:
        vm.toggle_settings_visible()
        window.update_from_view_model()

    window._handle_settings_clicked = on_settings_toggle
    window._settings_button.clicked.emit()
    QApplication.instance().processEvents()

    if vm.settings_visible:
        print("settings button: OK (panel opens)")
    else:
        print("settings button: FAIL (panel did not open)")
        checks_passed = False

    # Verify compact mode still works
    window._handle_compact_clicked()
    QApplication.instance().processEvents()

    if vm.compact_mode:
        print("compact mode: OK (switched to compact)")
    else:
        print("compact mode: FAIL (did not switch)")
        checks_passed = False

    # Exit compact mode
    window._handle_compact_clicked()
    QApplication.instance().processEvents()

    # Verify hide button is safe
    if hasattr(window, "_hide_button"):
        print("hide button: OK (exists)")
    else:
        print("hide button: FAIL (missing)")
        checks_passed = False

    if not checks_passed:
        print("\nFAIL")
        return 1

    print()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
