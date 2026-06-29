"""Probe script for V8-I Memory Suggestion UI.

This script validates the ViewModel memory suggestion handlers without
starting a real Qt app, writing files, networking, calling LLM, or using microphone.
"""

from app.contracts.events import (
    MEMORY_CONFIRMED,
    MEMORY_REJECTED,
    MEMORY_SUGGESTIONS_DETECTED,
    BaseEvent,
)
from app.ui.view_model import DesktopViewModel


def main() -> None:
    print("Memory Suggestion UI Probe")
    print("=" * 40)

    vm = DesktopViewModel()

    # Step 1-4: Create MEMORY_SUGGESTIONS_DETECTED event and verify suggestion stored
    event_detected = BaseEvent(
        event_type=MEMORY_SUGGESTIONS_DETECTED,
        request_id="probe-1",
        source="probe",
        payload={
            "suggestions": [
                {
                    "pending_id": "pending-probe-001",
                    "kind": "preference",
                    "importance": "medium",
                    "text": "用户喜欢你回复短一点。",
                }
            ]
        },
    )
    vm.handle_memory_suggestions_detected(event_detected)

    suggestion_visible_after_detected = 1 if vm.memory_suggestion is not None else 0
    print(f"suggestion_visible_after_detected={suggestion_visible_after_detected}")

    # Step 5-7: Construct MEMORY_CONFIRMED event and verify suggestion cleared
    event_confirmed = BaseEvent(
        event_type=MEMORY_CONFIRMED,
        request_id="probe-2",
        source="probe",
        payload={},
    )
    vm.handle_memory_confirmed(event_confirmed)

    suggestion_visible_after_confirmed = 1 if vm.memory_suggestion is not None else 0
    print(f"suggestion_visible_after_confirmed={suggestion_visible_after_confirmed}")

    # Step 8-9: Create another suggestion
    event_detected_2 = BaseEvent(
        event_type=MEMORY_SUGGESTIONS_DETECTED,
        request_id="probe-3",
        source="probe",
        payload={
            "suggestions": [
                {
                    "pending_id": "pending-probe-002",
                    "kind": "identity",
                    "importance": "high",
                    "text": "用户名字是小明。",
                }
            ]
        },
    )
    vm.handle_memory_suggestions_detected(event_detected_2)

    # Step 10-12: Construct MEMORY_REJECTED event and verify suggestion cleared
    event_rejected = BaseEvent(
        event_type=MEMORY_REJECTED,
        request_id="probe-4",
        source="probe",
        payload={},
    )
    vm.handle_memory_rejected(event_rejected)

    suggestion_visible_after_rejected = 1 if vm.memory_suggestion is not None else 0
    print(f"suggestion_visible_after_rejected={suggestion_visible_after_rejected}")

    print()

    # Verify all checks passed
    all_passed = (
        suggestion_visible_after_detected == 1
        and suggestion_visible_after_confirmed == 0
        and suggestion_visible_after_rejected == 0
    )

    if all_passed:
        print("PASS")
    else:
        print("FAIL")
        print(
            "Expected: suggestion_visible_after_detected=1, "
            "suggestion_visible_after_confirmed=0, "
            "suggestion_visible_after_rejected=0"
        )


if __name__ == "__main__":
    main()
