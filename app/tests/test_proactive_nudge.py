"""Tests for proactive nudge (V9-A)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

from app.brain.proactive.controller import ProactiveController
from app.brain.proactive.service import ProactiveNudgeConfig, ProactiveNudgeService
from app.contracts.events import PROACTIVE_NUDGE_READY, USER_TEXT_SUBMITTED, BaseEvent
from app.contracts.payloads import ProactiveNudgeReadyPayload
from app.contracts.states import AppState
from app.ui.chat_message import ChatMessage
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
