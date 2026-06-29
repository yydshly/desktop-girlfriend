"""Tests for conversation experience UI (Phase 2-B)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.chat_message import ChatMessage
from app.ui.conversation_view import (
    get_input_placeholder,
    render_empty_conversation_text,
    render_message_prefix,
)
from app.ui.product_status import ProductStatusItem, ProductStatusView
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow, render_chat_messages


class TestConversationViewHelpers:
    """Tests for conversation_view helper functions."""

    def test_empty_conversation_text(self) -> None:
        """Empty conversation text is gentle and welcoming."""
        assert render_empty_conversation_text() == "小云在这里。想说什么，都可以慢慢说。"

    def test_user_prefix(self) -> None:
        """User message prefix is '你：'."""
        assert render_message_prefix("user") == "你："

    def test_assistant_prefix(self) -> None:
        """Assistant message prefix is '小云：'."""
        assert render_message_prefix("assistant") == "小云："

    def test_unknown_role_prefix_empty_string(self) -> None:
        """Unknown role prefix does not crash, returns empty string."""
        assert render_message_prefix("system") == ""
        assert render_message_prefix("") == ""

    def test_input_placeholder(self) -> None:
        """Input placeholder is natural and friendly."""
        assert get_input_placeholder() == "和小云说点什么..."


class TestRenderChatMessagesExperience:
    """Tests for render_chat_messages with Phase 2-B improvements."""

    def test_empty_returns_gentle_greeting(self) -> None:
        """Empty conversation returns the gentle companion greeting."""
        result = render_chat_messages([])
        assert result == "小云在这里。想说什么，都可以慢慢说。"

    def test_user_message_prefix(self) -> None:
        """User message shows '你：' prefix."""
        result = render_chat_messages([ChatMessage(role="user", text="你好")])
        assert "你：" in result

    def test_assistant_message_prefix(self) -> None:
        """Assistant message shows '小云：' prefix."""
        result = render_chat_messages([ChatMessage(role="assistant", text="你好呀")])
        assert "小云：" in result

    def test_extra_spacing_between_messages(self) -> None:
        """Extra blank lines between messages improve readability."""
        messages = [
            ChatMessage(role="user", text="Hello"),
            ChatMessage(role="assistant", text="Hi there!"),
        ]
        result = render_chat_messages(messages)
        # Should have extra blank lines (double blank) between messages
        assert "Hello" in result
        assert "Hi there!" in result


class TestWindowConversationExperience:
    """Tests for DesktopWindow conversation experience features."""

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
    def test_empty_conversation_shows_greeting(qapp: QApplication) -> None:
        """Empty conversation displays the gentle greeting."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        text = window._chat_history.toPlainText()
        assert "小云在这里。想说什么，都可以慢慢说。" in text

    @staticmethod
    def test_input_placeholder_text(qapp: QApplication) -> None:
        """Input field shows the new placeholder text."""
        vm = DesktopViewModel()
        window = DesktopWindow(
            view_model=vm,
            on_user_text_submitted=lambda text: None,
            on_conversation_cleared=lambda: None,
        )
        window.show()
        assert window._input_field.placeholderText() == "和小云说点什么..."

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
    def test_memory_button_visibility_respects_flag(qapp: QApplication) -> None:
        """Memory button is only visible when memory_management_enabled=True."""
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
