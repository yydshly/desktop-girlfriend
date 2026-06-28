"""Payload type definitions."""

from dataclasses import dataclass
from typing import Any

from app.contracts.states import AppState

# Type alias for payload dictionaries
Payload = dict[str, Any]


@dataclass
class UserTextSubmittedPayload:
    """Payload for user text submission events."""

    text: str

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {"text": self.text}


@dataclass
class AssistantTextReceivedPayload:
    """Payload for assistant text response events."""

    text: str

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {"text": self.text}


@dataclass
class StateChangeRequestedPayload:
    """Payload for state change request events."""

    target_state: AppState | str
    reason: str | None = None


@dataclass
class StateChangedPayload:
    """Payload for state changed events."""

    previous_state: AppState
    current_state: AppState

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {
            "previous_state": self.previous_state.value,
            "current_state": self.current_state.value,
        }
