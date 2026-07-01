"""Application entry point."""

import logging
import sys
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Protocol

from PySide6.QtCore import QTimer
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
    MEMORY_ADD_REQUESTED,
    MEMORY_ADDED,
    MEMORY_CONFIRM_REQUESTED,
    MEMORY_CONFIRMED,
    MEMORY_DELETE_REQUESTED,
    MEMORY_DELETED,
    MEMORY_ERROR,
    MEMORY_LIST_REQUESTED,
    MEMORY_LISTED,
    MEMORY_REJECT_REQUESTED,
    MEMORY_REJECTED,
    MEMORY_SUGGESTIONS_DETECTED,
    PROACTIVE_NUDGE_READY,
    STATE_CHANGED,
    SYSTEM_ERROR,
    TTS_STOP_REQUESTED,
    USER_TEXT_SUBMITTED,
    VOICE_INPUT_REQUESTED,
    VOICE_RECORDING_FINISHED,
    VOICE_RECORDING_STARTED,
    BaseEvent,
)
from app.contracts.payloads import (
    AssistantTextReceivedPayload,
    MemoryAddRequestedPayload,
    MemoryConfirmRequestedPayload,
    MemoryDeleteRequestedPayload,
    MemoryListRequestedPayload,
    MemoryRejectRequestedPayload,
    UserTextSubmittedPayload,
)
from app.contracts.states import AppState
from app.core.config import get_config
from app.core.event_bus import EventBus
from app.core.logging import setup_logging
from app.core.startup_diagnostics import run_startup_diagnostics
from app.core.state_controller import StateController
from app.core.state_machine import StateMachine
from app.core.version import get_app_version
from app.expression.tts.controller import TTSController
from app.expression.tts.providers import TTSProviderError, create_tts_provider
from app.input.asr.controller import VoiceInputController
from app.input.asr.providers import ASRProviderError, create_asr_provider
from app.input.audio import MicrophoneRecorder, MicrophoneRecorderLike
from app.ui.close_behavior import decide_close_behavior
from app.ui.live2d_bridge import Live2DBridgeEventDispatcher
from app.ui.live2d_bridge_server import Live2DBridgeServer
from app.ui.live2d_desktop_process import Live2DDesktopProcess
from app.ui.live2d_desktop_window import default_live2d_position_path
from app.ui.live2d_model_catalog import (
    render_live2d_model_catalog_summary,
    scan_live2d_model_catalog,
)
from app.ui.onboarding_view import build_onboarding_view, render_onboarding_text
from app.ui.product_status_builder import build_product_status_view
from app.ui.qt_event_bridge import QtEventBridge
from app.ui.settings_view import build_settings_view, render_settings_view_text
from app.ui.startup_diagnostics_view import render_startup_diagnostics_details
from app.ui.system_tray import DesktopSystemTrayController
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow

logger = logging.getLogger(__name__)


class _Stoppable(Protocol):
    def stop(self) -> None:
        """Stop the component."""


def build_live2d_control_log_context(
    *,
    action: str,
    scale: float,
    opacity: float,
    visible: bool,
) -> str:
    """Build a compact diagnostic context for Live2D desktop control actions."""

    return (
        f"action={action} "
        f"scale={scale:g} "
        f"opacity={opacity:g} "
        f"visible={visible}"
    )


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

    # V11-C: Run startup diagnostics (non-blocking, only for display)
    startup_diagnostics = run_startup_diagnostics(config)

    # V12-B: Get app version for display in status panel
    app_version = get_app_version()

    app = QApplication(sys.argv)

    # Initialize Core components
    event_bus = EventBus()
    state_machine = StateMachine()
    live2d_bridge_server = Live2DBridgeServer()
    live2d_bridge_dispatcher = Live2DBridgeEventDispatcher(
        subscribe=event_bus.subscribe,
        unsubscribe=event_bus.unsubscribe,
        broadcast=live2d_bridge_server.broadcast,
    )
    live2d_desktop_process = (
        Live2DDesktopProcess() if config.live2d_desktop_auto_launch else None
    )

    # Initialize UI components
    view_model = DesktopViewModel()
    live2d_model_root = (
        Path(__file__).resolve().parents[1]
        / "showcase-demo"
        / "live2d-prototype"
        / "assets"
        / "models"
    )
    live2d_model_packages = scan_live2d_model_catalog(live2d_model_root)
    live2d_model_summary = render_live2d_model_catalog_summary(live2d_model_packages)
    view_model.set_live2d_model_catalog_summary(live2d_model_summary)
    logger.info(
        "Live2D model catalog scanned root=%s packages=%d summary=%s",
        live2d_model_root,
        len(live2d_model_packages),
        live2d_model_summary,
    )
    # V11-C: Set diagnostics text for display in status panel
    view_model.set_startup_diagnostics_text(
        render_startup_diagnostics_details(startup_diagnostics)
    )

    # Initialize session history before DesktopWindow so callback can reference it
    session_history = CurrentSessionHistory(max_turns=6)

    # V12-rc2: Pre-build product status view so first button click works immediately
    view_model.set_product_status_view(
        build_product_status_view(
            config=config,
            avatar_action=view_model.avatar_action,
            startup_diagnostics=startup_diagnostics,
            app_version=app_version,
        )
    )
    # Phase 2-E: Pre-build settings view text
    view_model.set_settings_text(
        render_settings_view_text(build_settings_view(config, app_version=app_version))
    )
    # Phase 3-B: Initialize onboarding text
    view_model.set_onboarding_text(
        render_onboarding_text(build_onboarding_view(companion_name="小云"))
    )

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

    # Callback to request memory confirm (V8-I)
    def request_memory_confirm(pending_id: str) -> None:
        event_bus.publish(
            BaseEvent(
                event_type=MEMORY_CONFIRM_REQUESTED,
                request_id=str(uuid.uuid4()),
                source="desktop_window",
                payload=MemoryConfirmRequestedPayload(pending_id=pending_id).to_event_payload(),
            )
        )

    # Callback to request memory reject (V8-I)
    def request_memory_reject(pending_id: str) -> None:
        event_bus.publish(
            BaseEvent(
                event_type=MEMORY_REJECT_REQUESTED,
                request_id=str(uuid.uuid4()),
                source="desktop_window",
                payload=MemoryRejectRequestedPayload(
                    pending_id=pending_id,
                    reason="user_rejected",
                ).to_event_payload(),
            )
        )

    # Callback to request memory list (V8-J)
    def request_memory_list() -> None:
        event_bus.publish(
            BaseEvent(
                event_type=MEMORY_LIST_REQUESTED,
                request_id=str(uuid.uuid4()),
                source="desktop_window",
                payload=MemoryListRequestedPayload().to_event_payload(),
            )
        )

    # Callback to request memory delete (V8-J)
    def request_memory_delete(record_id: str) -> None:
        event_bus.publish(
            BaseEvent(
                event_type=MEMORY_DELETE_REQUESTED,
                request_id=str(uuid.uuid4()),
                source="desktop_window",
                payload=MemoryDeleteRequestedPayload(record_id=record_id).to_event_payload(),
            )
        )

    # Callback to request memory add (V8-J manual add)
    def request_memory_add(text: str) -> None:
        event_bus.publish(
            BaseEvent(
                event_type=MEMORY_ADD_REQUESTED,
                request_id=str(uuid.uuid4()),
                source="desktop_window",
                payload=MemoryAddRequestedPayload(text=text).to_event_payload(),
            )
        )

    # V11-A / V11-C: Product status callback
    def _on_product_status_requested() -> None:
        view_model.toggle_product_status_visible()
        view_model.set_product_status_view(
            build_product_status_view(
                config=config,
                avatar_action=view_model.avatar_action,
                startup_diagnostics=startup_diagnostics,
                app_version=app_version,
            )
        )
        # V12-rc2: update UI immediately so first click works before any events
        window.update_from_view_model()

    # Phase 2-F: System tray controller (created after window)
    tray_controller: DesktopSystemTrayController | None = None

    def _on_hide_requested() -> None:
        """Handle hide button click: hide window to tray."""
        if tray_controller is not None and tray_controller.available:
            tray_controller.hide_to_tray()
            view_model.set_hidden_to_tray(True)

    def _on_quit_from_tray() -> None:
        """Handle quit from tray menu (Phase 3-A)."""
        view_model.request_force_quit()
        app.quit()

    def _handle_close_requested() -> bool:
        """Handle window close event (Phase 3-A).

        Returns True to accept close and exit, False to hide to tray instead.
        """
        decision = decide_close_behavior(
            tray_available=view_model.tray_available,
            force_quit=view_model.force_quit_requested,
        )
        if decision.should_hide_to_tray and tray_controller is not None:
            tray_controller.hide_to_tray()
            view_model.set_hidden_to_tray(True)
            return False
        return decision.should_accept_close

    live2d_desktop_scale = 1.0
    live2d_desktop_opacity = 1.0
    live2d_desktop_visible = live2d_desktop_process is not None

    def _restart_live2d_desktop() -> None:
        if live2d_desktop_process is None:
            return
        live2d_desktop_process.stop()
        live2d_desktop_process.scale = live2d_desktop_scale
        live2d_desktop_process.opacity = live2d_desktop_opacity
        if live2d_desktop_visible:
            live2d_desktop_process.start()

    def _on_live2d_scale_up_requested() -> None:
        nonlocal live2d_desktop_scale
        live2d_desktop_scale = min(1.35, round(live2d_desktop_scale + 0.1, 2))
        logger.info(
            "Live2D desktop control requested %s",
            build_live2d_control_log_context(
                action="scale_up",
                scale=live2d_desktop_scale,
                opacity=live2d_desktop_opacity,
                visible=live2d_desktop_visible,
            ),
        )
        _restart_live2d_desktop()

    def _on_live2d_scale_down_requested() -> None:
        nonlocal live2d_desktop_scale
        live2d_desktop_scale = max(0.65, round(live2d_desktop_scale - 0.1, 2))
        logger.info(
            "Live2D desktop control requested %s",
            build_live2d_control_log_context(
                action="scale_down",
                scale=live2d_desktop_scale,
                opacity=live2d_desktop_opacity,
                visible=live2d_desktop_visible,
            ),
        )
        _restart_live2d_desktop()

    def _on_live2d_opacity_down_requested() -> None:
        nonlocal live2d_desktop_opacity
        live2d_desktop_opacity = max(0.45, round(live2d_desktop_opacity - 0.1, 2))
        logger.info(
            "Live2D desktop control requested %s",
            build_live2d_control_log_context(
                action="opacity_down",
                scale=live2d_desktop_scale,
                opacity=live2d_desktop_opacity,
                visible=live2d_desktop_visible,
            ),
        )
        _restart_live2d_desktop()

    def _on_live2d_opacity_up_requested() -> None:
        nonlocal live2d_desktop_opacity
        live2d_desktop_opacity = min(1.0, round(live2d_desktop_opacity + 0.1, 2))
        logger.info(
            "Live2D desktop control requested %s",
            build_live2d_control_log_context(
                action="opacity_up",
                scale=live2d_desktop_scale,
                opacity=live2d_desktop_opacity,
                visible=live2d_desktop_visible,
            ),
        )
        _restart_live2d_desktop()

    def _on_live2d_visibility_toggled() -> None:
        nonlocal live2d_desktop_visible
        if live2d_desktop_process is None:
            return
        live2d_desktop_visible = not live2d_desktop_visible
        logger.info(
            "Live2D desktop control requested %s",
            build_live2d_control_log_context(
                action="toggle_visibility",
                scale=live2d_desktop_scale,
                opacity=live2d_desktop_opacity,
                visible=live2d_desktop_visible,
            ),
        )
        if live2d_desktop_visible:
            live2d_desktop_process.start()
        else:
            live2d_desktop_process.stop()

    def _on_live2d_position_reset_requested() -> None:
        position_path = default_live2d_position_path()
        if position_path.exists():
            position_path.unlink()
        logger.info(
            "Live2D desktop control requested %s position_path=%s",
            build_live2d_control_log_context(
                action="reset_position",
                scale=live2d_desktop_scale,
                opacity=live2d_desktop_opacity,
                visible=live2d_desktop_visible,
            ),
            position_path,
        )
        _restart_live2d_desktop()

    window = DesktopWindow(
        view_model,
        on_user_text_submitted=submit_user_text,
        on_conversation_cleared=clear_conversation,
        on_tts_stop_requested=request_tts_stop,
        on_voice_input_requested=request_voice_input,
        on_memory_confirm_requested=request_memory_confirm,
        on_memory_reject_requested=request_memory_reject,
        on_memory_list_requested=request_memory_list,
        on_memory_delete_requested=request_memory_delete,
        on_add_manual_memory_requested=request_memory_add,
        on_product_status_requested=_on_product_status_requested,
        on_hide_requested=_on_hide_requested,
        on_close_requested=_handle_close_requested,
        on_live2d_scale_up_requested=_on_live2d_scale_up_requested,
        on_live2d_scale_down_requested=_on_live2d_scale_down_requested,
        on_live2d_opacity_down_requested=_on_live2d_opacity_down_requested,
        on_live2d_opacity_up_requested=_on_live2d_opacity_up_requested,
        on_live2d_visibility_toggled=_on_live2d_visibility_toggled,
        on_live2d_position_reset_requested=_on_live2d_position_reset_requested,
        memory_management_enabled=config.memory_management_enabled,
    )

    # Create tray controller after window exists
    tray_controller = DesktopSystemTrayController(
        window=window,
        on_quit=_on_quit_from_tray,
    )
    view_model.set_tray_available(tray_controller.available)

    # Initialize StateController and wire EventBus + StateMachine
    state_controller = StateController(event_bus, state_machine)

    # Register ViewModel subscription to state.changed events
    def on_state_changed(event: BaseEvent) -> None:
        view_model.handle_state_changed(event)
        window.update_from_view_model()
        # V11-A / V11-C: refresh product status panel if visible
        if view_model.product_status_visible:
            view_model.set_product_status_view(
                build_product_status_view(
                    config=config,
                    avatar_action=view_model.avatar_action,
                    startup_diagnostics=startup_diagnostics,
                    app_version=app_version,
                )
            )

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

    # Register ViewModel subscription to memory events (V8-I)
    def on_memory_suggestions_detected(event: BaseEvent) -> None:
        view_model.handle_memory_suggestions_detected(event)
        window.update_from_view_model()

    event_bus.subscribe(MEMORY_SUGGESTIONS_DETECTED, on_memory_suggestions_detected)

    def on_memory_confirmed(event: BaseEvent) -> None:
        view_model.handle_memory_confirmed(event)
        window.update_from_view_model()

    event_bus.subscribe(MEMORY_CONFIRMED, on_memory_confirmed)

    def on_memory_rejected(event: BaseEvent) -> None:
        view_model.handle_memory_rejected(event)
        window.update_from_view_model()

    event_bus.subscribe(MEMORY_REJECTED, on_memory_rejected)

    def on_memory_error(event: BaseEvent) -> None:
        view_model.handle_memory_error(event)
        window.update_from_view_model()

    event_bus.subscribe(MEMORY_ERROR, on_memory_error)

    # Register ViewModel subscription to memory management events (V8-J)
    def on_memory_listed(event: BaseEvent) -> None:
        view_model.handle_memory_listed(event)
        window.update_from_view_model()

    event_bus.subscribe(MEMORY_LISTED, on_memory_listed)

    def on_memory_deleted(event: BaseEvent) -> None:
        view_model.handle_memory_deleted(event)
        window.update_from_view_model()

    event_bus.subscribe(MEMORY_DELETED, on_memory_deleted)

    # Register ViewModel subscription to memory.added (V8-J manual add)
    def on_memory_added(event: BaseEvent) -> None:
        view_model.handle_memory_added(event)
        # Immediately refresh the memory list so the new record appears
        request_memory_list()
        window.update_from_view_model()

    event_bus.subscribe(MEMORY_ADDED, on_memory_added)

    # Register ViewModel subscription to proactive nudge events (V9-A / V9-B / V10-C)
    def on_proactive_nudge_ready(event: BaseEvent) -> None:
        text = event.payload.get("text")
        if not isinstance(text, str) or not text.strip():
            return

        if config.proactive_tts_enabled:
            # V10-C: Always update avatar visual state for proactive nudge.
            view_model.handle_proactive_avatar_hint(event)
            window.update_from_view_model()
            # V9-B: route to TTS pipeline via ASSISTANT_TEXT_RECEIVED
            # This triggers both TTSController (plays audio) and
            # ViewModel's on_assistant_text_received (appends to chat_messages)
            event_bus.publish(
                BaseEvent(
                    event_type=ASSISTANT_TEXT_RECEIVED,
                    request_id=event.request_id,
                    source="proactive_controller",
                    payload=AssistantTextReceivedPayload(text=text).to_event_payload(),
                )
            )
            return

        # V9-A: text-only mode, direct to ViewModel (appends message + sets avatar)
        view_model.handle_proactive_nudge_ready(event)
        window.update_from_view_model()

    event_bus.subscribe(PROACTIVE_NUDGE_READY, on_proactive_nudge_ready)

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

    # V8-H / V8-J Patch: Create memory controller if suggestions or management is enabled
    memory_suggestion_controller = None
    memory_runtime = None

    memory_runtime_enabled = (
        config.memory_suggestions_enabled
        or config.memory_management_enabled
    )

    if memory_runtime_enabled:
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

    # V9-A: Proactive nudge controller
    proactive_controller = None
    proactive_timer = None

    if config.proactive_enabled:
        from app.brain.proactive.controller import ProactiveController
        from app.brain.proactive.service import ProactiveNudgeConfig, ProactiveNudgeService

        proactive_service = ProactiveNudgeService(
            ProactiveNudgeConfig(
                enabled=config.proactive_enabled,
                idle_seconds=config.proactive_idle_seconds,
                cooldown_seconds=config.proactive_cooldown_seconds,
                max_per_session=config.proactive_max_per_session,
                quiet_hours_enabled=config.proactive_quiet_hours_enabled,
                quiet_start_hour=config.proactive_quiet_start_hour,
                quiet_end_hour=config.proactive_quiet_end_hour,
                feedback_pause_seconds=config.proactive_feedback_pause_seconds,
            )
        )
        proactive_controller = ProactiveController(
            service=proactive_service,
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
    live2d_bridge_server.start()
    live2d_bridge_dispatcher.start()
    if live2d_desktop_process is not None:
        live2d_desktop_process.start()
    tts_controller.start()
    dialogue_controller.start()
    voice_input_controller.start()
    if memory_suggestion_controller is not None:
        memory_suggestion_controller.start()

    # V9-A: Start proactive nudge controller and timer
    if proactive_controller is not None:
        proactive_controller.start()

        proactive_timer = QTimer()
        proactive_timer.setInterval(10_000)
        proactive_timer.timeout.connect(
            lambda: proactive_controller.tick(
                is_busy=view_model.state in {
                    AppState.LISTENING,
                    AppState.THINKING,
                    AppState.SPEAKING,
                }
            )
        )
        proactive_timer.start()

    shutdown_components: list[object] = [
        voice_input_controller,
        tts_controller,
        dialogue_controller,
        state_controller,
        live2d_bridge_dispatcher,
        live2d_bridge_server,
    ]
    if memory_suggestion_controller is not None:
        shutdown_components.append(memory_suggestion_controller)
    if proactive_controller is not None:
        shutdown_components.append(proactive_controller)
    if live2d_desktop_process is not None:
        shutdown_components.append(live2d_desktop_process)
    _wire_shutdown(app, *shutdown_components)  # type: ignore[arg-type]

    window.show()
    # Phase 3-B: Ensure onboarding card and all UI labels are populated on first frame
    window.update_from_view_model()

    logger.info("Application started successfully")
    app.exec()


if __name__ == "__main__":
    main()
