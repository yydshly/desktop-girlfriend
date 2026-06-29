"""Application entry point."""

import logging
import sys
import uuid
from dataclasses import replace
from typing import Protocol

from PySide6.QtWidgets import QApplication

from app.brain.async_dialogue_controller import AsyncDialogueController
from app.brain.persona import DEFAULT_XIAOYUN_PERSONA, PersonaPromptBuilder
from app.brain.prompts.history import CurrentSessionHistory
from app.brain.prompts.registry import PromptRegistry
from app.brain.providers import ChatProviderError, create_chat_provider
from app.contracts.events import (
    ASR_RECOGNITION_STARTED,
    ASR_TEXT_RECOGNIZED,
    ASSISTANT_TEXT_RECEIVED,
    CONVERSATION_CLEARED,
    STATE_CHANGED,
    SYSTEM_ERROR,
    TTS_STOP_REQUESTED,
    USER_TEXT_SUBMITTED,
    VOICE_INPUT_REQUESTED,
    VOICE_RECORDING_FINISHED,
    VOICE_RECORDING_STARTED,
    BaseEvent,
)
from app.contracts.payloads import UserTextSubmittedPayload
from app.core.config import get_config
from app.core.event_bus import EventBus
from app.core.logging import setup_logging
from app.core.state_controller import StateController
from app.core.state_machine import StateMachine
from app.expression.tts.controller import TTSController
from app.expression.tts.providers import TTSProviderError, create_tts_provider
from app.input.asr.controller import VoiceInputController
from app.input.asr.providers import ASRProviderError, create_asr_provider
from app.input.audio import MicrophoneRecorder, MicrophoneRecorderLike
from app.ui.qt_event_bridge import QtEventBridge
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow

logger = logging.getLogger(__name__)


class _Stoppable(Protocol):
    def stop(self) -> None:
        """Stop the component."""


def _wire_shutdown(
    app: object, *components: _Stoppable
) -> None:
    """Stop components when the Qt application is about to quit."""

    def stop_components() -> None:
        for component in components:
            component.stop()

    # Narrow to the minimal interface we actually use at runtime
    if hasattr(app, "aboutToQuit"):
        signal: object = getattr(app, "aboutToQuit")
        if hasattr(signal, "connect"):
            signal.connect(stop_components)


def main() -> None:
    """Main application entry point."""
    config = get_config()
    setup_logging(config.app_env)

    logger.info("Starting %s", config.app_name)

    app = QApplication(sys.argv)

    # Initialize Core components
    event_bus = EventBus()
    state_machine = StateMachine()

    # Initialize UI components
    view_model = DesktopViewModel()

    # Initialize session history before DesktopWindow so callback can reference it
    session_history = CurrentSessionHistory(max_turns=6)

    # Callback to submit user text via EventBus
    def submit_user_text(text: str) -> None:
        event_bus.publish(
            BaseEvent(
                event_type=USER_TEXT_SUBMITTED,
                request_id=str(uuid.uuid4()),
                source="desktop_window",
                payload=UserTextSubmittedPayload(text=text).to_event_payload(),
            )
        )

    # Callback to clear conversation
    def clear_conversation() -> None:
        event_bus.publish(
            BaseEvent(
                event_type=CONVERSATION_CLEARED,
                request_id=str(uuid.uuid4()),
                source="desktop_window",
                payload={},
            )
        )

    # Callback to request TTS stop
    def request_tts_stop() -> None:
        event_bus.publish(
            BaseEvent(
                event_type=TTS_STOP_REQUESTED,
                request_id=str(uuid.uuid4()),
                source="desktop_window",
                payload={},
            )
        )

    # Callback to request voice input
    def request_voice_input() -> None:
        event_bus.publish(
            BaseEvent(
                event_type=VOICE_INPUT_REQUESTED,
                request_id=str(uuid.uuid4()),
                source="desktop_window",
                payload={},
            )
        )

    window = DesktopWindow(
        view_model,
        on_user_text_submitted=submit_user_text,
        on_conversation_cleared=clear_conversation,
        on_tts_stop_requested=request_tts_stop,
        on_voice_input_requested=request_voice_input,
    )

    # Initialize StateController and wire EventBus + StateMachine
    state_controller = StateController(event_bus, state_machine)

    # Register ViewModel subscription to state.changed events
    def on_state_changed(event: BaseEvent) -> None:
        view_model.handle_state_changed(event)
        window.update_from_view_model()

    event_bus.subscribe(STATE_CHANGED, on_state_changed)

    # Register ViewModel subscription to assistant.text_received events
    def on_assistant_text_received(event: BaseEvent) -> None:
        view_model.handle_assistant_text_received(event)
        window.update_from_view_model()

    event_bus.subscribe(ASSISTANT_TEXT_RECEIVED, on_assistant_text_received)

    # Register ViewModel subscription to system.error events
    def on_system_error(event: BaseEvent) -> None:
        view_model.handle_system_error(event)
        window.update_from_view_model()

    event_bus.subscribe(SYSTEM_ERROR, on_system_error)

    # Register ViewModel subscription to user.text_submitted events (before dialogue controller starts)
    def on_user_text_submitted(event: BaseEvent) -> None:
        view_model.handle_user_text_submitted(event)
        window.update_from_view_model()

    event_bus.subscribe(USER_TEXT_SUBMITTED, on_user_text_submitted)

    # Register ViewModel subscription to voice progress events
    def on_voice_progress_event(event: BaseEvent) -> None:
        view_model.handle_voice_progress_event(event)
        window.update_from_view_model()

    event_bus.subscribe(VOICE_RECORDING_STARTED, on_voice_progress_event)
    event_bus.subscribe(VOICE_RECORDING_FINISHED, on_voice_progress_event)
    event_bus.subscribe(ASR_RECOGNITION_STARTED, on_voice_progress_event)
    event_bus.subscribe(ASR_TEXT_RECOGNIZED, on_voice_progress_event)

    # Register handler for conversation.cleared events
    def on_conversation_cleared(event: BaseEvent) -> None:
        session_history.clear()
        view_model.handle_conversation_cleared(event)
        window.update_from_view_model()

    event_bus.subscribe(CONVERSATION_CLEARED, on_conversation_cleared)

    # Initialize Dialogue components
    persona_profile = replace(
        DEFAULT_XIAOYUN_PERSONA,
        name=config.persona_name,
        user_address=config.persona_user_address,
    )
    prompt_registry = PromptRegistry(
        persona_prompt_builder=PersonaPromptBuilder(persona_profile)
    )
    try:
        provider = create_chat_provider(config)
    except ChatProviderError:
        logger.exception(
            "Failed to create configured chat provider; falling back to FakeChatProvider"
        )
        from app.brain.providers.fake import FakeChatProvider

        provider = FakeChatProvider(
            reply_text="Provider configuration error. Falling back to fake response."
        )

    # Create Qt event bridge for thread-safe event dispatch
    event_bridge = QtEventBridge(event_bus.publish)

    # V8-G: Create read-only memory context provider if enabled
    session_memory_context_provider = None
    if config.memory_context_enabled:
        from app.brain.memory.integration import (
            create_memory_context_provider_from_config,
        )

        session_memory_context_provider = create_memory_context_provider_from_config(config)

    # V8-H: Create memory suggestion controller if enabled
    memory_suggestion_controller = None
    memory_runtime = None
    if config.memory_suggestions_enabled:
        from pathlib import Path

        from app.brain.memory.controller import MemorySuggestionController
        from app.brain.memory.repository import LocalJsonMemoryRepository
        from app.brain.memory.runtime import create_local_memory_runtime

        memory_repository = LocalJsonMemoryRepository(Path(config.memory_store_path))
        memory_runtime = create_local_memory_runtime(memory_repository)
        memory_suggestion_controller = MemorySuggestionController(
            runtime=memory_runtime,
            subscribe=event_bus.subscribe,
            unsubscribe=event_bus.unsubscribe,
            dispatch_event=event_bridge.event_ready.emit,
        )

    dialogue_controller = AsyncDialogueController(
        event_bus=event_bus,
        provider=provider,
        prompt_registry=prompt_registry,
        dispatch_event=event_bridge.event_ready.emit,
        session_history=session_history,
        complete_state_after_assistant_response=False,
        session_memory_context_provider=session_memory_context_provider,
    )

    # Initialize TTS components
    try:
        tts_provider = create_tts_provider(config)
    except TTSProviderError:
        logger.exception("Failed to create configured TTS provider; falling back to FakeTTSProvider")
        from app.expression.tts.providers.fake import FakeTTSProvider

        tts_provider = FakeTTSProvider(delay_seconds=0.1)

    # Create QtAudioPlayer for embedded audio playback (after QApplication is created)
    from app.expression.tts.player import QtAudioPlayer

    audio_player = QtAudioPlayer()

    tts_controller = TTSController(
        event_bus=event_bus,
        provider=tts_provider,
        dispatch_event=event_bridge.event_ready.emit,
        audio_player=audio_player,
    )

    # Initialize ASR components
    try:
        asr_provider = create_asr_provider(config)
    except ASRProviderError:
        logger.exception("Failed to create configured ASR provider; falling back to FakeASRProvider")
        from app.input.asr.providers.fake import FakeASRProvider

        asr_provider = FakeASRProvider()

    # Inject microphone recorder only when the ASR provider requires audio input
    recorder: MicrophoneRecorderLike | None = (
        MicrophoneRecorder() if asr_provider.requires_audio_path else None
    )

    voice_input_controller = VoiceInputController(
        event_bus=event_bus,
        provider=asr_provider,
        dispatch_event=event_bridge.event_ready.emit,
        recorder=recorder,
        recording_output_dir=config.asr_recording_output_dir,
        recording_duration_seconds=config.asr_recording_default_seconds,
        recording_sample_rate=config.asr_recording_sample_rate,
        recording_channels=config.asr_recording_channels,
    )

    # Start components
    # TTSController (consumer of ASSISTANT_TEXT_RECEIVED) starts before
    # DialogueController (producer) so it is ready to transition to SPEAKING
    # before DialogueController would send IDLE.
    state_controller.start()
    tts_controller.start()
    dialogue_controller.start()
    voice_input_controller.start()
    if memory_suggestion_controller is not None:
        memory_suggestion_controller.start()

    shutdown_components: list[object] = [
        voice_input_controller,
        tts_controller,
        dialogue_controller,
        state_controller,
    ]
    if memory_suggestion_controller is not None:
        shutdown_components.append(memory_suggestion_controller)
    _wire_shutdown(app, *shutdown_components)  # type: ignore[arg-type]

    window.show()

    logger.info("Application started successfully")
    app.exec()


if __name__ == "__main__":
    main()
