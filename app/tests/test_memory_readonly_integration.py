"""Tests for read-only memory context integration (V8-G)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.brain.memory.integration import (
    create_memory_context_provider_from_config,
    create_readonly_memory_context_provider,
)
from app.brain.memory.repository import (
    LocalJsonMemoryRepository,
    MemoryRecord,
    MemoryRecordStatus,
)
from app.brain.memory.session_context import SessionMemoryContextBuilder
from app.brain.memory.types import MemoryImportance, MemoryKind


class FakeMemoryRepository:
    """Fake repository for testing read-only provider behavior."""

    def __init__(self, records: tuple[MemoryRecord, ...] = ()) -> None:
        self._records = list(records)
        self._calls: list[str] = []

    def add(self, record: MemoryRecord) -> MemoryRecord:
        self._calls.append("add")
        raise AssertionError("add should not be called on read-only provider")

    def get(self, memory_id: str) -> MemoryRecord | None:
        self._calls.append("get")
        raise AssertionError("get should not be called on read-only provider")

    def list_active(self) -> tuple[MemoryRecord, ...]:
        self._calls.append("list_active")
        return tuple(r for r in self._records if r.status == MemoryRecordStatus.ACTIVE)

    def list_all(self) -> tuple[MemoryRecord, ...]:
        self._calls.append("list_all")
        raise AssertionError("list_all should not be called on read-only provider")

    def delete(self, memory_id: str) -> MemoryRecord:
        self._calls.append("delete")
        raise AssertionError("delete should not be called on read-only provider")

    def clear(self) -> None:
        self._calls.append("clear")
        raise AssertionError("clear should not be called on read-only provider")


def _make_record(
    record_id: str = "test-id",
    kind: MemoryKind = MemoryKind.PREFERENCE,
    importance: MemoryImportance = MemoryImportance.MEDIUM,
    text: str = "用户喜欢短回复。",
    status: MemoryRecordStatus = MemoryRecordStatus.ACTIVE,
) -> MemoryRecord:
    """Create a test MemoryRecord."""
    return MemoryRecord(
        id=record_id,
        kind=kind,
        importance=importance,
        text=text,
        source="test",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        status=status,
    )


class TestCreateReadonlyMemoryContextProvider:
    """Tests for create_readonly_memory_context_provider."""

    def test_returns_callable(self) -> None:
        """Provider is a callable."""
        repo = FakeMemoryRepository()
        provider = create_readonly_memory_context_provider(repo)
        assert callable(provider)

    def test_provider_reads_active_records(self) -> None:
        """Provider calls repository.list_active()."""
        record = _make_record(record_id="active-001")
        repo = FakeMemoryRepository(records=(record,))
        provider = create_readonly_memory_context_provider(repo)

        result = provider()

        assert "list_active" in repo._calls
        assert "用户喜欢短回复" in result

    def test_provider_builds_context_from_active_records(self) -> None:
        """Provider builds context from active records."""
        record = _make_record(
            record_id="context-001",
            kind=MemoryKind.PREFERENCE,
            text="用户喜欢短回复。",
        )
        repo = FakeMemoryRepository(records=(record,))
        builder = SessionMemoryContextBuilder()
        provider = create_readonly_memory_context_provider(repo, context_builder=builder)

        result = provider()

        assert "用户喜欢短回复" in result

    def test_provider_excludes_deleted_records(self) -> None:
        """Provider only includes active records through list_active()."""
        active = _make_record(record_id="active-001", text="活跃记录。")
        deleted = _make_record(
            record_id="deleted-001", text="已删除记录。", status=MemoryRecordStatus.DELETED
        )
        repo = FakeMemoryRepository(records=(active, deleted))
        provider = create_readonly_memory_context_provider(repo)

        result = provider()

        assert "活跃记录" in result
        assert "已删除记录" not in result

    def test_provider_returns_empty_when_no_active_records(self) -> None:
        """Provider returns empty string when no active records."""
        repo = FakeMemoryRepository(records=())
        provider = create_readonly_memory_context_provider(repo)

        result = provider()

        assert result == ""

    def test_provider_does_not_call_add(self) -> None:
        """Provider never calls repository.add()."""
        repo = FakeMemoryRepository()
        provider = create_readonly_memory_context_provider(repo)

        provider()

        assert "add" not in repo._calls

    def test_provider_does_not_call_delete(self) -> None:
        """Provider never calls repository.delete()."""
        repo = FakeMemoryRepository()
        provider = create_readonly_memory_context_provider(repo)

        provider()

        assert "delete" not in repo._calls

    def test_provider_does_not_call_clear(self) -> None:
        """Provider never calls repository.clear()."""
        repo = FakeMemoryRepository()
        provider = create_readonly_memory_context_provider(repo)

        provider()

        assert "clear" not in repo._calls

    def test_provider_does_not_call_get(self) -> None:
        """Provider never calls repository.get()."""
        repo = FakeMemoryRepository()
        provider = create_readonly_memory_context_provider(repo)

        provider()

        assert "get" not in repo._calls

    def test_provider_does_not_call_list_all(self) -> None:
        """Provider never calls repository.list_all()."""
        repo = FakeMemoryRepository()
        provider = create_readonly_memory_context_provider(repo)

        provider()

        assert "list_all" not in repo._calls


class TestCreateMemoryContextProviderFromConfig:
    """Tests for create_memory_context_provider_from_config."""

    def test_disabled_config_returns_none(self) -> None:
        """When memory_context_enabled is False, returns None."""

        class DisabledConfig:
            memory_context_enabled = False
            memory_store_path = ".tmp/memory.json"

        result = create_memory_context_provider_from_config(DisabledConfig())
        assert result is None

    def test_enabled_config_returns_callable(self) -> None:
        """When memory_context_enabled is True, returns a callable."""

        class EnabledConfig:
            memory_context_enabled = True
            memory_store_path = ".tmp/nonexistent.json"

        result = create_memory_context_provider_from_config(EnabledConfig())
        assert result is not None
        assert callable(result)

    def test_enabled_provider_returns_empty_context_for_missing_file(
        self, tmp_path: Path
    ) -> None:
        """Provider returns empty context when memory file does not exist."""
        json_path = tmp_path / "nonexistent.json"

        class EnabledConfig:
            memory_context_enabled = True
            memory_store_path = str(json_path)

        provider = create_memory_context_provider_from_config(EnabledConfig())
        assert provider is not None
        result = provider()
        assert result == ""


class TestIntegrationWithLocalJsonRepository:
    """Integration tests with real LocalJsonMemoryRepository using tmp_path."""

    def test_add_and_read_active_record(self, tmp_path: Path) -> None:
        """Add a record via repository and read it via provider."""
        json_path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(json_path)
        record = _make_record(
            record_id="integration-001",
            kind=MemoryKind.PREFERENCE,
            text="用户喜欢短回复。",
        )
        repo.add(record)

        provider = create_readonly_memory_context_provider(repo)
        context = provider()

        assert "用户喜欢短回复" in context

    def test_delete_record_removes_from_context(self, tmp_path: Path) -> None:
        """After deleting a record, provider no longer includes it."""
        json_path = tmp_path / "memory.json"
        repo = LocalJsonMemoryRepository(json_path)
        record = _make_record(
            record_id="delete-test-001",
            kind=MemoryKind.PREFERENCE,
            text="这条记录将被删除。",
        )
        repo.add(record)

        # Verify it's in context
        provider = create_readonly_memory_context_provider(repo)
        assert "这条记录将被删除" in provider()

        # Delete it
        repo.delete("delete-test-001")

        # Verify it's no longer in context
        assert "这条记录将被删除" not in provider()
