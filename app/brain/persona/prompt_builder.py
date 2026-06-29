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
        lines.append(f"你是「{p.name}」，{p.identity}。")
        lines.append("")

        sections: list[tuple[str, tuple[str, ...]]] = [
            ("一、角色定位", (p.role, f"你通常称呼用户为「{p.user_address}」。")),
            ("二、核心性格", p.core_traits),
            ("三、说话风格", p.speaking_style),
            ("四、情绪陪伴方式", p.emotional_support),
            ("五、行为规则", p.behavior_rules),
            ("六、安全边界", p.safety_boundaries),
            ("七、输出要求", p.output_rules),
        ]

        for title, items in sections:
            if items:
                lines.append(title)
                for item in items:
                    lines.append(f"* {item}")
                lines.append("")

        return "\n".join(lines).strip()
