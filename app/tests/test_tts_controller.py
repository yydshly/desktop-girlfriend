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


def _make_dispatch_collector(
    event_bus: EventBus | None = None,
) -> tuple[list[BaseEvent], Callable[[BaseEvent], None]]:
    """Create a list and a callback that optionally publishes to an event bus.

    When event_bus is provided, the collector also publishes events to it so that
    any handlers subscribed to those events will be triggered.
    This is necessary for TTS_AUDIO_READY handling where TTSController
    subscribes a handler to the event bus.
    """
    events: list[BaseEvent] = []

    def collect(event: BaseEvent) -> None:
        events.append(event)
        if event_bus is not None:
            event_bus.publish(event)

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


class SynthesizeOnlyProvider(TTSProvider):
    """Provider that implements synthesize() returning audio_path but not speak()."""

    def __init__(self, audio_path: str | None = "/tmp/test.mp3", should_fail: bool = False) -> None:
        self._audio_path = audio_path
        self._should_fail = should_fail
        self.speak_called = False
        self.synthesize_called = False

    def synthesize(self, request: TTSRequest) -> TTSResponse:
        self.synthesize_called = True
        if self._should_fail:
            raise TTSProviderError("Synthesize failed")
        return TTSResponse(duration_seconds=0.0, audio_path=self._audio_path)

    def speak(self, request: TTSRequest) -> TTSResponse:
        self.speak_called = True
        return TTSResponse(duration_seconds=0.0)


class MockAudioPlayer:
    """Mock audio player that captures play() calls."""

    def __init__(self) -> None:
        self.play_calls: list[tuple[str, Callable[[], None], Callable[[str], None]]] = []
        self._finished_callback: Callable[[], None] | None = None
        self._error_callback: Callable[[str], None] | None = None

    def play(
        self,
        path: str,
        on_finished: Callable[[], None],
        on_error: Callable[[str], None],
    ) -> None:
        self.play_calls.append((path, on_finished, on_error))
        self._finished_callback = on_finished
        self._error_callback = on_error

    def simulate_finished(self) -> None:
        if self._finished_callback:
            self._finished_callback()

    def simulate_error(self, message: str = "playback failed") -> None:
        if self._error_callback:
            self._error_callback(message)


class TestTTSControllerWithAudioPlayer:
    """Tests for TTSController with audio_player."""

    def test_without_audio_player_uses_speak(self) -> None:
        """Test controller without audio_player calls provider.speak()."""
        event_bus = EventBus()
        provider = ImmediateTTSProvider(delay=0.01)
        bus_events: list[BaseEvent] = []
        event_bus.subscribe(STATE_CHANGE_REQUESTED, bus_events.append)
        dispatch_events, dispatch_event = _make_dispatch_collector()

        controller = TTSController(event_bus, provider, dispatch_event)
        controller.start()

        event_bus.publish(_make_assistant_event("Hello"))
        time.sleep(0.05)

        idle_events = [
            e for e in dispatch_events if e.payload.get("target_state") == "idle"
        ]
        assert len(idle_events) >= 1

    def test_with_audio_player_calls_synthesize(self) -> None:
        """Test controller with audio_player calls provider.synthesize()."""
        event_bus = EventBus()
        provider = SynthesizeOnlyProvider()
        mock_player = MockAudioPlayer()
        bus_events: list[BaseEvent] = []
        event_bus.subscribe(STATE_CHANGE_REQUESTED, bus_events.append)
        dispatch_events, dispatch_event = _make_dispatch_collector(event_bus)

        controller = TTSController(
            event_bus,
            provider,
            dispatch_event,
            audio_player=mock_player,  # type: ignore[arg-type]
        )
        controller.start()

        event_bus.publish(_make_assistant_event("Hello"))
        time.sleep(0.05)

        assert provider.synthesize_called is True
        assert provider.speak_called is False

    def test_with_audio_player_dispatches_audio_ready_event(self) -> None:
        """Test controller with audio_player dispatches TTS_AUDIO_READY."""
        from app.contracts.events import TTS_AUDIO_READY

        event_bus = EventBus()
        provider = SynthesizeOnlyProvider(audio_path="/tmp/test.mp3")
        mock_player = MockAudioPlayer()
        bus_events: list[BaseEvent] = []
        event_bus.subscribe(STATE_CHANGE_REQUESTED, bus_events.append)
        dispatch_events, dispatch_event = _make_dispatch_collector()

        controller = TTSController(
            event_bus,
            provider,
            dispatch_event,
            audio_player=mock_player,  # type: ignore[arg-type]
        )
        controller.start()

        event_bus.publish(_make_assistant_event("Hello"))
        time.sleep(0.05)

        audio_ready_events = [
            e for e in dispatch_events if e.event_type == TTS_AUDIO_READY
        ]
        assert len(audio_ready_events) >= 1
        assert audio_ready_events[0].payload.get("audio_path") == "/tmp/test.mp3"

    def test_with_audio_player_calls_player_play_on_audio_ready(self) -> None:
        """Test audio_player.play() is called when TTS_AUDIO_READY is dispatched."""
        event_bus = EventBus()
        provider = SynthesizeOnlyProvider(audio_path="/tmp/test.mp3")
        mock_player = MockAudioPlayer()
        dispatch_events, dispatch_event = _make_dispatch_collector(event_bus)

        controller = TTSController(
            event_bus,
            provider,
            dispatch_event,
            audio_player=mock_player,  # type: ignore[arg-type]
        )
        controller.start()

        event_bus.publish(_make_assistant_event("Hello"))
        time.sleep(0.05)

        assert len(mock_player.play_calls) == 1
        audio_path, on_finished, on_error = mock_player.play_calls[0]
        assert audio_path == "/tmp/test.mp3"

    def test_audio_playback_finished_dispatches_idle(self) -> None:
        """Test playback finished callback dispatches IDLE."""
        event_bus = EventBus()
        provider = SynthesizeOnlyProvider(audio_path="/tmp/test.mp3")
        mock_player = MockAudioPlayer()
        dispatch_events, dispatch_event = _make_dispatch_collector(event_bus)

        controller = TTSController(
            event_bus,
            provider,
            dispatch_event,
            audio_player=mock_player,  # type: ignore[arg-type]
        )
        controller.start()

        event_bus.publish(_make_assistant_event("Hello"))
        time.sleep(0.05)

        # Simulate playback finished
        mock_player.simulate_finished()
        time.sleep(0.02)

        idle_events = [
            e for e in dispatch_events if e.payload.get("target_state") == "idle"
        ]
        assert len(idle_events) >= 1

    def test_audio_playback_error_dispatches_error_and_error_state(self) -> None:
        """Test playback error callback dispatches SYSTEM_ERROR and ERROR state."""
        event_bus = EventBus()
        provider = SynthesizeOnlyProvider(audio_path="/tmp/test.mp3")
        mock_player = MockAudioPlayer()
        dispatch_events, dispatch_event = _make_dispatch_collector(event_bus)

        controller = TTSController(
            event_bus,
            provider,
            dispatch_event,
            audio_player=mock_player,  # type: ignore[arg-type]
        )
        controller.start()

        event_bus.publish(_make_assistant_event("Hello"))
        time.sleep(0.05)

        # Simulate playback error
        mock_player.simulate_error("Audio playback failed")
        time.sleep(0.02)

        error_events = [
            e for e in dispatch_events if e.event_type == "system.error"
        ]
        assert len(error_events) >= 1
        error_msg = error_events[0].payload.get("message", "")
        assert error_msg == "语音播放失败，请稍后重试。"
        assert "Audio playback failed" not in error_msg

        error_state_events = [
            e for e in dispatch_events if e.payload.get("target_state") == "error"
        ]
        assert len(error_state_events) >= 1

    def test_synthesize_failure_dispatches_error_and_error_state(self) -> None:
        """Test synthesize failure dispatches SYSTEM_ERROR and ERROR state."""
        event_bus = EventBus()
        provider = SynthesizeOnlyProvider(should_fail=True)
        mock_player = MockAudioPlayer()
        dispatch_events, dispatch_event = _make_dispatch_collector(event_bus)

        controller = TTSController(
            event_bus,
            provider,
            dispatch_event,
            audio_player=mock_player,  # type: ignore[arg-type]
        )
        controller.start()

        event_bus.publish(_make_assistant_event("Hello"))
        time.sleep(0.05)

        error_events = [
            e for e in dispatch_events if e.event_type == "system.error"
        ]
        assert len(error_events) >= 1
        error_msg = error_events[0].payload.get("message", "")
        assert error_msg == "语音播放失败，请稍后重试。"

        error_state_events = [
            e for e in dispatch_events if e.payload.get("target_state") == "error"
        ]
        assert len(error_state_events) >= 1

    def test_empty_audio_path_dispatches_error_and_error_state(self) -> None:
        """Test empty audio_path dispatches SYSTEM_ERROR and ERROR state."""
        event_bus = EventBus()
        provider = SynthesizeOnlyProvider(audio_path=None)
        mock_player = MockAudioPlayer()
        dispatch_events, dispatch_event = _make_dispatch_collector(event_bus)

        controller = TTSController(
            event_bus,
            provider,
            dispatch_event,
            audio_player=mock_player,  # type: ignore[arg-type]
        )
        controller.start()

        event_bus.publish(_make_assistant_event("Hello"))
        time.sleep(0.05)

        error_events = [
            e for e in dispatch_events if e.event_type == "system.error"
        ]
        assert len(error_events) >= 1

        error_state_events = [
            e for e in dispatch_events if e.payload.get("target_state") == "error"
        ]
        assert len(error_state_events) >= 1

    def test_is_speaking_released_after_playback_finished(self) -> None:
        """Test _is_speaking is released after playback finishes."""
        from app.contracts.events import TTS_AUDIO_READY

        event_bus = EventBus()
        provider = SynthesizeOnlyProvider(audio_path="/tmp/test.mp3")
        mock_player = MockAudioPlayer()
        dispatch_events, dispatch_event = _make_dispatch_collector(event_bus)

        controller = TTSController(
            event_bus,
            provider,
            dispatch_event,
            audio_player=mock_player,  # type: ignore[arg-type]
        )
        controller.start()

        event_bus.publish(_make_assistant_event("Hello"))
        time.sleep(0.05)

        # Simulate finished
        mock_player.simulate_finished()
        time.sleep(0.02)

        # Second event should be processed (not blocked by _is_speaking)
        event_bus.publish(_make_assistant_event("Second"))
        time.sleep(0.05)

        # At least two sets of audio_ready events should have been dispatched
        audio_ready_events = [
            e for e in dispatch_events if e.event_type == TTS_AUDIO_READY
        ]
        assert len(audio_ready_events) >= 2
