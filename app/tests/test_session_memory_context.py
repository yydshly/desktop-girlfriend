"""Tests for session memory context builder."""

from app.brain.memory import ConfirmedMemory, MemoryImportance, MemoryKind
from app.brain.memory.session_context import (
    SessionMemoryContextBuilder,
    SessionMemoryContextConfig,
)


def _make_confirmed(text: str, kind: MemoryKind = MemoryKind.PREFERENCE) -> ConfirmedMemory:
    """Helper to create a ConfirmedMemory for testing."""
    from datetime import UTC, datetime

    from app.brain.memory.types import MemoryCandidate

    return ConfirmedMemory(
        id="test-id",
        candidate=MemoryCandidate(
            kind=kind,
            importance=MemoryImportance.MEDIUM,
            text=text,
            evidence="test evidence",
            confidence=0.8,
        ),
        created_at=datetime.now(UTC),
        confirmed_at=datetime.now(UTC),
    )


class TestSessionMemoryContextBuilder:
    """Tests for SessionMemoryContextBuilder."""

    def _make_builder(
        self, config: SessionMemoryContextConfig | None = None
    ) -> SessionMemoryContextBuilder:
        return SessionMemoryContextBuilder(config)

    def test_empty_confirmed_memories_returns_empty_string(self) -> None:
        builder = self._make_builder()
        result = builder.build(())
        assert result == ""

    def test_builder_includes_confirmed_candidate_text(self) -> None:
        builder = self._make_builder()
        memory = _make_confirmed("用户喜欢短回复。")
        result = builder.build((memory,))
        assert "用户喜欢短回复" in result

    def test_builder_does_not_include_candidate_evidence(self) -> None:
        builder = self._make_builder()
        memory = _make_confirmed("用户喜欢短回复。")
        result = builder.build((memory,))
        assert "test evidence" not in result

    def test_builder_excludes_boundary_by_default(self) -> None:
        builder = self._make_builder()
        boundary = _make_confirmed("不要记住某事。", MemoryKind.BOUNDARY)
        result = builder.build((boundary,))
        assert "不要记住" not in result
        assert result == ""

    def test_builder_can_include_boundary_when_enabled(self) -> None:
        config = SessionMemoryContextConfig(include_boundary=True)
        builder = self._make_builder(config)
        boundary = _make_confirmed("不要记住某事。", MemoryKind.BOUNDARY)
        result = builder.build((boundary,))
        assert "不要记住" in result

    def test_builder_respects_max_items(self) -> None:
        config = SessionMemoryContextConfig(max_items=2)
        builder = self._make_builder(config)
        memories = [
            _make_confirmed("记忆0。"),
            _make_confirmed("记忆1。"),
            _make_confirmed("记忆2。"),
        ]
        result = builder.build(tuple(memories))
        # Should contain at most 2 items
        assert result.count("- ") <= 2

    def test_builder_respects_max_item_chars(self) -> None:
        config = SessionMemoryContextConfig(max_item_chars=10)
        builder = self._make_builder(config)
        memory = _make_confirmed("这是一个非常非常长的记忆内容。")
        result = builder.build((memory,))
        # Should be truncated to 10 chars
        lines = result.strip().split("\n")
        for line in lines[1:]:  # Skip header
            content = line.lstrip("- ")
            assert len(content) <= 10 + 2  # +2 for "。"

    def test_builder_respects_max_total_chars(self) -> None:
        config = SessionMemoryContextConfig(max_total_chars=50)
        builder = self._make_builder(config)
        memories = [
            _make_confirmed("这是一个很长的记忆。"),
            _make_confirmed("这也是一个很长的记忆。"),
            _make_confirmed("这又是一个很长的记忆。"),
        ]
        result = builder.build(tuple(memories))
        assert len(result) <= 50

    def test_output_contains_safety_instruction(self) -> None:
        builder = self._make_builder()
        memory = _make_confirmed("用户喜欢短回复。")
        result = builder.build((memory,))
        assert "不要主动逐条复述" in result

    def test_output_does_not_use_wǒ_jì_de(self) -> None:
        """Test output does not use '我记得' phrase."""
        builder = self._make_builder()
        memory = _make_confirmed("用户喜欢短回复。")
        result = builder.build((memory,))
        assert "我记得" not in result

    def test_multiple_memories_formatted_correctly(self) -> None:
        builder = self._make_builder()
        memories = [
            _make_confirmed("用户喜欢短回复。"),
            _make_confirmed("用户正在做一个项目。"),
        ]
        result = builder.build(tuple(memories))
        lines = result.strip().split("\n")
        # Header line
        assert "已确认的用户会话记忆" in lines[0]
        # Memory lines should start with "- "
        memory_lines = [ln for ln in lines if ln.startswith("- ")]
        assert len(memory_lines) == 2

    def test_boundary_filtered_when_not_enabled(self) -> None:
        config = SessionMemoryContextConfig(include_boundary=False)
        builder = self._make_builder(config)
        memories = [
            _make_confirmed("用户喜欢短回复。"),
            _make_confirmed("不要记住。", MemoryKind.BOUNDARY),
            _make_confirmed("用户正在做一个项目。"),
        ]
        result = builder.build(tuple(memories))
        assert "不要记住" not in result
        assert "短回复" in result
        assert "项目" in result
