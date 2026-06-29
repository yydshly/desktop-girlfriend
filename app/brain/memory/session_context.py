"""Session memory context builder for V8-C and V8-E.

Formats confirmed memories and memory records into a prompt-safe context block.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.brain.memory.types import MemoryKind

if TYPE_CHECKING:
    from app.brain.memory.confirmation import ConfirmedMemory
    from app.brain.memory.repository import MemoryRecord


@dataclass(frozen=True)
class SessionMemoryContextConfig:
    """Configuration for session memory context building."""

    max_items: int = 5
    max_item_chars: int = 100
    max_total_chars: int = 600
    include_boundary: bool = False


@dataclass(frozen=True)
class _ContextItem:
    """Internal representation for context building."""

    kind: MemoryKind
    text: str


class SessionMemoryContextBuilder:
    """Builds a prompt-safe context block from confirmed session memories.

    V8-C does not persist memory. It only formats already-confirmed memories
    for optional prompt injection in the current runtime session.

    V8-E adds build_from_records() for use with persisted MemoryRecords.
    """

    def __init__(self, config: SessionMemoryContextConfig | None = None) -> None:
        self._config = config or SessionMemoryContextConfig()

    def build(self, confirmed_memories: tuple[ConfirmedMemory, ...]) -> str:
        """Build a context string from confirmed memories.

        Args:
            confirmed_memories: Tuple of confirmed memories to format.

        Returns:
            A formatted context string, or empty string if no valid memories.
        """
        if not confirmed_memories:
            return ""

        items = self._items_from_confirmed(confirmed_memories)
        return self._build_from_items(items)

    def build_from_records(self, records: tuple[MemoryRecord, ...]) -> str:
        """Build a context string from memory records.

        Args:
            records: Tuple of memory records to format.

        Returns:
            A formatted context string, or empty string if no valid records.
        """
        if not records:
            return ""

        items = self._items_from_records(records)
        return self._build_from_items(items)

    def _items_from_confirmed(
        self, confirmed_memories: tuple[ConfirmedMemory, ...]
    ) -> list[_ContextItem]:
        """Convert confirmed memories to context items."""
        result: list[_ContextItem] = []
        for memory in confirmed_memories:
            if memory.candidate.kind == MemoryKind.BOUNDARY:
                if not self._config.include_boundary:
                    continue
            if len(result) >= self._config.max_items:
                break
            result.append(_ContextItem(kind=memory.candidate.kind, text=memory.candidate.text))
        return result

    def _items_from_records(self, records: tuple[MemoryRecord, ...]) -> list[_ContextItem]:
        """Convert memory records to context items."""
        result: list[_ContextItem] = []
        for record in records:
            if record.kind == MemoryKind.BOUNDARY:
                if not self._config.include_boundary:
                    continue
            if len(result) >= self._config.max_items:
                break
            result.append(_ContextItem(kind=record.kind, text=record.text))
        return result

    def _build_from_items(self, items: list[_ContextItem]) -> str:
        """Build context string from context items."""
        if not items:
            return ""

        lines = self._format_items(items)

        header = "已确认的用户会话记忆，仅用于理解当前对话，不要主动逐条复述："
        body = "\n".join(lines)

        context = f"{header}\n{body}"

        # Truncate to max_total_chars
        if len(context) > self._config.max_total_chars:
            context = context[: self._config.max_total_chars]

        return context

    def _format_items(self, items: list[_ContextItem]) -> list[str]:
        """Format individual context items into lines."""
        lines: list[str] = []

        for item in items:
            text = item.text

            # Truncate individual item
            if len(text) > self._config.max_item_chars:
                text = text[: self._config.max_item_chars]

            # Remove trailing punctuation to keep format clean
            text = text.strip().rstrip("。.!！?？")
            if text:
                lines.append(f"- {text}。")

        return lines
