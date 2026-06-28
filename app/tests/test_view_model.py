"""Tests for DesktopViewModel."""

from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.contracts.states import AppState
from app.ui.chat_message import ChatMessage
from app.ui.view_model import (
    COMPANION_AVATAR_TEXT,
    COMPANION_NAME,
    COMPANION_SUBTITLE,
    DesktopViewModel,
)


def test_view_model_initial_state() -> None:
    """Test ViewModel initial state is IDLE with correct display text."""
    vm = DesktopViewModel()
    assert vm.state == AppState.IDLE
    assert vm.display_text == "当前状态：待机"
    assert vm.assistant_text == ""
    assert vm.companion_name == COMPANION_NAME
    assert vm.companion_subtitle == COMPANION_SUBTITLE
    assert vm.companion_avatar_text == COMPANION_AVATAR_TEXT


def test_companion_fields_defaults() -> None:
    """Test companion fields have expected default values."""
    assert COMPANION_NAME == "小云"
    assert COMPANION_SUBTITLE == "你的桌面 AI 伙伴"
    assert COMPANION_AVATAR_TEXT == "☁️"


def test_handle_state_changed_to_listening() -> None:
    """Test handle_state_changed updates to LISTENING state."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=STATE_CHANGED,
        request_id="req1",
        source="test",
        payload={
            "previous_state": "idle",
            "current_state": "listening",
        },
    )
    vm.handle_state_changed(event)

    assert vm.state == AppState.LISTENING
    assert vm.display_text == "当前状态：聆听中"


def test_handle_state_changed_to_thinking() -> None:
    """Test handle_state_changed updates to THINKING state."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=STATE_CHANGED,
        request_id="req2",
        source="test",
        payload={
            "previous_state": "listening",
            "current_state": "thinking",
        },
    )
    vm.handle_state_changed(event)

    assert vm.state == AppState.THINKING
    assert vm.display_text == "当前状态：正在想你说的话"


def test_handle_state_changed_to_speaking() -> None:
    """Test handle_state_changed updates to SPEAKING state."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=STATE_CHANGED,
        request_id="req3",
        source="test",
        payload={
            "previous_state": "thinking",
            "current_state": "speaking",
        },
    )
    vm.handle_state_changed(event)

    assert vm.state == AppState.SPEAKING
    assert vm.display_text == "当前状态：正在回应你"


def test_handle_state_changed_to_error() -> None:
    """Test handle_state_changed updates to ERROR state."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=STATE_CHANGED,
        request_id="req4",
        source="test",
        payload={
            "previous_state": "speaking",
            "current_state": "error",
        },
    )
    vm.handle_state_changed(event)

    assert vm.state == AppState.ERROR
    assert vm.display_text == "当前状态：出了一点小问题"


def test_handle_state_changed_ignores_non_state_changed_event() -> None:
    """Test handle_state_changed ignores non-state.changed events."""
    vm = DesktopViewModel()
    initial_state = vm.state
    initial_text = vm.display_text

    event = BaseEvent(
        event_type="other.event",
        request_id="req5",
        source="test",
        payload={},
    )
    vm.handle_state_changed(event)

    assert vm.state == initial_state
    assert vm.display_text == initial_text


def test_handle_state_changed_missing_current_state_defaults_to_error() -> None:
    """Test handle_state_changed with missing current_state defaults to ERROR."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=STATE_CHANGED,
        request_id="req6",
        source="test",
        payload={
            "previous_state": "idle",
        },
    )
    vm.handle_state_changed(event)

    assert vm.state == AppState.ERROR
    assert vm.display_text == "当前状态：出了一点小问题"


def test_handle_state_changed_enum_current_state_defaults_to_error() -> None:
    """Test handle_state_changed with AppState enum current_state defaults to ERROR."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=STATE_CHANGED,
        request_id="req7",
        source="test",
        payload={
            "previous_state": "idle",
            "current_state": AppState.LISTENING,
        },
    )
    vm.handle_state_changed(event)

    assert vm.state == AppState.ERROR
    assert vm.display_text == "当前状态：出了一点小问题"


def test_handle_state_changed_dict_current_state_defaults_to_error() -> None:
    """Test handle_state_changed with dict current_state defaults to ERROR."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=STATE_CHANGED,
        request_id="req8",
        source="test",
        payload={
            "previous_state": "idle",
            "current_state": {"value": "thinking"},
        },
    )
    vm.handle_state_changed(event)

    assert vm.state == AppState.ERROR
    assert vm.display_text == "当前状态：出了一点小问题"


def test_handle_state_changed_unknown_string_defaults_to_error() -> None:
    """Test handle_state_changed with unknown string state defaults to ERROR."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=STATE_CHANGED,
        request_id="req9",
        source="test",
        payload={
            "previous_state": "idle",
            "current_state": "unknown_state",
        },
    )
    vm.handle_state_changed(event)

    assert vm.state == AppState.ERROR
    assert vm.display_text == "当前状态：出了一点小问题"


# Assistant text tests


def test_handle_assistant_text_received_updates_assistant_text() -> None:
    """Test handle_assistant_text_received updates assistant_text and appends to chat_messages."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=ASSISTANT_TEXT_RECEIVED,
        request_id="req10",
        source="test",
        payload={"text": "Hello from assistant!"},
    )
    vm.handle_assistant_text_received(event)

    assert vm.assistant_text == "Hello from assistant!"
    assert len(vm.chat_messages) == 1
    assert vm.chat_messages[0].role == "assistant"
    assert vm.chat_messages[0].text == "Hello from assistant!"


def test_handle_assistant_text_received_ignores_non_assistant_event() -> None:
    """Test handle_assistant_text_received ignores non-assistant events."""
    vm = DesktopViewModel()
    vm.assistant_text = "existing"

    event = BaseEvent(
        event_type="other.event",
        request_id="req11",
        source="test",
        payload={"text": "should not update"},
    )
    vm.handle_assistant_text_received(event)

    assert vm.assistant_text == "existing"


def test_handle_assistant_text_received_missing_text_keeps_previous_and_does_not_append() -> None:
    """Test handle_assistant_text_received with missing text keeps previous and does not append."""
    vm = DesktopViewModel()
    vm.assistant_text = "previous"

    event = BaseEvent(
        event_type=ASSISTANT_TEXT_RECEIVED,
        request_id="req12",
        source="test",
        payload={},
    )
    vm.handle_assistant_text_received(event)

    assert vm.assistant_text == "previous"
    assert vm.chat_messages == []


def test_handle_assistant_text_received_non_string_text_keeps_previous_and_does_not_append() -> None:
    """Test handle_assistant_text_received with non-string text keeps previous and does not append."""
    vm = DesktopViewModel()
    vm.assistant_text = "previous"

    event = BaseEvent(
        event_type=ASSISTANT_TEXT_RECEIVED,
        request_id="req13",
        source="test",
        payload={"text": None},
    )
    vm.handle_assistant_text_received(event)

    assert vm.assistant_text == "previous"
    assert vm.chat_messages == []


def test_handle_assistant_text_received_str_subclass_keeps_previous_and_does_not_append() -> None:
    """Test handle_assistant_text_received with str subclass keeps previous and does not append."""

    class TextSubclass(str):
        pass

    vm = DesktopViewModel()
    vm.assistant_text = "previous"

    event = BaseEvent(
        event_type=ASSISTANT_TEXT_RECEIVED,
        request_id="req14",
        source="test",
        payload={"text": TextSubclass("bad")},
    )
    vm.handle_assistant_text_received(event)

    assert vm.assistant_text == "previous"
    assert vm.chat_messages == []


# System error tests


def test_initial_error_text_is_empty() -> None:
    """Test that initial error_text is empty."""
    vm = DesktopViewModel()
    assert vm.error_text == ""


def test_handle_system_error_with_valid_string_sets_error_text() -> None:
    """Test handle_system_error with valid string message sets error_text."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=SYSTEM_ERROR,
        request_id="req15",
        source="test",
        payload={"message": "对话生成失败，请检查网络或稍后重试。"},
    )
    vm.handle_system_error(event)

    assert vm.error_text == "对话生成失败，请检查网络或稍后重试。"


def test_handle_system_error_ignores_non_system_error_event() -> None:
    """Test handle_system_error ignores non-system.error events."""
    vm = DesktopViewModel()
    vm.error_text = "existing"

    event = BaseEvent(
        event_type="other.event",
        request_id="req16",
        source="test",
        payload={"message": "should not update"},
    )
    vm.handle_system_error(event)

    assert vm.error_text == "existing"


def test_handle_system_error_with_non_str_message_sets_fallback() -> None:
    """Test handle_system_error with non-str message sets fallback unknown error."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=SYSTEM_ERROR,
        request_id="req17",
        source="test",
        payload={"message": None},
    )
    vm.handle_system_error(event)

    assert vm.error_text == "发生未知错误。"


def test_handle_system_error_with_str_subclass_rejected() -> None:
    """Test handle_system_error with str subclass does not accept as exact str."""

    class MessageSubclass(str):
        pass

    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=SYSTEM_ERROR,
        request_id="req18",
        source="test",
        payload={"message": MessageSubclass("leaked secret")},
    )
    vm.handle_system_error(event)

    # Should use fallback because type(message) is not exactly str
    assert vm.error_text == "发生未知错误。"


def test_handle_state_changed_to_thinking_clears_error_text() -> None:
    """Test handle_state_changed to THINKING clears previous error_text."""
    vm = DesktopViewModel()
    vm.error_text = "Previous error"

    event = BaseEvent(
        event_type=STATE_CHANGED,
        request_id="req19",
        source="test",
        payload={
            "previous_state": "idle",
            "current_state": "thinking",
        },
    )
    vm.handle_state_changed(event)

    assert vm.error_text == ""


def test_handle_state_changed_to_error_does_not_clear_error_text() -> None:
    """Test handle_state_changed to ERROR does not clear error_text."""
    vm = DesktopViewModel()
    vm.error_text = "Some error"

    event = BaseEvent(
        event_type=STATE_CHANGED,
        request_id="req20",
        source="test",
        payload={
            "previous_state": "thinking",
            "current_state": "error",
        },
    )
    vm.handle_state_changed(event)

    assert vm.error_text == "Some error"


def test_handle_system_error_whitespace_only_message_sets_fallback() -> None:
    """Test handle_system_error with whitespace-only message sets fallback."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=SYSTEM_ERROR,
        request_id="req21",
        source="test",
        payload={"message": "   "},
    )
    vm.handle_system_error(event)

    assert vm.error_text == "发生未知错误。"


# Chat history tests


def test_initial_chat_messages_is_empty() -> None:
    """Test that initial chat_messages is empty."""
    vm = DesktopViewModel()
    assert vm.chat_messages == []


def test_handle_user_text_submitted_appends_user_message() -> None:
    """Test handle_user_text_submitted appends a user message to chat_messages."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=USER_TEXT_SUBMITTED,
        request_id="req22",
        source="test",
        payload={"text": "Hello"},
    )
    vm.handle_user_text_submitted(event)

    assert len(vm.chat_messages) == 1
    assert vm.chat_messages[0].role == "user"
    assert vm.chat_messages[0].text == "Hello"


def test_handle_user_text_submitted_ignores_wrong_event_type() -> None:
    """Test handle_user_text_submitted ignores non-user.text_submitted events."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type="other.event",
        request_id="req23",
        source="test",
        payload={"text": "Hello"},
    )
    vm.handle_user_text_submitted(event)

    assert vm.chat_messages == []


def test_handle_user_text_submitted_ignores_missing_text() -> None:
    """Test handle_user_text_submitted ignores missing text."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=USER_TEXT_SUBMITTED,
        request_id="req24",
        source="test",
        payload={},
    )
    vm.handle_user_text_submitted(event)

    assert vm.chat_messages == []


def test_handle_user_text_submitted_ignores_non_str_text() -> None:
    """Test handle_user_text_submitted ignores non-string text."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=USER_TEXT_SUBMITTED,
        request_id="req25",
        source="test",
        payload={"text": None},
    )
    vm.handle_user_text_submitted(event)

    assert vm.chat_messages == []


def test_handle_user_text_submitted_rejects_str_subclass() -> None:
    """Test handle_user_text_submitted rejects str subclass."""

    class TextSubclass(str):
        pass

    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=USER_TEXT_SUBMITTED,
        request_id="req26",
        source="test",
        payload={"text": TextSubclass("Hello")},
    )
    vm.handle_user_text_submitted(event)

    assert vm.chat_messages == []


def test_handle_user_text_submitted_strips_whitespace() -> None:
    """Test handle_user_text_submitted strips surrounding whitespace."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=USER_TEXT_SUBMITTED,
        request_id="req27",
        source="test",
        payload={"text": "  Hello  "},
    )
    vm.handle_user_text_submitted(event)

    assert len(vm.chat_messages) == 1
    assert vm.chat_messages[0].text == "Hello"


def test_handle_assistant_text_received_appends_assistant_message() -> None:
    """Test handle_assistant_text_received appends assistant message to chat_messages."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=ASSISTANT_TEXT_RECEIVED,
        request_id="req28",
        source="test",
        payload={"text": "Hi there!"},
    )
    vm.handle_assistant_text_received(event)

    assert len(vm.chat_messages) == 1
    assert vm.chat_messages[0].role == "assistant"
    assert vm.chat_messages[0].text == "Hi there!"
    assert vm.assistant_text == "Hi there!"


def test_system_error_does_not_append_chat_message() -> None:
    """Test handle_system_error does not append a chat message."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=SYSTEM_ERROR,
        request_id="req29",
        source="test",
        payload={"message": "Some error"},
    )
    vm.handle_system_error(event)

    assert vm.chat_messages == []
    assert vm.error_text == "Some error"


def test_thinking_clears_error_text_but_keeps_chat_messages() -> None:
    """Test handle_state_changed to THINKING clears error_text but keeps chat_messages."""
    vm = DesktopViewModel()
    vm.error_text = "Previous error"
    vm.chat_messages.append(ChatMessage(role="user", text="Hello"))

    event = BaseEvent(
        event_type=STATE_CHANGED,
        request_id="req30",
        source="test",
        payload={
            "previous_state": "idle",
            "current_state": "thinking",
        },
    )
    vm.handle_state_changed(event)

    assert vm.error_text == ""
    assert len(vm.chat_messages) == 1
    assert vm.chat_messages[0].text == "Hello"
