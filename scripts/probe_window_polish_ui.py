"""Window Polish UI Probe (Phase 2-C).

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
    print("Window Polish UI Probe\n")

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

    # Verify layout elements
    checks = [
        ("header widget", hasattr(window, "_name_label")),
        ("chat history", hasattr(window, "_chat_history")),
        ("input field", hasattr(window, "_input_field")),
        ("send button", hasattr(window, "_send_button")),
        ("status button", hasattr(window, "_product_status_button")),
    ]

    layout_ok = True
    for name, present in checks:
        if present:
            print(f"layout: {name} OK")
        else:
            print(f"layout: {name} MISSING")
            layout_ok = False

    if not layout_ok:
        return 1

    # Pre-fill product status
    vm.set_product_status_view(
        ProductStatusView(
            items=(
                ProductStatusItem("对话", True, "已启用"),
                ProductStatusItem("版本", True, "0.1.0-rc.3"),
                ProductStatusItem("发布阶段", True, "release-candidate"),
            )
        )
    )

    def on_status_requested() -> None:
        vm.toggle_product_status_visible()
        vm.set_product_status_view(
            ProductStatusView(
                items=(
                    ProductStatusItem("对话", True, "已启用"),
                    ProductStatusItem("版本", True, "0.1.0-rc.3"),
                    ProductStatusItem("发布阶段", True, "release-candidate"),
                )
            )
        )
        window.update_from_view_model()

    window._product_status_button.pressed.disconnect()
    window._product_status_button.pressed.connect(on_status_requested)

    # Status button first click opens panel
    window._product_status_button.pressed.emit()
    QApplication.instance().processEvents()

    if vm.product_status_visible and window._product_status_panel.isVisible():
        print("status button: OK")
    else:
        print("status button: FAIL")
        return 1

    # Status button second click closes panel
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
