"""Avatar expression view definitions (Phase 2-H)."""

from __future__ import annotations

from dataclasses import dataclass

from app.ui.avatar_action import AvatarAction


@dataclass(frozen=True)
class AvatarExpressionView:
    """Immutable view model for avatar expression display."""

    emoji: str
    label: str
    mood: str
    aria_text: str


def build_avatar_expression_view(action: AvatarAction) -> AvatarExpressionView:
    """Build avatar expression view for a given avatar action.

    Args:
        action: The current avatar action state.

    Returns:
        An AvatarExpressionView with emoji, label, mood, and aria_text.
    """
    if action is AvatarAction.IDLE:
        return AvatarExpressionView(
            emoji="☁️",
            label="安静陪着你",
            mood="idle",
            aria_text="小云正在安静陪伴",
        )
    if action is AvatarAction.LISTENING:
        return AvatarExpressionView(
            emoji="👂",
            label="认真听你说",
            mood="listening",
            aria_text="小云正在听你说话",
        )
    if action is AvatarAction.THINKING:
        return AvatarExpressionView(
            emoji="💭",
            label="想一想",
            mood="thinking",
            aria_text="小云正在思考",
        )
    if action is AvatarAction.SPEAKING:
        return AvatarExpressionView(
            emoji="🗣️",
            label="回应你",
            mood="speaking",
            aria_text="小云正在回应",
        )
    if action is AvatarAction.PROACTIVE:
        return AvatarExpressionView(
            emoji="✨",
            label="来陪你一下",
            mood="proactive",
            aria_text="小云主动来陪你",
        )
    if action is AvatarAction.ERROR:
        return AvatarExpressionView(
            emoji="⚠️",
            label="有点小状况",
            mood="error",
            aria_text="小云遇到了一点问题",
        )
    # Fallback to idle
    return AvatarExpressionView(
        emoji="☁️",
        label="安静陪着你",
        mood="idle",
        aria_text="小云正在安静陪伴",
    )
