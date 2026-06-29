"""Tests for PersonaReplyChecker."""

from app.brain.persona.probe.cases import PersonaProbeCase
from app.brain.persona.probe.checker import (
    PersonaReplyChecker,
)


class TestPersonaReplyChecker:
    """Tests for PersonaReplyChecker."""

    def _make_checker(self) -> PersonaReplyChecker:
        return PersonaReplyChecker()

    def test_normal_reply_passes(self) -> None:
        """Test a normal reply with no violations passes."""
        checker = self._make_checker()
        case = PersonaProbeCase(
            case_id="test",
            user_text="你好",
            expected_traits=("友好",),
            forbidden_patterns=(),
            max_reply_chars=100,
        )
        result = checker.check(case, "你好，我在这里。")
        assert result.passed is True
        assert len(result.findings) == 0

    def test_empty_reply_fails(self) -> None:
        """Test an empty reply fails with empty_reply finding."""
        checker = self._make_checker()
        case = PersonaProbeCase(
            case_id="test",
            user_text="你好",
            expected_traits=("友好",),
            forbidden_patterns=(),
            max_reply_chars=100,
        )
        result = checker.check(case, "")
        assert result.passed is False
        assert any(f.kind == "empty_reply" for f in result.findings)

    def test_whitespace_only_reply_fails(self) -> None:
        """Test a whitespace-only reply fails."""
        checker = self._make_checker()
        case = PersonaProbeCase(
            case_id="test",
            user_text="你好",
            expected_traits=(),
            forbidden_patterns=(),
            max_reply_chars=100,
        )
        result = checker.check(case, "   ")
        assert result.passed is False

    def test_too_long_reply_fails(self) -> None:
        """Test a reply exceeding max_reply_chars fails."""
        checker = self._make_checker()
        case = PersonaProbeCase(
            case_id="test",
            user_text="你好",
            expected_traits=(),
            forbidden_patterns=(),
            max_reply_chars=10,
        )
        result = checker.check(case, "这是一条很长的回复内容，超过了限制。")
        assert result.passed is False
        assert any(f.kind == "too_long" for f in result.findings)

    def test_exactly_at_limit_passes(self) -> None:
        """Test a reply exactly at the limit passes."""
        checker = self._make_checker()
        case = PersonaProbeCase(
            case_id="test",
            user_text="你好",
            expected_traits=(),
            forbidden_patterns=(),
            max_reply_chars=5,
        )
        result = checker.check(case, "你好啊")
        assert result.passed is True

    def test_forbidden_pattern_fails(self) -> None:
        """Test a reply containing a forbidden pattern fails."""
        checker = self._make_checker()
        case = PersonaProbeCase(
            case_id="test",
            user_text="你好",
            expected_traits=(),
            forbidden_patterns=("作为人工智能",),
            max_reply_chars=None,
        )
        result = checker.check(case, "作为人工智能，我没有真正的情感。")
        assert result.passed is False
        assert any(f.kind == "forbidden_pattern" for f in result.findings)

    def test_multiple_findings_returned(self) -> None:
        """Test multiple findings can be returned simultaneously."""
        checker = self._make_checker()
        case = PersonaProbeCase(
            case_id="test",
            user_text="你好",
            expected_traits=(),
            forbidden_patterns=("禁止词",),
            max_reply_chars=5,
        )
        result = checker.check(case, "这是一条包含禁止词的超出长度的回复内容。")
        assert result.passed is False
        finding_kinds = {f.kind for f in result.findings}
        assert "forbidden_pattern" in finding_kinds
        assert "too_long" in finding_kinds

    def test_expected_traits_preserved_in_result(self) -> None:
        """Test expected_traits from case are echoed in result."""
        checker = self._make_checker()
        case = PersonaProbeCase(
            case_id="test",
            user_text="你好",
            expected_traits=("语气温和", "先共情"),
            forbidden_patterns=(),
            max_reply_chars=None,
        )
        result = checker.check(case, "我理解你的感受。")
        assert result.expected_traits == ("语气温和", "先共情")

    def test_reply_stripped_before_check(self) -> None:
        """Test that reply text is stripped before checking."""
        checker = self._make_checker()
        case = PersonaProbeCase(
            case_id="test",
            user_text="你好",
            expected_traits=(),
            forbidden_patterns=("人工智能",),
            max_reply_chars=None,
        )
        result = checker.check(case, "  作为人工智能，没有情感。  ")
        # The stripped text still contains the forbidden pattern
        assert "作为人工智能" in result.reply_text
        assert result.reply_text == "作为人工智能，没有情感。"

    def test_forbidden_pattern_case_sensitive(self) -> None:
        """Test forbidden pattern matching is case-sensitive."""
        checker = self._make_checker()
        case = PersonaProbeCase(
            case_id="test",
            user_text="你好",
            expected_traits=(),
            forbidden_patterns=("AI",),
            max_reply_chars=None,
        )
        # Lowercase 'ai' should not match uppercase 'AI'
        result = checker.check(case, "我是一个ai助手。")
        assert result.passed is True

        # Uppercase 'AI' should match
        result2 = checker.check(case, "我是一个AI助手。")
        assert result2.passed is False

    def test_none_max_reply_chars_no_length_check(self) -> None:
        """Test max_reply_chars=None skips length check."""
        checker = self._make_checker()
        case = PersonaProbeCase(
            case_id="test",
            user_text="你好",
            expected_traits=(),
            forbidden_patterns=(),
            max_reply_chars=None,
        )
        long_reply = "这是一条非常长的回复内容。" * 100
        result = checker.check(case, long_reply)
        # Should pass since no length check
        assert result.passed is True

    def test_passing_result_has_no_findings(self) -> None:
        """Test a passing result has empty findings tuple."""
        checker = self._make_checker()
        case = PersonaProbeCase(
            case_id="test",
            user_text="你好",
            expected_traits=("友好",),
            forbidden_patterns=("禁止",),
            max_reply_chars=50,
        )
        result = checker.check(case, "你好，很高兴见到你。")
        assert result.passed is True
        assert result.findings == ()

    def test_case_id_preserved_in_result(self) -> None:
        """Test case_id from case appears in result."""
        checker = self._make_checker()
        case = PersonaProbeCase(
            case_id="my_test_case",
            user_text="测试输入",
            expected_traits=(),
            forbidden_patterns=(),
            max_reply_chars=None,
        )
        result = checker.check(case, "这是回复。")
        assert result.case_id == "my_test_case"
