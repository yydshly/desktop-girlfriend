"""Memory runtime service for V8-E.

Coordinates memory extraction, confirmation, persistence, and context building.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.brain.memory.confirmation import (
    InMemoryMemoryConfirmationStore,
    MemoryConfirmationService,
    PendingMemory,
    RejectedMemory,
)
from app.brain.memory.extractor import DeterministicMemoryExtractor
from app.brain.memory.repository import (
    MemoryRecord,
    MemoryRepository,
    memory_record_from_confirmed,
    new_memory_record_id,
    utc_now,
)
from app.brain.memory.session_context import SessionMemoryContextBuilder
from app.brain.memory.types import MemoryCandidate, MemoryImportance, MemoryKind


@dataclass(frozen=True)
class MemoryRuntimeSnapshot:
    """Snapshot of the current memory runtime state."""

    pending: tuple[PendingMemory, ...]
    active: tuple[MemoryRecord, ...]
    rejected: tuple[RejectedMemory, ...]


class MemoryRuntimeService:
    """Coordinates memory extraction, confirmation, persistence, and context building.

    V8-E is still not wired into the main chat flow.
    """

    def __init__(
        self,
        *,
        extractor: DeterministicMemoryExtractor,
        confirmation_service: MemoryConfirmationService,
        repository: MemoryRepository,
        context_builder: SessionMemoryContextBuilder,
    ) -> None:
        self._extractor = extractor
        self._confirmation_service = confirmation_service
        self._repository = repository
        self._context_builder = context_builder

    def extract_candidates(self, user_text: str) -> tuple[MemoryCandidate, ...]:
        """Extract memory candidates from user text.

        Does not create pending memories or persist anything.
        """
        return self._extractor.extract(user_text)

    def submit_user_text(self, user_text: str) -> tuple[PendingMemory, ...]:
        """Extract candidates and submit as pending memories.

        Does not auto-confirm or persist.
        """
        candidates = self._extractor.extract(user_text)
        if not candidates:
            return ()
        return self._confirmation_service.submit_candidates(candidates)

    def list_pending(self) -> tuple[PendingMemory, ...]:
        """List all pending memories."""
        return self._confirmation_service.list_pending()

    def confirm_pending(self, pending_id: str) -> MemoryRecord:
        """Confirm a pending memory and persist as a MemoryRecord.

        Args:
            pending_id: The id of the pending memory to confirm.

        Returns:
            The newly created MemoryRecord.

        Raises:
            KeyError: If pending_id is not found.
        """
        confirmed = self._confirmation_service.confirm(pending_id)
        record = memory_record_from_confirmed(confirmed)
        self._repository.add(record)
        return record

    def add_manual_record(self, text: str) -> MemoryRecord:
        """Add a memory record directly from manual user input (V8-J).

        Does not go through the confirmation flow. Does not save evidence.
        Does not save the full original conversation.

        Args:
            text: The memory text from the user's manual input.

        Returns:
            The newly created MemoryRecord.

        Raises:
            ValueError: If text is blank.
        """
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("manual memory text must not be blank")

        now = utc_now()
        record = MemoryRecord(
            id=new_memory_record_id(),
            kind=MemoryKind.OTHER,
            importance=MemoryImportance.MEDIUM,
            text=cleaned,
            source="manual_ui",
            created_at=now,
            updated_at=now,
        )
        self._repository.add(record)
        return record

    def reject_pending(self, pending_id: str, reason: str = "") -> RejectedMemory:
        """Reject a pending memory.

        Does not persist anything.

        Args:
            pending_id: The id of the pending memory to reject.
            reason: Optional rejection reason.

        Returns:
            The RejectedMemory.

        Raises:
            KeyError: If pending_id is not found.
        """
        return self._confirmation_service.reject(pending_id, reason)

    def list_active_records(self) -> tuple[MemoryRecord, ...]:
        """List all active (non-deleted) memory records."""
        return self._repository.list_active()

    def list_all_records(self) -> tuple[MemoryRecord, ...]:
        """List all memory records including deleted."""
        return self._repository.list_all()

    def delete_record(self, record_id: str) -> MemoryRecord:
        """Soft delete a memory record.

        Args:
            record_id: The id of the record to delete.

        Returns:
            The deleted MemoryRecord with status=DELETED.

        Raises:
            KeyError: If record_id is not found.
        """
        return self._repository.delete(record_id)

    def build_session_context(self) -> str:
        """Build a session memory context from active records.

        Returns:
            A formatted context string for prompt injection.
        """
        records = self._repository.list_active()
        return self._context_builder.build_from_records(records)

    def snapshot(self) -> MemoryRuntimeSnapshot:
        """Get a snapshot of the current runtime state.

        Returns:
            MemoryRuntimeSnapshot with pending, active, and rejected memories.
        """
        return MemoryRuntimeSnapshot(
            pending=self._confirmation_service.list_pending(),
            active=self._repository.list_active(),
            rejected=self._confirmation_service.list_rejected(),
        )


def create_local_memory_runtime(
    repository: MemoryRepository,
) -> MemoryRuntimeService:
    """Create a local memory runtime service with default components.

    Args:
        repository: The memory repository to use for persistence.

    Returns:
        A configured MemoryRuntimeService instance.
    """
    store = InMemoryMemoryConfirmationStore()
    confirmation_service = MemoryConfirmationService(store)
    return MemoryRuntimeService(
        extractor=DeterministicMemoryExtractor(),
        confirmation_service=confirmation_service,
        repository=repository,
        context_builder=SessionMemoryContextBuilder(),
    )
