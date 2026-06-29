"""Memory confirmation types and in-memory store for V8-B."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from app.brain.memory.types import MemoryCandidate


class MemoryConfirmationStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


@dataclass(frozen=True)
class PendingMemory:
    id: str
    candidate: MemoryCandidate
    created_at: datetime


@dataclass(frozen=True)
class ConfirmedMemory:
    id: str
    candidate: MemoryCandidate
    created_at: datetime
    confirmed_at: datetime


@dataclass(frozen=True)
class RejectedMemory:
    id: str
    candidate: MemoryCandidate
    created_at: datetime
    rejected_at: datetime
    reason: str = ""


def utc_now() -> datetime:
    """Return current UTC datetime with timezone awareness."""
    return datetime.now(UTC)


def new_memory_id() -> str:
    """Generate a new unique memory id."""
    return str(uuid4())


class InMemoryMemoryConfirmationStore:
    """In-memory confirmation store for V8-B.

    This store is intentionally not persistent.
    It exists only for tests and local probes.
    """

    def __init__(self) -> None:
        self._pending: dict[str, PendingMemory] = {}
        self._confirmed: dict[str, ConfirmedMemory] = {}
        self._rejected: dict[str, RejectedMemory] = {}

    def add_pending(self, candidate: MemoryCandidate) -> PendingMemory:
        """Add a candidate as a pending memory."""
        memory_id = new_memory_id()
        pending = PendingMemory(
            id=memory_id,
            candidate=candidate,
            created_at=utc_now(),
        )
        self._pending[memory_id] = pending
        return pending

    def get_pending(self, memory_id: str) -> PendingMemory | None:
        """Get a pending memory by id."""
        return self._pending.get(memory_id)

    def list_pending(self) -> tuple[PendingMemory, ...]:
        """List all pending memories."""
        return tuple(self._pending.values())

    def list_confirmed(self) -> tuple[ConfirmedMemory, ...]:
        """List all confirmed memories."""
        return tuple(self._confirmed.values())

    def list_rejected(self) -> tuple[RejectedMemory, ...]:
        """List all rejected memories."""
        return tuple(self._rejected.values())

    def confirm(self, memory_id: str) -> ConfirmedMemory:
        """Confirm a pending memory."""
        if memory_id in self._confirmed:
            raise KeyError(f"Memory already confirmed: {memory_id}")
        if memory_id in self._rejected:
            raise KeyError(f"Memory already rejected: {memory_id}")
        pending = self._pending.get(memory_id)
        if pending is None:
            raise KeyError(f"No pending memory with id: {memory_id}")

        confirmed = ConfirmedMemory(
            id=pending.id,
            candidate=pending.candidate,
            created_at=pending.created_at,
            confirmed_at=utc_now(),
        )
        del self._pending[memory_id]
        self._confirmed[memory_id] = confirmed
        return confirmed

    def reject(self, memory_id: str, reason: str = "") -> RejectedMemory:
        """Reject a pending memory."""
        if memory_id in self._confirmed:
            raise KeyError(f"Memory already confirmed: {memory_id}")
        if memory_id in self._rejected:
            raise KeyError(f"Memory already rejected: {memory_id}")
        pending = self._pending.get(memory_id)
        if pending is None:
            raise KeyError(f"No pending memory with id: {memory_id}")

        rejected = RejectedMemory(
            id=pending.id,
            candidate=pending.candidate,
            created_at=pending.created_at,
            rejected_at=utc_now(),
            reason=reason,
        )
        del self._pending[memory_id]
        self._rejected[memory_id] = rejected
        return rejected

    def clear(self) -> None:
        """Clear all states."""
        self._pending.clear()
        self._confirmed.clear()
        self._rejected.clear()


class MemoryConfirmationService:
    """Service for turning candidates into pending memories and resolving them."""

    def __init__(self, store: InMemoryMemoryConfirmationStore) -> None:
        self._store = store

    def submit_candidates(
        self,
        candidates: tuple[MemoryCandidate, ...],
    ) -> tuple[PendingMemory, ...]:
        """Submit candidates to become pending memories."""
        if not candidates:
            return ()
        pending_memories: list[PendingMemory] = []
        for candidate in candidates:
            pending = self._store.add_pending(candidate)
            pending_memories.append(pending)
        return tuple(pending_memories)

    def confirm(self, memory_id: str) -> ConfirmedMemory:
        """Confirm a pending memory."""
        return self._store.confirm(memory_id)

    def reject(self, memory_id: str, reason: str = "") -> RejectedMemory:
        """Reject a pending memory."""
        return self._store.reject(memory_id, reason)

    def list_pending(self) -> tuple[PendingMemory, ...]:
        """List all pending memories."""
        return self._store.list_pending()

    def list_confirmed(self) -> tuple[ConfirmedMemory, ...]:
        """List all confirmed memories."""
        return self._store.list_confirmed()

    def list_rejected(self) -> tuple[RejectedMemory, ...]:
        """List all rejected memories."""
        return self._store.list_rejected()
