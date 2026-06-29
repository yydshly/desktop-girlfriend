"""Companion Presence UI Probe (Phase 2-A).

Uses QT_QPA_PLATFORM=offscreen to avoid display requirement.
No real LLM/TTS/ASR, no memory access, no file writes, no network.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.avatar_action import AvatarAction
from app.ui.product_status import ProductStatusItem, ProductStatusView
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


def main() -> int:
    print("Companion Presence UI Probe\n")

    QApplication.instance() or QApplication(sys.argv)

    # Create view model
    vm = DesktopViewModel()

    # Create window
    window = DesktopWindow(
        view_model=vm,
        on_user_text_submitted=lambda text: None,
        on_conversation_cleared=lambda: None,
    )

    # Verify window initializes
    try:
        window.show()
        window.update_from_view_model()
        print("window: OK")
    except Exception as e:
        print(f"window: FAIL ({e})")
        return 1

    # Verify header contains companion name
    if "小云" in window._name_label.text():
        print("header: OK")
    else:
        print(f"header: FAIL (name='{window._name_label.text()}')")
        return 1

    # Verify subtitle
    if "你的桌面 AI 伙伴" in window._subtitle_label.text():
        print("subtitle: OK")
    else:
        print(f"subtitle: FAIL (subtitle='{window._subtitle_label.text()}')")
        return 1

    # Verify version text
    if "0.1.0-rc.3" in window._version_label.text():
        print("version label: OK")
    else:
        print(f"version label: FAIL ('{window._version_label.text()}')")
        return 1

    # Verify companion status text is set
    if vm.companion_status_text and len(vm.companion_status_text) > 0:
        print("companion status text: OK")
    else:
        print("companion status text: FAIL (empty)")
        return 1

    # Pre-fill product status
    vm.set_product_status_view(
        ProductStatusView(
            items=(
                ProductStatusItem("对话", True, "已启用"),
                ProductStatusItem("版本", True, "0.1.0-rc.3"),
            )
        )
    )

    click_count = {"value": 0}

    def on_status_requested() -> None:
        click_count["value"] += 1
        vm.toggle_product_status_visible()
        vm.set_product_status_view(
            ProductStatusView(
                items=(
                    ProductStatusItem("对话", True, "已启用"),
                    ProductStatusItem("版本", True, "0.1.0-rc.3"),
                    ProductStatusItem("当前角色状态", True, AvatarAction.IDLE.value),
                )
            )
        )
        window.update_from_view_model()

    # Wire callback directly to button (callback already set via constructor)
    window._product_status_button.pressed.disconnect()
    window._product_status_button.pressed.connect(on_status_requested)

    # Verify status button first click opens panel
    window._product_status_button.pressed.emit()
    QApplication.instance().processEvents()

    if vm.product_status_visible and window._product_status_panel.isVisible():
        print("status button first click: OK")
    else:
        print("status button first click: FAIL")
        return 1

    # Verify status button second click closes panel
    window._product_status_button.pressed.emit()
    QApplication.instance().processEvents()

    if not vm.product_status_visible and not window._product_status_panel.isVisible():
        print("status button second click: OK")
    else:
        print("status button second click: FAIL")
        return 1

    print()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
