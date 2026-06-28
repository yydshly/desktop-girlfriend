"""Application entry point."""

import logging
import sys
import uuid

from PySide6.QtWidgets import QApplication

from app.brain.async_dialogue_controller import AsyncDialogueController
from app.brain.prompts.registry import PromptRegistry
from app.brain.providers import ChatProviderError, create_chat_provider
from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.contracts.payloads import UserTextSubmittedPayload
from app.core.config import get_config
from app.core.event_bus import EventBus
from app.core.logging import setup_logging
from app.core.state_controller import StateController
from app.core.state_machine import StateMachine
from app.expression.tts.controller import TTSController
from app.expression.tts.providers.fake import FakeTTSProvider
from app.ui.qt_event_bridge import QtEventBridge
from app.ui.view_model import DesktopViewModel
from app.ui.window import DesktopWindow

logger = logging.getLogger(__name__)


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

    window = DesktopWindow(view_model, on_user_text_submitted=submit_user_text)

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

    # Initialize Dialogue components
    prompt_registry = PromptRegistry()
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

    dialogue_controller = AsyncDialogueController(
        event_bus=event_bus,
        provider=provider,
        prompt_registry=prompt_registry,
        dispatch_event=event_bridge.event_ready.emit,
    )

    # Initialize TTS components
    tts_provider = FakeTTSProvider(delay_seconds=0.1)
    tts_controller = TTSController(
        event_bus=event_bus,
        provider=tts_provider,
        dispatch_event=event_bridge.event_ready.emit,
    )

    # Start components
    state_controller.start()
    dialogue_controller.start()
    tts_controller.start()

    window.show()

    logger.info("Application started successfully")
    app.exec()


if __name__ == "__main__":
    main()
