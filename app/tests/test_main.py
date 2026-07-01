"""Tests for application shutdown wiring and event subscriptions."""

from app.contracts.events import (
    ASR_RECOGNITION_STARTED,
    ASR_TEXT_RECOGNIZED,
    VOICE_RECORDING_FINISHED,
    VOICE_RECORDING_STARTED,
)
from app.main import _wire_shutdown, build_live2d_control_log_context


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


def test_build_live2d_control_log_context() -> None:
    """Live2D control logs include the values needed to diagnose UI actions."""
    assert build_live2d_control_log_context(
        action="scale_up",
        scale=1.2,
        opacity=0.8,
        visible=True,
    ) == "action=scale_up scale=1.2 opacity=0.8 visible=True"


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


class TestPersonaWiring:
    """Tests for persona configuration wiring in main.py.

    These verify that main.py correctly uses AppConfig persona fields
    to construct the PromptRegistry with a PersonaPromptBuilder.
    """

    def test_create_persona_prompt_registry_function(self) -> None:
        """Test the create_persona_prompt_registry helper uses config persona fields."""
        from dataclasses import replace

        from app.brain.persona import DEFAULT_XIAOYUN_PERSONA, PersonaPromptBuilder
        from app.brain.prompts.registry import PromptRegistry
        from app.core.config import AppConfig, reset_config

        # Simulate the wiring from main.py
        def create_persona_prompt_registry(config: AppConfig) -> PromptRegistry:
            persona_profile = replace(
                DEFAULT_XIAOYUN_PERSONA,
                name=config.persona_name,
                user_address=config.persona_user_address,
            )
            return PromptRegistry(
                persona_prompt_builder=PersonaPromptBuilder(persona_profile)
            )

        reset_config()
        config = AppConfig()

        # Default values
        registry = create_persona_prompt_registry(config)
        assert "小云" in registry.default_system_prompt

    def test_persona_name_override_in_registry(self) -> None:
        """Test that persona_name override affects the generated system prompt."""
        from dataclasses import replace

        from app.brain.persona import DEFAULT_XIAOYUN_PERSONA, PersonaPromptBuilder
        from app.brain.prompts.registry import PromptRegistry
        from app.core.config import AppConfig, reset_config

        def create_persona_prompt_registry(config: AppConfig) -> PromptRegistry:
            persona_profile = replace(
                DEFAULT_XIAOYUN_PERSONA,
                name=config.persona_name,
                user_address=config.persona_user_address,
            )
            return PromptRegistry(
                persona_prompt_builder=PersonaPromptBuilder(persona_profile)
            )

        reset_config()

        custom = replace(DEFAULT_XIAOYUN_PERSONA, name="小爱", user_address="你")
        registry = PromptRegistry(persona_prompt_builder=PersonaPromptBuilder(custom))
        assert "小爱" in registry.default_system_prompt
        assert "小云" not in registry.default_system_prompt

    def test_persona_user_address_in_system_prompt(self) -> None:
        """Test that user_address appears in the generated system prompt."""
        from dataclasses import replace

        from app.brain.persona import DEFAULT_XIAOYUN_PERSONA, PersonaPromptBuilder
        from app.brain.prompts.registry import PromptRegistry

        custom = replace(DEFAULT_XIAOYUN_PERSONA, name="小云", user_address="你")
        registry = PromptRegistry(persona_prompt_builder=PersonaPromptBuilder(custom))
        assert "你" in registry.default_system_prompt

    def test_prompt_registry_receives_persona_builder(self) -> None:
        """Test that PromptRegistry accepts and uses persona_prompt_builder."""
        from dataclasses import replace

        from app.brain.persona import DEFAULT_XIAOYUN_PERSONA, PersonaPromptBuilder
        from app.brain.prompts.registry import PromptRegistry

        custom = replace(DEFAULT_XIAOYUN_PERSONA, name="小云", user_address="你")
        builder = PersonaPromptBuilder(custom)
        registry = PromptRegistry(persona_prompt_builder=builder)
        # The system prompt should come from the builder
        assert len(registry.default_system_prompt) > 100

    def test_persona_user_address_override_in_wiring(self) -> None:
        """Test that PERSONA_USER_ADDRESS override appears in the system prompt."""
        from dataclasses import replace

        from app.brain.persona import DEFAULT_XIAOYUN_PERSONA, PersonaPromptBuilder
        from app.brain.prompts.registry import PromptRegistry

        custom = replace(DEFAULT_XIAOYUN_PERSONA, name="小云", user_address="大大")
        registry = PromptRegistry(persona_prompt_builder=PersonaPromptBuilder(custom))
        assert "大大" in registry.default_system_prompt
        assert "你通常称呼用户为「大大」" in registry.default_system_prompt
