"""UI view objects for memory suggestion."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemorySuggestionView:
    """UI view object for a pending memory suggestion.

    This is a minimal view object containing only what the UI needs to display.
    It does NOT include evidence, source, or raw conversation text.
    """

    pending_id: str
    kind: str
    importance: str
    text: str


def render_memory_suggestion_text(text: str, max_chars: int = 80) -> str:
    """Render memory suggestion text, truncated to max_chars.

    Args:
        text: The suggestion text to render.
        max_chars: Maximum number of characters to display.

    Returns:
        Truncated text suitable for UI display.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"
