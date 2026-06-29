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


# Memory management payloads (V8-J)


@dataclass
class MemoryAddRequestedPayload:
    """Payload for memory.add_requested events (V8-J manual add)."""

    text: str

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {"text": self.text}


@dataclass
class MemoryAddedPayload:
    """Payload for memory.added events (V8-J manual add)."""

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
class MemoryRecordPayload:
    """Single memory record payload."""

    record_id: str
    kind: str
    importance: str
    text: str
    created_at: str
    updated_at: str

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {
            "record_id": self.record_id,
            "kind": self.kind,
            "importance": self.importance,
            "text": self.text,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class MemoryListedPayload:
    """Payload for memory.listed events."""

    records: list[MemoryRecordPayload]

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {
            "records": [
                record.to_event_payload() for record in self.records
            ]
        }


@dataclass
class MemoryListRequestedPayload:
    """Payload for memory.list_requested events."""

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {}


@dataclass
class MemoryDeleteRequestedPayload:
    """Payload for memory.delete_requested events."""

    record_id: str

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {"record_id": self.record_id}


@dataclass
class MemoryDeletedPayload:
    """Payload for memory.deleted events."""

    record_id: str

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {"record_id": self.record_id}


# Proactive nudge payloads (V9-A)


@dataclass
class ProactiveNudgeReadyPayload:
    """Payload for proactive.nudge_ready events."""

    text: str

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {"text": self.text}
