"""Avatar Expression Polish Probe (Phase 2-H).

Uses QT_QPA_PLATFORM=offscreen to avoid display requirement.
No real LLM/TTS/ASR, no memory access, no file writes, no network.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.avatar_action import AvatarAction
from app.ui.avatar_expression_view import build_avatar_expression_view
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


def main() -> int:
    print("Avatar Expression Polish Probe\n")

    QApplication.instance() or QApplication(sys.argv)

    checks_passed = True

    # Verify avatar expressions for all actions
    expected_labels = {
        AvatarAction.IDLE: "安静陪着你",
        AvatarAction.LISTENING: "认真听你说",
        AvatarAction.THINKING: "想一想",
        AvatarAction.SPEAKING: "回应你",
        AvatarAction.PROACTIVE: "来陪你一下",
        AvatarAction.ERROR: "有点小状况",
    }

    for action, expected_label in expected_labels.items():
        expr = build_avatar_expression_view(action)
        if expr.label == expected_label:
            print(f"avatar expressions: OK ({action.value} -> {expected_label})")
        else:
            print(f"avatar expressions: FAIL ({action.value} -> got '{expr.label}', expected '{expected_label}')")
            checks_passed = False

        if not expr.emoji:
            print(f"avatar expressions: FAIL ({action.value} missing emoji)")
            checks_passed = False

        if not expr.aria_text:
            print(f"avatar expressions: FAIL ({action.value} missing aria_text)")
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

    # Verify avatar expression label exists
    if hasattr(window, "_avatar_expression_label"):
        print("avatar expression label: OK (exists)")
    else:
        print("avatar expression label: FAIL (missing)")
        checks_passed = False

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

    # Verify compact mode switches
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

    if not vm.compact_mode:
        print("compact mode: OK (exited compact)")
    else:
        print("compact mode: FAIL (did not exit)")
        checks_passed = False

    # Verify hide button exists
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
