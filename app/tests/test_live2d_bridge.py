"""Tests for mapping app events to Live2D bridge messages."""

from __future__ import annotations

from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    CONVERSATION_CLEARED,
    STATE_CHANGED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.ui.live2d_bridge import Live2DBridgeEventMapper


def _event(event_type: str, payload: dict | None = None) -> BaseEvent:
    return BaseEvent(
        event_type=event_type,
        request_id="req-1",
        source="test",
        payload=payload or {},
    )


def test_user_text_maps_to_listen_sequence_and_stores_text() -> None:
    """User text makes the avatar listen and stores turn context."""
    mapper = Live2DBridgeEventMapper()

    message = mapper.map_event(_event(USER_TEXT_SUBMITTED, {"text": "  hello  "}))

    assert message == {
        "type": "avatar.sequence",
        "payload": {
            "name": "listen",
            "request_id": "req-1",
            "source_event": USER_TEXT_SUBMITTED,
            "user_text": "hello",
        },
    }
    assert mapper.last_user_text == "hello"


def test_assistant_text_maps_to_dialogue_turn_with_last_user_text() -> None:
    """Assistant text becomes a dialogue.turn message for reply animation."""
    mapper = Live2DBridgeEventMapper(last_user_text="hello")

    message = mapper.map_event(_event(ASSISTANT_TEXT_RECEIVED, {"text": "  hi  "}))

    assert message == {
        "type": "dialogue.turn",
        "payload": {
            "turn_id": "req-1",
            "intent": "reply",
            "user_text": "hello",
            "response_text": "hi",
            "tts_state": "speaking",
            "source_event": ASSISTANT_TEXT_RECEIVED,
        },
    }


def test_state_changed_maps_app_state_to_avatar_state() -> None:
    """State changes drive coarse avatar states."""
    mapper = Live2DBridgeEventMapper()

    message = mapper.map_event(_event(STATE_CHANGED, {"current_state": "speaking"}))

    assert message == {
        "type": "avatar.state",
        "payload": {
            "state": "speak",
            "request_id": "req-1",
            "source_event": STATE_CHANGED,
            "app_state": "speaking",
            "reason": "",
        },
    }


def test_error_event_maps_to_sad_state() -> None:
    """System errors make the avatar visibly low instead of silently idling."""
    mapper = Live2DBridgeEventMapper()

    message = mapper.map_event(_event(SYSTEM_ERROR, {"message": "boom"}))

    assert message["type"] == "avatar.state"
    assert message["payload"]["state"] == "sad"
    assert message["payload"]["reason"] == "system_error"


def test_conversation_cleared_resets_context_and_avatar() -> None:
    """Clearing conversation resets stored turn context and avatar state."""
    mapper = Live2DBridgeEventMapper(last_user_text="hello")

    message = mapper.map_event(_event(CONVERSATION_CLEARED))

    assert mapper.last_user_text == ""
    assert message["type"] == "avatar.state"
    assert message["payload"]["state"] == "idle"
    assert message["payload"]["reason"] == "conversation_cleared"


def test_unknown_event_is_ignored() -> None:
    """Unsupported events do not emit bridge noise."""
    mapper = Live2DBridgeEventMapper()

    assert mapper.map_event(_event("memory.listed")) is None
