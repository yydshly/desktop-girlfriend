"""Map application events to Live2D desktop bridge messages."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    CONVERSATION_CLEARED,
    STATE_CHANGED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)

_STATE_TO_AVATAR_STATE = {
    "idle": "idle",
    "listening": "think",
    "thinking": "think",
    "speaking": "speak",
    "error": "sad",
}

_SUPPORTED_EVENT_TYPES = (
    USER_TEXT_SUBMITTED,
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGED,
    SYSTEM_ERROR,
    CONVERSATION_CLEARED,
)


@dataclass
class Live2DBridgeEventMapper:
    """Convert EventBus events into JSON-safe Live2D bridge messages."""

    last_user_text: str = ""

    def map_event(self, event: BaseEvent) -> dict[str, Any] | None:
        """Return a bridge message for a supported event, otherwise None."""

        if event.event_type == USER_TEXT_SUBMITTED:
            return self._map_user_text_submitted(event)
        if event.event_type == ASSISTANT_TEXT_RECEIVED:
            return self._map_assistant_text_received(event)
        if event.event_type == STATE_CHANGED:
            return self._map_state_changed(event)
        if event.event_type == SYSTEM_ERROR:
            return self._avatar_state("sad", event, reason="system_error")
        if event.event_type == CONVERSATION_CLEARED:
            self.last_user_text = ""
            return self._avatar_state("idle", event, reason="conversation_cleared")
        return None

    def _map_user_text_submitted(self, event: BaseEvent) -> dict[str, Any]:
        text = event.payload.get("text")
        self.last_user_text = text.strip() if isinstance(text, str) else ""
        return self._avatar_sequence("listen", event, user_text=self.last_user_text)

    def _map_assistant_text_received(self, event: BaseEvent) -> dict[str, Any]:
        text = event.payload.get("text")
        response_text = text.strip() if isinstance(text, str) else ""
        return {
            "type": "dialogue.turn",
            "payload": {
                "turn_id": event.request_id,
                "intent": "reply",
                "user_text": self.last_user_text,
                "response_text": response_text,
                "tts_state": "speaking",
                "source_event": event.event_type,
            },
        }

    def _map_state_changed(self, event: BaseEvent) -> dict[str, Any]:
        current_state = event.payload.get("current_state")
        state_name = current_state if isinstance(current_state, str) else "error"
        avatar_state = _STATE_TO_AVATAR_STATE.get(state_name, "idle")
        return self._avatar_state(
            avatar_state,
            event,
            app_state=state_name,
            reason=event.payload.get("reason", ""),
        )

    @staticmethod
    def _avatar_state(
        state: str,
        event: BaseEvent,
        **payload: Any,
    ) -> dict[str, Any]:
        return {
            "type": "avatar.state",
            "payload": {
                "state": state,
                "request_id": event.request_id,
                "source_event": event.event_type,
                **payload,
            },
        }

    @staticmethod
    def _avatar_sequence(
        name: str,
        event: BaseEvent,
        **payload: Any,
    ) -> dict[str, Any]:
        return {
            "type": "avatar.sequence",
            "payload": {
                "name": name,
                "request_id": event.request_id,
                "source_event": event.event_type,
                **payload,
            },
        }


class Live2DBridgeEventDispatcher:
    """Subscribe to EventBus events and broadcast mapped Live2D messages."""

    def __init__(
        self,
        subscribe: Callable[[str, Callable[[BaseEvent], None]], None],
        unsubscribe: Callable[[str, Callable[[BaseEvent], None]], None],
        broadcast: Callable[[dict[str, Any]], None],
        mapper: Live2DBridgeEventMapper | None = None,
    ) -> None:
        self._subscribe = subscribe
        self._unsubscribe = unsubscribe
        self._broadcast = broadcast
        self._mapper = mapper or Live2DBridgeEventMapper()
        self._started = False

    def start(self) -> None:
        """Subscribe to supported app events."""

        if self._started:
            return
        for event_type in _SUPPORTED_EVENT_TYPES:
            self._subscribe(event_type, self._handle_event)
        self._started = True

    def stop(self) -> None:
        """Unsubscribe from supported app events."""

        if not self._started:
            return
        for event_type in _SUPPORTED_EVENT_TYPES:
            self._unsubscribe(event_type, self._handle_event)
        self._started = False

    def _handle_event(self, event: BaseEvent) -> None:
        message = self._mapper.map_event(event)
        if message is not None:
            self._broadcast(message)
