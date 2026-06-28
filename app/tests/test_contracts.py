"""Tests for contracts."""

from datetime import datetime

from app.contracts.events import (
    STATE_CHANGE_REQUESTED,
    STATE_CHANGED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.contracts.payloads import StateChangedPayload
from app.contracts.states import AppState


def test_app_state_values() -> None:
    """Test AppState enum values."""
    assert AppState.IDLE.value == "idle"
    assert AppState.LISTENING.value == "listening"
    assert AppState.THINKING.value == "thinking"
    assert AppState.SPEAKING.value == "speaking"
    assert AppState.ERROR.value == "error"


def test_base_event_creation() -> None:
    """Test BaseEvent creation."""
    event = BaseEvent(
        event_type="test.event",
        request_id="req1",
        source="test",
    )
    assert event.event_type == "test.event"
    assert event.request_id == "req1"
    assert event.source == "test"
    assert isinstance(event.timestamp, datetime)
    assert event.payload == {}


def test_base_event_with_payload() -> None:
    """Test BaseEvent with payload."""
    event = BaseEvent(
        event_type="test.event",
        request_id="req1",
        source="test",
        payload={"key": "value"},
    )
    assert event.payload == {"key": "value"}


def test_event_type_constants() -> None:
    """Test event type constants."""
    assert USER_TEXT_SUBMITTED == "user.text_submitted"
    assert STATE_CHANGE_REQUESTED == "state.change_requested"
    assert STATE_CHANGED == "state.changed"
    assert SYSTEM_ERROR == "system.error"


def test_state_changed_payload_to_event_payload() -> None:
    """Test state changed payload serializes states as stable strings."""
    payload = StateChangedPayload(
        previous_state=AppState.IDLE,
        current_state=AppState.THINKING,
    )

    assert payload.to_event_payload() == {
        "previous_state": "idle",
        "current_state": "thinking",
    }
