"""Integration tests for manual memory add persistence (V8-J).

Tests the full wiring:
EventBus.publish(MEMORY_ADD_REQUESTED)
  → MemorySuggestionController._on_memory_add_requested
  → MemoryRuntimeService.add_manual_record
  → LocalJsonMemoryRepository.add
  → dispatch MEMORY_ADDED
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


from app.brain.memory.controller import MemorySuggestionController
from app.brain.memory.repository import LocalJsonMemoryRepository, MemoryRecordStatus
from app.brain.memory.runtime import create_local_memory_runtime
from app.contracts.events import MEMORY_ADD_REQUESTED, MEMORY_ADDED, BaseEvent
from app.core.event_bus import EventBus


class TestManualMemoryAddPersistence:
    """Test manual memory add through the full EventBus → Controller → Repository chain."""

    def test_memory_add_requested_persists_to_repository(self) -> None:
        """Publishing MEMORY_ADD_REQUESTED writes to repository via controller."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LocalJsonMemoryRepository(Path(tmpdir) / "memory.json")
            runtime = create_local_memory_runtime(repo)

            dispatched: list[BaseEvent] = []
            bus = EventBus()

            def dispatcher(event: BaseEvent) -> None:
                dispatched.append(event)

            controller = MemorySuggestionController(
                runtime=runtime,
                subscribe=bus.subscribe,
                unsubscribe=bus.unsubscribe,
                dispatch_event=dispatcher,
            )
            controller.start()

            # Publish MEMORY_ADD_REQUESTED
            bus.publish(
                BaseEvent(
                    event_type=MEMORY_ADD_REQUESTED,
                    request_id="req-1",
                    source="test",
                    payload={"text": "我喜欢短回复"},
                )
            )

            # Controller should have dispatched MEMORY_ADDED
            assert len(dispatched) == 1, f"Expected 1 event, got {len(dispatched)}: {[e.event_type for e in dispatched]}"
            assert dispatched[0].event_type == MEMORY_ADDED
            payload = dispatched[0].payload
            assert payload["text"] == "我喜欢短回复"
            assert payload["kind"] == "other"
            assert payload["importance"] == "medium"

            # Repository should have the record
            records = repo.list_active()
            assert len(records) == 1
            assert records[0].text == "我喜欢短回复"
            assert records[0].source == "manual_ui"
            assert records[0].status == MemoryRecordStatus.ACTIVE

    def test_manual_record_has_no_evidence(self) -> None:
        """Manual records do not contain evidence fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LocalJsonMemoryRepository(Path(tmpdir) / "memory.json")
            runtime = create_local_memory_runtime(repo)

            dispatched: list[BaseEvent] = []
            bus = EventBus()

            controller = MemorySuggestionController(
                runtime=runtime,
                subscribe=bus.subscribe,
                unsubscribe=bus.unsubscribe,
                dispatch_event=lambda e: dispatched.append(e),
            )
            controller.start()

            bus.publish(
                BaseEvent(
                    event_type=MEMORY_ADD_REQUESTED,
                    request_id="req-1",
                    source="test",
                    payload={"text": "test evidence field"},
                )
            )

            record = repo.list_active()[0]
            # Ensure the record dataclass has no evidence field
            assert not hasattr(record, "evidence"), "MemoryRecord should not have evidence field"
            assert not hasattr(record, "original_text"), "MemoryRecord should not have original_text field"

    def test_memory_add_blank_text_does_not_persist(self) -> None:
        """Blank text MEMORY_ADD_REQUESTED does not write to repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LocalJsonMemoryRepository(Path(tmpdir) / "memory.json")
            runtime = create_local_memory_runtime(repo)

            dispatched: list[BaseEvent] = []
            bus = EventBus()

            controller = MemorySuggestionController(
                runtime=runtime,
                subscribe=bus.subscribe,
                unsubscribe=bus.unsubscribe,
                dispatch_event=lambda e: dispatched.append(e),
            )
            controller.start()

            # Blank text
            bus.publish(
                BaseEvent(
                    event_type=MEMORY_ADD_REQUESTED,
                    request_id="req-1",
                    source="test",
                    payload={"text": "   "},
                )
            )

            # Should dispatch MEMORY_ERROR, not MEMORY_ADDED
            error_events = [e for e in dispatched if e.event_type == "memory.error"]
            assert len(error_events) == 1, f"Expected 1 error event, got {len(error_events)}"
            assert "blank" in error_events[0].payload.get("message", "").lower()

            # Repository should be empty
            assert len(repo.list_active()) == 0

    def test_multiple_manual_adds_all_persist(self) -> None:
        """Multiple manual adds result in multiple records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = LocalJsonMemoryRepository(Path(tmpdir) / "memory.json")
            runtime = create_local_memory_runtime(repo)

            bus = EventBus()
            dispatched: list[BaseEvent] = []

            controller = MemorySuggestionController(
                runtime=runtime,
                subscribe=bus.subscribe,
                unsubscribe=bus.unsubscribe,
                dispatch_event=lambda e: dispatched.append(e),
            )
            controller.start()

            bus.publish(
                BaseEvent(
                    event_type=MEMORY_ADD_REQUESTED,
                    request_id="req-1",
                    source="test",
                    payload={"text": "记忆1"},
                )
            )
            bus.publish(
                BaseEvent(
                    event_type=MEMORY_ADD_REQUESTED,
                    request_id="req-2",
                    source="test",
                    payload={"text": "记忆2"},
                )
            )
            bus.publish(
                BaseEvent(
                    event_type=MEMORY_ADD_REQUESTED,
                    request_id="req-3",
                    source="test",
                    payload={"text": "记忆3"},
                )
            )

            added_events = [e for e in dispatched if e.event_type == MEMORY_ADDED]
            assert len(added_events) == 3

            records = repo.list_active()
            assert len(records) == 3
            texts = {r.text for r in records}
            assert texts == {"记忆1", "记忆2", "记忆3"}
