r"""Proactive avatar routing probe script (V10-C).

Run locally (no Qt, no network, no LLM, no TTS, no memory):
    .venv\Scripts\python.exe scripts/probe_proactive_avatar_routing.py
"""

from __future__ import annotations

from app.contracts.events import (
    PROACTIVE_NUDGE_READY,
    BaseEvent,
)
from app.ui.avatar_action import AvatarAction
from app.ui.view_model import DesktopViewModel


def main() -> None:
    """Run proactive avatar routing probe flow."""
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    vm = DesktopViewModel()

    # 1. Initial state
    assert vm.effective_avatar_text == "☁️", f"Expected ☁️, got {vm.effective_avatar_text}"
    assert len(vm.chat_messages) == 0, "chat_messages should be empty initially"
    print("[OK] Initial: ☁️, chat_messages empty")

    # 2. Call handle_proactive_avatar_hint
    event = BaseEvent(
        event_type=PROACTIVE_NUDGE_READY,
        request_id="probe-1",
        source="probe",
        payload={"text": "我在这儿。"},
    )
    vm.handle_proactive_avatar_hint(event)

    # 3. Confirm effective_avatar_text == ✨
    assert vm.effective_avatar_text == "✨", f"Expected ✨, got {vm.effective_avatar_text}"
    assert vm.avatar_action == AvatarAction.PROACTIVE, f"Expected PROACTIVE, got {vm.avatar_action}"
    print("[OK] handle_proactive_avatar_hint: avatar_action=PROACTIVE, effective_avatar_text=✨")

    # 4. Confirm chat_messages still empty
    assert len(vm.chat_messages) == 0, f"Expected 0 chat_messages, got {len(vm.chat_messages)}"
    print("[OK] handle_proactive_avatar_hint: chat_messages still empty")

    # 5. Call handle_proactive_nudge_ready
    vm.handle_proactive_nudge_ready(event)

    # 6. Confirm chat_messages increased by 1
    assert len(vm.chat_messages) == 1, f"Expected 1 chat_message, got {len(vm.chat_messages)}"
    assert vm.chat_messages[0].role == "assistant"
    assert vm.chat_messages[0].text == "我在这儿。"
    print("[OK] handle_proactive_nudge_ready: chat_messages increased by 1")

    # 7. Avatar should still be PROACTIVE
    assert vm.avatar_action == AvatarAction.PROACTIVE, f"Expected PROACTIVE, got {vm.avatar_action}"
    assert vm.effective_avatar_text == "✨", f"Expected ✨, got {vm.effective_avatar_text}"
    print("[OK] Avatar still PROACTIVE after handle_proactive_nudge_ready")

    print("PASS")


if __name__ == "__main__":
    main()
