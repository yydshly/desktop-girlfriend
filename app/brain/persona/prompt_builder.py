"""System prompt builder from structured persona profiles."""

from app.brain.persona.profile import PersonaProfile


class PersonaPromptBuilder:
    """Builds system prompt text from a structured persona profile."""

    def __init__(self, profile: PersonaProfile) -> None:
        self._profile = profile

    @property
    def profile(self) -> PersonaProfile:
        return self._profile

    def build_system_prompt(self) -> str:
        """Build a system prompt string from the persona profile.

        The output contains the following sections:
        一、角色定位
        二、核心性格
        三、说话风格
        四、情绪陪伴方式
        五、行为规则
        六、安全边界
        七、输出要求
        """
        p = self._profile
        lines: list[str] = []

        # Header
        lines.append(f'你是"{p.name}"，{p.identity}。')
        lines.append(f"角色定位：{p.role}。")
        lines.append("")

        # Core traits
        if p.core_traits:
            lines.append("一、核心性格")
            for trait in p.core_traits:
                lines.append(f"* {trait}")
            lines.append("")

        # Speaking style
        if p.speaking_style:
            lines.append("二、说话风格")
            for style in p.speaking_style:
                lines.append(f"* {style}")
            lines.append("")

        # Emotional support
        if p.emotional_support:
            lines.append("三、情绪陪伴方式")
            for strategy in p.emotional_support:
                lines.append(f"* {strategy}")
            lines.append("")

        # Behavior rules
        if p.behavior_rules:
            lines.append("四、行为规则")
            for rule in p.behavior_rules:
                lines.append(f"* {rule}")
            lines.append("")

        # Safety boundaries
        if p.safety_boundaries:
            lines.append("五、安全边界")
            for boundary in p.safety_boundaries:
                lines.append(f"* {boundary}")
            lines.append("")

        # Output rules
        if p.output_rules:
            lines.append("六、输出要求")
            for rule in p.output_rules:
                lines.append(f"* {rule}")
            lines.append("")

        return "\n".join(lines).strip()
