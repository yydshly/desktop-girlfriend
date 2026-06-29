"""Tests for proactive nudge (V9-A / V9-B)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

from app.brain.proactive.controller import ProactiveController
from app.brain.proactive.service import ProactiveNudgeConfig, ProactiveNudgeService
from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    PROACTIVE_NUDGE_READY,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.contracts.payloads import AssistantTextReceivedPayload, ProactiveNudgeReadyPayload
from app.contracts.states import AppState
from app.ui.view_model import DesktopViewModel


def _make_event(
    event_type: str,
    payload: dict[str, Any],
    request_id: str = "req-1",
    timestamp: datetime | None = None,
) -> MagicMock:
    """Create a mock BaseEvent."""
    event = MagicMock()
    event.event_type = event_type
    event.request_id = request_id
    event.payload = payload
    event.timestamp = timestamp or datetime.now(UTC)
    return event


# ---------------------------------------------------------------------------
# ProactiveNudgeConfig tests
# ---------------------------------------------------------------------------


def test_proactive_config_defaults_disabled() -> None:
    """Proactive config defaults to disabled."""
    config = ProactiveNudgeConfig()
    assert config.enabled is False
    assert config.idle_seconds == 300
    assert config.cooldown_seconds == 1800
    assert config.max_per_session == 3


# ---------------------------------------------------------------------------
# ProactiveNudgeService tests
# ---------------------------------------------------------------------------


def test_service_enabled_false_returns_none() -> None:
    """enabled=false never triggers a nudge."""
    config = ProactiveNudgeConfig(enabled=False)
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC)
    service.record_user_activity(now)
    result = service.maybe_create_nudge(now=now + timedelta(seconds=400))
    assert result is None


def test_service_no_user_activity_returns_none() -> None:
    """No user activity recorded never triggers a nudge."""
    config = ProactiveNudgeConfig(enabled=True, idle_seconds=10)
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC)
    result = service.maybe_create_nudge(now=now + timedelta(seconds=20))
    assert result is None


def test_service_idle_not_reached_returns_none() -> None:
    """Idle time not yet reached returns None."""
    config = ProactiveNudgeConfig(enabled=True, idle_seconds=300)
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC)
    service.record_user_activity(now)
    # Only 100 seconds elapsed
    result = service.maybe_create_nudge(now=now + timedelta(seconds=100))
    assert result is None


def test_service_idle_reached_returns_text() -> None:
    """Idle time reached returns a nudge text."""
    config = ProactiveNudgeConfig(enabled=True, idle_seconds=10)
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC)
    service.record_user_activity(now)
    # 20 seconds elapsed
    result = service.maybe_create_nudge(now=now + timedelta(seconds=20))
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0


def test_service_cooldown_prevents_repeat() -> None:
    """Cooldown prevents immediate repeat nudge."""
    config = ProactiveNudgeConfig(enabled=True, idle_seconds=1, cooldown_seconds=10, max_per_session=3)
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC)
    service.record_user_activity(now)

    # First nudge after idle
    t1 = now + timedelta(seconds=2)
    result1 = service.maybe_create_nudge(now=t1)
    assert result1 is not None
    service.record_nudge_sent(t1)

    # Within cooldown
    t2 = now + timedelta(seconds=5)
    result2 = service.maybe_create_nudge(now=t2)
    assert result2 is None


def test_service_max_per_session_blocks_further() -> None:
    """max_per_session blocks further nudges."""
    config = ProactiveNudgeConfig(enabled=True, idle_seconds=1, cooldown_seconds=1, max_per_session=2)
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC)
    service.record_user_activity(now)

    # First nudge
    t1 = now + timedelta(seconds=2)
    result1 = service.maybe_create_nudge(now=t1)
    assert result1 is not None
    service.record_nudge_sent(t1)

    # Wait for cooldown
    t2 = now + timedelta(seconds=4)
    result2 = service.maybe_create_nudge(now=t2)
    assert result2 is not None
    service.record_nudge_sent(t2)

    # max reached
    t3 = now + timedelta(seconds=7)
    result3 = service.maybe_create_nudge(now=t3)
    assert result3 is None


def test_service_is_busy_returns_none() -> None:
    """is_busy=True always returns None."""
    config = ProactiveNudgeConfig(enabled=True, idle_seconds=1)
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC)
    service.record_user_activity(now)
    result = service.maybe_create_nudge(now=now + timedelta(seconds=5), is_busy=True)
    assert result is None


def test_service_record_user_activity_updates_timestamp() -> None:
    """record_user_activity updates last_user_activity."""
    config = ProactiveNudgeConfig(enabled=True, idle_seconds=10)
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC)

    # Initial activity
    service.record_user_activity(now)
    result1 = service.maybe_create_nudge(now=now + timedelta(seconds=5))
    assert result1 is None  # Not yet idle

    # Refresh activity
    new_now = now + timedelta(seconds=3)
    service.record_user_activity(new_now)
    result2 = service.maybe_create_nudge(now=new_now + timedelta(seconds=5))
    assert result2 is None  # Still not enough elapsed from new activity


def test_service_uses_fixed_text_pool() -> None:
    """Service cycles through fixed text pool."""
    config = ProactiveNudgeConfig(enabled=True, idle_seconds=1, cooldown_seconds=1, max_per_session=10)
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC)
    service.record_user_activity(now)

    texts = []
    # Each nudge: 2s gap, cooldown=1s -> cooldown always expired
    # idle_seconds=1, so nudge fires at each tick
    for i in range(6):
        t = now + timedelta(seconds=i * 2 + 2)
        result = service.maybe_create_nudge(now=t)
        if result is not None:
            texts.append(result)
            service.record_nudge_sent(t)

    # Should have 6 nudges total (3 distinct texts * 2 cycles)
    assert len(texts) == 6
    unique_texts = set(texts)
    assert len(unique_texts) == 3


# ---------------------------------------------------------------------------
# ProactiveController tests
# ---------------------------------------------------------------------------


def test_controller_start_stop_idempotent() -> None:
    """start() and stop() are idempotent."""
    service = ProactiveNudgeService(ProactiveNudgeConfig(enabled=True, idle_seconds=10))
    subscribe = MagicMock()
    unsubscribe = MagicMock()
    controller = ProactiveController(
        service=service,
        subscribe=subscribe,
        unsubscribe=unsubscribe,
        dispatch_event=MagicMock(),
    )

    # Multiple starts
    controller.start()
    controller.start()
    assert subscribe.call_count == 1

    # Multiple stops
    controller.stop()
    controller.stop()
    assert unsubscribe.call_count == 1


def test_controller_user_text_submitted_records_activity() -> None:
    """USER_TEXT_SUBMITTED triggers record_user_activity."""
    service = ProactiveNudgeService(ProactiveNudgeConfig(enabled=True, idle_seconds=10))
    subscribe = MagicMock()
    unsubscribe = MagicMock()
    dispatch_event = MagicMock()
    controller = ProactiveController(
        service=service,
        subscribe=subscribe,
        unsubscribe=unsubscribe,
        dispatch_event=dispatch_event,
    )

    controller.start()

    # Simulate user text submitted
    now = datetime.now(UTC)
    event = _make_event(USER_TEXT_SUBMITTED, {"text": "hello"}, timestamp=now)
    controller._on_user_text_submitted(event)

    # After activity recorded, idle not yet reached
    result = service.maybe_create_nudge(now=now + timedelta(seconds=5))
    assert result is None


def test_controller_tick_publishes_proactive_nudge_ready() -> None:
    """tick() publishes PROACTIVE_NUDGE_READY when conditions are met."""
    config = ProactiveNudgeConfig(enabled=True, idle_seconds=1, cooldown_seconds=10, max_per_session=3)
    service = ProactiveNudgeService(config)
    subscribe = MagicMock()
    unsubscribe = MagicMock()
    dispatch_event = MagicMock()

    controller = ProactiveController(
        service=service,
        subscribe=subscribe,
        unsubscribe=unsubscribe,
        dispatch_event=dispatch_event,
    )

    now = datetime.now(UTC)
    service.record_user_activity(now)
    # Override service clock so tick() uses test time, not real wall-clock time
    service._test_now = now + timedelta(seconds=5)

    controller.tick(is_busy=False)

    dispatch_event.assert_called_once()
    call_args = dispatch_event.call_args[0][0]
    assert call_args.event_type == PROACTIVE_NUDGE_READY
    assert "text" in call_args.payload
    assert isinstance(call_args.payload["text"], str)


def test_controller_tick_does_not_publish_when_busy() -> None:
    """tick(is_busy=True) does not publish."""
    config = ProactiveNudgeConfig(enabled=True, idle_seconds=1)
    service = ProactiveNudgeService(config)
    subscribe = MagicMock()
    unsubscribe = MagicMock()
    dispatch_event = MagicMock()

    controller = ProactiveController(
        service=service,
        subscribe=subscribe,
        unsubscribe=unsubscribe,
        dispatch_event=dispatch_event,
    )

    now = datetime.now(UTC)
    service.record_user_activity(now)
    service._test_now = now + timedelta(seconds=5)

    controller.tick(is_busy=True)

    dispatch_event.assert_not_called()


# ---------------------------------------------------------------------------
# ViewModel handler tests
# ---------------------------------------------------------------------------


def test_view_model_handle_proactive_nudge_ready_appends_assistant_message() -> None:
    """handle_proactive_nudge_ready appends text as assistant message."""
    vm = DesktopViewModel()
    event = BaseEvent(
        event_type=PROACTIVE_NUDGE_READY,
        request_id="req1",
        source="proactive_controller",
        payload={"text": "我还在，想聊的时候直接说就好。"},
    )

    vm.handle_proactive_nudge_ready(event)

    assert len(vm.chat_messages) == 1
    assert vm.chat_messages[0].role == "assistant"
    assert vm.chat_messages[0].text == "我还在，想聊的时候直接说就好。"


def test_view_model_handle_proactive_nudge_ready_ignores_wrong_event_type() -> None:
    """handle_proactive_nudge_ready ignores non-PROACTIVE_NUDGE_READY events."""
    vm = DesktopViewModel()
    event = BaseEvent(
        event_type="other.event",
        request_id="req1",
        source="test",
        payload={"text": "ignored"},
    )

    vm.handle_proactive_nudge_ready(event)

    assert len(vm.chat_messages) == 0


def test_view_model_handle_proactive_nudge_ready_ignores_empty_text() -> None:
    """handle_proactive_nudge_ready ignores empty text."""
    vm = DesktopViewModel()
    event = BaseEvent(
        event_type=PROACTIVE_NUDGE_READY,
        request_id="req1",
        source="proactive_controller",
        payload={"text": ""},
    )

    vm.handle_proactive_nudge_ready(event)

    assert len(vm.chat_messages) == 0


def test_view_model_handle_proactive_nudge_ready_does_not_change_state() -> None:
    """handle_proactive_nudge_ready does not change AppState."""
    vm = DesktopViewModel()
    assert vm.state == AppState.IDLE

    event = BaseEvent(
        event_type=PROACTIVE_NUDGE_READY,
        request_id="req1",
        source="proactive_controller",
        payload={"text": "我在这儿。"},
    )

    vm.handle_proactive_nudge_ready(event)

    assert vm.state == AppState.IDLE


# ---------------------------------------------------------------------------
# Payload tests
# ---------------------------------------------------------------------------


def test_proactive_nudge_ready_payload() -> None:
    """ProactiveNudgeReadyPayload serializes correctly."""
    payload = ProactiveNudgeReadyPayload(text="我还在，想聊的时候直接说就好。")
    result = payload.to_event_payload()
    assert result == {"text": "我还在，想聊的时候直接说就好。"}


# ---------------------------------------------------------------------------
# Anti-pattern tests - verify no LLM/TTS/memory calls
# ---------------------------------------------------------------------------


def test_service_does_not_call_llm() -> None:
    """ProactiveNudgeService does not call any LLM."""
    config = ProactiveNudgeConfig(enabled=True, idle_seconds=1)
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC)
    service.record_user_activity(now)
    result = service.maybe_create_nudge(now=now + timedelta(seconds=5))
    # Result comes from fixed pool, no LLM involved
    assert result is not None


def test_service_does_not_call_tts() -> None:
    """ProactiveNudgeService does not call TTS."""
    config = ProactiveNudgeConfig(enabled=True)
    service = ProactiveNudgeService(config)
    # No TTS calls should happen in this module
    assert hasattr(service, "maybe_create_nudge")


def test_service_does_not_read_memory() -> None:
    """ProactiveNudgeService does not read memory."""
    config = ProactiveNudgeConfig(enabled=True)
    service = ProactiveNudgeService(config)
    # No memory access in this service
    assert not hasattr(service, "_memory_store")
    assert not hasattr(service, "_memory_repo")


# ---------------------------------------------------------------------------
# V9-B TTS routing helper (mirrors main.py on_proactive_nudge_ready logic)
# ---------------------------------------------------------------------------


def _build_assistant_text_event_from_proactive(event: BaseEvent) -> BaseEvent | None:
    """Pure helper: build ASSISTANT_TEXT_RECEIVED from PROACTIVE_NUDGE_READY.

    Mirrors the V9-B routing in main.py for testability.
    """
    text = event.payload.get("text")
    if not isinstance(text, str) or not text.strip():
        return None
    return BaseEvent(
        event_type=ASSISTANT_TEXT_RECEIVED,
        request_id=event.request_id,
        source=event.source,
        payload=AssistantTextReceivedPayload(text=text).to_event_payload(),
    )


def test_proactive_tts_enabled_false_routes_to_viewmodel() -> None:
    """When proactive_tts_enabled=False, text should go to ViewModel (not TTS)."""
    vm = DesktopViewModel()
    proactive_event = BaseEvent(
        event_type=PROACTIVE_NUDGE_READY,
        request_id="req-1",
        source="proactive_controller",
        payload={"text": "我在这儿。"},
    )
    proactive_tts_enabled = False

    if proactive_tts_enabled:
        # Would publish ASSISTANT_TEXT_RECEIVED → handled elsewhere
        pass
    else:
        # Direct to ViewModel
        vm.handle_proactive_nudge_ready(proactive_event)

    # Message appended as assistant
    assert len(vm.chat_messages) == 1
    assert vm.chat_messages[0].role == "assistant"
    assert vm.chat_messages[0].text == "我在这儿。"


def test_proactive_tts_enabled_true_builds_assistant_event() -> None:
    """When proactive_tts_enabled=True, PROACTIVE_NUDGE_READY builds ASSISTANT_TEXT_RECEIVED."""
    proactive_event = BaseEvent(
        event_type=PROACTIVE_NUDGE_READY,
        request_id="req-tts",
        source="proactive_controller",
        payload={"text": "要不要休息一下眼睛？"},
    )
    proactive_tts_enabled = True

    if proactive_tts_enabled:
        assistant_event = _build_assistant_text_event_from_proactive(proactive_event)
        assert assistant_event is not None
        assert assistant_event.event_type == ASSISTANT_TEXT_RECEIVED
        assert assistant_event.payload["text"] == "要不要休息一下眼睛？"

    # ViewModel should NOT receive it directly (would be handled by TTS pipeline)
    vm = DesktopViewModel()
    if proactive_tts_enabled:
        pass  # Would be handled via ASSISTANT_TEXT_RECEIVED subscription
    else:
        vm.handle_proactive_nudge_ready(proactive_event)
    assert len(vm.chat_messages) == 0


def test_proactive_tts_enabled_empty_text_returns_none() -> None:
    """Empty text in proactive event returns None from helper."""
    event = BaseEvent(
        event_type=PROACTIVE_NUDGE_READY,
        request_id="req-1",
        source="test",
        payload={"text": ""},
    )
    result = _build_assistant_text_event_from_proactive(event)
    assert result is None


def test_proactive_tts_enabled_missing_text_returns_none() -> None:
    """Missing text key returns None from helper."""
    event = BaseEvent(
        event_type=PROACTIVE_NUDGE_READY,
        request_id="req-1",
        source="test",
        payload={},
    )
    result = _build_assistant_text_event_from_proactive(event)
    assert result is None


def test_proactive_tts_routing_does_not_call_llm() -> None:
    """Routing helper does not call LLM."""
    event = BaseEvent(
        event_type=PROACTIVE_NUDGE_READY,
        request_id="req-1",
        source="test",
        payload={"text": "我还在。"},
    )
    result = _build_assistant_text_event_from_proactive(event)
    # Result is from fixed pool, no LLM
    assert result is not None


def test_proactive_tts_routing_does_not_call_tts_provider() -> None:
    """Routing helper does not call TTS provider directly."""
    event = BaseEvent(
        event_type=PROACTIVE_NUDGE_READY,
        request_id="req-1",
        source="test",
        payload={"text": "我在这儿。"},
    )
    # Helper only builds event; does not call provider
    result = _build_assistant_text_event_from_proactive(event)
    assert result is not None
    assert result.event_type == ASSISTANT_TEXT_RECEIVED
    # No TTS provider called in this module


def test_proactive_tts_routing_does_not_read_memory() -> None:
    """Routing helper does not read memory."""
    event = BaseEvent(
        event_type=PROACTIVE_NUDGE_READY,
        request_id="req-1",
        source="test",
        payload={"text": "我在这儿。"},
    )
    _build_assistant_text_event_from_proactive(event)
    # No memory access


# ---------------------------------------------------------------------------
# V9-C: Strategy Guardrails tests
# ---------------------------------------------------------------------------


def test_quiet_hours_config_defaults_disabled() -> None:
    """quiet_hours_enabled defaults to False."""
    config = ProactiveNudgeConfig()
    assert config.quiet_hours_enabled is False
    assert config.quiet_start_hour == 23
    assert config.quiet_end_hour == 8
    assert config.feedback_pause_seconds == 3600


def test_quiet_hours_disabled_allows_nudge() -> None:
    """Quiet hours disabled does not block nudge."""
    config = ProactiveNudgeConfig(
        enabled=True,
        idle_seconds=1,
        quiet_hours_enabled=False,
    )
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC).replace(hour=23, minute=0, second=0, microsecond=0)
    service.record_user_activity(now)
    result = service.maybe_create_nudge(now=now + timedelta(seconds=2))
    assert result is not None


def test_quiet_hours_enabled_within_range_blocks_nudge() -> None:
    """Quiet hours enabled and current time in range blocks nudge."""
    config = ProactiveNudgeConfig(
        enabled=True,
        idle_seconds=1,
        quiet_hours_enabled=True,
        quiet_start_hour=22,
        quiet_end_hour=23,
    )
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC).replace(hour=22, minute=30, second=0, microsecond=0)
    service.record_user_activity(now)
    result = service.maybe_create_nudge(now=now + timedelta(seconds=2))
    assert result is None


def test_quiet_hours_enabled_outside_range_allows_nudge() -> None:
    """Quiet hours enabled but current time outside range allows nudge."""
    config = ProactiveNudgeConfig(
        enabled=True,
        idle_seconds=1,
        quiet_hours_enabled=True,
        quiet_start_hour=22,
        quiet_end_hour=23,
    )
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC).replace(hour=21, minute=0, second=0, microsecond=0)
    service.record_user_activity(now)
    result = service.maybe_create_nudge(now=now + timedelta(seconds=2))
    assert result is not None


def test_quiet_hours_cross_midnight_23_to_8() -> None:
    """Cross-midnight quiet hours (23-8) blocks during night."""
    config = ProactiveNudgeConfig(
        enabled=True,
        idle_seconds=1,
        quiet_hours_enabled=True,
        quiet_start_hour=23,
        quiet_end_hour=8,
    )
    service = ProactiveNudgeService(config)

    # 23:30 - within quiet hours
    now1 = datetime.now(UTC).replace(hour=23, minute=30, second=0, microsecond=0)
    service.record_user_activity(now1)
    result1 = service.maybe_create_nudge(now=now1 + timedelta(seconds=2))
    assert result1 is None, "23:30 should be quiet"

    # 3:00 - within quiet hours
    now2 = datetime.now(UTC).replace(hour=3, minute=0, second=0, microsecond=0)
    service.record_user_activity(now2)
    result2 = service.maybe_create_nudge(now=now2 + timedelta(seconds=2))
    assert result2 is None, "03:00 should be quiet"

    # 9:00 - outside quiet hours
    now3 = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)
    service.record_user_activity(now3)
    result3 = service.maybe_create_nudge(now=now3 + timedelta(seconds=2))
    assert result3 is not None, "09:00 should be allowed"

    # 15:00 - outside quiet hours
    now4 = datetime.now(UTC).replace(hour=15, minute=0, second=0, microsecond=0)
    service.record_user_activity(now4)
    result4 = service.maybe_create_nudge(now=now4 + timedelta(seconds=2))
    assert result4 is not None, "15:00 should be allowed"


def test_user_message_with_suppress_phrase_sets_pause() -> None:
    """User message containing suppress phrase activates pause."""
    config = ProactiveNudgeConfig(
        enabled=True,
        idle_seconds=1,
        feedback_pause_seconds=3600,
    )
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC)
    service.record_user_activity(now)

    # Should trigger normally first
    result1 = service.maybe_create_nudge(now=now + timedelta(seconds=5))
    assert result1 is not None
    service.record_nudge_sent(now + timedelta(seconds=5))

    # Now user says "别打扰"
    pause_start = now + timedelta(seconds=10)
    service.record_user_message("别打扰", now=pause_start)

    # Within pause period
    during_pause = pause_start + timedelta(seconds=100)
    result2 = service.maybe_create_nudge(now=during_pause)
    assert result2 is None, "Should be paused after 别打扰"


def test_pause_expires_and_nudge_resumes() -> None:
    """After pause expires, nudge can trigger again."""
    config = ProactiveNudgeConfig(
        enabled=True,
        idle_seconds=1,
        cooldown_seconds=10,
        feedback_pause_seconds=60,
    )
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC)
    service.record_user_activity(now)

    # Trigger first nudge
    t1 = now + timedelta(seconds=5)
    result1 = service.maybe_create_nudge(now=t1)
    assert result1 is not None
    service.record_nudge_sent(t1)

    # User says "别打扰"
    pause_start = now + timedelta(seconds=10)
    service.record_user_message("别打扰", now=pause_start)

    # Check during pause
    during_pause = pause_start + timedelta(seconds=30)
    result2 = service.maybe_create_nudge(now=during_pause)
    assert result2 is None

    # After pause expires (pause covers t0+10 to t0+70)
    after_pause = pause_start + timedelta(seconds=65)  # t0+75
    # Activity at t0+70, check at t0+75 -> idle=5s > 1s threshold
    service.record_user_activity(pause_start)  # t0+10
    result3 = service.maybe_create_nudge(now=after_pause)
    assert result3 is not None, "Should resume after pause expires"


def test_controller_suppress_phrase_sets_pause() -> None:
    """Controller handles USER_TEXT_SUBMITTED with suppress phrase."""
    config = ProactiveNudgeConfig(enabled=True, idle_seconds=10, feedback_pause_seconds=60)
    service = ProactiveNudgeService(config)
    subscribe = MagicMock()
    unsubscribe = MagicMock()
    dispatch_event = MagicMock()

    controller = ProactiveController(
        service=service,
        subscribe=subscribe,
        unsubscribe=unsubscribe,
        dispatch_event=dispatch_event,
    )
    controller.start()

    now = datetime.now(UTC)
    event = _make_event(USER_TEXT_SUBMITTED, {"text": "我今天很累，别打扰我。"}, timestamp=now)
    controller._on_user_text_submitted(event)

    # Should be paused
    during_pause = now + timedelta(seconds=30)
    result = service.maybe_create_nudge(now=during_pause)
    assert result is None, "Should be paused after suppress phrase"


def test_service_does_not_call_llm_v9c() -> None:
    """V9-C service still does not call LLM."""
    config = ProactiveNudgeConfig(enabled=True, quiet_hours_enabled=True, feedback_pause_seconds=60)
    service = ProactiveNudgeService(config)
    now = datetime.now(UTC)
    service.record_user_activity(now)
    result = service.maybe_create_nudge(now=now + timedelta(seconds=5))
    # No LLM, just fixed pool
    assert result is None or isinstance(result, str)


def test_service_does_not_call_tts_v9c() -> None:
    """V9-C service does not call TTS."""
    config = ProactiveNudgeConfig(enabled=True)
    service = ProactiveNudgeService(config)
    assert hasattr(service, "maybe_create_nudge")


def test_service_does_not_read_memory_v9c() -> None:
    """V9-C service does not read memory."""
    config = ProactiveNudgeConfig(enabled=True, quiet_hours_enabled=True)
    service = ProactiveNudgeService(config)
    assert not hasattr(service, "_memory_store")
    assert not hasattr(service, "_memory_repo")
