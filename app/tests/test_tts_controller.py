"""Tests for TTSController."""

import time
from collections.abc import Callable

from app.contracts.events import ASSISTANT_TEXT_RECEIVED, STATE_CHANGE_REQUESTED, BaseEvent
from app.core.event_bus import EventBus
from app.expression.tts.controller import TTSController
from app.expression.tts.providers.base import TTSProvider, TTSProviderError, TTSRequest, TTSResponse


class FailingTTSProvider(TTSProvider):
    """Provider that raises TTSProviderError."""

    def speak(self, request: TTSRequest) -> TTSResponse:
        raise TTSProviderError("Bearer secret-should-not-leak")


class ImmediateTTSProvider(TTSProvider):
    """Provider that returns immediately."""

    def __init__(self, delay: float = 0.0) -> None:
        self._delay = delay

    def speak(self, request: TTSRequest) -> TTSResponse:
        time.sleep(self._delay)
        return TTSResponse(duration_seconds=self._delay)


def _make_dispatch_collector() -> tuple[list[BaseEvent], Callable[[BaseEvent], None]]:
    """Create a list and a callback that appends to it."""
    events: list[BaseEvent] = []

    def collect(event: BaseEvent) -> None:
        events.append(event)

    return events, collect


def _make_assistant_event(text: str) -> BaseEvent:
    return BaseEvent(
        event_type=ASSISTANT_TEXT_RECEIVED,
        request_id="req1",
        source="test",
        payload={"text": text},
    )


class TestTTSController:
    """Tests for TTSController."""

    def test_valid_text_publishes_speaking_then_dispatches_idle(self) -> None:
        """Test valid assistant text publishes SPEAKING then dispatches IDLE."""
        event_bus = EventBus()
        provider = ImmediateTTSProvider(delay=0.01)
        bus_events: list[BaseEvent] = []
        event_bus.subscribe(STATE_CHANGE_REQUESTED, bus_events.append)
        dispatch_events, dispatch_event = _make_dispatch_collector()

        controller = TTSController(event_bus, provider, dispatch_event)
        controller.start()

        event_bus.publish(_make_assistant_event("Hello"))

        # SPEAKING published synchronously
        speaking_events = [
            e for e in bus_events if e.payload.get("target_state") == "speaking"
        ]
        assert len(speaking_events) >= 1

        # Wait for worker to complete
        time.sleep(0.05)

        # IDLE dispatched via dispatch_event
        idle_events = [
            e for e in dispatch_events if e.payload.get("target_state") == "idle"
        ]
        assert len(idle_events) >= 1

    def test_invalid_event_type_ignored(self) -> None:
        """Test that non-assistant event type is ignored."""
        event_bus = EventBus()
        provider = ImmediateTTSProvider()
        bus_events: list[BaseEvent] = []
        event_bus.subscribe(STATE_CHANGE_REQUESTED, bus_events.append)
        dispatch_events, dispatch_event = _make_dispatch_collector()

        controller = TTSController(event_bus, provider, dispatch_event)
        controller.start()

        other_event = BaseEvent(
            event_type="other.event",
            request_id="req2",
            source="test",
            payload={"text": "Hello"},
        )
        event_bus.publish(other_event)
        time.sleep(0.02)

        # No state changes published
        speaking_events = [
            e for e in bus_events if e.payload.get("target_state") == "speaking"
        ]
        assert len(speaking_events) == 0
        assert len(dispatch_events) == 0

    def test_missing_text_ignored_silently(self) -> None:
        """Test that missing text is silently ignored, no state change."""
        event_bus = EventBus()
        provider = ImmediateTTSProvider()
        bus_events: list[BaseEvent] = []
        event_bus.subscribe(STATE_CHANGE_REQUESTED, bus_events.append)
        dispatch_events, dispatch_event = _make_dispatch_collector()

        controller = TTSController(event_bus, provider, dispatch_event)
        controller.start()

        event = BaseEvent(
            event_type=ASSISTANT_TEXT_RECEIVED,
            request_id="req3",
            source="test",
            payload={},
        )
        event_bus.publish(event)
        time.sleep(0.02)

        speaking_events = [
            e for e in bus_events if e.payload.get("target_state") == "speaking"
        ]
        assert len(speaking_events) == 0
        assert len(dispatch_events) == 0

    def test_non_str_text_ignored_silently(self) -> None:
        """Test that non-string text is silently ignored, no state change."""
        event_bus = EventBus()
        provider = ImmediateTTSProvider()
        bus_events: list[BaseEvent] = []
        event_bus.subscribe(STATE_CHANGE_REQUESTED, bus_events.append)
        dispatch_events, dispatch_event = _make_dispatch_collector()

        controller = TTSController(event_bus, provider, dispatch_event)
        controller.start()

        event = BaseEvent(
            event_type=ASSISTANT_TEXT_RECEIVED,
            request_id="req4",
            source="test",
            payload={"text": None},
        )
        event_bus.publish(event)
        time.sleep(0.02)

        speaking_events = [
            e for e in bus_events if e.payload.get("target_state") == "speaking"
        ]
        assert len(speaking_events) == 0
        assert len(dispatch_events) == 0

    def test_str_subclass_ignored_silently(self) -> None:
        """Test that str subclass text is silently ignored (type must be exact str)."""

        class TextSubclass(str):
            pass

        event_bus = EventBus()
        provider = ImmediateTTSProvider()
        bus_events: list[BaseEvent] = []
        event_bus.subscribe(STATE_CHANGE_REQUESTED, bus_events.append)
        dispatch_events, dispatch_event = _make_dispatch_collector()

        controller = TTSController(event_bus, provider, dispatch_event)
        controller.start()

        event = BaseEvent(
            event_type=ASSISTANT_TEXT_RECEIVED,
            request_id="req5",
            source="test",
            payload={"text": TextSubclass("Hello")},
        )
        event_bus.publish(event)
        time.sleep(0.02)

        speaking_events = [
            e for e in bus_events if e.payload.get("target_state") == "speaking"
        ]
        assert len(speaking_events) == 0
        assert len(dispatch_events) == 0

    def test_provider_failure_dispatches_safe_error_and_error_state(self) -> None:
        """Test provider failure dispatches SYSTEM_ERROR with safe message and ERROR state."""
        event_bus = EventBus()
        provider = FailingTTSProvider()
        bus_events: list[BaseEvent] = []
        event_bus.subscribe(STATE_CHANGE_REQUESTED, bus_events.append)
        dispatch_events, dispatch_event = _make_dispatch_collector()

        controller = TTSController(event_bus, provider, dispatch_event)
        controller.start()

        event_bus.publish(_make_assistant_event("Hello"))
        time.sleep(0.05)

        # SPEAKING published
        speaking_events = [
            e for e in bus_events if e.payload.get("target_state") == "speaking"
        ]
        assert len(speaking_events) >= 1

        # SYSTEM_ERROR dispatched with safe message (no secret)
        error_events = [e for e in dispatch_events if e.event_type == "system.error"]
        assert len(error_events) >= 1
        error_msg = error_events[0].payload.get("message", "")
        assert error_msg == "语音播放失败，请稍后重试。"
        assert "Bearer" not in error_msg
        assert "secret" not in error_msg

        # ERROR state dispatched
        error_state_events = [
            e for e in dispatch_events if e.payload.get("target_state") == "error"
        ]
        assert len(error_state_events) >= 1

    def test_inflight_guard_ignores_second_event_while_speaking(self) -> None:
        """Test that a second event while speaking is ignored."""
        event_bus = EventBus()
        provider = ImmediateTTSProvider(delay=0.1)
        bus_events: list[BaseEvent] = []
        event_bus.subscribe(STATE_CHANGE_REQUESTED, bus_events.append)
        dispatch_events, dispatch_event = _make_dispatch_collector()

        controller = TTSController(event_bus, provider, dispatch_event)
        controller.start()

        # Send first event
        event_bus.publish(_make_assistant_event("First"))
        # Immediately send second event while still speaking
        event_bus.publish(_make_assistant_event("Second"))

        # Only one SPEAKING
        speaking_events = [
            e for e in bus_events if e.payload.get("target_state") == "speaking"
        ]
        assert len(speaking_events) == 1

        # Wait for completion
        time.sleep(0.2)

    def test_worker_does_not_call_event_bus_for_idle(self) -> None:
        """Test worker dispatches IDLE via dispatch_event, not event_bus.publish."""
        event_bus = EventBus()
        provider = ImmediateTTSProvider(delay=0.01)
        bus_events: list[BaseEvent] = []
        event_bus.subscribe(STATE_CHANGE_REQUESTED, bus_events.append)
        dispatch_events, dispatch_event = _make_dispatch_collector()

        controller = TTSController(event_bus, provider, dispatch_event)
        controller.start()

        event_bus.publish(_make_assistant_event("Hello"))

        # Count bus_events before waiting
        count_before = len(bus_events)
        assert count_before >= 1  # At least SPEAKING

        time.sleep(0.1)

        # No additional STATE_CHANGE_REQUESTED published to event_bus
        # (worker should only use dispatch_event)
        assert len(bus_events) == count_before

        # IDLE should only be in dispatch_events, not event_bus
        idle_via_bus = [
            e for e in bus_events if e.payload.get("target_state") == "idle"
        ]
        idle_via_dispatch = [
            e for e in dispatch_events if e.payload.get("target_state") == "idle"
        ]
        assert len(idle_via_dispatch) >= 1
        assert len(idle_via_bus) == 0
