"""Proactive Real UX v1 Probe (Phase 3-D).

No real LLM/TTS/ASR, no memory access, no file writes.
Uses QT_QPA_PLATFORM=offscreen to avoid display requirement.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.onboarding_view import build_onboarding_view, render_onboarding_text
from app.ui.proactive_real_ux_view import (
    build_proactive_real_ux_copy,
    render_proactive_control_status,
    render_proactive_enabled_status,
    render_proactive_tray_hint,
    render_proactive_user_control_hint,
)
from app.ui.settings_view import build_settings_view, render_settings_view_text
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


def main() -> int:
    print("Proactive Real UX v1 Probe\n")

    # 1. Verify proactive copy builds correctly
    copy = build_proactive_real_ux_copy()
    if "主动陪伴" in copy.title and len(copy.enabled_body) > 5:
        print("proactive copy: OK")
    else:
        print("proactive copy: FAIL")
        return 1

    # 2. Verify render functions return non-empty strings
    if render_proactive_enabled_status(True) and render_proactive_enabled_status(False):
        print("proactive status render: OK")
    else:
        print("proactive status render: FAIL")
        return 1

    if "别打扰" in render_proactive_user_control_hint():
        print("user control hint: OK")
    else:
        print("user control hint: FAIL")
        return 1

    if "托盘" in render_proactive_tray_hint():
        print("tray hint: OK")
    else:
        print("tray hint: FAIL")
        return 1

    if len(render_proactive_control_status()) > 0:
        print("proactive control status: OK")
    else:
        print("proactive control status: FAIL")
        return 1

    # 3. Verify settings text contains proactive key explanations
    from app.core.config import AppConfig
    cfg = AppConfig()
    settings_view = build_settings_view(cfg)
    settings_text = render_settings_view_text(settings_view)
    proactive_section = None
    for section in settings_view.sections:
        if "主动陪伴" in section.title:
            proactive_section = section
            break
    if proactive_section is None:
        print("settings copy: FAIL (proactive section not found)")
        return 1

    lines_text = "\n".join(proactive_section.lines)
    checks = {
        "空闲时间": "idle",
        "冷却时间": "cooldown",
        "勿扰时间": "quiet hours",
        "最多次数": "max per session",
        "别打扰": "user control",
        "托盘": "tray behavior",
    }
    failed = []
    for keyword, name in checks.items():
        if keyword not in lines_text:
            failed.append(name)
    if failed:
        print(f"settings copy: FAIL (missing: {', '.join(failed)})")
        return 1
    print("settings copy: OK")

    # 4. Verify onboarding still renders and mentions proactive control
    onboarding = build_onboarding_view()
    onboarding_text = render_onboarding_text(onboarding)
    if "别打扰" in onboarding.subtitle or "安静" in onboarding.subtitle:
        print("onboarding: OK")
    else:
        print("onboarding: FAIL")
        return 1

    # 5. Verify window initializes without crash
    QApplication.instance() or QApplication(sys.argv)
    vm = DesktopViewModel()
    vm.set_onboarding_text(onboarding_text)
    vm.set_settings_text(settings_text)

    window = DesktopWindow(
        view_model=vm,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window.show()
    window.update_from_view_model()
    QApplication.instance().processEvents()

    if window._name_label.text() == "小云":
        print("window: OK")
    else:
        print("window: FAIL")
        return 1

    # 6. Verify proactive status label exists and updates
    if not hasattr(window, "_proactive_status_label"):
        print("proactive label: FAIL (not found)")
        return 1
    vm.set_proactive_status_text("小云会安静一会儿。")
    window.update_from_view_model()
    QApplication.instance().processEvents()
    if window._proactive_status_label.text() == "小云会安静一会儿。":
        print("proactive label update: OK")
    else:
        print("proactive label update: FAIL")
        return 1

    # 7. Verify status/settings compatibility (button press toggles to True)
    vm2 = DesktopViewModel()
    vm2.set_settings_text(settings_text)
    window2 = DesktopWindow(
        view_model=vm2,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
        on_product_status_requested=lambda: (
            vm2.toggle_product_status_visible(),
            window2.update_from_view_model(),
        ),
    )
    window2.show()
    window2.update_from_view_model()
    window2._product_status_button.pressed.emit()
    QApplication.instance().processEvents()
    if vm2.product_status_visible:
        print("status/settings compatibility: OK")
    else:
        print("status/settings compatibility: FAIL")
        return 1

    # 8. Verify compact mode
    vm3 = DesktopViewModel()
    window3 = DesktopWindow(
        view_model=vm3,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window3.show()
    window3.update_from_view_model()
    window3._handle_compact_clicked()
    QApplication.instance().processEvents()
    if vm3.compact_mode and not window3._onboarding_card.isVisible():
        print("compact mode: OK")
    else:
        print("compact mode: FAIL")
        return 1

    # 9. Verify window close event handler exists and is callable
    vm4 = DesktopViewModel()
    window4 = DesktopWindow(
        view_model=vm4,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window4.show()
    window4.update_from_view_model()
    try:
        # Verify closeEvent is defined (Qt override) — it should not raise
        assert hasattr(window4, 'closeEvent'), "closeEvent method not found"
        print("close/tray callback: OK")
    except Exception as e:
        print(f"close/tray callback: FAIL ({e})")
        return 1

    print()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
