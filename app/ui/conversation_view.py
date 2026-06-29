"""Conversation experience view helpers (Phase 2-B)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderedConversationMessage:
    """A single rendered conversation message with speaker label and text."""

    speaker: str
    text: str


_EMPTY_CONVERSATION_TEXT = "小云在这里。想说什么，都可以慢慢说。"
_INPUT_PLACEHOLDER = "和小云说点什么..."


def render_empty_conversation_text() -> str:
    """Return the empty conversation prompt text.

    Returns:
        A gentle, welcoming message shown when no chat history exists.
    """
    return _EMPTY_CONVERSATION_TEXT


def render_message_prefix(role: str) -> str:
    """Return the speaker label for a given message role.

    Args:
        role: The message role, either "user" or "assistant".

    Returns:
        The speaker prefix label, e.g. "你：" or "小云：".
    """
    if role == "user":
        return "你："
    if role == "assistant":
        return "小云："
    return ""


def get_input_placeholder() -> str:
    """Return the input field placeholder text.

    Returns:
        The placeholder shown in the text input field.
    """
    return _INPUT_PLACEHOLDER
