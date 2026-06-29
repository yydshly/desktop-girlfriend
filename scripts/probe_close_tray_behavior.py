"""Close Tray Behavior Probe (Phase 3-A).

No real LLM/TTS/ASR, no memory access, no file writes.
Uses QT_QPA_PLATFORM=offscreen to avoid display requirement.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.close_behavior import decide_close_behavior, render_close_to_tray_hint
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


def main() -> int:
    print("Close Tray Behavior Probe\n")

    # Test close behavior decisions
    decision_tray = decide_close_behavior(tray_available=True, force_quit=False)
    if decision_tray.should_hide_to_tray and not decision_tray.should_accept_close:
        print("close decision: OK (tray available -> hide to tray)")
    else:
        print(f"close decision: FAIL (got should_hide={decision_tray.should_hide_to_tray}, should_accept={decision_tray.should_accept_close})")
        return 1

    decision_no_tray = decide_close_behavior(tray_available=False, force_quit=False)
    if not decision_no_tray.should_hide_to_tray and decision_no_tray.should_accept_close:
        print("close decision: OK (tray unavailable -> accept close)")
    else:
        print("close decision: FAIL (tray unavailable case)")
        return 1

    decision_force = decide_close_behavior(tray_available=True, force_quit=True)
    if not decision_force.should_hide_to_tray and decision_force.should_accept_close:
        print("close decision: OK (force quit -> accept close)")
    else:
        print("close decision: FAIL (force quit case)")
        return 1

    # Test hint rendering
    hint_tray = render_close_to_tray_hint(tray_available=True)
    if "托盘" in hint_tray and "隐藏" in hint_tray:
        print("hint (tray): OK")
    else:
        print("hint (tray): FAIL ('" + hint_tray + "')")
        return 1

    hint_no_tray = render_close_to_tray_hint(tray_available=False)
    if "退出" in hint_no_tray:
        print("hint (no tray): OK")
    else:
        print("hint (no tray): FAIL ('" + hint_no_tray + "')")
        return 1

    QApplication.instance() or QApplication(sys.argv)

    # Test window initialization with close callback
    vm = DesktopViewModel()
    close_called = [False]
    close_result = [True]

    def on_close() -> bool:
        close_called[0] = True
        return close_result[0]

    window = DesktopWindow(
        view_model=vm,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
        on_close_requested=on_close,
    )

    try:
        window.show()
        window.update_from_view_model()
        print("window: OK")
    except Exception as e:
        print(f"window: FAIL ({e})")
        return 1

    # Test settings button still works
    vm.set_settings_text("test settings")
    window._settings_button.clicked.emit()
    QApplication.instance().processEvents()
    if vm.settings_visible and window._settings_panel.isVisible():
        print("settings button: OK")
    else:
        print("settings button: FAIL")
        return 1

    # Test status button still works - create window2 with status callback
    vm2 = DesktopViewModel()

    def on_status2() -> None:
        vm2.toggle_product_status_visible()
        window2.update_from_view_model()

    window2 = DesktopWindow(
        view_model=vm2,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
        on_product_status_requested=on_status2,
        on_close_requested=on_close,
    )
    window2.show()
    window2.update_from_view_model()

    window2._product_status_button.pressed.emit()
    QApplication.instance().processEvents()
    if vm2.product_status_visible and window2._product_status_panel.isVisible():
        print("status button: OK")
    else:
        print("status button: FAIL")
        return 1

    # Test compact mode still works
    vm3 = DesktopViewModel()
    window3 = DesktopWindow(
        view_model=vm3,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
        on_close_requested=on_close,
    )
    window3.show()
    window3._handle_compact_clicked()
    QApplication.instance().processEvents()
    if vm3.compact_mode:
        print("compact mode: OK")
    else:
        print("compact mode: FAIL")
        return 1

    print()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
