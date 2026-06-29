"""Memory core module for V8-A, V8-B, V8-C, and V8-D.

V8-A: Rule-based memory candidate extraction.
V8-B: Memory confirmation state machine (Pending -> Confirmed/Rejected).
V8-C: Session memory context injection (ConfirmedMemory -> prompt context).
V8-D: Local memory persistence repository (LocalJsonMemoryRepository).

Memory candidates are surfaced for inspection but not automatically persisted.
"""

from app.brain.memory.confirmation import (
    ConfirmedMemory,
    InMemoryMemoryConfirmationStore,
    MemoryConfirmationService,
    MemoryConfirmationStatus,
    PendingMemory,
    RejectedMemory,
)
from app.brain.memory.extractor import DeterministicMemoryExtractor
from app.brain.memory.probe_cases import DEFAULT_MEMORY_PROBE_CASES, MemoryProbeCase
from app.brain.memory.repository import (
    LocalJsonMemoryRepository,
    MemoryRecord,
    MemoryRecordStatus,
    MemoryRepository,
    memory_record_from_confirmed,
)
from app.brain.memory.session_context import (
    SessionMemoryContextBuilder,
    SessionMemoryContextConfig,
)
from app.brain.memory.types import MemoryCandidate, MemoryImportance, MemoryKind

__all__ = [
    "DeterministicMemoryExtractor",
    "MemoryCandidate",
    "MemoryImportance",
    "MemoryKind",
    "DEFAULT_MEMORY_PROBE_CASES",
    "MemoryProbeCase",
    # V8-B confirmation types
    "MemoryConfirmationStatus",
    "PendingMemory",
    "ConfirmedMemory",
    "RejectedMemory",
    "InMemoryMemoryConfirmationStore",
    "MemoryConfirmationService",
    # V8-C session context types
    "SessionMemoryContextBuilder",
    "SessionMemoryContextConfig",
    # V8-D repository types
    "MemoryRecordStatus",
    "MemoryRecord",
    "MemoryRepository",
    "LocalJsonMemoryRepository",
    "memory_record_from_confirmed",
]
