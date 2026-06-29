"""Tests for VoiceInputController."""

import time
from collections.abc import Callable
from unittest.mock import MagicMock

from app.contracts.events import (
    ASR_RECOGNITION_STARTED,
    ASR_TEXT_RECOGNIZED,
    STATE_CHANGE_REQUESTED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    VOICE_INPUT_REQUESTED,
    VOICE_RECORDING_FINISHED,
    VOICE_RECORDING_STARTED,
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


class FakeAudioRequiredProvider(ASRProvider):
    """ASR provider that requires audio_path."""

    requires_audio_path = True

    def __init__(self, transcript: str = "Recognized from audio", should_fail: bool = False) -> None:
        self._transcript = transcript
        self._should_fail = should_fail

    def recognize(self, request: ASRRequest) -> ASRResponse:
        if self._should_fail:
            raise ASRProviderError("Audio ASR failed")
        if request.audio_path is None:
            raise ASRProviderError("audio_path is required")
        return ASRResponse(text=self._transcript)


class CapturingAudioRequiredProvider(FakeAudioRequiredProvider):
    """Subclass that captures the ASRRequest."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._captured_request: ASRRequest | None = None

    def recognize(self, request: ASRRequest) -> ASRResponse:
        self._captured_request = request
        return super().recognize(request)


class FakeMicrophoneRecorder:
    """Fake microphone recorder for testing."""

    def __init__(self) -> None:
        self.record_called = False
        self.last_request = None
        self.should_fail = False

    def record(self, request):
        self.record_called = True
        self.last_request = request
        if self.should_fail:
            from app.input.audio import AudioRecordingError
            raise AudioRecordingError("microphone recording failed")
        return MagicMock(
            audio_path="/tmp/fake_recording.wav",
            duration_seconds=request.duration_seconds,
            sample_rate=request.sample_rate,
            channels=request.channels,
        )


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


class TestVoiceInputControllerWithRecorder:
    """Tests for VoiceInputController with microphone recording."""

    def _make_event(self) -> BaseEvent:
        return BaseEvent(
            event_type=VOICE_INPUT_REQUESTED,
            request_id="req-voice-rec-1",
            source="test",
            payload={},
        )

    def test_fake_asr_does_not_call_recorder(self) -> None:
        """Test that fake ASR does not call the microphone recorder."""
        event_bus = MagicMock()
        provider = FakeASRProviderForTest()
        fake_recorder = FakeMicrophoneRecorder()
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(
            event_bus=event_bus,
            provider=provider,
            dispatch_event=dispatch_event,
            recorder=fake_recorder,
            recording_output_dir=".tmp/asr",
            recording_duration_seconds=4.0,
            recording_sample_rate=16000,
            recording_channels=1,
        )
        controller.start()

        controller._on_voice_input_requested(self._make_event())
        time.sleep(0.05)

        assert not fake_recorder.record_called

    def test_audio_path_not_required_does_not_publish_recording_events(self) -> None:
        """Test that provider not requiring audio_path does not publish recording events."""
        event_bus = MagicMock()
        provider = FakeASRProviderForTest()
        fake_recorder = FakeMicrophoneRecorder()
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(
            event_bus=event_bus,
            provider=provider,
            dispatch_event=dispatch_event,
            recorder=fake_recorder,
            recording_output_dir=".tmp/asr",
            recording_duration_seconds=4.0,
            recording_sample_rate=16000,
            recording_channels=1,
        )
        controller.start()

        controller._on_voice_input_requested(self._make_event())
        time.sleep(0.05)

        recording_started = [e for e in dispatch_events if e.event_type == VOICE_RECORDING_STARTED]
        recording_finished = [e for e in dispatch_events if e.event_type == VOICE_RECORDING_FINISHED]
        assert len(recording_started) == 0
        assert len(recording_finished) == 0

    def test_audio_required_provider_calls_recorder(self) -> None:
        """Test that audio-required ASR provider calls the microphone recorder."""
        event_bus = MagicMock()
        provider = FakeAudioRequiredProvider()
        fake_recorder = FakeMicrophoneRecorder()
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(
            event_bus=event_bus,
            provider=provider,
            dispatch_event=dispatch_event,
            recorder=fake_recorder,
            recording_output_dir=".tmp/asr",
            recording_duration_seconds=4.0,
            recording_sample_rate=16000,
            recording_channels=1,
        )
        controller.start()

        controller._on_voice_input_requested(self._make_event())

        # Wait for worker thread to complete
        for _ in range(50):
            time.sleep(0.01)
            if fake_recorder.record_called:
                break

        assert fake_recorder.record_called

    def test_recorder_output_passed_to_asr_request(self) -> None:
        """Test that recorder output audio_path is passed to ASRRequest."""
        event_bus = MagicMock()
        provider = CapturingAudioRequiredProvider()
        fake_recorder = FakeMicrophoneRecorder()
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(
            event_bus=event_bus,
            provider=provider,
            dispatch_event=dispatch_event,
            recorder=fake_recorder,
            recording_output_dir=".tmp/asr",
            recording_duration_seconds=4.0,
            recording_sample_rate=16000,
            recording_channels=1,
        )
        controller.start()

        controller._on_voice_input_requested(self._make_event())

        # Wait for worker thread to complete
        for _ in range(50):
            time.sleep(0.01)
            if provider._captured_request is not None:
                break

        assert provider._captured_request is not None
        assert provider._captured_request.audio_path == "/tmp/fake_recording.wav"
        assert provider._captured_request.mime_type == "audio/wav"

    def test_recorder_raises_audio_recording_error(self) -> None:
        """Test that AudioRecordingError is converted to safe recording error."""
        event_bus = MagicMock()
        provider = FakeAudioRequiredProvider()
        fake_recorder = FakeMicrophoneRecorder()
        fake_recorder.should_fail = True
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(
            event_bus=event_bus,
            provider=provider,
            dispatch_event=dispatch_event,
            recorder=fake_recorder,
            recording_output_dir=".tmp/asr",
            recording_duration_seconds=4.0,
            recording_sample_rate=16000,
            recording_channels=1,
        )
        controller.start()

        controller._on_voice_input_requested(self._make_event())

        # Wait for worker thread to complete
        for _ in range(50):
            time.sleep(0.01)
            error_events = [e for e in dispatch_events if e.event_type == SYSTEM_ERROR]
            if error_events:
                break

        error_events = [e for e in dispatch_events if e.event_type == SYSTEM_ERROR]
        assert len(error_events) >= 1
        assert error_events[0].payload["message"] == "录音失败，请检查麦克风后重试。"
        assert "microphone recording failed" not in error_events[0].payload["message"]

    def test_recorder_error_dispatches_error_state(self) -> None:
        """Test that AudioRecordingError results in ERROR state with recording_error reason."""
        event_bus = MagicMock()
        provider = FakeAudioRequiredProvider()
        fake_recorder = FakeMicrophoneRecorder()
        fake_recorder.should_fail = True
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(
            event_bus=event_bus,
            provider=provider,
            dispatch_event=dispatch_event,
            recorder=fake_recorder,
            recording_output_dir=".tmp/asr",
            recording_duration_seconds=4.0,
            recording_sample_rate=16000,
            recording_channels=1,
        )
        controller.start()

        controller._on_voice_input_requested(self._make_event())

        # Wait for worker thread to complete
        for _ in range(50):
            time.sleep(0.01)
            error_state_events = [
                e for e in dispatch_events
                if e.event_type == STATE_CHANGE_REQUESTED
                and e.payload.get("target_state") == "error"
                and e.payload.get("reason") == "recording_error"
            ]
            if error_state_events:
                break

        error_state_events = [
            e for e in dispatch_events
            if e.event_type == STATE_CHANGE_REQUESTED
            and e.payload.get("target_state") == "error"
            and e.payload.get("reason") == "recording_error"
        ]
        assert len(error_state_events) >= 1

    def test_audio_required_publishes_recording_started(self) -> None:
        """Test that audio-required provider publishes VOICE_RECORDING_STARTED."""
        event_bus = MagicMock()
        provider = FakeAudioRequiredProvider()
        fake_recorder = FakeMicrophoneRecorder()
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(
            event_bus=event_bus,
            provider=provider,
            dispatch_event=dispatch_event,
            recorder=fake_recorder,
            recording_output_dir=".tmp/asr",
            recording_duration_seconds=4.0,
            recording_sample_rate=16000,
            recording_channels=1,
        )
        controller.start()

        controller._on_voice_input_requested(self._make_event())

        # Wait for worker thread to complete
        for _ in range(50):
            time.sleep(0.01)
            recording_started = [e for e in dispatch_events if e.event_type == VOICE_RECORDING_STARTED]
            if recording_started:
                break

        recording_started = [e for e in dispatch_events if e.event_type == VOICE_RECORDING_STARTED]
        assert len(recording_started) == 1
        assert "duration_seconds" in recording_started[0].payload

    def test_audio_required_publishes_recording_finished(self) -> None:
        """Test that audio-required provider publishes VOICE_RECORDING_FINISHED."""
        event_bus = MagicMock()
        provider = FakeAudioRequiredProvider()
        fake_recorder = FakeMicrophoneRecorder()
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(
            event_bus=event_bus,
            provider=provider,
            dispatch_event=dispatch_event,
            recorder=fake_recorder,
            recording_output_dir=".tmp/asr",
            recording_duration_seconds=4.0,
            recording_sample_rate=16000,
            recording_channels=1,
        )
        controller.start()

        controller._on_voice_input_requested(self._make_event())

        # Wait for worker thread to complete
        for _ in range(50):
            time.sleep(0.01)
            recording_finished = [e for e in dispatch_events if e.event_type == VOICE_RECORDING_FINISHED]
            if recording_finished:
                break

        recording_finished = [e for e in dispatch_events if e.event_type == VOICE_RECORDING_FINISHED]
        assert len(recording_finished) == 1
        assert "audio_path" in recording_finished[0].payload
        assert "duration_seconds" in recording_finished[0].payload
        assert "sample_rate" in recording_finished[0].payload
        assert "channels" in recording_finished[0].payload

    def test_audio_required_publishes_asr_recognition_started(self) -> None:
        """Test that audio-required provider publishes ASR_RECOGNITION_STARTED."""
        event_bus = MagicMock()
        provider = FakeAudioRequiredProvider()
        fake_recorder = FakeMicrophoneRecorder()
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(
            event_bus=event_bus,
            provider=provider,
            dispatch_event=dispatch_event,
            recorder=fake_recorder,
            recording_output_dir=".tmp/asr",
            recording_duration_seconds=4.0,
            recording_sample_rate=16000,
            recording_channels=1,
        )
        controller.start()

        controller._on_voice_input_requested(self._make_event())

        # Wait for worker thread to complete
        for _ in range(50):
            time.sleep(0.01)
            recognition_started = [e for e in dispatch_events if e.event_type == ASR_RECOGNITION_STARTED]
            if recognition_started:
                break

        recognition_started = [e for e in dispatch_events if e.event_type == ASR_RECOGNITION_STARTED]
        assert len(recognition_started) == 1

    def test_audio_required_successful_still_publishes_asr_text_recognized(self) -> None:
        """Test that successful audio-required ASR still publishes ASR_TEXT_RECOGNIZED."""
        event_bus = MagicMock()
        provider = FakeAudioRequiredProvider(transcript="识别成功")
        fake_recorder = FakeMicrophoneRecorder()
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(
            event_bus=event_bus,
            provider=provider,
            dispatch_event=dispatch_event,
            recorder=fake_recorder,
            recording_output_dir=".tmp/asr",
            recording_duration_seconds=4.0,
            recording_sample_rate=16000,
            recording_channels=1,
        )
        controller.start()

        controller._on_voice_input_requested(self._make_event())

        # Wait for worker thread to complete
        for _ in range(50):
            time.sleep(0.01)
            asr_events = [e for e in dispatch_events if e.event_type == ASR_TEXT_RECOGNIZED]
            if asr_events:
                break

        asr_events = [e for e in dispatch_events if e.event_type == ASR_TEXT_RECOGNIZED]
        assert len(asr_events) == 1
        assert asr_events[0].payload["text"] == "识别成功"

    def test_audio_required_successful_still_publishes_user_text_submitted(self) -> None:
        """Test that successful audio-required ASR still publishes USER_TEXT_SUBMITTED."""
        event_bus = MagicMock()
        provider = FakeAudioRequiredProvider(transcript="语音识别结果")
        fake_recorder = FakeMicrophoneRecorder()
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(
            event_bus=event_bus,
            provider=provider,
            dispatch_event=dispatch_event,
            recorder=fake_recorder,
            recording_output_dir=".tmp/asr",
            recording_duration_seconds=4.0,
            recording_sample_rate=16000,
            recording_channels=1,
        )
        controller.start()

        controller._on_voice_input_requested(self._make_event())

        # Wait for worker thread to complete
        for _ in range(50):
            time.sleep(0.01)
            user_events = [e for e in dispatch_events if e.event_type == USER_TEXT_SUBMITTED]
            if user_events:
                break

        user_events = [e for e in dispatch_events if e.event_type == USER_TEXT_SUBMITTED]
        assert len(user_events) == 1
        assert user_events[0].payload["text"] == "语音识别结果"

    def test_asr_provider_error_still_asr_error_reason(self) -> None:
        """Test that ASRProviderError results in ERROR state with asr_error reason."""
        event_bus = MagicMock()
        provider = FakeAudioRequiredProvider(should_fail=True)
        fake_recorder = FakeMicrophoneRecorder()
        dispatch_events, dispatch_event = make_dispatch_collector()
        controller = VoiceInputController(
            event_bus=event_bus,
            provider=provider,
            dispatch_event=dispatch_event,
            recorder=fake_recorder,
            recording_output_dir=".tmp/asr",
            recording_duration_seconds=4.0,
            recording_sample_rate=16000,
            recording_channels=1,
        )
        controller.start()

        controller._on_voice_input_requested(self._make_event())

        # Wait for worker thread to complete
        for _ in range(50):
            time.sleep(0.01)
            error_state_events = [
                e for e in dispatch_events
                if e.event_type == STATE_CHANGE_REQUESTED
                and e.payload.get("target_state") == "error"
                and e.payload.get("reason") == "asr_error"
            ]
            if error_state_events:
                break

        error_state_events = [
            e for e in dispatch_events
            if e.event_type == STATE_CHANGE_REQUESTED
            and e.payload.get("target_state") == "error"
            and e.payload.get("reason") == "asr_error"
        ]
        assert len(error_state_events) >= 1


class TestProviderCapabilityFlags:
    """Tests for ASR provider capability flags."""

    def test_fake_asr_provider_does_not_require_audio_path(self) -> None:
        """Test FakeASRProvider.requires_audio_path is False."""
        from app.input.asr.providers.fake import FakeASRProvider

        provider = FakeASRProvider()
        assert provider.requires_audio_path is False

    def test_mimo_asr_provider_requires_audio_path(self) -> None:
        """Test MimoASRProvider.requires_audio_path is True."""
        from app.input.asr.providers.mimo import MimoASRProvider

        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
        )
        assert provider.requires_audio_path is True

    def test_base_asr_provider_default_requires_audio_path(self) -> None:
        """Test ASRProvider default requires_audio_path is False."""
        from app.input.asr.providers.base import ASRProvider

        assert ASRProvider.requires_audio_path is False
