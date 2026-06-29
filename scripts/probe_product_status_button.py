"""Product status button wiring probe.

No real LLM/TTS/ASR, no memory access, no file writes.
Uses QT_QPA_PLATFORM=offscreen to avoid display requirement.
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
    QApplication.instance() or QApplication(sys.argv)

    view_model = DesktopViewModel()
    clicked = {"count": 0}

    def on_status_requested() -> None:
        clicked["count"] += 1
        view_model.toggle_product_status_visible()
        view_model.set_product_status_view(
            ProductStatusView(
                items=(
                    ProductStatusItem("对话", True, "已启用"),
                    ProductStatusItem("版本", True, "0.1.0-rc.0"),
                    ProductStatusItem("当前角色状态", True, AvatarAction.IDLE.value),
                )
            )
        )
        window.update_from_view_model()

    window = DesktopWindow(
        view_model=view_model,
        on_user_text_submitted=lambda text: None,
        on_conversation_cleared=lambda: None,
        on_product_status_requested=on_status_requested,
    )

    # Verify initial state: panel not visible
    assert not view_model.product_status_visible, "product_status_visible should be False initially"
    window.show()
    assert not window._product_status_panel.isVisible(), "panel should be hidden initially"

    # Click the status button
    window._product_status_button.click()
    QApplication.instance().processEvents()

    if clicked["count"] != 1:
        print("Product Status Button Probe")
        print(f"button wiring: FAIL (callback called {clicked['count']} times, expected 1)")
        return 1

    if not view_model.product_status_visible:
        print("Product Status Button Probe")
        print("button wiring: OK")
        print("toggle: FAIL (product_status_visible not toggled)")
        return 1

    if not window._product_status_panel.isVisible():
        print("Product Status Button Probe")
        print("button wiring: OK")
        print("panel visible: FAIL (panel still hidden after click)")
        return 1

    if "版本" not in view_model.product_status_text:
        print("Product Status Button Probe")
        print("button wiring: OK")
        print("panel visible: OK")
        print("text update: FAIL")
        return 1

    # Click again to verify toggle off
    window._product_status_button.click()
    QApplication.instance().processEvents()
    if view_model.product_status_visible:
        print("Product Status Button Probe")
        print("button wiring: OK")
        print("panel visible: OK")
        print("toggle off: FAIL")
        return 1

    print("Product Status Button Probe")
    print("button wiring: OK")
    print("panel visible: OK")
    print("text update: OK")
    print("toggle off: OK")
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
