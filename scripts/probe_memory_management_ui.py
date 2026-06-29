"""Probe script for V8-J Memory Management UI.

This script validates the ViewModel memory management handlers without
starting a real Qt app, writing files, networking, calling LLM, or using microphone.
"""

from app.contracts.events import (
    MEMORY_DELETED,
    MEMORY_LISTED,
    BaseEvent,
)
from app.ui.view_model import DesktopViewModel


def main() -> None:
    print("Memory Management UI Probe")
    print("=" * 40)

    vm = DesktopViewModel()

    # Step 1-4: Create MEMORY_LISTED event with 2 records and verify
    event_listed = BaseEvent(
        event_type=MEMORY_LISTED,
        request_id="probe-1",
        source="probe",
        payload={
            "records": [
                {
                    "record_id": "record-001",
                    "kind": "preference",
                    "importance": "medium",
                    "text": "用户喜欢你回复短一点。",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                },
                {
                    "record_id": "record-002",
                    "kind": "identity",
                    "importance": "high",
                    "text": "用户名字是小明。",
                    "created_at": "2024-01-02T00:00:00",
                    "updated_at": "2024-01-02T00:00:00",
                },
            ]
        },
    )
    vm.handle_memory_listed(event_listed)

    records_after_listed = len(vm.memory_records)
    print(f"records_after_listed={records_after_listed}")

    # Step 5-7: Create MEMORY_DELETED event for first record and verify
    event_deleted = BaseEvent(
        event_type=MEMORY_DELETED,
        request_id="probe-2",
        source="probe",
        payload={"record_id": "record-001"},
    )
    vm.handle_memory_deleted(event_deleted)

    records_after_deleted = len(vm.memory_records)
    print(f"records_after_deleted={records_after_deleted}")

    # Step 8-9: Toggle panel and verify
    vm.toggle_memory_panel()
    visible_after_toggle = vm.memory_panel_visible
    print(f"visible_after_toggle={visible_after_toggle}")

    vm.toggle_memory_panel()
    visible_after_toggle_back = vm.memory_panel_visible
    print(f"visible_after_toggle_back={visible_after_toggle_back}")

    print()

    # Verify all checks passed
    # Note: handle_memory_listed sets panel_visible=True, so:
    # - First toggle: True -> False
    # - Second toggle: False -> True
    all_passed = (
        records_after_listed == 2
        and records_after_deleted == 1
        and visible_after_toggle is False
        and visible_after_toggle_back is True
    )

    if all_passed:
        print("PASS")
    else:
        print("FAIL")
        print(
            "Expected: records_after_listed=2, records_after_deleted=1, "
            "visible_after_toggle=False, visible_after_toggle_back=True"
        )


if __name__ == "__main__":
    main()
