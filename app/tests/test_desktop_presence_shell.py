"""Tests for desktop presence shell (Phase 2-D)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.desktop_presence import (
    COMPACT_MODE_HEIGHT,
    COMPACT_MODE_WIDTH,
    DesktopPresenceState,
    render_compact_button_text,
    render_pin_button_text,
)
from app.ui.product_status import ProductStatusItem, ProductStatusView
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


class TestDesktopPresenceState:
    """Tests for DesktopPresenceState."""

    def test_default_always_on_top_false(self) -> None:
        """Default always_on_top is False."""
        state = DesktopPresenceState()
        assert state.always_on_top is False

    def test_default_compact_mode_false(self) -> None:
        """Default compact_mode is False."""
        state = DesktopPresenceState()
        assert state.compact_mode is False


class TestPresenceButtonText:
    """Tests for render_pin_button_text and render_compact_button_text."""

    def test_pin_button_not_on_top(self) -> None:
        """render_pin_button_text(False) returns '置顶'."""
        assert render_pin_button_text(False) == "置顶"

    def test_pin_button_on_top(self) -> None:
        """render_pin_button_text(True) returns '取消置顶'."""
        assert render_pin_button_text(True) == "取消置顶"

    def test_compact_button_normal(self) -> None:
        """render_compact_button_text(False) returns '小窗'."""
        assert render_compact_button_text(False) == "小窗"

    def test_compact_button_compact(self) -> None:
        """render_compact_button_text(True) returns '展开'."""
        assert render_compact_button_text(True) == "展开"


class TestCompactModeDimensions:
    """Tests for compact mode dimensions."""

    def test_compact_width(self) -> None:
        """COMPACT_MODE_WIDTH is 340."""
        assert COMPACT_MODE_WIDTH == 340

    def test_compact_height(self) -> None:
        """COMPACT_MODE_HEIGHT is 320."""
        assert COMPACT_MODE_HEIGHT == 320


class TestViewModelPresenceMethods:
    """Tests for ViewModel presence toggle methods."""

    def test_toggle_always_on_top(self) -> None:
        """toggle_always_on_top flips always_on_top."""
        vm = DesktopViewModel()
        assert vm.always_on_top is False
        vm.toggle_always_on_top()
        assert vm.always_on_top is True
        vm.toggle_always_on_top()
        assert vm.always_on_top is False

    def test_toggle_compact_mode(self) -> None:
        """toggle_compact_mode flips compact_mode."""
        vm = DesktopViewModel()
        assert vm.compact_mode is False
        vm.toggle_compact_mode()
        assert vm.compact_mode is True
        vm.toggle_compact_mode()
        assert vm.compact_mode is False

    def test_enter_compact_mode_closes_status_panel(self) -> None:
        """Entering compact mode closes status panel if open."""
        vm = DesktopViewModel()
        vm.set_product_status_view(
            ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
        )
        vm.toggle_product_status_visible()
        assert vm.product_status_visible is True
        vm.toggle_compact_mode()
        assert vm.compact_mode is True
        assert vm.product_status_visible is False


class TestWindowPresenceShell:
    """Tests for DesktopWindow presence shell features."""

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
    def test_pin_button_present(qapp: QApplication) -> None:
        """Pin button exists."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert hasattr(window, "_pin_button")
        assert window._pin_button.text() == "置顶"

    @staticmethod
    def test_compact_button_present(qapp: QApplication) -> None:
        """Compact button exists."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert hasattr(window, "_compact_button")
        assert window._compact_button.text() == "小窗"

    @staticmethod
    def test_status_button_first_click_opens_panel(qapp: QApplication) -> None:
        """First click on status button opens the panel."""
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
            ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
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
            ProductStatusView(items=(ProductStatusItem("对话", True, "已启用"),))
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
    def test_compact_mode_preserves_chat_history(qapp: QApplication) -> None:
        """Compact mode does not clear chat messages."""
        vm = DesktopViewModel()
        vm.chat_messages.append(
            __import__("app.ui.chat_message", fromlist=["ChatMessage"]).ChatMessage(
                role="user", text="Hello"
            )
        )

        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        assert len(vm.chat_messages) == 1

        window._handle_compact_clicked()
        qapp.processEvents()

        assert vm.compact_mode is True
        assert len(vm.chat_messages) == 1  # preserved

    @staticmethod
    def test_pin_button_toggles_label(qapp: QApplication) -> None:
        """Pin button label toggles between 置顶 and 取消置顶."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        assert window._pin_button.text() == "置顶"
        assert vm.always_on_top is False

        window._pin_button.pressed.emit()
        qapp.processEvents()

        assert vm.always_on_top is True
        # Note: actual window flag is set but offscreen Qt may not reflect it
        window.update_from_view_model()
        assert window._pin_button.text() == "取消置顶"

    @staticmethod
    def test_compact_button_toggles_label(qapp: QApplication) -> None:
        """Compact button label toggles between 小窗 and 展开."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()

        assert window._compact_button.text() == "小窗"
        assert vm.compact_mode is False

        window._compact_button.pressed.emit()
        qapp.processEvents()

        assert vm.compact_mode is True
        window.update_from_view_model()
        assert window._compact_button.text() == "展开"
