"""Tests for persona probe cases."""

from app.brain.persona.probe.cases import DEFAULT_PERSONA_PROBE_CASES, PersonaProbeCase


class TestPersonaProbeCases:
    """Tests for DEFAULT_PERSONA_PROBE_CASES."""

    def test_default_cases_non_empty(self) -> None:
        """Test DEFAULT_PERSONA_PROBE_CASES is non-empty."""
        assert len(DEFAULT_PERSONA_PROBE_CASES) > 0

    def test_case_ids_are_unique(self) -> None:
        """Test all case_ids are unique."""
        ids = [c.case_id for c in DEFAULT_PERSONA_PROBE_CASES]
        assert len(ids) == len(set(ids)), "case_ids must be unique"

    def test_each_user_text_non_empty(self) -> None:
        """Test every case has a non-empty user_text."""
        for case in DEFAULT_PERSONA_PROBE_CASES:
            assert case.user_text, f"Case {case.case_id} has empty user_text"

    def test_each_case_has_expected_traits(self) -> None:
        """Test every case has at least one expected_trait."""
        for case in DEFAULT_PERSONA_PROBE_CASES:
            assert len(case.expected_traits) > 0, \
                f"Case {case.case_id} has no expected_traits"

    def test_casual_greeting_case_exists(self) -> None:
        """Test casual_greeting case exists and has correct fields."""
        case = next((c for c in DEFAULT_PERSONA_PROBE_CASES if c.case_id == "casual_greeting"), None)
        assert case is not None
        assert case.user_text == "你好小云，今天有点累。"
        assert len(case.expected_traits) > 0

    def test_low_mood_case_exists(self) -> None:
        """Test low_mood case exists."""
        case = next((c for c in DEFAULT_PERSONA_PROBE_CASES if c.case_id == "low_mood"), None)
        assert case is not None
        assert "没用" in case.user_text

    def test_help_request_case_exists(self) -> None:
        """Test help_request case exists."""
        case = next((c for c in DEFAULT_PERSONA_PROBE_CASES if c.case_id == "help_request"), None)
        assert case is not None
        assert "项目" in case.user_text

    def test_romantic_boundary_case_has_forbidden_patterns(self) -> None:
        """Test romantic_boundary contains恋爱 commitment forbidden patterns."""
        case = next((c for c in DEFAULT_PERSONA_PROBE_CASES if c.case_id == "romantic_boundary"), None)
        assert case is not None
        forbidden_texts = "\n".join(case.forbidden_patterns)
        assert "我愿意做你真正的女朋友" in forbidden_texts
        assert "我们结婚" in forbidden_texts

    def test_prompt_injection_case_has_forbidden_patterns(self) -> None:
        """Test prompt_injection contains system prompt leaking forbidden patterns."""
        case = next((c for c in DEFAULT_PERSONA_PROBE_CASES if c.case_id == "prompt_injection"), None)
        assert case is not None
        forbidden_texts = "\n".join(case.forbidden_patterns)
        assert "一、角色定位" in forbidden_texts
        assert "DEFAULT_XIAOYUN_PERSONA" in forbidden_texts

    def test_medical_boundary_case_has_forbidden_patterns(self) -> None:
        """Test medical_boundary contains medical boundary forbidden patterns."""
        case = next((c for c in DEFAULT_PERSONA_PROBE_CASES if c.case_id == "medical_boundary"), None)
        assert case is not None
        forbidden_texts = "\n".join(case.forbidden_patterns)
        assert "我可以替代医生" in forbidden_texts

    def test_all_cases_have_max_reply_chars(self) -> None:
        """Test every case has a max_reply_chars set."""
        for case in DEFAULT_PERSONA_PROBE_CASES:
            assert case.max_reply_chars is not None, \
                f"Case {case.case_id} missing max_reply_chars"

    def test_persona_probe_case_is_frozen(self) -> None:
        """Test PersonaProbeCase is a frozen dataclass."""
        import dataclasses

        case = PersonaProbeCase(
            case_id="test",
            user_text="hello",
        )
        assert dataclasses.is_dataclass(case)
