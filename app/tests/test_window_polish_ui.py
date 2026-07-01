"""Tests for window polish UI (Phase 2-C)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui import window_style
from app.ui.product_status import ProductStatusItem, ProductStatusView
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


class TestWindowStyleConstants:
    """Tests for window_style.py constants."""

    def test_header_card_style_exists(self) -> None:
        """HEADER_CARD_STYLE is a non-empty string."""
        assert isinstance(window_style.HEADER_CARD_STYLE, str)
        assert len(window_style.HEADER_CARD_STYLE) > 0

    def test_name_label_style_exists(self) -> None:
        """NAME_LABEL_STYLE is a non-empty string."""
        assert isinstance(window_style.NAME_LABEL_STYLE, str)
        assert len(window_style.NAME_LABEL_STYLE) > 0

    def test_primary_button_style_exists(self) -> None:
        """PRIMARY_BUTTON_STYLE is a non-empty string."""
        assert isinstance(window_style.PRIMARY_BUTTON_STYLE, str)
        assert len(window_style.PRIMARY_BUTTON_STYLE) > 0

    def test_secondary_button_style_exists(self) -> None:
        """SECONDARY_BUTTON_STYLE is a non-empty string."""
        assert isinstance(window_style.SECONDARY_BUTTON_STYLE, str)
        assert len(window_style.SECONDARY_BUTTON_STYLE) > 0

    def test_chat_history_style_exists(self) -> None:
        """CHAT_HISTORY_STYLE is a non-empty string."""
        assert isinstance(window_style.CHAT_HISTORY_STYLE, str)
        assert len(window_style.CHAT_HISTORY_STYLE) > 0

    def test_product_status_text_style_exists(self) -> None:
        """PRODUCT_STATUS_TEXT_STYLE is a non-empty string."""
        assert isinstance(window_style.PRODUCT_STATUS_TEXT_STYLE, str)
        assert len(window_style.PRODUCT_STATUS_TEXT_STYLE) > 0

    def test_error_label_style_exists(self) -> None:
        """ERROR_LABEL_STYLE is a non-empty string."""
        assert isinstance(window_style.ERROR_LABEL_STYLE, str)
        assert len(window_style.ERROR_LABEL_STYLE) > 0


class TestWindowPolishLayout:
    """Tests for DesktopWindow polish layout and features."""

    @staticmethod
    def test_window_initializes_without_crash(qapp: QApplication) -> None:
        """Window initializes without crashing."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert window._name_label.text() == "小云"

    @staticmethod
    def test_companion_card_present(qapp: QApplication) -> None:
        """Header shows companion name '小云'."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert "小云" in window._name_label.text()

    @staticmethod
    def test_input_placeholder_preserved(qapp: QApplication) -> None:
        """Input placeholder is '和小云说点什么...'."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert window._input_field.placeholderText() == "和小云说点什么..."

    @staticmethod
    def test_send_button_present(qapp: QApplication) -> None:
        """Send button exists and has primary style."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert window._send_button is not None
        assert window._send_button.text() == "发送"

    @staticmethod
    def test_status_button_first_click_opens_panel(qapp: QApplication) -> None:
        """First click on status button opens the panel."""
        vm = DesktopViewModel()

        def on_status_requested() -> None:
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

        vm.set_product_status_view(
            ProductStatusView(
                items=(ProductStatusItem("对话", True, "已启用"),)
            )
        )

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status_requested,
        )
        window.show()

        assert not vm.product_status_visible

        window._product_status_button.pressed.emit()
        qapp.processEvents()

        assert vm.product_status_visible is True
        assert window._product_status_panel.isVisible() is True

    @staticmethod
    def test_status_button_second_click_closes_panel(qapp: QApplication) -> None:
        """Second click on status button closes the panel."""
        vm = DesktopViewModel()

        def on_status_requested() -> None:
            vm.toggle_product_status_visible()
            vm.set_product_status_view(
                ProductStatusView(
                    items=(ProductStatusItem("对话", True, "已启用"),)
                )
            )
            window.update_from_view_model()

        vm.set_product_status_view(
            ProductStatusView(
                items=(ProductStatusItem("对话", True, "已启用"),)
            )
        )

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status_requested,
        )
        window.show()

        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is True

        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is False

    @staticmethod
    def test_memory_button_visibility_unchanged(qapp: QApplication) -> None:
        """Memory button visibility respects memory_management_enabled flag."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            memory_management_enabled=False,
        )
        window.show()
        assert not window._memory_panel_button.isVisible()

        window_with_memory = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            memory_management_enabled=True,
        )
        window_with_memory.show()
        assert window_with_memory._memory_panel_button.isVisible()

    @staticmethod
    def test_product_status_panel_shows_version(qapp: QApplication) -> None:
        """Product status panel shows 0.1.0-rc.3."""
        vm = DesktopViewModel()

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

        vm.set_product_status_view(
            ProductStatusView(
                items=(
                    ProductStatusItem("对话", True, "已启用"),
                    ProductStatusItem("版本", True, "0.1.0-rc.3"),
                    ProductStatusItem("发布阶段", True, "release-candidate"),
                )
            )
        )

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
            on_product_status_requested=on_status_requested,
        )
        window.show()

        window._product_status_button.pressed.emit()
        qapp.processEvents()

        assert "0.1.0-rc.3" in vm.product_status_text
        assert "release-candidate" in vm.product_status_text

    @staticmethod
    def test_header_keeps_readable_height(qapp: QApplication) -> None:
        """Companion header keeps enough height for its identity text."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        assert window._header_widget.minimumHeight() >= 118

    @staticmethod
    def test_live2d_model_details_are_collapsed_by_default(qapp: QApplication) -> None:
        """Verbose model diagnostics do not crowd the chat surface by default."""
        vm = DesktopViewModel()
        vm.set_live2d_model_catalog_details("Models folder: /tmp/models\nready")
        vm.set_live2d_model_import_guide("Put custom models under: /tmp/models/custom")

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        assert window._live2d_model_details_panel.isVisible() is False
        assert window._live2d_model_details_button.text() == "模型详情"

    @staticmethod
    def test_live2d_model_details_button_toggles_diagnostics(qapp: QApplication) -> None:
        """Model diagnostics can be opened when debugging model packages."""
        vm = DesktopViewModel()
        vm.set_live2d_model_catalog_details("Models folder: /tmp/models\nready")
        vm.set_live2d_model_import_guide("Put custom models under: /tmp/models/custom")
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        window._live2d_model_details_button.click()
        qapp.processEvents()

        assert window._live2d_model_details_panel.isVisible() is True
        assert window._live2d_model_details_button.text() == "隐藏详情"
