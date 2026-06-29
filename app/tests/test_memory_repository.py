"""Tests for LocalJsonMemoryRepository."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.brain.memory import (
    ConfirmedMemory,
    MemoryImportance,
    MemoryKind,
)
from app.brain.memory.repository import (
    LocalJsonMemoryRepository,
    MemoryRecord,
    MemoryRecordStatus,
    memory_record_from_confirmed,
)
from app.brain.memory.types import MemoryCandidate


def _make_record(
    id: str = "test-id",
    text: str = "测试记忆。",
    kind: MemoryKind = MemoryKind.PREFERENCE,
    status: MemoryRecordStatus = MemoryRecordStatus.ACTIVE,
) -> MemoryRecord:
    """Helper to create a MemoryRecord for testing."""
    now = datetime.now(UTC)
    return MemoryRecord(
        id=id,
        kind=kind,
        importance=MemoryImportance.MEDIUM,
        text=text,
        source="deterministic_extractor",
        created_at=now,
        updated_at=now,
        status=status,
    )


class TestLocalJsonMemoryRepository:
    """Tests for LocalJsonMemoryRepository."""

    def test_missing_file_list_active_returns_empty_tuple(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(path)
        result = repo.list_active()
        assert result == ()

    def test_missing_file_list_all_returns_empty_tuple(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(path)
        result = repo.list_all()
        assert result == ()

    def test_add_creates_parent_directory_and_file(self, tmp_path: Path) -> None:
        path = tmp_path / "subdir" / "memory.json"
        repo = LocalJsonMemoryRepository(path)
        record = _make_record()
        repo.add(record)
        assert path.exists()
        assert path.read_text(encoding="utf-8")

    def test_add_then_get_returns_same_record(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(path)
        record = _make_record()
        repo.add(record)
        result = repo.get(record.id)
        assert result is not None
        assert result.id == record.id
        assert result.text == record.text
        assert result.kind == record.kind

    def test_add_duplicate_id_raises_value_error(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(path)
        record = _make_record()
        repo.add(record)
        with pytest.raises(ValueError, match="already exists"):
            repo.add(record)

    def test_list_active_excludes_deleted(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(path)
        active = _make_record(id="active-id")
        deleted = _make_record(id="deleted-id", status=MemoryRecordStatus.DELETED)
        repo.add(active)
        repo.add(deleted)
        result = repo.list_active()
        assert len(result) == 1
        assert result[0].id == "active-id"

    def test_list_all_includes_deleted(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(path)
        active = _make_record(id="active-id")
        deleted = _make_record(id="deleted-id", status=MemoryRecordStatus.DELETED)
        repo.add(active)
        repo.add(deleted)
        result = repo.list_all()
        assert len(result) == 2

    def test_delete_marks_status_deleted(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(path)
        record = _make_record()
        repo.add(record)
        result = repo.delete(record.id)
        assert result.status == MemoryRecordStatus.DELETED

    def test_delete_updates_updated_at(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(path)
        record = _make_record()
        repo.add(record)
        original_updated = record.updated_at
        result = repo.delete(record.id)
        assert result.updated_at >= original_updated

    def test_delete_unknown_id_raises_key_error(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(path)
        with pytest.raises(KeyError):
            repo.delete("unknown-id")

    def test_clear_removes_all_records(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(path)
        repo.add(_make_record())
        repo.add(_make_record(id="second"))
        repo.clear()
        assert repo.list_all() == ()

    def test_invalid_json_raises_value_error(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        path.write_text("not valid json", encoding="utf-8")
        repo = LocalJsonMemoryRepository(path)
        with pytest.raises(ValueError):
            repo.list_all()

    def test_missing_required_field_raises_value_error(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        path.write_text('{"version":1,"records":[{"id":"test"}]}', encoding="utf-8")
        repo = LocalJsonMemoryRepository(path)
        with pytest.raises(ValueError, match="Missing required field"):
            repo.list_all()

    def test_record_serialization_roundtrip(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(path)
        original = _make_record()
        repo.add(original)
        result = repo.get(original.id)
        assert result is not None
        assert result.id == original.id
        assert result.kind == original.kind
        assert result.importance == original.importance
        assert result.text == original.text
        assert result.source == original.source
        assert result.status == original.status

    def test_datetimes_are_isoformat_and_timezone_aware(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(path)
        record = _make_record()
        repo.add(record)
        text = path.read_text(encoding="utf-8")
        assert "+00:00" in text or "Z" in text
        result = repo.get(record.id)
        assert result is not None
        assert result.created_at.tzinfo is not None
        assert result.updated_at.tzinfo is not None

    def test_json_file_contains_no_evidence_field(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(path)
        record = _make_record()
        repo.add(record)
        text = path.read_text(encoding="utf-8")
        assert "evidence" not in text


class TestMemoryRecordFromConfirmed:
    """Tests for memory_record_from_confirmed."""

    def _make_candidate(self) -> MemoryCandidate:
        return MemoryCandidate(
            kind=MemoryKind.PREFERENCE,
            importance=MemoryImportance.MEDIUM,
            text="用户喜欢短回复。",
            evidence="用户说：我喜欢短回复。",
            confidence=0.8,
        )

    def test_memory_record_from_confirmed_copies_candidate_text(self) -> None:
        now = datetime.now(UTC)
        confirmed = ConfirmedMemory(
            id="confirm-id",
            candidate=self._make_candidate(),
            created_at=now,
            confirmed_at=now,
        )
        record = memory_record_from_confirmed(confirmed)
        assert record.text == "用户喜欢短回复。"

    def test_memory_record_from_confirmed_does_not_copy_evidence(self) -> None:
        now = datetime.now(UTC)
        confirmed = ConfirmedMemory(
            id="confirm-id",
            candidate=self._make_candidate(),
            created_at=now,
            confirmed_at=now,
        )
        record = memory_record_from_confirmed(confirmed)
        # evidence is not stored in MemoryRecord
        assert not hasattr(record, "evidence")

    def test_memory_record_from_confirmed_uses_confirmed_at_as_created_at(self) -> None:
        now = datetime.now(UTC)
        confirmed = ConfirmedMemory(
            id="confirm-id",
            candidate=self._make_candidate(),
            created_at=now,
            confirmed_at=now,
        )
        record = memory_record_from_confirmed(confirmed)
        assert record.created_at == confirmed.confirmed_at

    def test_memory_record_from_confirmed_with_custom_id(self) -> None:
        now = datetime.now(UTC)
        confirmed = ConfirmedMemory(
            id="confirm-id",
            candidate=self._make_candidate(),
            created_at=now,
            confirmed_at=now,
        )
        record = memory_record_from_confirmed(confirmed, memory_id="custom-id")
        assert record.id == "custom-id"

    def test_memory_record_from_confirmed_sets_active_status(self) -> None:
        now = datetime.now(UTC)
        confirmed = ConfirmedMemory(
            id="confirm-id",
            candidate=self._make_candidate(),
            created_at=now,
            confirmed_at=now,
        )
        record = memory_record_from_confirmed(confirmed)
        assert record.status == MemoryRecordStatus.ACTIVE
