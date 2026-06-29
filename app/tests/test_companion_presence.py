"""Tests for companion presence UI (Phase 2-A)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.contracts.events import (
    CONVERSATION_CLEARED,
    PROACTIVE_NUDGE_READY,
    STATE_CHANGED,
    SYSTEM_ERROR,
    BaseEvent,
)
from app.ui.avatar_action import AvatarAction
from app.ui.companion_presence import render_companion_status_text
from app.ui.product_status import ProductStatusItem, ProductStatusView
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow


class TestRenderCompanionStatusText:
    """Tests for render_companion_status_text()."""

    def test_idle(self) -> None:
        """IDLE returns idle companion status text."""
        assert render_companion_status_text(AvatarAction.IDLE) == "我在这里，想聊就叫我。"

    def test_listening(self) -> None:
        """LISTENING returns listening companion status text."""
        assert render_companion_status_text(AvatarAction.LISTENING) == "我正在听你说。"

    def test_thinking(self) -> None:
        """THINKING returns thinking companion status text."""
        assert render_companion_status_text(AvatarAction.THINKING) == "我在想怎么回答你。"

    def test_speaking(self) -> None:
        """SPEAKING returns speaking companion status text."""
        assert render_companion_status_text(AvatarAction.SPEAKING) == "我正在回应你。"

    def test_proactive(self) -> None:
        """PROACTIVE returns proactive companion status text."""
        assert render_companion_status_text(AvatarAction.PROACTIVE) == "我看到你安静了一会儿，就来陪你一下。"

    def test_error(self) -> None:
        """ERROR returns error companion status text."""
        assert render_companion_status_text(AvatarAction.ERROR) == "我遇到了一点问题。"


class TestViewModelCompanionPresence:
    """Tests for ViewModel companion presence fields."""

    def test_initial_companion_status_text_is_idle_text(self) -> None:
        """Initial companion_status_text matches IDLE text."""
        vm = DesktopViewModel()
        assert vm.companion_status_text == "我在这里，想聊就叫我。"

    def test_state_changed_to_idle_updates_companion_status_text(self) -> None:
        """STATE_CHANGED to idle updates companion_status_text."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=STATE_CHANGED,
            request_id="req1",
            source="test",
            payload={"current_state": "idle"},
        )
        vm.handle_state_changed(event)
        assert vm.companion_status_text == "我在这里，想聊就叫我。"

    def test_state_changed_to_listening_updates_companion_status_text(self) -> None:
        """STATE_CHANGED to listening updates companion_status_text."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=STATE_CHANGED,
            request_id="req1",
            source="test",
            payload={"current_state": "listening"},
        )
        vm.handle_state_changed(event)
        assert vm.companion_status_text == "我正在听你说。"

    def test_state_changed_to_thinking_updates_companion_status_text(self) -> None:
        """STATE_CHANGED to thinking updates companion_status_text."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=STATE_CHANGED,
            request_id="req1",
            source="test",
            payload={"current_state": "thinking"},
        )
        vm.handle_state_changed(event)
        assert vm.companion_status_text == "我在想怎么回答你。"

    def test_state_changed_to_speaking_updates_companion_status_text(self) -> None:
        """STATE_CHANGED to speaking updates companion_status_text."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=STATE_CHANGED,
            request_id="req1",
            source="test",
            payload={"current_state": "speaking"},
        )
        vm.handle_state_changed(event)
        assert vm.companion_status_text == "我正在回应你。"

    def test_system_error_updates_companion_status_text(self) -> None:
        """SYSTEM_ERROR updates companion_status_text to error text."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=SYSTEM_ERROR,
            request_id="req1",
            source="test",
            payload={"message": "Oops"},
        )
        vm.handle_system_error(event)
        assert vm.companion_status_text == "我遇到了一点问题。"

    def test_proactive_nudge_updates_companion_status_text(self) -> None:
        """PROACTIVE_NUDGE_READY updates companion_status_text to proactive text."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=PROACTIVE_NUDGE_READY,
            request_id="req1",
            source="test",
            payload={"text": "我在这儿。"},
        )
        vm.handle_proactive_nudge_ready(event)
        assert vm.companion_status_text == "我看到你安静了一会儿，就来陪你一下。"

    def test_conversation_cleared_resets_companion_status_text_to_idle(self) -> None:
        """conversation.cleared resets companion_status_text to idle text."""
        vm = DesktopViewModel()
        # Set to speaking first
        event = BaseEvent(
            event_type=STATE_CHANGED,
            request_id="req1",
            source="test",
            payload={"current_state": "speaking"},
        )
        vm.handle_state_changed(event)
        assert vm.companion_status_text == "我正在回应你。"

        # Clear conversation
        event_clear = BaseEvent(
            event_type=CONVERSATION_CLEARED,
            request_id="req2",
            source="test",
            payload={},
        )
        vm.handle_conversation_cleared(event_clear)
        assert vm.companion_status_text == "我在这里，想聊就叫我。"

    def test_companion_version_text(self) -> None:
        """ViewModel companion_version_text is 0.2.0-alpha.2."""
        vm = DesktopViewModel()
        assert vm.companion_version_text == "0.2.0-alpha.2"

    def test_companion_release_stage_text(self) -> None:
        """ViewModel companion_release_stage_text is alpha."""
        vm = DesktopViewModel()
        assert vm.companion_release_stage_text == "alpha"

    def test_companion_name(self) -> None:
        """ViewModel companion_name is 小云."""
        vm = DesktopViewModel()
        assert vm.companion_name == "小云"

    def test_companion_subtitle(self) -> None:
        """ViewModel companion_subtitle is 你的桌面 AI 伙伴."""
        vm = DesktopViewModel()
        assert vm.companion_subtitle == "你的桌面 AI 伙伴"


class TestWindowCompanionPresence:
    """Tests for DesktopWindow companion presence header."""

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
        # Verify header labels are present
        assert window._name_label.text() == "小云"
        assert "你的桌面 AI 伙伴" in window._subtitle_label.text()
        assert "0.2.0-alpha.2" in window._version_label.text()

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
                        ProductStatusItem("当前角色状态", True, AvatarAction.IDLE.value),
                    )
                )
            )
            window.update_from_view_model()

        # Pre-fill so panel has content
        vm.set_product_status_view(
            ProductStatusView(
                items=(
                    ProductStatusItem("对话", True, "已启用"),
                    ProductStatusItem("版本", True, "0.1.0-rc.3"),
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

        # Panel should be hidden initially
        assert not vm.product_status_visible

        # First press opens panel
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

        # First press opens
        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is True

        # Second press closes
        window._product_status_button.pressed.emit()
        qapp.processEvents()
        assert vm.product_status_visible is False
