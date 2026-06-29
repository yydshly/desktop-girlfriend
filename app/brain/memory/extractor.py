"""Deterministic memory candidate extractor for V8-A."""

from __future__ import annotations

import re

from app.brain.memory.types import MAX_TEXT_LEN, MemoryCandidate, MemoryImportance, MemoryKind


class DeterministicMemoryExtractor:
    """Rule-based memory candidate extractor for V8-A.

    This extractor is intentionally conservative.
    It never persists memory and never calls a model.
    """

    MAX_CANDIDATES = 3

    def extract(self, user_text: str) -> tuple[MemoryCandidate, ...]:
        """Extract memory candidates from user text.

        Args:
            user_text: The raw user input text.

        Returns:
            A tuple of MemoryCandidate objects (up to MAX_CANDIDATES).
        """
        if not user_text or not user_text.strip():
            return ()

        # Truncate input early to avoid producing oversized candidates
        raw = user_text.strip()
        if len(raw) > MAX_TEXT_LEN:
            raw = raw[:MAX_TEXT_LEN]

        candidates: list[MemoryCandidate] = []

        # Boundary (highest priority — user explicitly says don't remember)
        candidates.extend(self._extract_boundary(raw))

        # Collect from all sentences, allowing multiple kinds per sentence
        sentences = self._split_sentences(raw)
        for sent in sentences:
            candidates.extend(self._extract_from_sentence(sent))

        # Limit to MAX_CANDIDATES, preferring earlier (higher-priority) candidates
        return tuple(candidates[: self.MAX_CANDIDATES])

    def _extract_from_sentence(self, sentence: str) -> list[MemoryCandidate]:
        """Extract all applicable memory kinds from a single sentence."""
        results: list[MemoryCandidate] = []

        # Relationship
        results.extend(self._extract_relationship_from_sentence(sentence))

        # Health (may be multiple: sleep + anxiety)
        results.extend(self._extract_health_from_sentence(sentence))

        # Emotion pattern
        results.extend(self._extract_emotion_pattern_from_sentence(sentence))

        # Preference
        results.extend(self._extract_preference_from_sentence(sentence))

        # Project
        results.extend(self._extract_project_from_sentence(sentence))

        return results

    def _extract_boundary(self, text: str) -> list[MemoryCandidate]:
        triggers = [
            "不要记住",
            "别记住",
            "不要提醒我",
            "别再提",
            "不要这样说",
            "我不想让你",
        ]
        for trigger in triggers:
            if trigger in text:
                return [
                    MemoryCandidate(
                        kind=MemoryKind.BOUNDARY,
                        importance=MemoryImportance.HIGH,
                        text="用户请求不要记住特定内容",
                        evidence=self._truncate(text),
                        confidence=0.85,
                    )
                ]
        return []

    def _extract_relationship_from_sentence(self, sentence: str) -> list[MemoryCandidate]:
        triggers = [
            "我女朋友",
            "我的女朋友",
            "我女朋友叫",
            "我老婆",
            "我妈",
            "我妈妈",
            "我爸",
            "我爸爸",
            "我奶奶",
            "我爷爷",
            "我朋友",
            "我哥们",
            "我同事",
            "我老板",
            "我老师",
        ]
        for trigger in triggers:
            if trigger in sentence:
                return [
                    MemoryCandidate(
                        kind=MemoryKind.RELATIONSHIP,
                        importance=MemoryImportance.HIGH,
                        text=self._normalize(sentence),
                        evidence=self._truncate(sentence),
                        confidence=0.80,
                    )
                ]
        return []

    def _extract_health_from_sentence(self, sentence: str) -> list[MemoryCandidate]:
        triggers = [
            ("我头疼", "头痛"),
            ("我头痛", "头痛"),
            ("我胸口痛", "胸痛"),
            ("我胃疼", "胃痛"),
            ("我睡不着", "失眠"),
            ("我失眠", "失眠"),
            ("焦虑", "焦虑"),
            ("我焦虑", "焦虑"),
            ("抑郁", "抑郁"),
            ("我抑郁", "抑郁"),
            ("我身体不舒服", "身体不适"),
            ("我不舒服", "身体不适"),
            ("我累", "疲劳"),
            ("我很累", "疲劳"),
            ("累", "疲劳"),
            ("困", "困倦"),
            ("难受", "不适"),
            ("疼", "疼痛"),
        ]
        results: list[MemoryCandidate] = []
        found: set[str] = set()
        # Strip leading subject/particle to improve trigger matching
        stripped = _strip_subject(sentence)
        for trigger, label in triggers:
            if trigger in stripped and label not in found:
                results.append(
                    MemoryCandidate(
                        kind=MemoryKind.HEALTH,
                        importance=MemoryImportance.HIGH,
                        text=f"用户提到{label}",
                        evidence=self._truncate(sentence),
                        confidence=0.75,
                    )
                )
                found.add(label)
        return results

    def _extract_emotion_pattern_from_sentence(self, sentence: str) -> list[MemoryCandidate]:
        triggers = [
            "我最近总是",
            "我经常觉得",
            "我总觉得",
            "我容易",
            "我害怕",
            "我担心",
        ]
        for trigger in triggers:
            if trigger in sentence:
                return [
                    MemoryCandidate(
                        kind=MemoryKind.EMOTION_PATTERN,
                        importance=MemoryImportance.MEDIUM,
                        text=self._normalize(sentence),
                        evidence=self._truncate(sentence),
                        confidence=0.70,
                    )
                ]
        return []

    def _extract_preference_from_sentence(self, sentence: str) -> list[MemoryCandidate]:
        triggers = [
            ("我喜欢", "用户喜欢"),
            ("我不喜欢", "用户不喜欢"),
            ("我更喜欢", "用户更喜欢"),
            ("我讨厌", "用户讨厌"),
            ("我偏好", "用户偏好"),
            ("我习惯", "用户习惯"),
            ("你最好", "用户希望"),
        ]
        for trigger, _prefix in triggers:
            if trigger in sentence:
                return [
                    MemoryCandidate(
                        kind=MemoryKind.PREFERENCE,
                        importance=MemoryImportance.MEDIUM,
                        text=self._normalize(sentence),
                        evidence=self._truncate(sentence),
                        confidence=0.75,
                    )
                ]
        return []

    def _extract_project_from_sentence(self, sentence: str) -> list[MemoryCandidate]:
        triggers = [
            "我正在做",
            "我在做",
            "我的项目",
            "这个项目",
            "我们的项目",
            "项目推进",
        ]
        for trigger in triggers:
            if trigger in sentence:
                return [
                    MemoryCandidate(
                        kind=MemoryKind.PROJECT,
                        importance=MemoryImportance.MEDIUM,
                        text=self._normalize(sentence),
                        evidence=self._truncate(sentence),
                        confidence=0.70,
                    )
                ]
        return []

    def _normalize(self, sentence: str) -> str:
        """Normalize a sentence and truncate to MAX_TEXT_LEN."""
        sentence = sentence.strip().rstrip("。.!！?？")
        if not sentence.endswith("。"):
            sentence += "。"
        return self._truncate(sentence)

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        parts = re.split(r"(?<=[。！？.!?])", text)
        return [p.strip() for p in parts if p.strip()]

    def _truncate(self, text: str) -> str:
        """Truncate text to MAX_TEXT_LEN."""
        text = text.strip()
        if len(text) > MAX_TEXT_LEN:
            return text[:MAX_TEXT_LEN]
        return text


def _strip_subject(text: str) -> str:
    """Strip common leading subject/particle prefixes to improve trigger matching."""
    prefixes = (
        "我最近",
        "我白天",
        "我晚上",
        "我总是",
        "经常",
        "总是",
        "最近",
        "有时候",
        "白天",
        "晚上",
        "早上",
    )
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):]
    return text
