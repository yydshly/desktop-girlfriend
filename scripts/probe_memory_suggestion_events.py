"""Probe script for memory suggestion events (V8-H).

Verifies:
1. USER_TEXT_SUBMITTED generates pending memories
2. MEMORY_SUGGESTIONS_DETECTED event is emitted
3. MEMORY_CONFIRM_REQUESTED persists record
4. MEMORY_CONFIRMED event is emitted
5. MEMORY_REJECT_REQUESTED rejects without persisting
6. MEMORY_REJECTED event is emitted
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.brain.memory.controller import MemorySuggestionController
from app.brain.memory.repository import LocalJsonMemoryRepository
from app.brain.memory.runtime import create_local_memory_runtime
from app.contracts.events import (
    BaseEvent,
    MEMORY_CONFIRM_REQUESTED,
    MEMORY_CONFIRMED,
    MEMORY_REJECT_REQUESTED,
    MEMORY_REJECTED,
    MEMORY_SUGGESTIONS_DETECTED,
    USER_TEXT_SUBMITTED,
)


def _make_event(event_type: str, payload: dict[str, Any]) -> BaseEvent:
    """Create a BaseEvent for testing."""
    return BaseEvent(
        event_type=event_type,
        request_id="probe-req-1",
        source="probe",
        payload=payload,
    )


def main() -> None:
    print("Memory Suggestion Event Probe\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "memory_probe.json"
        repository = LocalJsonMemoryRepository(json_path)
        runtime = create_local_memory_runtime(repository)

        # Track dispatched events
        dispatched_events: list[BaseEvent] = []

        def capture_dispatch(event: BaseEvent) -> None:
            dispatched_events.append(event)

        controller = MemorySuggestionController(
            runtime=runtime,
            subscribe=lambda _et, _h: None,
            unsubscribe=lambda _et, _h: None,
            dispatch_event=capture_dispatch,
        )
        controller.start()

        # Step 1: Submit text that generates a preference memory candidate
        event1 = _make_event(USER_TEXT_SUBMITTED, {"text": "我喜欢你回复短一点。"})
        controller._on_user_text_submitted(event1)

        suggestions_1 = [
            e for e in dispatched_events
            if e.event_type == MEMORY_SUGGESTIONS_DETECTED
        ]
        if not suggestions_1:
            raise AssertionError("No suggestions detected for first text")

        first_suggestion = suggestions_1[0].payload["suggestions"][0]
        pending_id_confirm = first_suggestion["pending_id"]

        # Step 2: Submit text with boundary trigger
        event2 = _make_event(
            USER_TEXT_SUBMITTED, {"text": "我女朋友叫红红，这件事不要记住。"}
        )
        controller._on_user_text_submitted(event2)

        all_suggestions = [
            e for e in dispatched_events
            if e.event_type == MEMORY_SUGGESTIONS_DETECTED
        ]
        # Count total suggestions detected
        total_suggestions = sum(
            len(e.payload.get("suggestions", [])) for e in all_suggestions
        )

        # Get boundary pending_id for rejection
        boundary_pending_id: str | None = None
        for evt in all_suggestions:
            for s in evt.payload.get("suggestions", []):
                if s["kind"] == "boundary":
                    boundary_pending_id = s["pending_id"]
                    break

        # Step 3: Confirm the first pending
        confirm_event = _make_event(
            MEMORY_CONFIRM_REQUESTED, {"pending_id": pending_id_confirm}
        )
        controller._on_memory_confirm_requested(confirm_event)

        confirmed_count = sum(
            1 for e in dispatched_events if e.event_type == MEMORY_CONFIRMED
        )

        # Step 4: Reject boundary pending if found
        rejected_count = 0
        if boundary_pending_id:
            reject_event = _make_event(
                MEMORY_REJECT_REQUESTED, {"pending_id": boundary_pending_id}
            )
            controller._on_memory_reject_requested(reject_event)
            rejected_count = sum(
                1 for e in dispatched_events if e.event_type == MEMORY_REJECTED
            )

        # Check active records
        active_records = len(repository.list_active())

        controller.stop()

        print(f"suggestions_detected={total_suggestions}")
        print(f"confirmed={confirmed_count}")
        print(f"rejected={rejected_count}")
        print(f"active_records={active_records}")

        # Assertions
        assert total_suggestions >= 1, f"Should detect at least 1 suggestion, got {total_suggestions}"
        assert confirmed_count == 1, f"Should have 1 confirmed, got {confirmed_count}"
        assert rejected_count == 1, f"Should have 1 rejected, got {rejected_count}"
        assert active_records == 1, f"Should have 1 active record, got {active_records}"

        # Verify "红红" does not appear in output (sensitive name)
        output = "\n".join(str(e.payload) for e in dispatched_events)
        assert "红红" not in output, "Should not print sensitive text '红红'"

        print("\nPASS")


if __name__ == "__main__":
    main()
