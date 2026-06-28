"""Application entry point."""

import logging
import sys
import uuid

from PySide6.QtWidgets import QApplication

from app.brain.dialogue_controller import DialogueController
from app.brain.prompts.registry import PromptRegistry
from app.brain.providers import ChatProviderError, create_chat_provider
from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGED,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.contracts.payloads import UserTextSubmittedPayload
from app.core.config import get_config
from app.core.event_bus import EventBus
from app.core.logging import setup_logging
from app.core.state_controller import StateController
from app.core.state_machine import StateMachine
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
    dialogue_controller = DialogueController(event_bus, provider, prompt_registry)

    # Start components
    state_controller.start()
    dialogue_controller.start()

    window.show()

    logger.info("Application started successfully")
    app.exec()


if __name__ == "__main__":
    main()
