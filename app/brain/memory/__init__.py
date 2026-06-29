"""Memory core module for V8-A and V8-B.

V8-A: Rule-based memory candidate extraction.
V8-B: Memory confirmation state machine (Pending -> Confirmed/Rejected).

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
]
