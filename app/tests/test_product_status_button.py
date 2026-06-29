"""Tests for product status button wiring (V12-rc2).

Tests first-click scenario: panel must open on the very first button press
without any prior chat interaction.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.product_status import ProductStatusItem, ProductStatusView
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


class TestProductStatusButtonFirstClick:
    """Tests for first-click reliability (V12-rc2 fix)."""

    @staticmethod
    def test_prefilled_product_status_text_not_empty(qapp: QApplication) -> None:
        """product_status_text must be pre-filled at startup, not empty."""
        view_model = DesktopViewModel()
        # Pre-fill (simulates startup pre-build in main.py)
        view_model.set_product_status_view(
            ProductStatusView(
                items=(
                    ProductStatusItem("对话", True, "已启用"),
                    ProductStatusItem("版本", True, "0.1.0-rc.2"),
                )
            )
        )
        window = DesktopWindow(
            view_model=view_model,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert view_model.product_status_text != "", \
            "product_status_text should be pre-filled before first click"

    @staticmethod
    def test_first_press_opens_panel_without_prior_interaction(qapp: QApplication) -> None:
        """First button press must open panel — no prior chat/interaction required."""
        view_model = DesktopViewModel()
        call_count = [0]

        def on_status_requested() -> None:
            call_count[0] += 1
            view_model.toggle_product_status_visible()
            view_model.set_product_status_view(
                ProductStatusView(
                    items=(ProductStatusItem("对话", True, "已启用"),)
                )
            )
            window.update_from_view_model()

        # Pre-fill (simulates startup pre-build)
        view_model.set_product_status_view(
            ProductStatusView(
                items=(ProductStatusItem("对话", True, "已启用"),)
            )
        )

        window = DesktopWindow(
            view_model=view_model,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status_requested,
        )
        window.show()

        # No prior interaction — directly press the button
        window._product_status_button.pressed.emit()
        qapp.processEvents()

        assert call_count[0] == 1, "callback must fire on first press"
        assert view_model.product_status_visible is True, \
            "panel must open on first press"
        assert window._product_status_panel.isVisible() is True, \
            "panel widget must be visible after first press"

    @staticmethod
    def test_second_press_closes_panel(qapp: QApplication) -> None:
        """Second button press must close the panel."""
        view_model = DesktopViewModel()

        def on_status_requested() -> None:
            view_model.toggle_product_status_visible()

        view_model.set_product_status_view(
            ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
        )

        window = DesktopWindow(
            view_model=view_model,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status_requested,
        )
        window.show()

        # First press
        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert view_model.product_status_visible is True

        # Second press
        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert view_model.product_status_visible is False

    @staticmethod
    def test_panel_contains_version_after_first_press(qapp: QApplication) -> None:
        """Panel must show version 0.1.0-rc.2 after first press."""
        view_model = DesktopViewModel()

        def on_status_requested() -> None:
            view_model.toggle_product_status_visible()
            view_model.set_product_status_view(
                ProductStatusView(
                    items=(
                        ProductStatusItem("对话", True, "已启用"),
                        ProductStatusItem("版本", True, "0.1.0-rc.2"),
                    )
                )
            )
            window.update_from_view_model()

        view_model.set_product_status_view(
            ProductStatusView(
                items=(
                    ProductStatusItem("对话", True, "已启用"),
                    ProductStatusItem("版本", True, "0.1.0-rc.2"),
                )
            )
        )

        window = DesktopWindow(
            view_model=view_model,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status_requested,
        )
        window.show()

        window._product_status_button.pressed.emit()
        qapp.processEvents()

        assert "版本" in view_model.product_status_text
        assert "0.1.0-rc.2" in view_model.product_status_text


class TestProductStatusButton:
    @staticmethod
    def test_button_callback_is_called_on_press(qapp: QApplication) -> None:
        view_model = DesktopViewModel()
        call_count = [0]

        def on_status_requested() -> None:
            call_count[0] += 1

        window = DesktopWindow(
            view_model=view_model,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status_requested,
        )
        window.show()

        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert call_count[0] == 1, "callback should be called once per press"
