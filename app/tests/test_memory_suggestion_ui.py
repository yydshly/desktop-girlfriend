"""Tests for V8-I Memory Suggestion UI."""

import pytest

from app.contracts.events import (
    MEMORY_CONFIRMED,
    MEMORY_ERROR,
    MEMORY_REJECTED,
    MEMORY_SUGGESTIONS_DETECTED,
    BaseEvent,
)
from app.ui.memory_suggestion import MemorySuggestionView, render_memory_suggestion_text
from app.ui.view_model import DesktopViewModel

# =============================================================================
# ViewModel tests
# =============================================================================


class TestMemorySuggestionView:
    """Tests for MemorySuggestionView dataclass."""

    def test_creation_with_required_fields(self) -> None:
        """Test MemorySuggestionView can be created with required fields."""
        view = MemorySuggestionView(
            pending_id="pending-123",
            kind="preference",
            importance="medium",
            text="用户喜欢简短回复",
        )
        assert view.pending_id == "pending-123"
        assert view.kind == "preference"
        assert view.importance == "medium"
        assert view.text == "用户喜欢简短回复"

    def test_is_frozen(self) -> None:
        """Test MemorySuggestionView is a frozen dataclass."""
        view = MemorySuggestionView(
            pending_id="pending-123",
            kind="preference",
            importance="medium",
            text="用户喜欢简短回复",
        )
        with pytest.raises(AttributeError):
            view.pending_id = "changed"  # type: ignore[assignment]

    def test_excludes_evidence(self) -> None:
        """Test MemorySuggestionView does not have evidence field."""
        assert not hasattr(MemorySuggestionView, "evidence")

    def test_excludes_source(self) -> None:
        """Test MemorySuggestionView does not have source field."""
        assert not hasattr(MemorySuggestionView, "source")


class TestRenderMemorySuggestionText:
    """Tests for render_memory_suggestion_text function."""

    def test_short_text_unchanged(self) -> None:
        """Test text shorter than max_chars is returned unchanged."""
        text = "用户喜欢你回复短一点。"
        result = render_memory_suggestion_text(text, max_chars=80)
        assert result == text

    def test_exact_max_chars_unchanged(self) -> None:
        """Test text exactly at max_chars is returned unchanged."""
        text = "a" * 80
        result = render_memory_suggestion_text(text, max_chars=80)
        assert result == text

    def test_truncated_with_ellipsis(self) -> None:
        """Test text longer than max_chars is truncated with ellipsis."""
        text = "a" * 100
        result = render_memory_suggestion_text(text, max_chars=80)
        assert len(result) == 81  # 80 chars + ellipsis
        assert result.endswith("…")

    def test_default_max_chars_80(self) -> None:
        """Test default max_chars is 80."""
        text = "a" * 100
        result = render_memory_suggestion_text(text)
        assert len(result) == 81


class TestDesktopViewModelMemorySuggestion:
    """Tests for DesktopViewModel memory suggestion handlers."""

    def test_initial_memory_suggestion_is_none(self) -> None:
        """Test initial memory_suggestion is None."""
        vm = DesktopViewModel()
        assert vm.memory_suggestion is None

    def test_initial_memory_status_text_is_empty(self) -> None:
        """Test initial memory_status_text is empty."""
        vm = DesktopViewModel()
        assert vm.memory_status_text == ""

    def test_handle_memory_suggestions_detected_stores_first_suggestion(self) -> None:
        """Test handle_memory_suggestions_detected stores the first suggestion."""
        vm = DesktopViewModel()

        event = BaseEvent(
            event_type=MEMORY_SUGGESTIONS_DETECTED,
            request_id="req1",
            source="test",
            payload={
                "suggestions": [
                    {
                        "pending_id": "pending-123",
                        "kind": "preference",
                        "importance": "medium",
                        "text": "用户喜欢简短回复",
                    },
                    {
                        "pending_id": "pending-456",
                        "kind": "identity",
                        "importance": "high",
                        "text": "用户叫张三",
                    },
                ]
            },
        )
        vm.handle_memory_suggestions_detected(event)

        assert vm.memory_suggestion is not None
        assert vm.memory_suggestion.pending_id == "pending-123"
        assert vm.memory_suggestion.kind == "preference"
        assert vm.memory_suggestion.importance == "medium"
        assert vm.memory_suggestion.text == "用户喜欢简短回复"
        assert vm.memory_status_text == "小云发现一条可能值得记住的信息"

    def test_handle_memory_suggestions_detected_ignores_invalid_payload_missing_suggestions(
        self,
    ) -> None:
        """Test handle_memory_suggestions_detected ignores payload without suggestions list."""
        vm = DesktopViewModel()
        vm.memory_suggestion = "existing"  # type: ignore[assignment]

        event = BaseEvent(
            event_type=MEMORY_SUGGESTIONS_DETECTED,
            request_id="req2",
            source="test",
            payload={},
        )
        vm.handle_memory_suggestions_detected(event)

        assert vm.memory_suggestion is None
        assert vm.memory_status_text == ""

    def test_handle_memory_suggestions_detected_ignores_empty_suggestions_list(self) -> None:
        """Test handle_memory_suggestions_detected clears suggestion when list is empty."""
        vm = DesktopViewModel()

        event = BaseEvent(
            event_type=MEMORY_SUGGESTIONS_DETECTED,
            request_id="req3",
            source="test",
            payload={"suggestions": []},
        )
        vm.handle_memory_suggestions_detected(event)

        assert vm.memory_suggestion is None
        assert vm.memory_status_text == ""

    def test_handle_memory_suggestions_detected_ignores_non_list_suggestions(self) -> None:
        """Test handle_memory_suggestions_detected ignores non-list suggestions."""
        vm = DesktopViewModel()

        event = BaseEvent(
            event_type=MEMORY_SUGGESTIONS_DETECTED,
            request_id="req4",
            source="test",
            payload={"suggestions": "not-a-list"},
        )
        vm.handle_memory_suggestions_detected(event)

        assert vm.memory_suggestion is None

    def test_handle_memory_suggestions_detected_ignores_non_memory_event(self) -> None:
        """Test handle_memory_suggestions_detected ignores non-memory event."""
        vm = DesktopViewModel()
        existing = MemorySuggestionView(
            pending_id="existing",
            kind="preference",
            importance="medium",
            text="existing",
        )
        vm.memory_suggestion = existing

        event = BaseEvent(
            event_type="other.event",
            request_id="req5",
            source="test",
            payload={"suggestions": []},
        )
        vm.handle_memory_suggestions_detected(event)

        assert vm.memory_suggestion == existing

    def test_handle_memory_suggestions_detected_ignores_invalid_suggestion_not_dict(
        self,
    ) -> None:
        """Test handle_memory_suggestions_detected ignores non-dict suggestion."""
        vm = DesktopViewModel()

        event = BaseEvent(
            event_type=MEMORY_SUGGESTIONS_DETECTED,
            request_id="req6",
            source="test",
            payload={"suggestions": ["not-a-dict"]},
        )
        vm.handle_memory_suggestions_detected(event)

        assert vm.memory_suggestion is None

    def test_handle_memory_suggestions_detected_ignores_missing_fields(self) -> None:
        """Test handle_memory_suggestions_detected ignores suggestion with missing fields."""
        vm = DesktopViewModel()

        event = BaseEvent(
            event_type=MEMORY_SUGGESTIONS_DETECTED,
            request_id="req7",
            source="test",
            payload={
                "suggestions": [
                    {
                        "pending_id": "pending-123",
                        # missing kind, importance, text
                    }
                ]
            },
        )
        vm.handle_memory_suggestions_detected(event)

        assert vm.memory_suggestion is None

    def test_handle_memory_suggestions_detected_ignores_non_string_fields(self) -> None:
        """Test handle_memory_suggestions_detected ignores suggestion with non-string fields."""
        vm = DesktopViewModel()

        event = BaseEvent(
            event_type=MEMORY_SUGGESTIONS_DETECTED,
            request_id="req8",
            source="test",
            payload={
                "suggestions": [
                    {
                        "pending_id": 123,  # not string
                        "kind": "preference",
                        "importance": "medium",
                        "text": "用户喜欢简短回复",
                    }
                ]
            },
        )
        vm.handle_memory_suggestions_detected(event)

        assert vm.memory_suggestion is None

    def test_suggestion_view_excludes_evidence(self) -> None:
        """Test suggestion stored in view model does not include evidence."""
        vm = DesktopViewModel()

        event = BaseEvent(
            event_type=MEMORY_SUGGESTIONS_DETECTED,
            request_id="req9",
            source="test",
            payload={
                "suggestions": [
                    {
                        "pending_id": "pending-123",
                        "kind": "preference",
                        "importance": "medium",
                        "text": "用户喜欢简短回复",
                        "evidence": "原始对话内容很长很长...",
                    }
                ]
            },
        )
        vm.handle_memory_suggestions_detected(event)

        assert vm.memory_suggestion is not None
        assert not hasattr(vm.memory_suggestion, "evidence")

    def test_handle_memory_confirmed_clears_suggestion(self) -> None:
        """Test handle_memory_confirmed clears memory_suggestion."""
        vm = DesktopViewModel()
        vm.memory_suggestion = MemorySuggestionView(
            pending_id="pending-123",
            kind="preference",
            importance="medium",
            text="用户喜欢简短回复",
        )
        vm.memory_status_text = "小云发现一条可能值得记住的信息"

        event = BaseEvent(
            event_type=MEMORY_CONFIRMED,
            request_id="req10",
            source="test",
            payload={},
        )
        vm.handle_memory_confirmed(event)

        assert vm.memory_suggestion is None
        assert vm.memory_status_text == "已记住"

    def test_handle_memory_confirmed_ignores_non_memory_confirmed_event(self) -> None:
        """Test handle_memory_confirmed ignores non-memory.confirmed event."""
        vm = DesktopViewModel()
        existing = MemorySuggestionView(
            pending_id="pending-123",
            kind="preference",
            importance="medium",
            text="用户喜欢简短回复",
        )
        vm.memory_suggestion = existing

        event = BaseEvent(
            event_type="other.event",
            request_id="req11",
            source="test",
            payload={},
        )
        vm.handle_memory_confirmed(event)

        assert vm.memory_suggestion == existing

    def test_handle_memory_rejected_clears_suggestion(self) -> None:
        """Test handle_memory_rejected clears memory_suggestion."""
        vm = DesktopViewModel()
        vm.memory_suggestion = MemorySuggestionView(
            pending_id="pending-123",
            kind="preference",
            importance="medium",
            text="用户喜欢简短回复",
        )
        vm.memory_status_text = "小云发现一条可能值得记住的信息"

        event = BaseEvent(
            event_type=MEMORY_REJECTED,
            request_id="req12",
            source="test",
            payload={},
        )
        vm.handle_memory_rejected(event)

        assert vm.memory_suggestion is None
        assert vm.memory_status_text == "已忽略"

    def test_handle_memory_rejected_ignores_non_memory_rejected_event(self) -> None:
        """Test handle_memory_rejected ignores non-memory.rejected event."""
        vm = DesktopViewModel()
        existing = MemorySuggestionView(
            pending_id="pending-123",
            kind="preference",
            importance="medium",
            text="用户喜欢简短回复",
        )
        vm.memory_suggestion = existing

        event = BaseEvent(
            event_type="other.event",
            request_id="req13",
            source="test",
            payload={},
        )
        vm.handle_memory_rejected(event)

        assert vm.memory_suggestion == existing

    def test_handle_memory_error_sets_status_text(self) -> None:
        """Test handle_memory_error sets memory_status_text without clearing suggestion."""
        vm = DesktopViewModel()
        vm.memory_suggestion = MemorySuggestionView(
            pending_id="pending-123",
            kind="preference",
            importance="medium",
            text="用户喜欢简短回复",
        )

        event = BaseEvent(
            event_type=MEMORY_ERROR,
            request_id="req14",
            source="test",
            payload={"message": "保存失败"},
        )
        vm.handle_memory_error(event)

        assert vm.memory_suggestion is not None  # not cleared
        assert vm.memory_status_text == "保存失败"

    def test_handle_memory_error_fallback_message(self) -> None:
        """Test handle_memory_error uses fallback when message is not valid."""
        vm = DesktopViewModel()

        event = BaseEvent(
            event_type=MEMORY_ERROR,
            request_id="req15",
            source="test",
            payload={},
        )
        vm.handle_memory_error(event)

        assert vm.memory_status_text == "记忆处理失败"

    def test_handle_memory_error_ignores_non_memory_error_event(self) -> None:
        """Test handle_memory_error ignores non-memory.error event."""
        vm = DesktopViewModel()
        vm.memory_status_text = "existing"

        event = BaseEvent(
            event_type="other.event",
            request_id="req16",
            source="test",
            payload={"message": "保存失败"},
        )
        vm.handle_memory_error(event)

        assert vm.memory_status_text == "existing"

    def test_handle_conversation_cleared_clears_memory_suggestion(self) -> None:
        """Test handle_conversation_cleared clears memory_suggestion."""
        vm = DesktopViewModel()
        vm.memory_suggestion = MemorySuggestionView(
            pending_id="pending-123",
            kind="preference",
            importance="medium",
            text="用户喜欢简短回复",
        )
        vm.memory_status_text = "小云发现一条可能值得记住的信息"

        from app.contracts.events import CONVERSATION_CLEARED

        event = BaseEvent(
            event_type=CONVERSATION_CLEARED,
            request_id="req17",
            source="test",
            payload={},
        )
        vm.handle_conversation_cleared(event)

        assert vm.memory_suggestion is None
        assert vm.memory_status_text == ""

    def test_view_model_does_not_publish_events(self) -> None:
        """Test that ViewModel handlers do not publish any events (pure state management)."""
        vm = DesktopViewModel()
        # ViewModel has no event_bus reference - handlers only update internal state
        assert not hasattr(vm, "event_bus")
        assert not hasattr(vm, "publish")

        # Verify handlers can be called without side effects
        event = BaseEvent(
            event_type=MEMORY_SUGGESTIONS_DETECTED,
            request_id="req18",
            source="test",
            payload={
                "suggestions": [
                    {
                        "pending_id": "pending-123",
                        "kind": "preference",
                        "importance": "medium",
                        "text": "用户喜欢简短回复",
                    }
                ]
            },
        )
        vm.handle_memory_suggestions_detected(event)
        assert vm.memory_suggestion is not None
