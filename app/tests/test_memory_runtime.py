"""Tests for MemoryRuntimeService."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.brain.memory import (
    DeterministicMemoryExtractor,
    InMemoryMemoryConfirmationStore,
    MemoryConfirmationService,
    MemoryImportance,
    MemoryKind,
)
from app.brain.memory.repository import (
    LocalJsonMemoryRepository,
    MemoryRecord,
    MemoryRecordStatus,
)
from app.brain.memory.runtime import (
    MemoryRuntimeService,
    create_local_memory_runtime,
)


def _make_record(
    id: str = "test-id",
    text: str = "测试记忆。",
    kind: MemoryKind = MemoryKind.PREFERENCE,
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
        status=MemoryRecordStatus.ACTIVE,
    )


class TestMemoryRuntimeService:
    """Tests for MemoryRuntimeService."""

    def _make_runtime(self, tmp_path: Path) -> MemoryRuntimeService:
        """Create a runtime with LocalJsonMemoryRepository."""
        repo = LocalJsonMemoryRepository(tmp_path / "memory.json")
        store = InMemoryMemoryConfirmationStore()
        confirmation_service = MemoryConfirmationService(store)
        extractor = DeterministicMemoryExtractor()
        from app.brain.memory.session_context import SessionMemoryContextBuilder
        return MemoryRuntimeService(
            extractor=extractor,
            confirmation_service=confirmation_service,
            repository=repo,
            context_builder=SessionMemoryContextBuilder(),
        )

    def test_extract_candidates_returns_candidates_but_does_not_create_pending(
        self, tmp_path: Path
    ) -> None:
        runtime = self._make_runtime(tmp_path)
        candidates = runtime.extract_candidates("我女朋友叫红红。")
        assert len(candidates) >= 1
        assert runtime.list_pending() == ()

    def test_submit_user_text_creates_pending(self, tmp_path: Path) -> None:
        runtime = self._make_runtime(tmp_path)
        pending = runtime.submit_user_text("我女朋友叫红红。")
        assert len(pending) >= 1
        assert len(runtime.list_pending()) >= 1

    def test_submit_user_text_with_smalltalk_returns_empty(self, tmp_path: Path) -> None:
        runtime = self._make_runtime(tmp_path)
        pending = runtime.submit_user_text("你好小云！")
        assert pending == ()

    def test_submit_user_text_does_not_persist(self, tmp_path: Path) -> None:
        runtime = self._make_runtime(tmp_path)
        runtime.submit_user_text("我女朋友叫红红。")
        assert runtime.list_active_records() == ()

    def test_confirm_pending_moves_pending_to_repository_active_record(
        self, tmp_path: Path
    ) -> None:
        runtime = self._make_runtime(tmp_path)
        pending = runtime.submit_user_text("我喜欢你回复短一点。")
        assert len(pending) >= 1
        record = runtime.confirm_pending(pending[0].id)
        # Record text comes from extractor output
        assert "回复" in record.text
        active = runtime.list_active_records()
        assert len(active) == 1
        assert active[0].id == record.id

    def test_confirm_pending_returns_memory_record(self, tmp_path: Path) -> None:
        runtime = self._make_runtime(tmp_path)
        pending = runtime.submit_user_text("我喜欢你回复短一点。")
        record = runtime.confirm_pending(pending[0].id)
        assert isinstance(record, MemoryRecord)

    def test_confirm_pending_unknown_id_raises_key_error(self, tmp_path: Path) -> None:
        runtime = self._make_runtime(tmp_path)
        with pytest.raises(KeyError):
            runtime.confirm_pending("unknown-id")

    def test_reject_pending_returns_rejected_memory(self, tmp_path: Path) -> None:
        runtime = self._make_runtime(tmp_path)
        pending = runtime.submit_user_text("我女朋友叫红红。")
        rejected = runtime.reject_pending(pending[0].id, reason="user_declined")
        assert rejected.reason == "user_declined"

    def test_reject_pending_does_not_persist(self, tmp_path: Path) -> None:
        runtime = self._make_runtime(tmp_path)
        pending = runtime.submit_user_text("我女朋友叫红红。")
        runtime.reject_pending(pending[0].id)
        assert runtime.list_active_records() == ()

    def test_rejected_pending_does_not_appear_in_active_records(self, tmp_path: Path) -> None:
        runtime = self._make_runtime(tmp_path)
        pending = runtime.submit_user_text("我女朋友叫红红。")
        runtime.reject_pending(pending[0].id)
        assert len(runtime.list_active_records()) == 0

    def test_list_active_records_returns_repository_active(self, tmp_path: Path) -> None:
        runtime = self._make_runtime(tmp_path)
        pending = runtime.submit_user_text("我喜欢你回复短一点。")
        runtime.confirm_pending(pending[0].id)
        active = runtime.list_active_records()
        assert len(active) == 1

    def test_delete_record_soft_deletes_repository_record(self, tmp_path: Path) -> None:
        runtime = self._make_runtime(tmp_path)
        pending = runtime.submit_user_text("我喜欢你回复短一点。")
        record = runtime.confirm_pending(pending[0].id)
        deleted = runtime.delete_record(record.id)
        assert deleted.status == MemoryRecordStatus.DELETED
        assert runtime.list_active_records() == ()

    def test_build_session_context_includes_active_record_text(self, tmp_path: Path) -> None:
        runtime = self._make_runtime(tmp_path)
        pending = runtime.submit_user_text("我喜欢你回复短一点。")
        runtime.confirm_pending(pending[0].id)
        context = runtime.build_session_context()
        # Context includes the preference text from the record
        assert "回复" in context

    def test_build_session_context_excludes_deleted_record(self, tmp_path: Path) -> None:
        runtime = self._make_runtime(tmp_path)
        pending = runtime.submit_user_text("我喜欢你回复短一点。")
        record = runtime.confirm_pending(pending[0].id)
        runtime.delete_record(record.id)
        context = runtime.build_session_context()
        assert context == ""

    def test_build_session_context_excludes_boundary_by_default(self, tmp_path: Path) -> None:
        runtime = self._make_runtime(tmp_path)
        pending = runtime.submit_user_text("这件事不要记住。")
        runtime.confirm_pending(pending[0].id)
        context = runtime.build_session_context()
        assert context == ""

    def test_snapshot_includes_pending_active_rejected(self, tmp_path: Path) -> None:
        runtime = self._make_runtime(tmp_path)
        p1 = runtime.submit_user_text("我喜欢你回复短一点。")
        p2 = runtime.submit_user_text("我女朋友叫红红。")
        runtime.confirm_pending(p1[0].id)
        runtime.reject_pending(p2[0].id)
        snapshot = runtime.snapshot()
        assert len(snapshot.pending) == 0
        assert len(snapshot.active) == 1
        assert len(snapshot.rejected) == 1

    def test_runtime_does_not_write_repository_until_confirm_pending(
        self, tmp_path: Path
    ) -> None:
        runtime = self._make_runtime(tmp_path)
        runtime.submit_user_text("我女朋友叫红红。")
        assert runtime.list_active_records() == ()
        assert runtime.list_all_records() == ()

    def test_create_local_memory_runtime_wires_default_components(
        self, tmp_path: Path
    ) -> None:
        repo = LocalJsonMemoryRepository(tmp_path / "memory.json")
        runtime = create_local_memory_runtime(repo)
        pending = runtime.submit_user_text("我喜欢你回复短一点。")
        record = runtime.confirm_pending(pending[0].id)
        # Record text comes from extractor output
        assert "回复" in record.text


class TestBuildFromRecords:
    """Tests for SessionMemoryContextBuilder.build_from_records."""

    def test_build_from_records_includes_record_text(self, tmp_path: Path) -> None:
        from app.brain.memory.session_context import SessionMemoryContextBuilder

        builder = SessionMemoryContextBuilder()
        records = (_make_record(text="用户喜欢短回复。"),)
        context = builder.build_from_records(records)
        assert "用户喜欢短回复" in context

    def test_build_from_records_excludes_boundary_by_default(self, tmp_path: Path) -> None:
        from app.brain.memory.session_context import SessionMemoryContextBuilder

        builder = SessionMemoryContextBuilder()
        records = (_make_record(kind=MemoryKind.BOUNDARY, text="不要记住某事。"),)
        context = builder.build_from_records(records)
        assert context == ""

    def test_build_from_records_respects_limits(self, tmp_path: Path) -> None:
        from app.brain.memory.session_context import SessionMemoryContextBuilder

        builder = SessionMemoryContextBuilder()
        records = tuple(_make_record(text=f"记忆{i}。") for i in range(10))
        context = builder.build_from_records(records)
        # Should be limited to max_items=5
        assert context.count("- ") <= 5

    def test_build_from_records_does_not_require_evidence(self, tmp_path: Path) -> None:
        from app.brain.memory.session_context import SessionMemoryContextBuilder

        builder = SessionMemoryContextBuilder()
        records = (_make_record(text="用户喜欢短回复。"),)
        # MemoryRecord has no evidence field
        context = builder.build_from_records(records)
        assert "用户喜欢短回复" in context
