"""Tests for memory probe cases."""

import pytest

from app.brain.memory import DEFAULT_MEMORY_PROBE_CASES, MemoryKind
from app.brain.memory.probe_cases import MemoryProbeCase


class TestDefaultMemoryProbeCases:
    """Tests for DEFAULT_MEMORY_PROBE_CASES."""

    def test_non_empty(self) -> None:
        assert len(DEFAULT_MEMORY_PROBE_CASES) > 0

    def test_case_ids_unique(self) -> None:
        ids = [c.case_id for c in DEFAULT_MEMORY_PROBE_CASES]
        assert len(ids) == len(set(ids)), "case_ids must be unique"

    def test_count_min_le_max(self) -> None:
        for case in DEFAULT_MEMORY_PROBE_CASES:
            assert case.expected_count_min <= case.expected_count_max, (
                f"case {case.case_id}: expected_count_min > expected_count_max"
            )

    def test_smalltalk_zero_max(self) -> None:
        smalltalk_cases = [
            c for c in DEFAULT_MEMORY_PROBE_CASES if "smalltalk" in c.case_id
        ]
        for case in smalltalk_cases:
            assert case.expected_count_max == 0, (
                f"case {case.case_id}: smalltalk should have expected_count_max=0"
            )

    def test_boundary_single_max(self) -> None:
        boundary_cases = [
            c for c in DEFAULT_MEMORY_PROBE_CASES if "boundary" in c.case_id
        ]
        for case in boundary_cases:
            assert case.expected_count_max == 1, (
                f"case {case.case_id}: boundary should have expected_count_max=1"
            )

    def test_all_expected_kinds_valid(self) -> None:
        valid_kinds = {k.value for k in MemoryKind}
        for case in DEFAULT_MEMORY_PROBE_CASES:
            for kind_str in case.expected_kinds:
                assert kind_str in valid_kinds, (
                    f"case {case.case_id}: invalid kind {kind_str!r}"
                )

    def test_user_text_not_empty(self) -> None:
        for case in DEFAULT_MEMORY_PROBE_CASES:
            assert case.user_text.strip(), f"case {case.case_id}: user_text is empty"


class TestMemoryProbeCase:
    """Tests for MemoryProbeCase dataclass."""

    def test_case_creation(self) -> None:
        case = MemoryProbeCase(
            case_id="test",
            user_text="我女朋友叫小红。",
            expected_kinds=("relationship",),
            expected_count_min=1,
            expected_count_max=2,
        )
        assert case.case_id == "test"
        assert case.user_text == "我女朋友叫小红。"
        assert case.expected_kinds == ("relationship",)
        assert case.expected_count_min == 1
        assert case.expected_count_max == 2

    def test_case_is_frozen(self) -> None:
        case = DEFAULT_MEMORY_PROBE_CASES[0]
        with pytest.raises(AttributeError):
            case.case_id = "changed"  # type: ignore[misc]
