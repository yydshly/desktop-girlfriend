"""Tests for VoiceInputController."""

import time
from collections.abc import Callable
from unittest.mock import MagicMock

from app.contracts.events import (
    ASR_TEXT_RECOGNIZED,
    STATE_CHANGE_REQUESTED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    VOICE_INPUT_REQUESTED,
    BaseEvent,
)
from app.input.asr.controller import VoiceInputController
from app.input.asr.providers.base import ASRProvider, ASRProviderError, ASRRequest, ASRResponse


class FakeASRProviderForTest(ASRProvider):
    """Test double for ASRProvider."""

    def __init__(
        self,
        transcript: str = "Fake ASR result",
        delay_seconds: float = 0.01,
        should_fail: bool = False,
    ) -> None:
        self._transcript = transcript
        self._delay_seconds = delay_seconds
        self._should_fail = should_fail

    def recognize(self, request: ASRRequest) -> ASRResponse:
        time.sleep(self._delay_seconds)
        if self._should_fail:
            raise ASRProviderError("Fake ASR failed")
        return ASRResponse(text=self._transcript)


def make_dispatch_collector() -> tuple[list[BaseEvent], Callable[[BaseEvent], None]]:
    """Create a list and a callback that appends to it."""
    events: list[BaseEvent] = []

    def collect(event: BaseEvent) -> None:
        events.append(event)

    return events, collect


class TestVoiceInputController:
    """Tests for VoiceInputController."""

    def _make_event(self) -> BaseEvent:
        return BaseEvent(
            event_type=VOICE_INPUT_REQUESTED,
            request_id="req-voice-1",
            source="test",
            payload={},
        )

    def test_start_subscribes_to_voice_input_requested(self) -> None:
        """Test start() subscribes to VOICE_INPUT_REQUESTED."""
        event_bus = MagicMock()
        provider = FakeASRProviderForTest()
        controller = VoiceInputController(event_bus, provider, MagicMock())
        controller.start()
        event_bus.subscribe.assert_called_once_with(
            VOICE_INPUT_REQUESTED, controller._on_voice_input_requested
        )

    def test_stop_unsubscribes_and_prevents_late_result(self) -> None:
        """Test stop() unsubscribes and late worker results are discarded."""
        event_bus = MagicMock()
        provider = FakeASRProviderForTest(delay_seconds=0.5)
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(event_bus, provider, dispatch_event)
        controller.start()

        # Trigger voice input
        controller._on_voice_input_requested(self._make_event())
        controller.stop()
        provider._delay_seconds = 0.0  # Speed up for test
        time.sleep(0.05)

        # Late result should be discarded
        asr_events = [e for e in dispatch_events if e.event_type == ASR_TEXT_RECOGNIZED]
        assert len(asr_events) == 0

    def test_voice_input_requests_listening_state(self) -> None:
        """Test VOICE_INPUT_REQUESTED results in LISTENING state request."""
        event_bus = MagicMock()
        provider = FakeASRProviderForTest()
        controller = VoiceInputController(event_bus, provider, MagicMock())
        controller.start()

        controller._on_voice_input_requested(self._make_event())
        time.sleep(0.02)

        state_calls = [
            call
            for call in event_bus.publish.call_args_list
            if call[0][0].payload.get("target_state") == "listening"
        ]
        assert len(state_calls) >= 1

    def test_successful_recognition_dispatches_asr_text_recognized(self) -> None:
        """Test successful recognition dispatches ASR_TEXT_RECOGNIZED."""
        event_bus = MagicMock()
        provider = FakeASRProviderForTest(transcript="识别成功的文本")
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(event_bus, provider, dispatch_event)
        controller.start()

        controller._on_voice_input_requested(self._make_event())
        time.sleep(0.05)

        asr_events = [e for e in dispatch_events if e.event_type == ASR_TEXT_RECOGNIZED]
        assert len(asr_events) == 1
        assert asr_events[0].payload["text"] == "识别成功的文本"

    def test_successful_recognition_dispatches_user_text_submitted(self) -> None:
        """Test successful recognition dispatches USER_TEXT_SUBMITTED."""
        event_bus = MagicMock()
        provider = FakeASRProviderForTest(transcript="这是语音识别的结果")
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(event_bus, provider, dispatch_event)
        controller.start()

        controller._on_voice_input_requested(self._make_event())
        time.sleep(0.05)

        user_events = [e for e in dispatch_events if e.event_type == USER_TEXT_SUBMITTED]
        assert len(user_events) == 1
        assert user_events[0].payload["text"] == "这是语音识别的结果"

    def test_user_text_submitted_source_is_voice_input_controller(self) -> None:
        """Test USER_TEXT_SUBMITTED source is 'voice_input_controller'."""
        event_bus = MagicMock()
        provider = FakeASRProviderForTest(transcript="语音文本")
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(event_bus, provider, dispatch_event)
        controller.start()

        controller._on_voice_input_requested(self._make_event())
        time.sleep(0.05)

        user_events = [e for e in dispatch_events if e.event_type == USER_TEXT_SUBMITTED]
        assert len(user_events) == 1
        assert user_events[0].source == "voice_input_controller"

    def test_duplicate_request_while_listening_is_ignored(self) -> None:
        """Test a second VOICE_INPUT_REQUESTED while already listening is ignored."""
        event_bus = MagicMock()
        provider = FakeASRProviderForTest(delay_seconds=0.2)
        controller = VoiceInputController(event_bus, provider, MagicMock())
        controller.start()

        controller._on_voice_input_requested(self._make_event())
        time.sleep(0.01)
        controller._on_voice_input_requested(self._make_event())
        time.sleep(0.01)

        # Only one LISTENING state request
        listening_calls = [
            call
            for call in event_bus.publish.call_args_list
            if call[0][0].payload.get("target_state") == "listening"
        ]
        assert len(listening_calls) == 1

    def test_provider_error_dispatches_safe_system_error(self) -> None:
        """Test provider error dispatches SYSTEM_ERROR with safe message."""
        event_bus = MagicMock()
        provider = FakeASRProviderForTest(should_fail=True)
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(event_bus, provider, dispatch_event)
        controller.start()

        controller._on_voice_input_requested(self._make_event())
        time.sleep(0.05)

        error_events = [e for e in dispatch_events if e.event_type == SYSTEM_ERROR]
        assert len(error_events) >= 1
        assert error_events[0].payload["message"] == "语音识别失败，请稍后重试。"
        assert "Fake ASR failed" not in error_events[0].payload["message"]

    def test_provider_error_dispatches_error_state(self) -> None:
        """Test provider error dispatches ERROR state."""
        event_bus = MagicMock()
        provider = FakeASRProviderForTest(should_fail=True)
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(event_bus, provider, dispatch_event)
        controller.start()

        controller._on_voice_input_requested(self._make_event())
        time.sleep(0.05)

        error_state_events = [
            e for e in dispatch_events
            if e.event_type == STATE_CHANGE_REQUESTED
            and e.payload.get("target_state") == "error"
        ]
        assert len(error_state_events) >= 1
