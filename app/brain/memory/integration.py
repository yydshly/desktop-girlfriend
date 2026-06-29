"""Read-only memory context integration for V8-G.

Provides a read-only provider that reads active memory records and builds
a session memory context for prompt injection. This module does not:

- Extract memory candidates from user input
- Create pending memories
- Confirm or reject memories
- Persist or mutate memories
- Call LLM or access network
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.brain.memory.repository import MemoryRepository
    from app.brain.memory.session_context import SessionMemoryContextBuilder


def create_readonly_memory_context_provider(
    repository: MemoryRepository,
    context_builder: SessionMemoryContextBuilder | None = None,
) -> Callable[[], str]:
    """Create a read-only memory context provider for dialogue prompt injection.

    This provider only reads active memory records from the repository.
    It does not extract, confirm, reject, persist, or mutate memories.

    Args:
        repository: The memory repository to read from.
        context_builder: Optional context builder. If None, uses default.

    Returns:
        A callable that returns a formatted session memory context string.
    """
    from app.brain.memory.session_context import SessionMemoryContextBuilder

    builder = context_builder or SessionMemoryContextBuilder()

    def provider() -> str:
        records = repository.list_active()
        return builder.build_from_records(records)

    return provider


class MemoryContextConfigLike(Protocol):
    """Protocol for memory context configuration.

    Use this to avoid circular imports when AppConfig is not available.
    """

    memory_context_enabled: bool
    memory_store_path: str


def create_memory_context_provider_from_config(
    config: MemoryContextConfigLike,
) -> Callable[[], str] | None:
    """Create a memory context provider from a config object.

    Args:
        config: Object with memory_context_enabled and memory_store_path.

    Returns:
        A callable provider if memory_context_enabled is True, else None.
    """
    if not config.memory_context_enabled:
        return None

    from pathlib import Path

    from app.brain.memory.repository import LocalJsonMemoryRepository

    repository = LocalJsonMemoryRepository(Path(config.memory_store_path))
    return create_readonly_memory_context_provider(repository)
