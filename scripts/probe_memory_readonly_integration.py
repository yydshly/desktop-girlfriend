"""Probe script for read-only memory context integration (V8-G).

Verifies:
1. create_readonly_memory_context_provider works with LocalJsonMemoryRepository
2. Provider reads active records and builds context
3. Provider returns empty context when no records
4. Deleted records are not included in context
"""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.brain.memory.integration import create_readonly_memory_context_provider
from app.brain.memory.repository import (
    LocalJsonMemoryRepository,
    MemoryRecord,
    MemoryRecordStatus,
)
from app.brain.memory.types import MemoryImportance, MemoryKind


def _make_record(
    record_id: str,
    text: str,
    kind: MemoryKind = MemoryKind.PREFERENCE,
    importance: MemoryImportance = MemoryImportance.MEDIUM,
) -> MemoryRecord:
    """Create a test MemoryRecord."""
    return MemoryRecord(
        id=record_id,
        kind=kind,
        importance=importance,
        text=text,
        source="probe",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        status=MemoryRecordStatus.ACTIVE,
    )


def main() -> None:
    print("Read-only Memory Integration Probe\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "memory_probe.json"
        repo = LocalJsonMemoryRepository(json_path)

        # Add a record
        record = _make_record(
            record_id="probe-record-001",
            text="用户喜欢简短的回复。",
        )
        repo.add(record)

        # Create provider
        provider = create_readonly_memory_context_provider(repo)

        # First call — should have context
        context_before = provider()
        context_before_chars = len(context_before)
        print(f"context_before_delete_chars={context_before_chars}")

        # Delete the record
        repo.delete("probe-record-001")

        # Second call — context should be empty
        context_after = provider()
        context_after_chars = len(context_after)
        print(f"context_after_delete_chars={context_after_chars}")

        assert context_before_chars > 0, "context_before should not be empty"
        assert context_after_chars == 0, "context_after should be empty"
        assert "用户喜欢简短的回复" in context_before, "should contain record text"
        assert context_after == "", "context_after should be empty string"

        print("\nPASS")


if __name__ == "__main__":
    main()
