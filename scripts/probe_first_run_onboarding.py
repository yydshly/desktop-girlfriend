"""First Run Onboarding Probe (Phase 3-B).

No real LLM/TTS/ASR, no memory access, no file writes.
Uses QT_QPA_PLATFORM=offscreen to avoid display requirement.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.onboarding_view import build_onboarding_view, render_onboarding_text
from app.ui.product_status import ProductStatusItem, ProductStatusView
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


def main() -> int:
    print("First Run Onboarding Probe\n")

    # Test onboarding view content
    view = build_onboarding_view(companion_name="小云")
    text = render_onboarding_text(view)
    if "小云" in view.title and len(view.bullets) > 0:
        print("onboarding view: OK")
    else:
        print("onboarding view: FAIL")
        return 1

    if "语音输入" in text and "设置" in text and "状态" in text and "托盘" in text:
        print("onboarding content: OK")
    else:
        print("onboarding content: FAIL")
        return 1

    QApplication.instance() or QApplication(sys.argv)

    # Test window with onboarding
    vm = DesktopViewModel()
    vm.set_onboarding_text(text)
    vm.set_product_status_view(
        ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
    )

    window = DesktopWindow(
        view_model=vm,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window.show()
    # Phase 3-B fix: update_from_view_model MUST be called before show(),
    # and we verify initial render without any further manual update
    window.update_from_view_model()
    QApplication.instance().processEvents()

    # Verify onboarding card is visible by default
    if vm.onboarding_visible and window._onboarding_card.isVisible():
        print("onboarding visible: OK")
    else:
        print("onboarding visible: FAIL")
        return 1

    # Verify onboarding text is rendered on first frame (key fix verification)
    title = window._onboarding_title.text()
    subtitle = window._onboarding_subtitle.text()
    bullets = window._onboarding_bullets.text()
    if "小云" in title and len(subtitle) > 0 and len(bullets) > 0:
        print("initial render: OK")
    else:
        msg = f"initial render: FAIL (title='{title}', subtitle='{subtitle}', bullets='{bullets}')"
        print(msg)
        return 1

    if "语音输入" in bullets and "设置" in bullets and "托盘" in bullets:
        print("onboarding text: OK")
    else:
        print("onboarding text: FAIL")
        return 1

    # Test dismiss action
    window._onboarding_dismiss_button.clicked.emit()
    QApplication.instance().processEvents()
    if not vm.onboarding_visible and not window._onboarding_card.isVisible():
        print("dismiss action: OK")
    else:
        print("dismiss action: FAIL")
        return 1

    # Test open settings action - create new window
    vm2 = DesktopViewModel()
    vm2.set_onboarding_text(text)
    vm2.set_settings_text("test settings")

    def on_settings_clicked() -> None:
        vm2.toggle_settings_visible()
        window2.update_from_view_model()

    window2 = DesktopWindow(
        view_model=vm2,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window2._settings_button.clicked.connect(on_settings_clicked)
    window2.show()
    window2.update_from_view_model()

    # Click "打开设置" on onboarding
    window2._onboarding_settings_button.clicked.emit()
    QApplication.instance().processEvents()
    if not vm2.onboarding_visible and vm2.settings_visible and not vm2.product_status_visible:
        print("open settings action: OK")
    else:
        print("open settings action: FAIL")
        return 1

    # Verify status/settings compatibility after onboarding
    def on_status() -> None:
        vm2.toggle_product_status_visible()
        window2.update_from_view_model()

    window3 = DesktopWindow(
        view_model=vm2,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
        on_product_status_requested=on_status,
    )
    window3.show()
    window3.update_from_view_model()

    # Verify status button still works
    window3._product_status_button.pressed.emit()
    QApplication.instance().processEvents()
    if vm2.product_status_visible:
        print("status/settings compatibility: OK")
    else:
        print("status/settings compatibility: FAIL")
        return 1

    # Verify compact mode hides onboarding
    vm4 = DesktopViewModel()
    vm4.set_onboarding_text(text)
    window4 = DesktopWindow(
        view_model=vm4,
        on_user_text_submitted=lambda t: None,
        on_conversation_cleared=lambda: None,
    )
    window4.show()
    window4.update_from_view_model()
    window4._handle_compact_clicked()
    QApplication.instance().processEvents()
    if not vm4.onboarding_visible and vm4.compact_mode:
        print("compact mode: OK")
    else:
        print("compact mode: FAIL")
        return 1

    print()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
