"""Companion presence view types and helpers (Phase 2-A)."""

from __future__ import annotations

from dataclasses import dataclass

from app.ui.avatar_action import AvatarAction


@dataclass(frozen=True)
class CompanionPresenceView:
    """Data for the companion presence header card."""

    name: str
    subtitle: str
    status_text: str
    avatar_text: str
    avatar_label: str
    version: str
    release_stage: str


# Mapping from AvatarAction to natural-language companion status text
_COMPANTION_STATUS_TEXT: dict[AvatarAction, str] = {
    AvatarAction.IDLE: "我在这里，想聊就叫我。",
    AvatarAction.LISTENING: "我正在听你说。",
    AvatarAction.THINKING: "我在想怎么回答你。",
    AvatarAction.SPEAKING: "我正在回应你。",
    AvatarAction.PROACTIVE: "我看到你安静了一会儿，就来陪你一下。",
    AvatarAction.ERROR: "我遇到了一点问题。",
}


def render_companion_status_text(action: AvatarAction) -> str:
    """Return the natural-language companion status text for the given action.

    Args:
        action: The current avatar action state.

    Returns:
        A friendly, natural-language status string suitable for display
        in the companion header.
    """
    return _COMPANTION_STATUS_TEXT.get(action, "我在这里，想聊就叫我。")
