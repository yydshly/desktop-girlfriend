"""Session memory context builder for V8-C.

Formats confirmed memories into a prompt-safe context block for injection.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.brain.memory.confirmation import ConfirmedMemory
from app.brain.memory.types import MemoryKind


@dataclass(frozen=True)
class SessionMemoryContextConfig:
    """Configuration for session memory context building."""

    max_items: int = 5
    max_item_chars: int = 100
    max_total_chars: int = 600
    include_boundary: bool = False


class SessionMemoryContextBuilder:
    """Builds a prompt-safe context block from confirmed session memories.

    V8-C does not persist memory. It only formats already-confirmed memories
    for optional prompt injection in the current runtime session.
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

        # Filter memories according to config
        filtered = self._filter_memories(confirmed_memories)
        if not filtered:
            return ""

        # Build lines
        lines = self._format_memories(filtered)

        # Build final context
        header = "已确认的用户会话记忆，仅用于理解当前对话，不要主动逐条复述："
        body = "\n".join(lines)

        context = f"{header}\n{body}"

        # Truncate to max_total_chars
        if len(context) > self._config.max_total_chars:
            context = context[: self._config.max_total_chars]

        return context

    def _filter_memories(self, memories: tuple[ConfirmedMemory, ...]) -> list[ConfirmedMemory]:
        """Filter memories based on config rules."""
        result: list[ConfirmedMemory] = []

        for memory in memories:
            # Exclude boundary unless explicitly allowed
            if memory.candidate.kind == MemoryKind.BOUNDARY:
                if not self._config.include_boundary:
                    continue

            # Respect max_items
            if len(result) >= self._config.max_items:
                break

            result.append(memory)

        return result

    def _format_memories(self, memories: list[ConfirmedMemory]) -> list[str]:
        """Format individual memories into lines."""
        lines: list[str] = []

        for memory in memories:
            text = memory.candidate.text

            # Truncate individual item
            if len(text) > self._config.max_item_chars:
                text = text[: self._config.max_item_chars]

            # Remove trailing punctuation to keep format clean
            text = text.strip().rstrip("。.!！?？")
            if text:
                lines.append(f"- {text}。")

        return lines
