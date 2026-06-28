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

    supports_audio_path_playback = True

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
        self._is_playing = False

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def play(
        self,
        path: str,
        on_finished: Callable[[], None],
        on_error: Callable[[str], None],
    ) -> None:
        self.play_calls.append((path, on_finished, on_error))
        self._finished_callback = on_finished
        self._error_callback = on_error
        self._is_playing = True

    def stop(self) -> bool:
        """Stop playback. Returns True if was playing, False otherwise."""
        if not self._is_playing:
            return False
        self._is_playing = False
        self._finished_callback = None
        self._error_callback = None
        return True

    def simulate_finished(self) -> None:
        if self._finished_callback:
            self._finished_callback()
        self._is_playing = False

    def simulate_error(self, message: str = "playback failed") -> None:
        if self._error_callback:
            self._error_callback(message)
        self._is_playing = False


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


class TestTTSControllerWithAudioPlayerAndFakeProvider:
    """Tests for FakeTTSProvider + audio_player: must use legacy speak() path."""

    def test_fake_provider_with_audio_player_uses_speak_legacy_path(self) -> None:
        """Test FakeTTSProvider + audio_player dispatches SPEAKING → IDLE via speak()."""
        from app.expression.tts.providers.fake import FakeTTSProvider

        event_bus = EventBus()
        provider = FakeTTSProvider(delay_seconds=0.01)
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

        # Should dispatch IDLE, not ERROR
        idle_events = [
            e for e in dispatch_events if e.payload.get("target_state") == "idle"
        ]
        assert len(idle_events) >= 1

        error_events = [
            e for e in dispatch_events if e.event_type == "system.error"
        ]
        assert len(error_events) == 0

        # audio_player.play should NOT have been called
        assert len(mock_player.play_calls) == 0

    def test_fake_provider_with_audio_player_does_not_require_audio_path(self) -> None:
        """Test FakeTTSProvider + audio_player does not raise on missing audio_path."""
        from app.expression.tts.providers.fake import FakeTTSProvider

        event_bus = EventBus()
        provider = FakeTTSProvider(delay_seconds=0.01)
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

        # No system error should have been dispatched
        error_events = [
            e for e in dispatch_events if e.event_type == "system.error"
        ]
        assert len(error_events) == 0


class TestEmbeddedPlaybackStateGuard:
    """Tests for _is_speaking release timing in embedded playback path."""

    def test_is_speaking_not_released_until_playback_finished(self) -> None:
        """Test _is_speaking stays True while playback is in progress."""
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

        # audio_ready dispatched, playback in progress — _is_speaking still True
        audio_ready_events = [
            e for e in dispatch_events if e.event_type == "tts.audio_ready"
        ]
        assert len(audio_ready_events) >= 1

        # Second event while playback in progress should be ignored
        event_bus.publish(_make_assistant_event("Second"))
        time.sleep(0.05)

        # Only one audio_ready should have been dispatched (second ignored)
        audio_ready_after = [
            e for e in dispatch_events if e.event_type == "tts.audio_ready"
        ]
        assert len(audio_ready_after) == 1

    def test_on_error_releases_is_speaking(self) -> None:
        """Test on_error callback releases _is_speaking so new events are processed."""
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

        # After error, new events should be processed
        event_bus.publish(_make_assistant_event("After error"))
        time.sleep(0.05)

        # Should have 2 audio_ready events (original + new after error release)
        audio_ready_events = [
            e for e in dispatch_events if e.event_type == "tts.audio_ready"
        ]
        assert len(audio_ready_events) >= 2

    def test_invalid_audio_path_releases_is_speaking(self) -> None:
        """Test invalid/missing audio_path releases _is_speaking."""
        event_bus = EventBus()
        provider = SynthesizeOnlyProvider(audio_path=None)  # invalid
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

        # Should have error state dispatched
        error_events = [
            e for e in dispatch_events if e.event_type == "system.error"
        ]
        assert len(error_events) >= 1

        # New event should now be processed (not permanently blocked)
        event_bus.publish(_make_assistant_event("After invalid"))
        time.sleep(0.05)

        # The second event should have been processed (ERROR state dispatched)
        error_events_after = [
            e for e in dispatch_events if e.event_type == "system.error"
        ]
        assert len(error_events_after) >= 2


class TestTTSControllerStop:
    """Tests for TTS stop functionality."""

    def test_stop_requested_while_not_speaking_does_not_dispatch_error(self) -> None:
        """Test stop requested while not speaking does not dispatch ERROR."""
        from app.contracts.events import TTS_STOP_REQUESTED

        event_bus = EventBus()
        provider = ImmediateTTSProvider(delay=0.0)
        dispatch_events, dispatch_event = _make_dispatch_collector(event_bus)

        controller = TTSController(event_bus, provider, dispatch_event)
        controller.start()

        # Publish stop without any preceding speech
        stop_event = BaseEvent(
            event_type=TTS_STOP_REQUESTED,
            request_id="stop1",
            source="test",
            payload={},
        )
        event_bus.publish(stop_event)
        time.sleep(0.02)

        error_events = [
            e for e in dispatch_events if e.event_type == "system.error"
        ]
        assert len(error_events) == 0

    def test_stop_legacy_fake_speaking_releases_and_idles(self) -> None:
        """Test stop during legacy fake speak() releases _is_speaking and dispatches IDLE."""
        from app.contracts.events import TTS_STOP_REQUESTED

        event_bus = EventBus()
        provider = ImmediateTTSProvider(delay=0.5)  # long enough to be stoppable
        dispatch_events, dispatch_event = _make_dispatch_collector(event_bus)

        controller = TTSController(event_bus, provider, dispatch_event)
        controller.start()

        event_bus.publish(_make_assistant_event("Hello"))
        time.sleep(0.05)

        # Stop while speaking
        stop_event = BaseEvent(
            event_type=TTS_STOP_REQUESTED,
            request_id="stop2",
            source="test",
            payload={},
        )
        event_bus.publish(stop_event)
        time.sleep(0.05)

        # Should dispatch IDLE with reason tts_stopped
        idle_events = [
            e for e in dispatch_events
            if e.payload.get("target_state") == "idle"
        ]
        assert len(idle_events) >= 1

        # Should NOT dispatch SYSTEM_ERROR
        error_events = [
            e for e in dispatch_events if e.event_type == "system.error"
        ]
        assert len(error_events) == 0

    def test_stop_embedded_playback_calls_player_stop(self) -> None:
        """Test stop during embedded playback calls audio_player.stop()."""
        from app.contracts.events import TTS_STOP_REQUESTED

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

        # Stop while audio is ready (before simulate_finished)
        stop_event = BaseEvent(
            event_type=TTS_STOP_REQUESTED,
            request_id="stop3",
            source="test",
            payload={},
        )
        event_bus.publish(stop_event)
        time.sleep(0.05)

        # audio_player.stop() should have been called
        # Since MockAudioPlayer.stop() returns True when playing, we check play_calls is empty
        # because stop clears the callbacks
        # Verify audio_player.stop was called (it's a side effect we can check via state)
        assert mock_player.is_playing is False

    def test_stop_embedded_dispatches_idle_without_error(self) -> None:
        """Test stop during embedded playback dispatches IDLE without ERROR."""
        from app.contracts.events import TTS_STOP_REQUESTED

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

        stop_event = BaseEvent(
            event_type=TTS_STOP_REQUESTED,
            request_id="stop4",
            source="test",
            payload={},
        )
        event_bus.publish(stop_event)
        time.sleep(0.05)

        idle_events = [
            e for e in dispatch_events
            if e.payload.get("target_state") == "idle"
        ]
        assert len(idle_events) >= 1

        error_events = [
            e for e in dispatch_events if e.event_type == "system.error"
        ]
        assert len(error_events) == 0

    def test_stop_during_synthesize_prevents_audio_ready(self) -> None:
        """Test stop during synthesize prevents TTS_AUDIO_READY dispatch.

        Since SynthesizeOnlyProvider is immediate, we test the guard logic:
        when stop is called, the request_id is added to _stop_requested_request_ids,
        so even if synthesize returns afterward, audio_ready is not dispatched.
        """
        import threading

        from app.contracts.events import TTS_STOP_REQUESTED

        # A provider that blocks until we release it
        class BlockingSynthesizeProvider(TTSProvider):
            supports_audio_path_playback = True

            def __init__(self) -> None:
                self._block_event = threading.Event()
                self.synthesize_called = False

            def unblock(self) -> None:
                self._block_event.set()

            def synthesize(self, request: TTSRequest) -> TTSResponse:
                self.synthesize_called = True
                self._block_event.wait()  # Block until test unblocks
                return TTSResponse(duration_seconds=0.0, audio_path="/tmp/test.mp3")

            def speak(self, request: TTSRequest) -> TTSResponse:
                return self.synthesize(request)

        event_bus = EventBus()
        provider = BlockingSynthesizeProvider()
        mock_player = MockAudioPlayer()
        dispatch_events, dispatch_event = _make_dispatch_collector(event_bus)

        controller = TTSController(
            event_bus,
            provider,
            dispatch_event,
            audio_player=mock_player,  # type: ignore[arg-type]
        )
        controller.start()

        # Start TTS in another thread (speak_text will block on provider)
        event_bus.publish(_make_assistant_event("Hello"))

        # Wait for synthesize to be called (provider is blocking)
        for _ in range(50):
            if provider.synthesize_called:
                break
            time.sleep(0.01)

        # Now stop while synthesize is blocked
        stop_event = BaseEvent(
            event_type=TTS_STOP_REQUESTED,
            request_id="stop5",
            source="test",
            payload={},
        )
        event_bus.publish(stop_event)

        # Release the provider's block
        provider.unblock()

        time.sleep(0.1)

        # audio_player.play should NOT have been called because stop was requested
        assert len(mock_player.play_calls) == 0

        # Should have IDLE (tts_stopped), not ERROR
        idle_events = [
            e for e in dispatch_events
            if e.payload.get("target_state") == "idle"
            and e.payload.get("reason") == "tts_stopped"
        ]
        assert len(idle_events) >= 1

    def test_after_stop_can_start_new_tts(self) -> None:
        """Test after stop, a new assistant.text_received can start a new TTS."""
        import threading

        from app.contracts.events import TTS_STOP_REQUESTED

        # A provider that blocks until released
        class BlockingFakeProvider(TTSProvider):
            def __init__(self) -> None:
                self._block_event = threading.Event()
                self.speak_calls = 0

            def unblock(self) -> None:
                self._block_event.set()

            def speak(self, request: TTSRequest) -> TTSResponse:
                self.speak_calls += 1
                self._block_event.wait()
                return TTSResponse(duration_seconds=0.0)

        event_bus = EventBus()
        provider = BlockingFakeProvider()
        dispatch_events, dispatch_event = _make_dispatch_collector(event_bus)

        controller = TTSController(event_bus, provider, dispatch_event)
        controller.start()

        # First TTS
        event_bus.publish(_make_assistant_event("First"))

        # Wait for first speak to be called
        for _ in range(50):
            if provider.speak_calls > 0:
                break
            time.sleep(0.01)

        # Stop it
        stop_event = BaseEvent(
            event_type=TTS_STOP_REQUESTED,
            request_id="stop6",
            source="test",
            payload={},
        )
        event_bus.publish(stop_event)
        time.sleep(0.05)

        # Unblock first provider - its speak will return but should not cause issues
        provider.unblock()
        time.sleep(0.05)

        # New TTS should be allowed
        event_bus.publish(_make_assistant_event("Second"))
        time.sleep(0.05)

        # Should have at least 2 speak calls (one per TTS)
        assert provider.speak_calls >= 2

    def test_stale_audio_ready_after_stop_is_ignored(self) -> None:
        """Test that TTS_AUDIO_READY dispatched before stop is ignored after stop.

        Simulates the real Qt behavior where dispatch_event is async (Signal.emit
        queues to Qt event loop), so the worker dispatches audio_ready but it
        hasn't been processed by the UI thread yet when stop is called.
        """
        from app.contracts.events import TTS_AUDIO_READY, TTS_STOP_REQUESTED

        # Capture audio_ready without immediately publishing to event_bus.
        # This simulates async dispatch where the event is queued but not yet
        # processed by the UI thread when stop arrives.
        captured_audio_ready: list[BaseEvent] = []
        all_dispatched: list[BaseEvent] = []

        def capturing_dispatch(event: BaseEvent) -> None:
            all_dispatched.append(event)
            if event.event_type == TTS_AUDIO_READY:
                captured_audio_ready.append(event)
            else:
                event_bus.publish(event)

        event_bus = EventBus()
        provider = SynthesizeOnlyProvider(audio_path="/tmp/test.mp3")
        mock_player = MockAudioPlayer()

        controller = TTSController(
            event_bus,
            provider,
            capturing_dispatch,
            audio_player=mock_player,  # type: ignore[arg-type]
        )
        controller.start()

        # Start TTS - capture the actual request_id used by the worker
        original_event = _make_assistant_event("Hello")
        stale_request_id = original_event.request_id
        event_bus.publish(original_event)
        time.sleep(0.05)

        # Worker has dispatched audio_ready (captured, not yet published)
        assert len(captured_audio_ready) >= 1
        audio_ready_events = [e for e in captured_audio_ready if e.event_type == TTS_AUDIO_READY]
        assert len(audio_ready_events) >= 1

        # Stop BEFORE the audio_ready is processed (UI thread hasn't received it yet)
        stop_event = BaseEvent(
            event_type=TTS_STOP_REQUESTED,
            request_id="stop_stale",
            source="test",
            payload={},
        )
        event_bus.publish(stop_event)
        time.sleep(0.05)

        # Now publish the stale audio_ready (simulating Qt event loop processing it late)
        for ae in audio_ready_events:
            event_bus.publish(ae)
        time.sleep(0.05)

        # audio_player.play should NOT have been called (stop should have ignored it)
        assert len(mock_player.play_calls) == 0

        # No SYSTEM_ERROR should be dispatched
        error_events = [
            e for e in all_dispatched if e.event_type == "system.error"
        ]
        assert len(error_events) == 0

        # No ERROR state should be dispatched
        error_state_events = [
            e for e in all_dispatched if e.payload.get("target_state") == "error"
        ]
        assert len(error_state_events) == 0

    def test_synthesize_error_after_stop_is_silently_discarded(self) -> None:
        """Test that synthesize error after stop does not dispatch error."""
        import threading

        from app.contracts.events import TTS_STOP_REQUESTED

        # Provider that blocks during synthesize then raises error
        class BlockingFailingProvider(TTSProvider):
            supports_audio_path_playback = True

            def __init__(self) -> None:
                self._block_event = threading.Event()
                self.synthesize_called = False

            def unblock(self) -> None:
                self._block_event.set()

            def synthesize(self, request: TTSRequest) -> TTSResponse:
                self.synthesize_called = True
                self._block_event.wait()
                raise TTSProviderError("Synthesize failed after stop")

            def speak(self, request: TTSRequest) -> TTSResponse:
                return self.synthesize(request)

        event_bus = EventBus()
        provider = BlockingFailingProvider()
        mock_player = MockAudioPlayer()
        dispatch_events, dispatch_event = _make_dispatch_collector(event_bus)

        controller = TTSController(
            event_bus,
            provider,
            dispatch_event,
            audio_player=mock_player,  # type: ignore[arg-type]
        )
        controller.start()

        # Start TTS (will block in synthesize)
        event_bus.publish(_make_assistant_event("Hello"))

        # Wait for synthesize to be called
        for _ in range(50):
            if provider.synthesize_called:
                break
            time.sleep(0.01)

        # Stop while synthesize is blocked
        stop_event = BaseEvent(
            event_type=TTS_STOP_REQUESTED,
            request_id="stop_err",
            source="test",
            payload={},
        )
        event_bus.publish(stop_event)
        time.sleep(0.05)

        # Now unblock synthesize - it will throw
        provider.unblock()
        time.sleep(0.1)

        # No SYSTEM_ERROR should be dispatched (error is silently discarded)
        error_events = [
            e for e in dispatch_events if e.event_type == "system.error"
        ]
        assert len(error_events) == 0

        # No ERROR state should be dispatched
        error_state_events = [
            e for e in dispatch_events if e.payload.get("target_state") == "error"
        ]
        assert len(error_state_events) == 0

        # State should be IDLE (from stop), not ERROR
        idle_events = [
            e for e in dispatch_events
            if e.payload.get("target_state") == "idle"
            and e.payload.get("reason") == "tts_stopped"
        ]
        assert len(idle_events) >= 1

    def test_old_finished_callback_does_not_release_new_request(self) -> None:
        """Test that old on_finished callback does not affect new request's state."""
        from app.contracts.events import TTS_AUDIO_READY, TTS_STOP_REQUESTED

        # A mock that captures callbacks for later invocation
        class CapturingMockPlayer(MockAudioPlayer):
            def __init__(self) -> None:
                super().__init__()
                self._last_finished_callback: Callable[[], None] | None = None
                self._last_error_callback: Callable[[str], None] | None = None

            def play(
                self,
                path: str,
                on_finished: Callable[[], None],
                on_error: Callable[[str], None],
            ) -> None:
                super().play(path, on_finished, on_error)
                self._last_finished_callback = on_finished
                self._last_error_callback = on_error

            def stop(self) -> bool:
                """Stop playback without clearing callbacks."""
                if not self._is_playing:
                    return False
                self._is_playing = False
                # Do NOT clear callbacks - they are still valid for the current request
                return True

            def simulate_finished(self) -> None:
                """Simulate playback finished, invoking the stored callback."""
                if self._finished_callback is not None:
                    cb = self._finished_callback
                    self._finished_callback = None
                    self._error_callback = None
                    self._is_playing = False
                    cb()
                else:
                    self._is_playing = False

        event_bus = EventBus()
        provider = SynthesizeOnlyProvider(audio_path="/tmp/test.mp3")
        mock_player = CapturingMockPlayer()
        dispatch_events, dispatch_event = _make_dispatch_collector(event_bus)

        controller = TTSController(
            event_bus,
            provider,
            dispatch_event,
            audio_player=mock_player,  # type: ignore[arg-type]
        )
        controller.start()

        # Request A starts with unique request_id
        event_a = BaseEvent(
            event_type=ASSISTANT_TEXT_RECEIVED,
            request_id="req_a",
            source="test",
            payload={"text": "First"},
        )
        event_bus.publish(event_a)
        time.sleep(0.05)

        # Stop request A
        stop_event = BaseEvent(
            event_type=TTS_STOP_REQUESTED,
            request_id="stop_old",
            source="test",
            payload={},
        )
        event_bus.publish(stop_event)
        time.sleep(0.05)

        # Request B starts with DIFFERENT request_id
        event_b = BaseEvent(
            event_type=ASSISTANT_TEXT_RECEIVED,
            request_id="req_b",
            source="test",
            payload={"text": "Second"},
        )
        event_bus.publish(event_b)
        time.sleep(0.05)

        # Request B should have called play (at least once for B)
        assert len(mock_player.play_calls) >= 1

        # Simulate request B's playback finishing normally
        mock_player.simulate_finished()
        time.sleep(0.05)

        # State should be IDLE (from B's normal completion)
        idle_events = [
            e for e in dispatch_events
            if e.payload.get("target_state") == "idle"
            and e.payload.get("reason") == "tts_complete"
        ]
        assert len(idle_events) >= 1
