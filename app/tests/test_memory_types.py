"""Tests for memory types."""

import pytest

from app.brain.memory import MemoryCandidate, MemoryImportance, MemoryKind


class TestMemoryKind:
    """Tests for MemoryKind enum."""

    def test_memory_kind_values(self) -> None:
        assert MemoryKind.IDENTITY.value == "identity"
        assert MemoryKind.PREFERENCE.value == "preference"
        assert MemoryKind.RELATIONSHIP.value == "relationship"
        assert MemoryKind.PROJECT.value == "project"
        assert MemoryKind.HEALTH.value == "health"
        assert MemoryKind.EMOTION_PATTERN.value == "emotion_pattern"
        assert MemoryKind.BOUNDARY.value == "boundary"
        assert MemoryKind.OTHER.value == "other"


class TestMemoryImportance:
    """Tests for MemoryImportance enum."""

    def test_memory_importance_values(self) -> None:
        assert MemoryImportance.LOW.value == "low"
        assert MemoryImportance.MEDIUM.value == "medium"
        assert MemoryImportance.HIGH.value == "high"


class TestMemoryCandidate:
    """Tests for MemoryCandidate dataclass."""

    def test_default_source(self) -> None:
        candidate = MemoryCandidate(
            kind=MemoryKind.PREFERENCE,
            importance=MemoryImportance.MEDIUM,
            text="用户喜欢短回复。",
            evidence="我喜欢短回复。",
            confidence=0.75,
        )
        assert candidate.source == "deterministic_extractor"

    def test_confidence_zero_legal(self) -> None:
        candidate = MemoryCandidate(
            kind=MemoryKind.PREFERENCE,
            importance=MemoryImportance.MEDIUM,
            text="用户喜欢短回复。",
            evidence="我喜欢短回复。",
            confidence=0.0,
        )
        assert candidate.confidence == 0.0

    def test_confidence_one_legal(self) -> None:
        candidate = MemoryCandidate(
            kind=MemoryKind.PREFERENCE,
            importance=MemoryImportance.MEDIUM,
            text="用户喜欢短回复。",
            evidence="我喜欢短回复。",
            confidence=1.0,
        )
        assert candidate.confidence == 1.0

    def test_confidence_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence must be between"):
            MemoryCandidate(
                kind=MemoryKind.PREFERENCE,
                importance=MemoryImportance.MEDIUM,
                text="用户喜欢短回复。",
                evidence="我喜欢短回复。",
                confidence=-0.1,
            )

    def test_confidence_over_one_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence must be between"):
            MemoryCandidate(
                kind=MemoryKind.PREFERENCE,
                importance=MemoryImportance.MEDIUM,
                text="用户喜欢短回复。",
                evidence="我喜欢短回复。",
                confidence=1.1,
            )

    def test_text_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="text must not exceed"):
            MemoryCandidate(
                kind=MemoryKind.PREFERENCE,
                importance=MemoryImportance.MEDIUM,
                text="x" * 161,
                evidence="我喜欢短回复。",
                confidence=0.75,
            )

    def test_evidence_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="evidence must not exceed"):
            MemoryCandidate(
                kind=MemoryKind.PREFERENCE,
                importance=MemoryImportance.MEDIUM,
                text="用户喜欢短回复。",
                evidence="x" * 161,
                confidence=0.75,
            )

    def test_custom_source(self) -> None:
        candidate = MemoryCandidate(
            kind=MemoryKind.PREFERENCE,
            importance=MemoryImportance.MEDIUM,
            text="用户喜欢短回复。",
            evidence="我喜欢短回复。",
            confidence=0.75,
            source="custom_source",
        )
        assert candidate.source == "custom_source"

    def test_frozen_immutable(self) -> None:
        candidate = MemoryCandidate(
            kind=MemoryKind.PREFERENCE,
            importance=MemoryImportance.MEDIUM,
            text="用户喜欢短回复。",
            evidence="我喜欢短回复。",
            confidence=0.75,
        )
        with pytest.raises(AttributeError):
            candidate.confidence = 0.5  # type: ignore[misc]
