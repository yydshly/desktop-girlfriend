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


# Memory suggestion payloads (V8-H)


@dataclass
class MemorySuggestionPayload:
    """Single memory suggestion payload."""

    pending_id: str
    kind: str
    importance: str
    text: str

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {
            "pending_id": self.pending_id,
            "kind": self.kind,
            "importance": self.importance,
            "text": self.text,
        }


@dataclass
class MemorySuggestionsDetectedPayload:
    """Payload for memory.suggestions_detected events."""

    suggestions: list[MemorySuggestionPayload]

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {
            "suggestions": [
                suggestion.to_event_payload() for suggestion in self.suggestions
            ]
        }


@dataclass
class MemoryConfirmRequestedPayload:
    """Payload for memory.confirm_requested events."""

    pending_id: str

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {"pending_id": self.pending_id}


@dataclass
class MemoryRejectRequestedPayload:
    """Payload for memory.reject_requested events."""

    pending_id: str
    reason: str = ""

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {"pending_id": self.pending_id, "reason": self.reason}


@dataclass
class MemoryConfirmedPayload:
    """Payload for memory.confirmed events."""

    record_id: str
    kind: str
    importance: str
    text: str

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {
            "record_id": self.record_id,
            "kind": self.kind,
            "importance": self.importance,
            "text": self.text,
        }


@dataclass
class MemoryRejectedPayload:
    """Payload for memory.rejected events."""

    rejected_id: str
    kind: str
    reason: str

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {
            "rejected_id": self.rejected_id,
            "kind": self.kind,
            "reason": self.reason,
        }


@dataclass
class MemoryErrorPayload:
    """Payload for memory.error events."""

    message: str

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {"message": self.message}
