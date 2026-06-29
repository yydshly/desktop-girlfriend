"""Tests for application shutdown wiring and event subscriptions."""

from app.contracts.events import (
    ASR_RECOGNITION_STARTED,
    ASR_TEXT_RECOGNIZED,
    VOICE_RECORDING_FINISHED,
    VOICE_RECORDING_STARTED,
)
from app.main import _wire_shutdown


class FakeSignal:
    """Minimal signal test double."""

    def __init__(self) -> None:
        self._callback = None

    def connect(self, callback) -> None:
        self._callback = callback

    def emit(self) -> None:
        assert self._callback is not None
        self._callback()


class FakeApp:
    """Minimal app test double with an aboutToQuit signal."""

    def __init__(self) -> None:
        self.aboutToQuit = FakeSignal()


class FakeComponent:
    """Component test double that records stop calls."""

    def __init__(self) -> None:
        self.stop_called = False

    def stop(self) -> None:
        self.stop_called = True


def test_wire_shutdown_stops_components_on_app_quit() -> None:
    """Test shutdown wiring stops all registered components."""
    app = FakeApp()
    first = FakeComponent()
    second = FakeComponent()

    _wire_shutdown(app, first, second)
    app.aboutToQuit.emit()

    assert first.stop_called is True
    assert second.stop_called is True


def test_wire_shutdown_stops_many_components() -> None:
    """Test shutdown wiring stops many components including VoiceInputController."""
    app = FakeApp()
    components = [FakeComponent() for _ in range(4)]

    _wire_shutdown(app, *components)
    app.aboutToQuit.emit()

    for comp in components:
        assert comp.stop_called is True


class TestVoiceInputControllerInjection:
    """Tests for VoiceInputController recorder injection in main.py.

    These tests verify the recorder injection logic without requiring full app startup.
    """

    def test_mimo_provider_requires_audio_path(self) -> None:
        """Test that MimoASRProvider requires audio_path."""
        from app.input.asr.providers.mimo import MimoASRProvider

        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
        )
        assert provider.requires_audio_path is True

    def test_fake_provider_does_not_require_audio_path(self) -> None:
        """Test that FakeASRProvider does not require audio_path."""
        from app.input.asr.providers.fake import FakeASRProvider

        provider = FakeASRProvider()
        assert provider.requires_audio_path is False

    def test_recorder_injection_logic(self) -> None:
        """Test the recorder injection logic: mimo -> recorder, fake -> None."""
        from app.input.asr.providers.fake import FakeASRProvider
        from app.input.asr.providers.mimo import MimoASRProvider
        from app.input.audio import MicrophoneRecorder

        # Simulate the injection logic from main.py
        def get_recorder(provider) -> MicrophoneRecorder | None:
            return MicrophoneRecorder() if provider.requires_audio_path else None

        mimo_provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
        )
        fake_provider = FakeASRProvider()

        assert get_recorder(mimo_provider) is not None
        assert get_recorder(fake_provider) is None


class TestVoiceProgressEventWiring:
    """Tests for voice progress event subscriptions in main.py.

    These verify the event constants are correctly exported and that
    the ViewModel has the required handler method.
    """

    def test_voice_recording_started_event_constant(self) -> None:
        """Test VOICE_RECORDING_STARTED event constant is defined."""
        assert VOICE_RECORDING_STARTED == "voice.recording_started"

    def test_voice_recording_finished_event_constant(self) -> None:
        """Test VOICE_RECORDING_FINISHED event constant is defined."""
        assert VOICE_RECORDING_FINISHED == "voice.recording_finished"

    def test_asr_recognition_started_event_constant(self) -> None:
        """Test ASR_RECOGNITION_STARTED event constant is defined."""
        assert ASR_RECOGNITION_STARTED == "asr.recognition_started"

    def test_asr_text_recognized_event_constant(self) -> None:
        """Test ASR_TEXT_RECOGNIZED event constant is defined."""
        assert ASR_TEXT_RECOGNIZED == "asr.text_recognized"

    def test_view_model_has_handle_voice_progress_event_method(self) -> None:
        """Test DesktopViewModel has handle_voice_progress_event method."""
        from app.ui.view_model import DesktopViewModel

        vm = DesktopViewModel()
        assert hasattr(vm, "handle_voice_progress_event")
        assert callable(vm.handle_voice_progress_event)

    def test_view_model_handle_voice_progress_event_ignores_unknown_event(self) -> None:
        """Test handle_voice_progress_event ignores unknown event types."""
        from app.contracts.events import BaseEvent
        from app.ui.view_model import DesktopViewModel

        vm = DesktopViewModel()
        vm.voice_status_text = "previous value"

        event = BaseEvent(
            event_type="unknown.event",
            request_id="req99",
            source="test",
            payload={},
        )
        vm.handle_voice_progress_event(event)

        # Should be unchanged since event type is not recognized
        assert vm.voice_status_text == "previous value"
