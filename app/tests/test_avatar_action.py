"""Tests for avatar action (V10-A / V10-B)."""

from __future__ import annotations

from app.contracts.events import (
    CONVERSATION_CLEARED,
    PROACTIVE_NUDGE_READY,
    STATE_CHANGED,
    SYSTEM_ERROR,
    BaseEvent,
)
from app.contracts.states import AppState
from app.ui.avatar_action import (
    AvatarAction,
    avatar_label_for_action,
    avatar_style_for_action,
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


class TestAvatarActionStyles:
    """Tests for avatar action styles (V10-B)."""

    def test_all_actions_have_style(self) -> None:
        """Every AvatarAction has a non-empty style."""
        for action in AvatarAction:
            style = avatar_style_for_action(action)
            assert isinstance(style, str)
            assert len(style) > 0

    def test_effective_avatar_style_initial_is_idle_style(self) -> None:
        """ViewModel effective_avatar_style is IDLE style initially."""
        vm = DesktopViewModel()
        assert vm.effective_avatar_style == avatar_style_for_action(AvatarAction.IDLE)

    def test_listening_style_different_from_idle(self) -> None:
        """LISTENING style differs from IDLE style."""
        idle_style = avatar_style_for_action(AvatarAction.IDLE)
        listening_style = avatar_style_for_action(AvatarAction.LISTENING)
        assert idle_style != listening_style

    def test_proactive_has_non_empty_style(self) -> None:
        """PROACTIVE action has a non-empty style."""
        style = avatar_style_for_action(AvatarAction.PROACTIVE)
        assert len(style) > 0

    def test_error_has_non_empty_style(self) -> None:
        """ERROR action has a non-empty style."""
        style = avatar_style_for_action(AvatarAction.ERROR)
        assert len(style) > 0

    def test_state_change_updates_effective_avatar_style(self) -> None:
        """State change updates effective_avatar_style."""
        vm = DesktopViewModel()
        initial_style = vm.effective_avatar_style

        event = BaseEvent(
            event_type=STATE_CHANGED,
            request_id="req1",
            source="test",
            payload={"current_state": "listening"},
        )
        vm.handle_state_changed(event)

        assert vm.effective_avatar_style != initial_style
        assert vm.effective_avatar_style == avatar_style_for_action(AvatarAction.LISTENING)

    def test_proactive_nudge_updates_style(self) -> None:
        """proactive.nudge_ready updates avatar style to PROACTIVE."""
        vm = DesktopViewModel()
        initial_style = vm.effective_avatar_style

        event = BaseEvent(
            event_type=PROACTIVE_NUDGE_READY,
            request_id="req1",
            source="test",
            payload={"text": "我在这儿。"},
        )
        vm.handle_proactive_nudge_ready(event)

        assert vm.effective_avatar_style != initial_style
        assert vm.effective_avatar_style == avatar_style_for_action(AvatarAction.PROACTIVE)

    def test_error_updates_style(self) -> None:
        """system.error updates avatar style to ERROR."""
        vm = DesktopViewModel()
        initial_style = vm.effective_avatar_style

        event = BaseEvent(
            event_type=SYSTEM_ERROR,
            request_id="req1",
            source="test",
            payload={"message": "Oops"},
        )
        vm.handle_system_error(event)

        assert vm.effective_avatar_style != initial_style
        assert vm.effective_avatar_style == avatar_style_for_action(AvatarAction.ERROR)


class TestHandleProactiveAvatarHint:
    """Tests for handle_proactive_avatar_hint (V10-C)."""

    def test_sets_avatar_action_proactive(self) -> None:
        """handle_proactive_avatar_hint sets AvatarAction.PROACTIVE."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=PROACTIVE_NUDGE_READY,
            request_id="req1",
            source="test",
            payload={"text": "我在这儿。"},
        )
        vm.handle_proactive_avatar_hint(event)
        assert vm.avatar_action == AvatarAction.PROACTIVE
        assert vm.effective_avatar_text == "✨"

    def test_does_not_append_chat_messages(self) -> None:
        """handle_proactive_avatar_hint does not append chat_messages."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=PROACTIVE_NUDGE_READY,
            request_id="req1",
            source="test",
            payload={"text": "我在这儿。"},
        )
        vm.handle_proactive_avatar_hint(event)
        assert len(vm.chat_messages) == 0

    def test_does_not_modify_assistant_text(self) -> None:
        """handle_proactive_avatar_hint does not modify assistant_text."""
        vm = DesktopViewModel()
        vm.assistant_text = "original"
        event = BaseEvent(
            event_type=PROACTIVE_NUDGE_READY,
            request_id="req1",
            source="test",
            payload={"text": "我在这儿。"},
        )
        vm.handle_proactive_avatar_hint(event)
        assert vm.assistant_text == "original"

    def test_does_not_change_app_state(self) -> None:
        """handle_proactive_avatar_hint does not change AppState."""
        vm = DesktopViewModel()
        assert vm.state == AppState.IDLE
        event = BaseEvent(
            event_type=PROACTIVE_NUDGE_READY,
            request_id="req1",
            source="test",
            payload={"text": "我在这儿。"},
        )
        vm.handle_proactive_avatar_hint(event)
        assert vm.state == AppState.IDLE

    def test_ignores_wrong_event_type(self) -> None:
        """handle_proactive_avatar_hint ignores non-PROACTIVE_NUDGE_READY events."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type="other.event",
            request_id="req1",
            source="test",
            payload={"text": "ignored"},
        )
        vm.handle_proactive_avatar_hint(event)
        assert vm.avatar_action == AvatarAction.IDLE
        assert len(vm.chat_messages) == 0

    def test_empty_text_still_sets_proactive(self) -> None:
        """handle_proactive_avatar_hint sets PROACTIVE even for empty text (no text check per spec)."""
        vm = DesktopViewModel()
        event = BaseEvent(
            event_type=PROACTIVE_NUDGE_READY,
            request_id="req1",
            source="test",
            payload={"text": ""},
        )
        vm.handle_proactive_avatar_hint(event)
        # Spec: only sets avatar_action and avatar_action_label, no text check
        assert vm.avatar_action == AvatarAction.PROACTIVE
        assert len(vm.chat_messages) == 0

    def test_updates_avatar_action_label(self) -> None:
        """handle_proactive_avatar_hint updates avatar_action_label."""
        vm = DesktopViewModel()
        initial_label = vm.avatar_action_label
        event = BaseEvent(
            event_type=PROACTIVE_NUDGE_READY,
            request_id="req1",
            source="test",
            payload={"text": "我在这儿。"},
        )
        vm.handle_proactive_avatar_hint(event)
        assert vm.avatar_action_label != initial_label
        assert "主动" in vm.avatar_action_label or "proactive" in vm.avatar_action_label.lower()
