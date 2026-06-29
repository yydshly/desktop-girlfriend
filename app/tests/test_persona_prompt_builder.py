"""Tests for PersonaPromptBuilder."""

from app.brain.persona import DEFAULT_XIAOYUN_PERSONA, PersonaProfile, PersonaPromptBuilder


class TestPersonaPromptBuilder:
    """Tests for PersonaPromptBuilder."""

    def _make_builder(self) -> PersonaPromptBuilder:
        return PersonaPromptBuilder(DEFAULT_XIAOYUN_PERSONA)

    def test_build_system_prompt_contains_name(self) -> None:
        """Test build_system_prompt contains the persona name."""
        prompt = self._make_builder().build_system_prompt()
        assert "小云" in prompt

    def test_build_system_prompt_contains_identity(self) -> None:
        """Test build_system_prompt contains the persona identity."""
        prompt = self._make_builder().build_system_prompt()
        assert DEFAULT_XIAOYUN_PERSONA.identity in prompt

    def test_build_system_prompt_contains_role(self) -> None:
        """Test build_system_prompt contains the persona role."""
        prompt = self._make_builder().build_system_prompt()
        assert DEFAULT_XIAOYUN_PERSONA.role in prompt

    def test_build_system_prompt_contains_user_address(self) -> None:
        """Test build_system_prompt contains the user_address."""
        prompt = self._make_builder().build_system_prompt()
        assert DEFAULT_XIAOYUN_PERSONA.user_address in prompt

    def test_build_system_prompt_contains_core_traits(self) -> None:
        """Test build_system_prompt contains core_traits."""
        prompt = self._make_builder().build_system_prompt()
        for trait in DEFAULT_XIAOYUN_PERSONA.core_traits:
            assert trait in prompt

    def test_build_system_prompt_contains_speaking_style(self) -> None:
        """Test build_system_prompt contains speaking_style."""
        prompt = self._make_builder().build_system_prompt()
        for style in DEFAULT_XIAOYUN_PERSONA.speaking_style:
            assert style in prompt

    def test_build_system_prompt_contains_emotional_support(self) -> None:
        """Test build_system_prompt contains emotional_support."""
        prompt = self._make_builder().build_system_prompt()
        for support in DEFAULT_XIAOYUN_PERSONA.emotional_support:
            assert support in prompt

    def test_build_system_prompt_contains_behavior_rules(self) -> None:
        """Test build_system_prompt contains behavior_rules."""
        prompt = self._make_builder().build_system_prompt()
        for rule in DEFAULT_XIAOYUN_PERSONA.behavior_rules:
            assert rule in prompt

    def test_build_system_prompt_contains_safety_boundaries(self) -> None:
        """Test build_system_prompt contains safety_boundaries."""
        prompt = self._make_builder().build_system_prompt()
        for boundary in DEFAULT_XIAOYUN_PERSONA.safety_boundaries:
            assert boundary in prompt

    def test_build_system_prompt_contains_output_rules(self) -> None:
        """Test build_system_prompt contains output_rules."""
        prompt = self._make_builder().build_system_prompt()
        for rule in DEFAULT_XIAOYUN_PERSONA.output_rules:
            assert rule in prompt

    def test_build_system_prompt_no_empty_sections(self) -> None:
        """Test build_system_prompt does not contain empty section headers."""
        prompt = self._make_builder().build_system_prompt()
        lines = prompt.split("\n")
        # Section headers like "一、核心性格" should be followed by content
        for i, line in enumerate(lines):
            if line.startswith(("一、", "二、", "三、", "四、", "五、", "六、", "七、")):
                # Check that the next line is not another section header or end of content
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    assert next_line and not next_line.startswith("八"), \
                        f"Section {line} appears empty or followed by another header"

    def test_build_system_prompt_no_internal_object_repr(self) -> None:
        """Test build_system_prompt does not leak internal object reprs."""
        prompt = self._make_builder().build_system_prompt()
        # Should not contain dataclass repr patterns
        assert "PersonaProfile(" not in prompt
        assert "core_traits=" not in prompt
        assert "speaking_style=" not in prompt
        assert "field(" not in prompt

    def test_build_system_prompt_returns_string(self) -> None:
        """Test build_system_prompt returns a string."""
        result = self._make_builder().build_system_prompt()
        assert isinstance(result, str)

    def test_build_system_prompt_not_empty(self) -> None:
        """Test build_system_prompt returns non-empty string."""
        result = self._make_builder().build_system_prompt()
        assert len(result) > 100

    def test_profile_property_returns_profile(self) -> None:
        """Test the profile property returns the underlying PersonaProfile."""
        builder = self._make_builder()
        assert builder.profile is DEFAULT_XIAOYUN_PERSONA

    def test_custom_profile(self) -> None:
        """Test building prompt from a custom profile."""
        custom = PersonaProfile(
            name="小爱",
            identity="一个测试AI",
            role="测试角色",
            user_address="你",
            core_traits=("安静",),
            speaking_style=("简洁",),
            emotional_support=("陪伴",),
            behavior_rules=("不说谎",),
            safety_boundaries=("不做坏事",),
            output_rules=("简短回复",),
        )
        prompt = PersonaPromptBuilder(custom).build_system_prompt()
        assert "小爱" in prompt
        assert "一个测试AI" in prompt
        assert "测试角色" in prompt
        assert "安静" in prompt
        assert "简洁" in prompt
        assert "陪伴" in prompt
        assert "不说谎" in prompt
        assert "不做坏事" in prompt
        assert "简短回复" in prompt

    def test_user_address_appears_in_correct_format(self) -> None:
        """Test user_address appears in the prompt in the expected format."""
        prompt = self._make_builder().build_system_prompt()
        assert "你通常称呼用户为「你」" in prompt

    def test_custom_user_address_in_prompt(self) -> None:
        """Test custom user_address appears in the generated prompt."""
        custom = PersonaProfile(
            name="小爱",
            identity="一个测试AI",
            role="测试角色",
            user_address="大大",
            core_traits=(),
            speaking_style=(),
            emotional_support=(),
            behavior_rules=(),
            safety_boundaries=(),
            output_rules=(),
        )
        prompt = PersonaPromptBuilder(custom).build_system_prompt()
        assert "大大" in prompt
        assert "你通常称呼用户为「大大」" in prompt

    def test_no_double_bullets_in_prompt(self) -> None:
        """Test prompt does not contain double bullet patterns like '* * '."""
        prompt = self._make_builder().build_system_prompt()
        assert "* * " not in prompt

    def test_role_appears_as_single_bullet(self) -> None:
        """Test role appears as a single bullet in the prompt."""
        prompt = self._make_builder().build_system_prompt()
        assert "* 长期陪伴型桌面伙伴，不是工具客服，也不是虚拟恋人" in prompt

    def test_default_user_address_single_bullet(self) -> None:
        """Test default user_address appears as a single bullet in the prompt."""
        prompt = self._make_builder().build_system_prompt()
        assert "* 你通常称呼用户为「你」。" in prompt

    def test_custom_user_address_single_bullet(self) -> None:
        """Test custom user_address appears as a single bullet in the prompt."""
        custom = PersonaProfile(
            name="小爱",
            identity="一个测试AI",
            role="测试角色",
            user_address="大大",
            core_traits=(),
            speaking_style=(),
            emotional_support=(),
            behavior_rules=(),
            safety_boundaries=(),
            output_rules=(),
        )
        prompt = PersonaPromptBuilder(custom).build_system_prompt()
        assert "* 你通常称呼用户为「大大」。" in prompt

    def test_section_one_identity_present(self) -> None:
        """Test that section 一、角色定位 is present in the prompt."""
        prompt = self._make_builder().build_system_prompt()
        assert "一、角色定位" in prompt

    def test_section_seven_output_rules_present(self) -> None:
        """Test that section 七、输出要求 is present in the prompt."""
        prompt = self._make_builder().build_system_prompt()
        assert "七、输出要求" in prompt
