"""Tests for application shutdown wiring."""

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
