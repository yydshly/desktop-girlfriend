r"""Avatar action state probe script (V10-A / V10-B).

Run locally (no Qt, no network, no LLM, no TTS, no memory):
    .venv\Scripts\python.exe scripts/probe_avatar_action.py
"""

from __future__ import annotations

from app.contracts.events import (
    CONVERSATION_CLEARED,
    PROACTIVE_NUDGE_READY,
    STATE_CHANGED,
    SYSTEM_ERROR,
    BaseEvent,
)
from app.ui.avatar_action import AvatarAction, avatar_style_for_action
from app.ui.view_model import DesktopViewModel


def main() -> None:
    """Run avatar action state probe flow."""
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    vm = DesktopViewModel()

    # 1. Initial state
    assert vm.effective_avatar_text == "☁️", f"Expected ☁️, got {vm.effective_avatar_text}"
    initial_style = vm.effective_avatar_style
    assert len(initial_style) > 0, "Initial style should be non-empty"
    print("[OK] Initial: ☁️ (style non-empty)")

    # 2. state.changed LISTENING -> 👂
    vm.handle_state_changed(
        BaseEvent(
            event_type=STATE_CHANGED,
            request_id="probe-1",
            source="probe",
            payload={"current_state": "listening"},
        )
    )
    assert vm.effective_avatar_text == "👂", f"Expected 👂, got {vm.effective_avatar_text}"
    listening_style = vm.effective_avatar_style
    assert len(listening_style) > 0, "LISTENING style should be non-empty"
    assert listening_style != initial_style, "LISTENING style should differ from IDLE"
    print("[OK] LISTENING: 👂 (style non-empty, different from IDLE)")

    # 3. state.changed THINKING -> 💭
    vm.handle_state_changed(
        BaseEvent(
            event_type=STATE_CHANGED,
            request_id="probe-2",
            source="probe",
            payload={"current_state": "thinking"},
        )
    )
    assert vm.effective_avatar_text == "💭", f"Expected 💭, got {vm.effective_avatar_text}"
    print("[OK] THINKING: 💭")

    # 4. state.changed SPEAKING -> 🗣️
    vm.handle_state_changed(
        BaseEvent(
            event_type=STATE_CHANGED,
            request_id="probe-3",
            source="probe",
            payload={"current_state": "speaking"},
        )
    )
    assert vm.effective_avatar_text == "🗣️", f"Expected 🗣️, got {vm.effective_avatar_text}"
    print("[OK] SPEAKING: 🗣️")

    # 5. proactive.nudge_ready -> ✨
    vm.handle_proactive_nudge_ready(
        BaseEvent(
            event_type=PROACTIVE_NUDGE_READY,
            request_id="probe-4",
            source="probe",
            payload={"text": "我在这儿。"},
        )
    )
    assert vm.effective_avatar_text == "✨", f"Expected ✨, got {vm.effective_avatar_text}"
    proactive_style = vm.effective_avatar_style
    assert len(proactive_style) > 0, "PROACTIVE style should be non-empty"
    assert proactive_style == avatar_style_for_action(AvatarAction.PROACTIVE)
    print("[OK] PROACTIVE: ✨ (style non-empty)")

    # 6. system.error -> ⚠️
    vm.handle_system_error(
        BaseEvent(
            event_type=SYSTEM_ERROR,
            request_id="probe-5",
            source="probe",
            payload={"message": "test error"},
        )
    )
    assert vm.effective_avatar_text == "⚠️", f"Expected ⚠️, got {vm.effective_avatar_text}"
    error_style = vm.effective_avatar_style
    assert len(error_style) > 0, "ERROR style should be non-empty"
    assert error_style == avatar_style_for_action(AvatarAction.ERROR)
    print("[OK] ERROR: ⚠️ (style non-empty)")

    # 7. conversation.cleared -> ☁️
    vm.handle_conversation_cleared(
        BaseEvent(
            event_type=CONVERSATION_CLEARED,
            request_id="probe-6",
            source="probe",
            payload={},
        )
    )
    assert vm.effective_avatar_text == "☁️", f"Expected ☁️, got {vm.effective_avatar_text}"
    print("[OK] CLEARED: ☁️")

    print("PASS")


if __name__ == "__main__":
    main()
