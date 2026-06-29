"""Structured persona definition for the desktop companion."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PersonaProfile:
    """Structured persona definition for the desktop companion.

    Attributes:
        name: The companion's name, e.g. 小云.
        identity: Who she is, e.g. 运行在用户桌面上的 AI 伙伴.
        role: Her relationship to the user, e.g. 长期陪伴型桌面伙伴.
        user_address: How she refers to the user by default, e.g. 你.
        core_traits: Core personality traits.
        speaking_style: Speaking style guidelines.
        emotional_support: Emotional support strategies.
        behavior_rules: Behavioral rules.
        safety_boundaries: Safety boundaries.
        output_rules: Output formatting rules.
    """

    name: str
    identity: str
    role: str
    user_address: str
    core_traits: tuple[str, ...] = field(default_factory=tuple)
    speaking_style: tuple[str, ...] = field(default_factory=tuple)
    emotional_support: tuple[str, ...] = field(default_factory=tuple)
    behavior_rules: tuple[str, ...] = field(default_factory=tuple)
    safety_boundaries: tuple[str, ...] = field(default_factory=tuple)
    output_rules: tuple[str, ...] = field(default_factory=tuple)
