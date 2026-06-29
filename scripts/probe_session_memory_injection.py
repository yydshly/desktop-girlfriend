r"""Session memory injection probe script.

Run locally (no network, no LLM):
    .venv\Scripts\python.exe scripts/probe_session_memory_injection.py
"""

from __future__ import annotations

from app.brain.memory import (
    DeterministicMemoryExtractor,
    InMemoryMemoryConfirmationStore,
    MemoryConfirmationService,
    SessionMemoryContextBuilder,
)
from app.brain.prompts.registry import PromptRegistry


def main() -> None:
    print("Session Memory Injection Probe")
    print()

    # Setup
    extractor = DeterministicMemoryExtractor()
    store = InMemoryMemoryConfirmationStore()
    service = MemoryConfirmationService(store)
    context_builder = SessionMemoryContextBuilder()
    prompt_registry = PromptRegistry()

    # Extract and submit candidates
    candidates = extractor.extract("我女朋友叫红红，我喜欢短回复，我正在做一个桌面女友项目。")
    print(f"extracted_candidates: {len(candidates)}")

    pending = service.submit_candidates(candidates)
    print(f"pending: {len(pending)}")

    # Confirm first two, reject third
    if len(pending) >= 1:
        service.confirm(pending[0].id)
    if len(pending) >= 2:
        service.confirm(pending[1].id)
    if len(pending) >= 3:
        service.reject(pending[2].id)

    confirmed = service.list_confirmed()
    rejected = service.list_rejected()

    print(f"confirmed_count: {len(confirmed)}")
    print(f"rejected_count: {len(rejected)}")
    print()

    # Build session memory context
    memory_context = context_builder.build(tuple(confirmed))
    print(f"memory_context_chars: {len(memory_context)}")
    print()

    # Build chat messages with memory context
    messages = prompt_registry.build_chat_messages(
        "今天继续推进项目。",
        session_memory_context=memory_context,
    )

    print("messages:")
    for i, msg in enumerate(messages):
        content_preview = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
        content_preview = content_preview.replace("\n", " ")
        print(f"{i} {msg.role} {content_preview}")

    print()
    print("Note: This probe does NOT call any LLM or write any files.")


if __name__ == "__main__":
    main()
