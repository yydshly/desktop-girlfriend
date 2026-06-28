"""Tests for DesktopViewModel."""

from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGED,
    BaseEvent,
)
from app.contracts.states import AppState
from app.ui.view_model import DesktopViewModel


def test_view_model_initial_state() -> None:
    """Test ViewModel initial state is IDLE with correct display text."""
    vm = DesktopViewModel()
    assert vm.state == AppState.IDLE
    assert vm.display_text == "状态：待机"
    assert vm.assistant_text == ""


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
    assert vm.display_text == "状态：聆听中"


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
    assert vm.display_text == "状态：思考中"


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
    assert vm.display_text == "状态：说话中"


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
    assert vm.display_text == "状态：错误"


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
    assert vm.display_text == "状态：错误"


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
    assert vm.display_text == "状态：错误"


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
    assert vm.display_text == "状态：错误"


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
    assert vm.display_text == "状态：错误"


# Assistant text tests


def test_handle_assistant_text_received_updates_assistant_text() -> None:
    """Test handle_assistant_text_received updates assistant_text."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=ASSISTANT_TEXT_RECEIVED,
        request_id="req10",
        source="test",
        payload={"text": "Hello from assistant!"},
    )
    vm.handle_assistant_text_received(event)

    assert vm.assistant_text == "Hello from assistant!"


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


def test_handle_assistant_text_received_missing_text_keeps_previous() -> None:
    """Test handle_assistant_text_received with missing text keeps previous."""
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


def test_handle_assistant_text_received_non_string_text_keeps_previous() -> None:
    """Test handle_assistant_text_received with non-string text keeps previous."""
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


def test_handle_assistant_text_received_str_subclass_keeps_previous() -> None:
    """Test handle_assistant_text_received with str subclass keeps previous."""

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
