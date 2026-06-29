r"""Memory repository probe script.

Run locally (no network, no LLM):
    .venv\Scripts\python.exe scripts/probe_memory_repository.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.brain.memory import (
    DeterministicMemoryExtractor,
    InMemoryMemoryConfirmationStore,
    MemoryConfirmationService,
)
from app.brain.memory.repository import (
    LocalJsonMemoryRepository,
    memory_record_from_confirmed,
)


def main() -> None:
    print("Memory Repository Probe")
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "memory.json"

        # Setup
        extractor = DeterministicMemoryExtractor()
        store = InMemoryMemoryConfirmationStore()
        service = MemoryConfirmationService(store)
        repo = LocalJsonMemoryRepository(path)

        # Extract and confirm a candidate
        candidates = extractor.extract("我女朋友叫红红，我喜欢短回复。")
        print(f"extracted_candidates: {len(candidates)}")

        pending = service.submit_candidates(candidates)
        print(f"pending: {len(pending)}")

        # Confirm the first candidate
        if pending:
            confirmed = service.confirm(pending[0].id)
            print(f"confirmed: {confirmed.candidate.text[:20]}...")

            # Convert to MemoryRecord
            record = memory_record_from_confirmed(confirmed)
            print(f"record_id: {record.id[:8]}...")

            # Add to repository
            repo.add(record)
            print("added: 1")

        # List active
        active = repo.list_active()
        print(f"active_before_delete: {len(active)}")

        # Delete
        if active:
            deleted = repo.delete(active[0].id)
            print(f"deleted_status: {deleted.status.value}")

        # List after delete
        active_after = repo.list_active()
        all_after = repo.list_all()
        print(f"active_after_delete: {len(active_after)}")
        print(f"all_after_delete: {len(all_after)}")

        print()
        print("PASS")


if __name__ == "__main__":
    main()
