"""Tests for V8-J Memory Management UI."""

import pytest

from app.contracts.events import (
    MEMORY_DELETED,
    MEMORY_LISTED,
    BaseEvent,
)
from app.ui.memory_record_view import MemoryRecordView, render_memory_record_text
from app.ui.view_model import DesktopViewModel


class TestMemoryRecordView:
    """Tests for MemoryRecordView dataclass."""

    def test_creation_with_required_fields(self) -> None:
        """Test MemoryRecordView can be created with required fields."""
        view = MemoryRecordView(
            record_id="record-123",
            kind="preference",
            importance="medium",
            text="用户喜欢简短回复",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        assert view.record_id == "record-123"
        assert view.kind == "preference"
        assert view.importance == "medium"
        assert view.text == "用户喜欢简短回复"
        assert view.created_at == "2024-01-01T00:00:00"
        assert view.updated_at == "2024-01-01T00:00:00"

    def test_is_frozen(self) -> None:
        """Test MemoryRecordView is a frozen dataclass."""
        view = MemoryRecordView(
            record_id="record-123",
            kind="preference",
            importance="medium",
            text="用户喜欢简短回复",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        with pytest.raises(AttributeError):
            view.record_id = "changed"  # type: ignore[misc]

    def test_excludes_evidence(self) -> None:
        """Test MemoryRecordView does not have evidence field."""
        assert not hasattr(MemoryRecordView, "evidence")

    def test_excludes_source(self) -> None:
        """Test MemoryRecordView does not have source field."""
        assert not hasattr(MemoryRecordView, "source")

    def test_excludes_status(self) -> None:
        """Test MemoryRecordView does not have status field."""
        assert not hasattr(MemoryRecordView, "status")


class TestRenderMemoryRecordText:
    """Tests for render_memory_record_text function."""

    def test_short_text_unchanged(self) -> None:
        """Test text shorter than max_chars is returned unchanged."""
        text = "用户喜欢你回复短一点。"
        result = render_memory_record_text(text, max_chars=80)
        assert result == text

    def test_exact_max_chars_unchanged(self) -> None:
        """Test text exactly at max_chars is returned unchanged."""
        text = "a" * 80
        result = render_memory_record_text(text, max_chars=80)
        assert result == text

    def test_truncated_with_ellipsis(self) -> None:
        """Test text longer than max_chars is truncated with ellipsis."""
        text = "a" * 100
        result = render_memory_record_text(text, max_chars=80)
        assert len(result) == 81  # 80 chars + ellipsis
        assert result.endswith("…")

    def test_default_max_chars_80(self) -> None:
        """Test default max_chars is 80."""
        text = "a" * 100
        result = render_memory_record_text(text)
        assert len(result) == 81


class TestDesktopViewModelMemoryManagement:
    """Tests for DesktopViewModel memory management handlers."""

    def test_initial_memory_records_empty(self) -> None:
        """Test initial memory_records is empty."""
        vm = DesktopViewModel()
        assert vm.memory_records == []

    def test_memory_panel_visible_default_false(self) -> None:
        """Test memory_panel_visible defaults to False."""
        vm = DesktopViewModel()
        assert vm.memory_panel_visible is False

    def test_toggle_memory_panel_toggles_state(self) -> None:
        """Test toggle_memory_panel toggles the panel visibility."""
        vm = DesktopViewModel()
        assert vm.memory_panel_visible is False
        vm.toggle_memory_panel()
        assert vm.memory_panel_visible is True
        vm.toggle_memory_panel()
        assert vm.memory_panel_visible is False

    def test_handle_memory_listed_parses_valid_records(self) -> None:
        """Test handle_memory_listed parses valid records."""
        vm = DesktopViewModel()

        event = BaseEvent(
            event_type=MEMORY_LISTED,
            request_id="req1",
            source="test",
            payload={
                "records": [
                    {
                        "record_id": "record-123",
                        "kind": "preference",
                        "importance": "medium",
                        "text": "用户喜欢简短回复",
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-01T00:00:00",
                    },
                    {
                        "record_id": "record-456",
                        "kind": "identity",
                        "importance": "high",
                        "text": "用户叫张三",
                        "created_at": "2024-01-02T00:00:00",
                        "updated_at": "2024-01-02T00:00:00",
                    },
                ]
            },
        )
        vm.handle_memory_listed(event)

        assert len(vm.memory_records) == 2
        assert vm.memory_records[0].record_id == "record-123"
        assert vm.memory_records[0].text == "用户喜欢简短回复"
        assert vm.memory_records[1].record_id == "record-456"
        assert vm.memory_panel_visible is True
        assert vm.memory_status_text == "已加载记忆"

    def test_handle_memory_listed_skips_invalid_records(self) -> None:
        """Test handle_memory_listed skips records with invalid fields."""
        vm = DesktopViewModel()

        event = BaseEvent(
            event_type=MEMORY_LISTED,
            request_id="req2",
            source="test",
            payload={
                "records": [
                    {
                        "record_id": "record-123",
                        "kind": "preference",
                        "importance": "medium",
                        "text": "用户喜欢简短回复",
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-01T00:00:00",
                    },
                    {
                        "record_id": 456,  # invalid: not string
                        "kind": "identity",
                        "importance": "high",
                        "text": "用户叫张三",
                        "created_at": "2024-01-02T00:00:00",
                        "updated_at": "2024-01-02T00:00:00",
                    },
                ]
            },
        )
        vm.handle_memory_listed(event)

        assert len(vm.memory_records) == 1
        assert vm.memory_records[0].record_id == "record-123"

    def test_handle_memory_listed_does_not_include_evidence_source(self) -> None:
        """Test handle_memory_listed result does not have evidence or source fields."""
        vm = DesktopViewModel()

        event = BaseEvent(
            event_type=MEMORY_LISTED,
            request_id="req3",
            source="test",
            payload={
                "records": [
                    {
                        "record_id": "record-123",
                        "kind": "preference",
                        "importance": "medium",
                        "text": "用户喜欢简短回复",
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-01T00:00:00",
                        "evidence": "原始对话内容很长...",
                        "source": "some_source",
                    }
                ]
            },
        )
        vm.handle_memory_listed(event)

        assert len(vm.memory_records) == 1
        assert not hasattr(vm.memory_records[0], "evidence")
        assert not hasattr(vm.memory_records[0], "source")

    def test_handle_memory_listed_ignores_non_memory_listed_event(self) -> None:
        """Test handle_memory_listed ignores non-memory.listed events."""
        vm = DesktopViewModel()
        vm.memory_records = [
            MemoryRecordView(
                record_id="existing",
                kind="preference",
                importance="medium",
                text="existing",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            )
        ]

        event = BaseEvent(
            event_type="other.event",
            request_id="req4",
            source="test",
            payload={
                "records": [
                    {
                        "record_id": "record-123",
                        "kind": "preference",
                        "importance": "medium",
                        "text": "new text",
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-01T00:00:00",
                    }
                ]
            },
        )
        vm.handle_memory_listed(event)

        assert len(vm.memory_records) == 1
        assert vm.memory_records[0].record_id == "existing"

    def test_handle_memory_deleted_removes_matching_record(self) -> None:
        """Test handle_memory_deleted removes the matching record."""
        vm = DesktopViewModel()
        vm.memory_records = [
            MemoryRecordView(
                record_id="record-123",
                kind="preference",
                importance="medium",
                text="用户喜欢简短回复",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            ),
            MemoryRecordView(
                record_id="record-456",
                kind="identity",
                importance="high",
                text="用户叫张三",
                created_at="2024-01-02T00:00:00",
                updated_at="2024-01-02T00:00:00",
            ),
        ]

        event = BaseEvent(
            event_type=MEMORY_DELETED,
            request_id="req5",
            source="test",
            payload={"record_id": "record-123"},
        )
        vm.handle_memory_deleted(event)

        assert len(vm.memory_records) == 1
        assert vm.memory_records[0].record_id == "record-456"
        assert vm.memory_status_text == "已删除记忆"

    def test_handle_memory_deleted_unknown_id_no_crash(self) -> None:
        """Test handle_memory_deleted with unknown id does not crash."""
        vm = DesktopViewModel()
        vm.memory_records = [
            MemoryRecordView(
                record_id="record-123",
                kind="preference",
                importance="medium",
                text="用户喜欢简短回复",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            )
        ]

        event = BaseEvent(
            event_type=MEMORY_DELETED,
            request_id="req6",
            source="test",
            payload={"record_id": "unknown-id"},
        )
        vm.handle_memory_deleted(event)  # should not raise

        assert len(vm.memory_records) == 1
        assert vm.memory_records[0].record_id == "record-123"

    def test_handle_memory_deleted_ignores_non_memory_deleted_event(self) -> None:
        """Test handle_memory_deleted ignores non-memory.deleted events."""
        vm = DesktopViewModel()
        vm.memory_records = [
            MemoryRecordView(
                record_id="record-123",
                kind="preference",
                importance="medium",
                text="用户喜欢简短回复",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            )
        ]

        event = BaseEvent(
            event_type="other.event",
            request_id="req7",
            source="test",
            payload={"record_id": "record-123"},
        )
        vm.handle_memory_deleted(event)

        assert len(vm.memory_records) == 1
        assert vm.memory_records[0].record_id == "record-123"

    def test_conversation_cleared_closes_panel_but_keeps_records(self) -> None:
        """Test handle_conversation_cleared closes panel but keeps records."""
        vm = DesktopViewModel()
        vm.memory_records = [
            MemoryRecordView(
                record_id="record-123",
                kind="preference",
                importance="medium",
                text="用户喜欢简短回复",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
            )
        ]
        vm.memory_panel_visible = True

        from app.contracts.events import CONVERSATION_CLEARED

        event = BaseEvent(
            event_type=CONVERSATION_CLEARED,
            request_id="req8",
            source="test",
            payload={},
        )
        vm.handle_conversation_cleared(event)

        assert vm.memory_panel_visible is False
        assert len(vm.memory_records) == 1  # records are kept
