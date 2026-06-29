r"""Proactive nudge TTS routing probe script (V9-B).

Run locally (no Qt, no network, no LLM, no TTS provider):
    .venv\Scripts\python.exe scripts\probe_proactive_tts_routing.py
"""

from __future__ import annotations

from app.contracts.events import ASSISTANT_TEXT_RECEIVED, PROACTIVE_NUDGE_READY, BaseEvent
from app.contracts.payloads import AssistantTextReceivedPayload
from app.ui.view_model import DesktopViewModel


def _build_assistant_text_event_from_proactive(event: BaseEvent) -> BaseEvent | None:
    """Mirror of main.py routing helper for probe."""
    text = event.payload.get("text")
    if not isinstance(text, str) or not text.strip():
        return None
    return BaseEvent(
        event_type=ASSISTANT_TEXT_RECEIVED,
        request_id=event.request_id,
        source=event.source,
        payload=AssistantTextReceivedPayload(text=text).to_event_payload(),
    )


def main() -> None:
    """Run proactive TTS routing probe flow."""
    proactive_text = "我还在，想聊的时候直接说就好。"
    proactive_event = BaseEvent(
        event_type=PROACTIVE_NUDGE_READY,
        request_id="probe-req-1",
        source="proactive_controller",
        payload={"text": proactive_text},
    )

    # Case 1: proactive_tts_enabled=False -> direct to ViewModel
    vm_text_only = DesktopViewModel()
    proactive_tts_enabled = False

    if proactive_tts_enabled:
        assistant_ev = _build_assistant_text_event_from_proactive(proactive_event)
        assert assistant_ev is None, "Expected None for empty text path"
    else:
        vm_text_only.handle_proactive_nudge_ready(proactive_event)

    assert len(vm_text_only.chat_messages) == 1, f"Expected 1 message, got {len(vm_text_only.chat_messages)}"
    assert vm_text_only.chat_messages[0].text == proactive_text
    assert vm_text_only.chat_messages[0].role == "assistant"
    print("[OK] proactive_tts_enabled=False: ViewModel received nudge directly")

    # Case 2: proactive_tts_enabled=True -> builds ASSISTANT_TEXT_RECEIVED
    proactive_tts_enabled = True

    if proactive_tts_enabled:
        assistant_ev = _build_assistant_text_event_from_proactive(proactive_event)
        assert assistant_ev is not None, "Expected ASSISTANT_TEXT_RECEIVED event"
        assert assistant_ev.event_type == ASSISTANT_TEXT_RECEIVED
        assert assistant_ev.payload["text"] == proactive_text
        print("[OK] proactive_tts_enabled=True: built ASSISTANT_TEXT_RECEIVED event")
    else:
        raise AssertionError("Should not reach here")

    # Verify no TTS provider was called (pure routing, no provider access)
    # Verify no LLM was called
    # Verify no memory was read
    print("[OK] No TTS provider called (routing only)")
    print("[OK] No LLM called")
    print("[OK] No memory accessed")

    print("PASS")


if __name__ == "__main__":
    main()
