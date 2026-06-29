"""Memory core module for V8-A.

This module provides a conservative, rule-based memory candidate extractor.
Memory candidates are surfaced for inspection but not automatically persisted.
"""

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
]
