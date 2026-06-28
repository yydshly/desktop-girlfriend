"""Tests for DesktopViewModel."""

from app.contracts.events import STATE_CHANGED, BaseEvent
from app.contracts.states import AppState
from app.ui.view_model import DesktopViewModel


def test_view_model_initial_state() -> None:
    """Test ViewModel initial state is IDLE with correct display text."""
    vm = DesktopViewModel()
    assert vm.state == AppState.IDLE
    assert vm.display_text == "状态：待机"


def test_handle_state_changed_to_listening() -> None:
    """Test handle_state_changed updates to LISTENING state."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=STATE_CHANGED,
        request_id="req1",
        source="test",
        payload={
            "previous_state": AppState.IDLE,
            "current_state": AppState.LISTENING,
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
            "previous_state": AppState.LISTENING,
            "current_state": AppState.THINKING,
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
            "previous_state": AppState.THINKING,
            "current_state": AppState.SPEAKING,
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
            "previous_state": AppState.SPEAKING,
            "current_state": AppState.ERROR,
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


def test_handle_state_changed_with_string_current_state() -> None:
    """Test handle_state_changed handles string current_state in payload."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=STATE_CHANGED,
        request_id="req6",
        source="test",
        payload={
            "previous_state": {"value": "idle"},
            "current_state": {"value": "thinking"},
        },
    )
    vm.handle_state_changed(event)

    assert vm.state == AppState.THINKING
    assert vm.display_text == "状态：思考中"


def test_handle_state_changed_invalid_state_defaults_to_error() -> None:
    """Test handle_state_changed with invalid state defaults to ERROR."""
    vm = DesktopViewModel()

    event = BaseEvent(
        event_type=STATE_CHANGED,
        request_id="req7",
        source="test",
        payload={
            "previous_state": AppState.IDLE,
            "current_state": "invalid_state",
        },
    )
    vm.handle_state_changed(event)

    assert vm.state == AppState.ERROR
