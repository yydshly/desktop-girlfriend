"""Local memory repository for V8-D.

Provides a JSON-file based persistence layer for confirmed memories.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from app.brain.memory.types import MemoryImportance, MemoryKind

if TYPE_CHECKING:
    from app.brain.memory.confirmation import ConfirmedMemory


class MemoryRecordStatus(StrEnum):
    ACTIVE = "active"
    DELETED = "deleted"


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    kind: MemoryKind
    importance: MemoryImportance
    text: str
    source: str
    created_at: datetime
    updated_at: datetime
    status: MemoryRecordStatus = MemoryRecordStatus.ACTIVE


class MemoryRepository(Protocol):
    """Protocol for memory repository."""

    def add(self, record: MemoryRecord) -> MemoryRecord:
        ...

    def get(self, memory_id: str) -> MemoryRecord | None:
        ...

    def list_active(self) -> tuple[MemoryRecord, ...]:
        ...

    def list_all(self) -> tuple[MemoryRecord, ...]:
        ...

    def delete(self, memory_id: str) -> MemoryRecord:
        ...

    def clear(self) -> None:
        ...


def utc_now() -> datetime:
    """Return current UTC datetime with timezone awareness."""
    return datetime.now(UTC)


def new_memory_record_id() -> str:
    """Generate a new unique memory record id."""
    import uuid
    return str(uuid.uuid4())


class LocalJsonMemoryRepository:
    """JSON-file based memory repository.

    V8-D repository is local-only and explicit. It is not wired into the chat flow.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def add(self, record: MemoryRecord) -> MemoryRecord:
        """Add a new memory record."""
        records = self._read_records()

        # Check for duplicate id
        for existing in records:
            if existing["id"] == record.id:
                raise ValueError(f"Record with id {record.id!r} already exists")

        records.append(self._record_to_dict(record))
        self._write_records(records)
        return record

    def get(self, memory_id: str) -> MemoryRecord | None:
        """Get a memory record by id, including deleted."""
        records = self._read_records()
        for data in records:
            if data["id"] == memory_id:
                return self._record_from_dict(data)
        return None

    def list_active(self) -> tuple[MemoryRecord, ...]:
        """List all active (non-deleted) memory records."""
        records = self._read_records()
        result = []
        for data in records:
            record = self._record_from_dict(data)
            if record.status == MemoryRecordStatus.ACTIVE:
                result.append(record)
        return tuple(result)

    def list_all(self) -> tuple[MemoryRecord, ...]:
        """List all memory records including deleted."""
        records = self._read_records()
        return tuple(self._record_from_dict(data) for data in records)

    def delete(self, memory_id: str) -> MemoryRecord:
        """Soft delete a memory record by marking it as DELETED."""
        records = self._read_records()
        for i, data in enumerate(records):
            if data["id"] == memory_id:
                # Update status and updated_at
                data["status"] = MemoryRecordStatus.DELETED.value
                data["updated_at"] = utc_now().isoformat()
                self._write_records(records)
                return self._record_from_dict(data)

        raise KeyError(f"No record with id {memory_id!r}")

    def clear(self) -> None:
        """Clear all records."""
        if self._path.exists():
            self._path.unlink()

    def _read_records(self) -> list[dict[str, object]]:
        """Read records from JSON file."""
        if not self._path.exists():
            return []
        with open(self._path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "records" not in data:
            raise ValueError("Invalid JSON format: expected {version, records}")
        records = data["records"]
        if not isinstance(records, list):
            raise ValueError("Invalid JSON format: records must be a list")
        return records

    def _write_records(self, records: list[dict[str, object]]) -> None:
        """Write records to JSON file."""
        # Create parent directory if needed
        self._path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": 1,
            "records": records,
        }
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _record_to_dict(self, record: MemoryRecord) -> dict[str, object]:
        """Serialize a MemoryRecord to a dict."""
        return {
            "id": record.id,
            "kind": record.kind.value,
            "importance": record.importance.value,
            "text": record.text,
            "source": record.source,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "status": record.status.value,
        }

    def _record_from_dict(self, data: dict[str, object]) -> MemoryRecord:
        """Deserialize a MemoryRecord from a dict."""
        required_fields = ("id", "kind", "importance", "text", "source", "created_at", "updated_at", "status")
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field!r}")

        return MemoryRecord(
            id=str(data["id"]),
            kind=MemoryKind(str(data["kind"])),
            importance=MemoryImportance(str(data["importance"])),
            text=str(data["text"]),
            source=str(data["source"]),
            created_at=datetime.fromisoformat(str(data["created_at"])),
            updated_at=datetime.fromisoformat(str(data["updated_at"])),
            status=MemoryRecordStatus(str(data["status"])),
        )


def memory_record_from_confirmed(
    confirmed: ConfirmedMemory,
    *,
    memory_id: str | None = None,
) -> MemoryRecord:
    """Create a MemoryRecord from a ConfirmedMemory.

    Args:
        confirmed: The confirmed memory to convert.
        memory_id: Optional id to use. If None, a new uuid is generated.

    Returns:
        A MemoryRecord for persistence.
    """
    now = utc_now()
    return MemoryRecord(
        id=memory_id or new_memory_record_id(),
        kind=confirmed.candidate.kind,
        importance=confirmed.candidate.importance,
        text=confirmed.candidate.text,
        source=confirmed.candidate.source,
        created_at=confirmed.confirmed_at,
        updated_at=now,
        status=MemoryRecordStatus.ACTIVE,
    )
