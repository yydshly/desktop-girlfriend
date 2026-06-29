"""Tests for avatar action (V10-A)."""

from __future__ import annotations

from app.contracts.events import (
    CONVERSATION_CLEARED,
    PROACTIVE_NUDGE_READY,
    STATE_CHANGED,
    SYSTEM_ERROR,
    BaseEvent,
)
from app.ui.avatar_action import (
    AvatarAction,
    avatar_label_for_action,
    avatar_text_for_action,
)
from app.ui.view_model import DesktopViewModel


class TestAvatarActionHelpers:
    """Tests for avatar action helper functions."""

    def test_avatar_text_idle(self) -> None:
        """avatar_text_for_action(IDLE) returns ☁️."""
        assert avatar_text_for_action(AvatarAction.IDLE) == "☁️"

    def test_avatar_text_listening(self) -> None:
        """avatar_text_for_action(LISTENING) returns 👂."""
        assert avatar_text_for_action(AvatarAction.LISTENING) == "👂"

    def test_avatar_text_thinking(self) -> None:
        """avatar_text_for_action(THINKING) returns 💭."""
        assert avatar_text_for_action(AvatarAction.THINKING) == "💭"

    def test_avatar_text_speaking(self) -> None:
        """avatar_text_for_action(SPEAKING) returns 🗣️."""
        assert avatar_text_for_action(AvatarAction.SPEAKING) == "🗣️"

    def test_avatar_text_proactive(self) -> None:
        """avatar_text_for_action(PROACTIVE) returns ✨."""
        assert avatar_text_for_action(AvatarAction.PROACTIVE) == "✨"

    def test_avatar_text_error(self) -> None:
        """avatar_text_for_action(ERROR) returns ⚠️."""
        assert avatar_text_for_action(AvatarAction.ERROR) == "⚠️"

    def test_avatar_label_listening_has_text(self) -> None:
        """avatar_label_for_action(LISTENING) returns non-empty text."""
        label = avatar_label_for_action(AvatarAction.LISTENING)
        assert isinstance(label, str)
        assert len(label) > 0

    def test_avatar_label_proactive_has_text(self) -> None:
        """avatar_label_for_action(PROACTIVE) returns non-empty text."""
        label = avatar_label_for_action(AvatarAction.PROACTIVE)
        assert isinstance(label, str)
        assert len(label) > 0


class TestViewModelAvatarAction:
    """Tests for ViewModel avatar action state."""

    def test_view_model_initial_avatar_action_is_idle(self) -> None:
        """ViewModel initial avatar_action is IDLE."""
        vm = DesktopViewModel()
        assert vm.avatar_action == AvatarAction.IDLE

    def test_view_model_initial_effective_avatar_text(self) -> None:
        """ViewModel initial effective_avatar_text is ☁️."""
        vm = DesktopViewModel()
        assert vm.effective_avatar_text == "☁️"

    def test_state_changed_idle_maps_to_avatar_idle(self) -> None:
        """AppState.IDLE -> AvatarAction.IDLE."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=STATE_CHANGED,
            request_id="req1",
            source="test",
            payload={"current_state": "idle"},
        )
        vm.handle_state_changed(event)
        assert vm.avatar_action == AvatarAction.IDLE
        assert vm.effective_avatar_text == "☁️"

    def test_state_changed_listening_maps_to_avatar_listening(self) -> None:
        """AppState.LISTENING -> AvatarAction.LISTENING."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=STATE_CHANGED,
            request_id="req1",
            source="test",
            payload={"current_state": "listening"},
        )
        vm.handle_state_changed(event)
        assert vm.avatar_action == AvatarAction.LISTENING
        assert vm.effective_avatar_text == "👂"

    def test_state_changed_thinking_maps_to_avatar_thinking(self) -> None:
        """AppState.THINKING -> AvatarAction.THINKING."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=STATE_CHANGED,
            request_id="req1",
            source="test",
            payload={"current_state": "thinking"},
        )
        vm.handle_state_changed(event)
        assert vm.avatar_action == AvatarAction.THINKING
        assert vm.effective_avatar_text == "💭"

    def test_state_changed_speaking_maps_to_avatar_speaking(self) -> None:
        """AppState.SPEAKING -> AvatarAction.SPEAKING."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=STATE_CHANGED,
            request_id="req1",
            source="test",
            payload={"current_state": "speaking"},
        )
        vm.handle_state_changed(event)
        assert vm.avatar_action == AvatarAction.SPEAKING
        assert vm.effective_avatar_text == "🗣️"

    def test_state_changed_error_maps_to_avatar_error(self) -> None:
        """AppState.ERROR -> AvatarAction.ERROR."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=STATE_CHANGED,
            request_id="req1",
            source="test",
            payload={"current_state": "error"},
        )
        vm.handle_state_changed(event)
        assert vm.avatar_action == AvatarAction.ERROR
        assert vm.effective_avatar_text == "⚠️"

    def test_proactive_nudge_ready_sets_proactive_avatar(self) -> None:
        """proactive.nudge_ready -> AvatarAction.PROACTIVE."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=PROACTIVE_NUDGE_READY,
            request_id="req1",
            source="test",
            payload={"text": "我在这儿。"},
        )
        vm.handle_proactive_nudge_ready(event)
        assert vm.avatar_action == AvatarAction.PROACTIVE
        assert vm.effective_avatar_text == "✨"

    def test_system_error_sets_error_avatar(self) -> None:
        """system.error -> AvatarAction.ERROR."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=SYSTEM_ERROR,
            request_id="req1",
            source="test",
            payload={"message": "Oops"},
        )
        vm.handle_system_error(event)
        assert vm.avatar_action == AvatarAction.ERROR
        assert vm.effective_avatar_text == "⚠️"

    def test_conversation_cleared_resets_to_idle(self) -> None:
        """conversation.cleared -> AvatarAction.IDLE."""
        vm = DesktopViewModel()
        # First set to something else
        event_speaking = BaseEvent(
            event_type=STATE_CHANGED,
            request_id="req1",
            source="test",
            payload={"current_state": "speaking"},
        )
        vm.handle_state_changed(event_speaking)
        assert vm.avatar_action == AvatarAction.SPEAKING

        # Clear conversation
        event_clear = BaseEvent(
            event_type=CONVERSATION_CLEARED,
            request_id="req2",
            source="test",
            payload={},
        )
        vm.handle_conversation_cleared(event_clear)
        assert vm.avatar_action == AvatarAction.IDLE
        assert vm.effective_avatar_text == "☁️"

    def test_avatar_change_does_not_clear_chat_messages(self) -> None:
        """Avatar state changes do not affect chat_messages."""
        vm = DesktopViewModel()

        # Add a user message
        from app.ui.chat_message import ChatMessage

        vm.chat_messages.append(ChatMessage(role="user", text="Hello"))
        assert len(vm.chat_messages) == 1

        # Change state
        event = BaseEvent(
            event_type=STATE_CHANGED,
            request_id="req1",
            source="test",
            payload={"current_state": "thinking"},
        )
        vm.handle_state_changed(event)

        # Chat messages should still have the user message
        assert len(vm.chat_messages) == 1
        assert vm.chat_messages[0].role == "user"
        assert vm.chat_messages[0].text == "Hello"

    def test_avatar_label_is_updated_on_state_change(self) -> None:
        """avatar_action_label is updated when state changes."""
        vm = DesktopViewModel()
        assert vm.avatar_action == AvatarAction.IDLE
        assert "待机" in vm.avatar_action_label

        event = BaseEvent(
            event_type=STATE_CHANGED,
            request_id="req1",
            source="test",
            payload={"current_state": "listening"},
        )
        vm.handle_state_changed(event)
        assert "听" in vm.avatar_action_label
