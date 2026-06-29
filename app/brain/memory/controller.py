"""Memory suggestion controller for V8-H.

Coordinates memory suggestion events:
- Listens for USER_TEXT_SUBMITTED to generate pending memories
- Publishes MEMORY_SUGGESTIONS_DETECTED with pending memory info
- Handles MEMORY_CONFIRM_REQUESTED to persist active memory
- Handles MEMORY_REJECT_REQUESTED to reject pending memory

This controller does not:
- Auto-confirm or auto-reject memories
- Auto-save user chat
- Call LLM or access network
- Open microphone
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable

from app.brain.memory.runtime import MemoryRuntimeService
from app.contracts.events import (
    MEMORY_ADD_REQUESTED,
    MEMORY_ADDED,
    MEMORY_CONFIRM_REQUESTED,
    MEMORY_CONFIRMED,
    MEMORY_DELETE_REQUESTED,
    MEMORY_DELETED,
    MEMORY_ERROR,
    MEMORY_LIST_REQUESTED,
    MEMORY_LISTED,
    MEMORY_REJECT_REQUESTED,
    MEMORY_REJECTED,
    MEMORY_SUGGESTIONS_DETECTED,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.contracts.payloads import (
    MemoryAddedPayload,
    MemoryConfirmedPayload,
    MemoryDeletedPayload,
    MemoryErrorPayload,
    MemoryListedPayload,
    MemoryRecordPayload,
    MemoryRejectedPayload,
    MemorySuggestionPayload,
    MemorySuggestionsDetectedPayload,
)

logger = logging.getLogger(__name__)


class MemorySuggestionController:
    """Coordinates memory suggestion events.

    V8-H creates pending memories and emits events.
    It does not auto-confirm or auto-persist user chat.
    """

    def __init__(
        self,
        *,
        runtime: MemoryRuntimeService,
        subscribe: Callable[[str, Callable[[BaseEvent], None]], None],
        unsubscribe: Callable[[str, Callable[[BaseEvent], None]], None],
        dispatch_event: Callable[[BaseEvent], None],
    ) -> None:
        self._runtime = runtime
        self._subscribe = subscribe
        self._unsubscribe = unsubscribe
        self._dispatch_event = dispatch_event
        self._started = False

    def start(self) -> None:
        """Start the controller by subscribing to relevant events.

        Idempotent: calling start multiple times does not duplicate subscriptions.
        """
        if self._started:
            return
        self._started = True
        self._subscribe(USER_TEXT_SUBMITTED, self._on_user_text_submitted)
        self._subscribe(MEMORY_CONFIRM_REQUESTED, self._on_memory_confirm_requested)
        self._subscribe(MEMORY_REJECT_REQUESTED, self._on_memory_reject_requested)
        self._subscribe(MEMORY_ADD_REQUESTED, self._on_memory_add_requested)
        self._subscribe(MEMORY_LIST_REQUESTED, self._on_memory_list_requested)
        self._subscribe(MEMORY_DELETE_REQUESTED, self._on_memory_delete_requested)

    def stop(self) -> None:
        """Stop the controller by unsubscribing from events.

        Idempotent: calling stop multiple times does not cause errors.
        """
        if not self._started:
            return
        self._started = False
        self._unsubscribe(USER_TEXT_SUBMITTED, self._on_user_text_submitted)
        self._unsubscribe(MEMORY_CONFIRM_REQUESTED, self._on_memory_confirm_requested)
        self._unsubscribe(MEMORY_REJECT_REQUESTED, self._on_memory_reject_requested)
        self._unsubscribe(MEMORY_ADD_REQUESTED, self._on_memory_add_requested)
        self._unsubscribe(MEMORY_LIST_REQUESTED, self._on_memory_list_requested)
        self._unsubscribe(MEMORY_DELETE_REQUESTED, self._on_memory_delete_requested)

    def _dispatch_memory_error(self, message: str) -> None:
        """Dispatch a memory error event."""
        self._dispatch_event(
            BaseEvent(
                event_type=MEMORY_ERROR,
                request_id=str(uuid.uuid4()),
                source="memory_suggestion_controller",
                payload=MemoryErrorPayload(message=message).to_event_payload(),
            )
        )

    def _on_user_text_submitted(self, event: BaseEvent) -> None:
        """Handle user text submission by extracting memory candidates.

        Does not auto-confirm or auto-persist. Only creates pending memories.
        """
        text = event.payload.get("text")
        if not isinstance(text, str) or not text.strip():
            return

        try:
            pending = self._runtime.submit_user_text(text)
        except Exception:
            logger.exception("Memory suggestion extraction failed")
            self._dispatch_memory_error("Memory suggestion extraction failed")
            return

        if not pending:
            return

        suggestions = [
            MemorySuggestionPayload(
                pending_id=p.id,
                kind=p.candidate.kind.value,
                importance=p.candidate.importance.value,
                text=p.candidate.text,
            )
            for p in pending
        ]

        self._dispatch_event(
            BaseEvent(
                event_type=MEMORY_SUGGESTIONS_DETECTED,
                request_id=event.request_id or str(uuid.uuid4()),
                source="memory_suggestion_controller",
                payload=MemorySuggestionsDetectedPayload(
                    suggestions=suggestions
                ).to_event_payload(),
            )
        )

    def _on_memory_confirm_requested(self, event: BaseEvent) -> None:
        """Handle confirm request by persisting the pending memory.

        Only confirm_requested writes to the repository.
        """
        pending_id = event.payload.get("pending_id")
        if not isinstance(pending_id, str) or not pending_id.strip():
            self._dispatch_memory_error("Invalid pending_id")
            return

        try:
            record = self._runtime.confirm_pending(pending_id)
        except KeyError:
            self._dispatch_memory_error("Pending memory not found")
            return
        except Exception:
            logger.exception("Memory confirmation failed")
            self._dispatch_memory_error("Memory confirmation failed")
            return

        self._dispatch_event(
            BaseEvent(
                event_type=MEMORY_CONFIRMED,
                request_id=event.request_id or str(uuid.uuid4()),
                source="memory_suggestion_controller",
                payload=MemoryConfirmedPayload(
                    record_id=record.id,
                    kind=record.kind.value,
                    importance=record.importance.value,
                    text=record.text,
                ).to_event_payload(),
            )
        )

    def _on_memory_reject_requested(self, event: BaseEvent) -> None:
        """Handle reject request by rejecting the pending memory.

        Does not write to the repository.
        """
        pending_id = event.payload.get("pending_id")
        reason = event.payload.get("reason", "")

        if not isinstance(pending_id, str) or not pending_id.strip():
            self._dispatch_memory_error("Invalid pending_id")
            return

        if not isinstance(reason, str):
            reason = ""

        try:
            rejected = self._runtime.reject_pending(pending_id, reason)
        except KeyError:
            self._dispatch_memory_error("Pending memory not found")
            return
        except Exception:
            logger.exception("Memory rejection failed")
            self._dispatch_memory_error("Memory rejection failed")
            return

        self._dispatch_event(
            BaseEvent(
                event_type=MEMORY_REJECTED,
                request_id=event.request_id or str(uuid.uuid4()),
                source="memory_suggestion_controller",
                payload=MemoryRejectedPayload(
                    rejected_id=rejected.id,
                    kind=rejected.candidate.kind.value,
                    reason=rejected.reason,
                ).to_event_payload(),
            )
        )

    def _on_memory_add_requested(self, event: BaseEvent) -> None:
        """Handle manual memory add request by persisting a record."""
        text = event.payload.get("text")
        if not isinstance(text, str) or not text.strip():
            self._dispatch_memory_error("Manual memory text cannot be blank")
            return

        try:
            record = self._runtime.add_manual_record(text)
        except Exception:
            logger.exception("Manual memory add failed")
            self._dispatch_memory_error("Manual memory add failed")
            return

        self._dispatch_event(
            BaseEvent(
                event_type=MEMORY_ADDED,
                request_id=event.request_id or str(uuid.uuid4()),
                source="memory_suggestion_controller",
                payload=MemoryAddedPayload(
                    record_id=record.id,
                    kind=record.kind.value,
                    importance=record.importance.value,
                    text=record.text,
                ).to_event_payload(),
            )
        )

    def _on_memory_list_requested(self, event: BaseEvent) -> None:
        """Handle list request by returning all active memory records.

        Only returns active (non-deleted) records.
        """
        try:
            records = self._runtime.list_active_records()
        except Exception:
            logger.exception("Memory list failed")
            self._dispatch_memory_error("Memory list failed")
            return

        payload_records = [
            MemoryRecordPayload(
                record_id=r.id,
                kind=r.kind.value,
                importance=r.importance.value,
                text=r.text,
                created_at=r.created_at.isoformat(),
                updated_at=r.updated_at.isoformat(),
            )
            for r in records
        ]

        self._dispatch_event(
            BaseEvent(
                event_type=MEMORY_LISTED,
                request_id=event.request_id or str(uuid.uuid4()),
                source="memory_suggestion_controller",
                payload=MemoryListedPayload(
                    records=payload_records
                ).to_event_payload(),
            )
        )

    def _on_memory_delete_requested(self, event: BaseEvent) -> None:
        """Handle delete request by soft-deleting a memory record."""
        record_id = event.payload.get("record_id")
        if not isinstance(record_id, str) or not record_id.strip():
            self._dispatch_memory_error("Invalid record_id")
            return

        try:
            deleted = self._runtime.delete_record(record_id)
        except KeyError:
            self._dispatch_memory_error("Memory record not found")
            return
        except Exception:
            logger.exception("Memory delete failed")
            self._dispatch_memory_error("Memory delete failed")
            return

        self._dispatch_event(
            BaseEvent(
                event_type=MEMORY_DELETED,
                request_id=event.request_id or str(uuid.uuid4()),
                source="memory_suggestion_controller",
                payload=MemoryDeletedPayload(
                    record_id=deleted.id
                ).to_event_payload(),
            )
        )
