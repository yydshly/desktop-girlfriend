"""Conversation Experience UI Probe (Phase 2-B).

Uses QT_QPA_PLATFORM=offscreen to avoid display requirement.
No real LLM/TTS/ASR, no memory access, no file writes, no network.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.product_status import ProductStatusItem, ProductStatusView
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


def main() -> int:
    print("Conversation Experience UI Probe\n")

    QApplication.instance() or QApplication(sys.argv)

    vm = DesktopViewModel()

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

    # Verify empty state greeting
    empty_text = window._chat_history.toPlainText()
    if "小云在这里。想说什么，都可以慢慢说。" in empty_text:
        print("empty state: OK")
    else:
        print(f"empty state: FAIL ('{empty_text}')")
        return 1

    # Verify input placeholder
    if window._input_field.placeholderText() == "和小云说点什么...":
        print("input: OK")
    else:
        print(f"input: FAIL (placeholder='{window._input_field.placeholderText()}')")
        return 1

    # Pre-fill product status
    vm.set_product_status_view(
        ProductStatusView(
            items=(ProductStatusItem("对话", True, "已启用"),)
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
                )
            )
        )
        window.update_from_view_model()

    window._product_status_button.pressed.disconnect()
    window._product_status_button.pressed.connect(on_status_requested)

    # First click opens panel
    window._product_status_button.pressed.emit()
    QApplication.instance().processEvents()

    if vm.product_status_visible and window._product_status_panel.isVisible():
        print("status button: OK")
    else:
        print("status button: FAIL")
        return 1

    # Second click closes panel
    window._product_status_button.pressed.emit()
    QApplication.instance().processEvents()

    if not vm.product_status_visible and not window._product_status_panel.isVisible():
        print("status button toggle off: OK")
    else:
        print("status button toggle off: FAIL")
        return 1

    print()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
