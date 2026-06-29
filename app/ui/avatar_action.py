"""Avatar action types and display helpers (V10-A / V10-B)."""

from __future__ import annotations

from enum import StrEnum


class AvatarAction(StrEnum):
    """Avatar action states for UI display."""

    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    PROACTIVE = "proactive"
    ERROR = "error"


_AVATAR_ACTION_TEXT: dict[AvatarAction, str] = {
    AvatarAction.IDLE: "☁️",
    AvatarAction.LISTENING: "👂",
    AvatarAction.THINKING: "💭",
    AvatarAction.SPEAKING: "🗣️",
    AvatarAction.PROACTIVE: "✨",
    AvatarAction.ERROR: "⚠️",
}


_AVATAR_ACTION_LABEL: dict[AvatarAction, str] = {
    AvatarAction.IDLE: "小云在待机",
    AvatarAction.LISTENING: "小云正在听你说",
    AvatarAction.THINKING: "小云正在想",
    AvatarAction.SPEAKING: "小云正在回应",
    AvatarAction.PROACTIVE: "小云来陪你一下",
    AvatarAction.ERROR: "小云遇到了一点问题",
}

# V10-B: Per-action background color stylesheet
_AVATAR_ACTION_STYLE: dict[AvatarAction, str] = {
    AvatarAction.IDLE: (
        "font-size: 32px; min-width: 56px; max-width: 56px; "
        "min-height: 56px; max-height: 56px; "
        "background-color: #eef3ff; qproperty-alignment: AlignCenter;"
    ),
    AvatarAction.LISTENING: (
        "font-size: 32px; min-width: 56px; max-width: 56px; "
        "min-height: 56px; max-height: 56px; "
        "background-color: #e8f7ff; qproperty-alignment: AlignCenter;"
    ),
    AvatarAction.THINKING: (
        "font-size: 32px; min-width: 56px; max-width: 56px; "
        "min-height: 56px; max-height: 56px; "
        "background-color: #f3edff; qproperty-alignment: AlignCenter;"
    ),
    AvatarAction.SPEAKING: (
        "font-size: 32px; min-width: 56px; max-width: 56px; "
        "min-height: 56px; max-height: 56px; "
        "background-color: #fff3df; qproperty-alignment: AlignCenter;"
    ),
    AvatarAction.PROACTIVE: (
        "font-size: 32px; min-width: 56px; max-width: 56px; "
        "min-height: 56px; max-height: 56px; "
        "background-color: #fff7cc; qproperty-alignment: AlignCenter;"
    ),
    AvatarAction.ERROR: (
        "font-size: 32px; min-width: 56px; max-width: 56px; "
        "min-height: 56px; max-height: 56px; "
        "background-color: #ffecec; qproperty-alignment: AlignCenter;"
    ),
}


def avatar_text_for_action(action: AvatarAction) -> str:
    """Return the emoji text for the given avatar action."""
    return _AVATAR_ACTION_TEXT[action]


def avatar_label_for_action(action: AvatarAction) -> str:
    """Return the label text for the given avatar action."""
    return _AVATAR_ACTION_LABEL[action]


def avatar_style_for_action(action: AvatarAction) -> str:
    """Return the stylesheet for the given avatar action."""
    return _AVATAR_ACTION_STYLE[action]
