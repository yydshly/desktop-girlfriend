"""Product status button wiring probe.

No real LLM/TTS/ASR, no memory access, no file writes.
Uses QT_QPA_PLATFORM=offscreen to avoid display requirement.

Tests the first-click scenario:
1. Pre-fill product_status_view (simulates startup initialization)
2. Create window
3. First button press opens panel immediately
4. Second button press closes panel
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
                    ProductStatusItem("版本", True, "0.1.0-rc.3"),
                    ProductStatusItem("当前角色状态", True, AvatarAction.IDLE.value),
                )
            )
        )
        window.update_from_view_model()

    # V12-rc2: Pre-fill product_status_view (simulates startup pre-build)
    view_model.set_product_status_view(
        ProductStatusView(
            items=(
                ProductStatusItem("对话", True, "已启用"),
                ProductStatusItem("版本", True, "0.1.0-rc.3"),
                ProductStatusItem("当前角色状态", True, AvatarAction.IDLE.value),
            )
        )
    )

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
    # Verify pre-filled text is already set
    assert "版本" in view_model.product_status_text, "product_status_text should be pre-filled before first click"

    # First button press - should open panel immediately
    window._product_status_button.pressed.emit()
    QApplication.instance().processEvents()

    if clicked["count"] != 1:
        print("Product Status Button Probe")
        print("button wiring: FAIL (callback called {} times, expected 1)".format(clicked["count"]))
        return 1

    if not view_model.product_status_visible:
        print("Product Status Button Probe")
        print("button wiring: OK")
        print("toggle: FAIL (product_status_visible not toggled on first press)")
        return 1

    if not window._product_status_panel.isVisible():
        print("Product Status Button Probe")
        print("button wiring: OK")
        print("panel visible: FAIL (panel still hidden after first press)")
        return 1

    # Second button press - should close panel
    window._product_status_button.pressed.emit()
    QApplication.instance().processEvents()
    if view_model.product_status_visible:
        print("Product Status Button Probe")
        print("button wiring: OK")
        print("panel visible: OK")
        print("toggle off: FAIL")
        return 1

    # Test mutual exclusivity: product status and settings cannot both be visible
    from app.core.config import AppConfig
    from app.ui.settings_view import build_settings_view, render_settings_view_text

    config = AppConfig()
    settings_view = build_settings_view(config)
    settings_text = render_settings_view_text(settings_view)
    view_model.set_settings_text(settings_text)

    def on_settings_clicked() -> None:
        view_model.toggle_settings_visible()
        window.update_from_view_model()

    # Create new window with settings callback
    window2 = DesktopWindow(
        view_model=view_model,
        on_user_text_submitted=lambda text: None,
        on_conversation_cleared=lambda: None,
        on_product_status_requested=on_status_requested,
    )
    window2._settings_button.clicked.connect(on_settings_clicked)
    window2.show()
    window2.update_from_view_model()

    # Open settings first - call handler directly to avoid double-toggle
    # (window already has _handle_settings_clicked connected to _settings_button.clicked)
    window2._handle_settings_clicked()
    QApplication.instance().processEvents()
    if not view_model.settings_visible:
        print("Product Status Button Probe")
        print("mutual exclusion: FAIL (settings not opened)")
        return 1
    if view_model.product_status_visible:
        print("Product Status Button Probe")
        print("mutual exclusion: FAIL (product status visible after opening settings)")
        return 1
    print("Product Status Button Probe")
    print("mutual exclusion: OK (settings opens, product status closed)")

    # Open product status - should close settings
    # Call handler directly (window already has _handle_product_status_clicked connected)
    window2._handle_product_status_clicked()
    QApplication.instance().processEvents()
    if view_model.settings_visible:
        print("Product Status Button Probe")
        print("mutual exclusion: FAIL (settings still visible after opening status)")
        return 1
    if not view_model.product_status_visible:
        print("Product Status Button Probe")
        print("mutual exclusion: FAIL (product status not opened)")
        return 1
    print("Product Status Button Probe")
    print("mutual exclusion: OK (status opens, settings closed)")

    print("Product Status Button Probe")
    print("button wiring: OK")
    print("panel visible: OK")
    print("text pre-fill: OK")
    print("toggle off: OK")
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
