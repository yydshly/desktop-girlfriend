"""Memory type definitions for V8-A."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MemoryKind(StrEnum):
    """Types of user memory candidates."""

    IDENTITY = "identity"
    PREFERENCE = "preference"
    RELATIONSHIP = "relationship"
    PROJECT = "project"
    HEALTH = "health"
    EMOTION_PATTERN = "emotion_pattern"
    BOUNDARY = "boundary"
    OTHER = "other"


class MemoryImportance(StrEnum):
    """Importance level for memory candidates."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


MAX_TEXT_LEN = 160


@dataclass(frozen=True)
class MemoryCandidate:
    """A possible memory item extracted from user text.

    V8-A candidates are not persisted automatically.
    They are only surfaced for inspection and later approval workflows.
    """

    kind: MemoryKind
    importance: MemoryImportance
    text: str
    evidence: str
    confidence: float
    source: str = "deterministic_extractor"

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if len(self.text) > MAX_TEXT_LEN:
            raise ValueError(f"text must not exceed {MAX_TEXT_LEN} characters")
        if len(self.evidence) > MAX_TEXT_LEN:
            raise ValueError(f"evidence must not exceed {MAX_TEXT_LEN} characters")
