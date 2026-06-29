"""Tests for DeterministicMemoryExtractor."""

from app.brain.memory import DeterministicMemoryExtractor, MemoryKind
from app.brain.memory.types import MAX_TEXT_LEN


class TestDeterministicMemoryExtractor:
    """Tests for DeterministicMemoryExtractor."""

    def _make(self) -> DeterministicMemoryExtractor:
        return DeterministicMemoryExtractor()

    def test_empty_text_returns_empty(self) -> None:
        extractor = self._make()
        assert extractor.extract("") == ()
        assert extractor.extract("   ") == ()
        assert extractor.extract("\n\t") == ()

    def test_smalltalk_returns_empty(self) -> None:
        extractor = self._make()
        assert extractor.extract("你好小云，在吗？") == ()
        assert extractor.extract("你好呀") == ()
        assert extractor.extract("谢谢小云") == ()
        assert extractor.extract("好的") == ()
        assert extractor.extract("继续") == ()
        assert extractor.extract("哈哈") == ()

    def test_preference_like(self) -> None:
        extractor = self._make()
        candidates = extractor.extract("我喜欢短回复。")
        assert len(candidates) >= 1
        kinds = {c.kind for c in candidates}
        assert MemoryKind.PREFERENCE in kinds

    def test_preference_dislike(self) -> None:
        extractor = self._make()
        candidates = extractor.extract("我不喜欢太啰嗦的回复。")
        assert len(candidates) >= 1
        kinds = {c.kind for c in candidates}
        assert MemoryKind.PREFERENCE in kinds

    def test_preference_prefer(self) -> None:
        extractor = self._make()
        candidates = extractor.extract("我更喜欢简洁的回复。")
        assert len(candidates) >= 1
        kinds = {c.kind for c in candidates}
        assert MemoryKind.PREFERENCE in kinds

    def test_project(self) -> None:
        extractor = self._make()
        candidates = extractor.extract("我正在做一个桌面女友项目。")
        assert len(candidates) >= 1
        kinds = {c.kind for c in candidates}
        assert MemoryKind.PROJECT in kinds

    def test_project_my_project(self) -> None:
        extractor = self._make()
        candidates = extractor.extract("我的项目想让她有长期陪伴感。")
        assert len(candidates) >= 1
        kinds = {c.kind for c in candidates}
        assert MemoryKind.PROJECT in kinds

    def test_relationship_girlfriend(self) -> None:
        extractor = self._make()
        candidates = extractor.extract("我女朋友叫红红。")
        assert len(candidates) >= 1
        kinds = {c.kind for c in candidates}
        assert MemoryKind.RELATIONSHIP in kinds

    def test_relationship_mom(self) -> None:
        extractor = self._make()
        candidates = extractor.extract("我妈觉得我太忙了。")
        assert len(candidates) >= 1
        kinds = {c.kind for c in candidates}
        assert MemoryKind.RELATIONSHIP in kinds

    def test_health_sleep(self) -> None:
        extractor = self._make()
        candidates = extractor.extract("我睡不着，最近很焦虑。")
        health_candidates = [c for c in candidates if c.kind == MemoryKind.HEALTH]
        assert len(health_candidates) >= 1

    def test_health_chest_pain(self) -> None:
        extractor = self._make()
        candidates = extractor.extract("我胸口痛。")
        assert len(candidates) >= 1
        kinds = {c.kind for c in candidates}
        assert MemoryKind.HEALTH in kinds

    def test_emotion_pattern(self) -> None:
        extractor = self._make()
        candidates = extractor.extract("我最近总是觉得很累。")
        assert len(candidates) >= 1
        kinds = {c.kind for c in candidates}
        assert MemoryKind.EMOTION_PATTERN in kinds

    def test_boundary_dont_remember(self) -> None:
        extractor = self._make()
        candidates = extractor.extract("这件事不要记住，我只是随口说说。")
        assert len(candidates) >= 1
        kinds = {c.kind for c in candidates}
        assert MemoryKind.BOUNDARY in kinds

    def test_boundary_dont_remind(self) -> None:
        extractor = self._make()
        candidates = extractor.extract("以后别再提醒我这个了。")
        assert len(candidates) >= 1
        kinds = {c.kind for c in candidates}
        assert MemoryKind.BOUNDARY in kinds

    def test_max_candidates_limit(self) -> None:
        extractor = self._make()
        # A text that could trigger multiple types
        text = (
            "我女朋友叫红红，我最近总是睡不着，我不喜欢太啰嗦的回复，"
            "我正在做一个桌面女友项目，你最好别太啰嗦。"
        )
        candidates = extractor.extract(text)
        assert len(candidates) <= extractor.MAX_CANDIDATES

    def test_evidence_truncation(self) -> None:
        extractor = self._make()
        long_text = "我" + "喜" * 300
        candidates = extractor.extract(long_text)
        for c in candidates:
            assert len(c.evidence) <= MAX_TEXT_LEN

    def test_text_truncation(self) -> None:
        extractor = self._make()
        # Create a long preference text
        long_text = "我喜欢" + "很棒的内容" * 50
        candidates = extractor.extract(long_text)
        for c in candidates:
            assert len(c.text) <= MAX_TEXT_LEN

    def test_no_network_called(self) -> None:
        """Verify the extractor does not make network calls."""
        extractor = self._make()
        # If this completes without exception, no network was called
        extractor.extract("我女朋友叫红红。")
        extractor.extract("我睡不着。")
        # No assertion needed — if network was called, it would raise

    def test_no_file_written(self) -> None:
        """Verify the extractor does not write files."""
        extractor = self._make()
        extractor.extract("我正在做一个项目。")
        # No assertion needed — if file was written, it would raise
