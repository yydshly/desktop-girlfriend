"""UI view objects for memory records."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryRecordView:
    """UI view object for a memory record.

    This is a minimal view object containing only what the UI needs to display.
    It does NOT include evidence, source, or status fields.
    """

    record_id: str
    kind: str
    importance: str
    text: str
    created_at: str
    updated_at: str


def render_memory_record_text(text: str, max_chars: int = 80) -> str:
    """Render memory record text, truncated to max_chars.

    Args:
        text: The record text to render.
        max_chars: Maximum number of characters to display.

    Returns:
        Truncated text suitable for UI display.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"
