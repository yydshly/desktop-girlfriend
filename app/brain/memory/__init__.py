"""Memory core module for V8-A through V8-H.

V8-A: Rule-based memory candidate extraction.
V8-B: Memory confirmation state machine (Pending -> Confirmed/Rejected).
V8-C: Session memory context injection (ConfirmedMemory -> prompt context).
V8-D: Local memory persistence repository (LocalJsonMemoryRepository).
V8-E: Memory runtime service coordinating all above modules.
V8-F: Memory runtime CLI for local debugging and probe.
V8-G: Read-only memory context integration for main chat flow.
V8-H: Memory suggestion event flow.

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
from app.brain.memory.runtime import (
    MemoryRuntimeService,
    MemoryRuntimeSnapshot,
    create_local_memory_runtime,
)
from app.brain.memory.cli import run_memory_cli
from app.brain.memory.controller import MemorySuggestionController
from app.brain.memory.integration import (
    create_memory_context_provider_from_config,
    create_readonly_memory_context_provider,
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
    # V8-E runtime types
    "MemoryRuntimeSnapshot",
    "MemoryRuntimeService",
    "create_local_memory_runtime",
    # V8-F CLI
    "run_memory_cli",
    # V8-G integration
    "create_readonly_memory_context_provider",
    "create_memory_context_provider_from_config",
    # V8-H controller
    "MemorySuggestionController",
]
