"""Tests for product status button wiring."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.product_status import ProductStatusItem, ProductStatusView
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


class TestProductStatusButton:
    @staticmethod
    def test_button_callback_is_called_on_click(qapp: QApplication) -> None:
        view_model = DesktopViewModel()
        call_count = 0

        def on_status_requested() -> None:
            nonlocal call_count
            call_count += 1

        window = DesktopWindow(
            view_model=view_model,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status_requested,
        )

        window._product_status_button.click()
        assert call_count == 1, "callback should be called exactly once per click"

    @staticmethod
    def test_toggle_product_status_visible(qapp: QApplication) -> None:
        view_model = DesktopViewModel()
        assert view_model.product_status_visible is False

        window = DesktopWindow(
            view_model=view_model,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=lambda: view_model.toggle_product_status_visible(),
        )

        assert view_model.product_status_visible is False
        window._product_status_button.click()
        assert view_model.product_status_visible is True
        window._product_status_button.click()
        assert view_model.product_status_visible is False

    @staticmethod
    def test_panel_visible_after_click(qapp: QApplication) -> None:
        view_model = DesktopViewModel()

        def on_status_requested() -> None:
            view_model.toggle_product_status_visible()
            view_model.set_product_status_view(
                ProductStatusView(
                    items=(ProductStatusItem("对话", True, "已启用"),)
                )
            )
            window.update_from_view_model()

        window = DesktopWindow(
            view_model=view_model,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status_requested,
        )

        assert window._product_status_panel.isVisible() is False
        window.show()
        window._product_status_button.click()
        qapp.processEvents()
        assert window._product_status_panel.isVisible() is True

    @staticmethod
    def test_status_text_updated_after_click(qapp: QApplication) -> None:
        view_model = DesktopViewModel()

        def on_status_requested() -> None:
            view_model.toggle_product_status_visible()
            view_model.set_product_status_view(
                ProductStatusView(
                    items=(
                        ProductStatusItem("对话", True, "已启用"),
                        ProductStatusItem("版本", True, "0.1.0-rc.0"),
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

        window._product_status_button.click()
        assert "版本" in view_model.product_status_text
        assert "0.1.0-rc.0" in view_model.product_status_text

    @staticmethod
    def test_toggle_off_after_second_click(qapp: QApplication) -> None:
        view_model = DesktopViewModel()

        def on_status_requested() -> None:
            view_model.toggle_product_status_visible()

        window = DesktopWindow(
            view_model=view_model,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status_requested,
        )

        window._product_status_button.click()
        qapp.processEvents()
        assert view_model.product_status_visible is True
        window._product_status_button.click()
        qapp.processEvents()
        assert view_model.product_status_visible is False
