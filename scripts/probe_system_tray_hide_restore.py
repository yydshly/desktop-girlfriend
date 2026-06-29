"""System Tray Hide Restore Probe (Phase 2-F).

Uses QT_QPA_PLATFORM=offscreen to avoid display requirement.
No real LLM/TTS/ASR, no memory access, no file writes, no network.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.system_tray import DesktopSystemTrayController
from app.ui.tray_view import build_tray_view, render_tray_availability_text
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


def main() -> int:
    print("System Tray Hide Restore Probe\n")

    QApplication.instance() or QApplication(sys.argv)

    checks_passed = True

    # Verify tray_view functions
    tray_view = build_tray_view()
    if "小云" in tray_view.tooltip:
        print("tray_view: OK (tooltip contains 小云)")
    else:
        print(f"tray_view: FAIL (tooltip='{tray_view.tooltip}')")
        checks_passed = False

    if tray_view.show_text == "显示小云":
        print("tray_view: OK (show_text correct)")
    else:
        print(f"tray_view: FAIL (show_text='{tray_view.show_text}')")
        checks_passed = False

    if tray_view.hide_text == "隐藏小云":
        print("tray_view: OK (hide_text correct)")
    else:
        print(f"tray_view: FAIL (hide_text='{tray_view.hide_text}')")
        checks_passed = False

    if tray_view.quit_text == "退出":
        print("tray_view: OK (quit_text correct)")
    else:
        print(f"tray_view: FAIL (quit_text='{tray_view.quit_text}')")
        checks_passed = False

    # Verify tray availability text
    if render_tray_availability_text(True) == "托盘可用":
        print("tray_availability: OK (true -> 托盘可用)")
    else:
        print("tray_availability: FAIL")
        checks_passed = False

    if render_tray_availability_text(False) == "托盘不可用":
        print("tray_availability: OK (false -> 托盘不可用)")
    else:
        print("tray_availability: FAIL")
        checks_passed = False

    # Verify ViewModel tray fields
    vm = DesktopViewModel()
    if vm.tray_available is False:
        print("view_model: OK (tray_available defaults false)")
    else:
        print("view_model: FAIL (tray_available should default false)")
        checks_passed = False

    if vm.hidden_to_tray is False:
        print("view_model: OK (hidden_to_tray defaults false)")
    else:
        print("view_model: FAIL (hidden_to_tray should default false)")
        checks_passed = False

    vm.set_tray_available(True)
    if vm.tray_available is True:
        print("view_model: OK (set_tray_available works)")
    else:
        print("view_model: FAIL (set_tray_available broken)")
        checks_passed = False

    vm.set_hidden_to_tray(True)
    if vm.hidden_to_tray is True:
        print("view_model: OK (set_hidden_to_tray works)")
    else:
        print("view_model: FAIL (set_hidden_to_tray broken)")
        checks_passed = False

    # Create window with hide callback
    window = DesktopWindow(
        view_model=vm,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
        on_hide_requested=lambda: None,
    )

    try:
        window.show()
        window.update_from_view_model()
        print("window: OK")
    except Exception as e:
        print(f"window: FAIL ({e})")
        return 1

    # Verify hide button exists
    if hasattr(window, "_hide_button") and window._hide_button.text() == "隐藏":
        print("hide button: OK (exists with correct text)")
    else:
        label = getattr(window, "_hide_button", None).text() if hasattr(window, "_hide_button") else "MISSING"
        print(f"hide button: FAIL (label='{label}')")
        return 1

    # Test hide button click
    hide_called = False

    def on_hide() -> None:
        nonlocal hide_called
        hide_called = True

    window._on_hide_requested = on_hide
    window._hide_button.clicked.emit()
    QApplication.instance().processEvents()

    if hide_called:
        print("hide action: OK (callback triggered)")
    else:
        print("hide action: FAIL (callback not triggered)")
        checks_passed = False

    # Test tray controller initialization (may not have real tray in offscreen)
    quit_called = False

    def on_quit() -> None:
        nonlocal quit_called
        quit_called = True

    try:
        tray_ctrl = DesktopSystemTrayController(
            window=window,
            on_quit=on_quit,
        )
        print("tray controller: OK (initializes without crash)")

        if tray_ctrl.available is False:
            print("tray controller: OK (tray not available in offscreen)")
        else:
            print("tray controller: INFO (tray available in this environment)")
    except Exception as e:
        print(f"tray controller: FAIL ({e})")
        checks_passed = False

    # Verify status button still works
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

    # Verify settings button still works
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
    initial_chat_count = len(vm.chat_messages)
    window._handle_compact_clicked()
    QApplication.instance().processEvents()

    if vm.compact_mode and not window._hide_button.isVisible():
        print("compact mode: OK (hides hide button)")
    else:
        print("compact mode: FAIL")
        checks_passed = False

    # Verify chat messages preserved
    if len(vm.chat_messages) == initial_chat_count:
        print("compact mode: OK (chat messages preserved)")
    else:
        print("compact mode: FAIL (chat messages cleared)")
        checks_passed = False

    if not checks_passed:
        print("\nFAIL")
        return 1

    print()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
