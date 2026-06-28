"""Application entry point."""

import logging
import sys

from PySide6.QtWidgets import QApplication

from app.contracts.events import STATE_CHANGED
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

    # Initialize Core components
    event_bus = EventBus()
    state_machine = StateMachine()

    # Initialize UI components
    view_model = DesktopViewModel()
    window = DesktopWindow(view_model)

    # Initialize StateController and wire EventBus + StateMachine
    state_controller = StateController(event_bus, state_machine)

    # Register ViewModel subscription to state.changed events
    def on_state_changed(event: object) -> None:
        view_model.handle_state_changed(event)  # type: ignore[arg-type]
        window.update_from_view_model()

    event_bus.subscribe(STATE_CHANGED, on_state_changed)

    # Start StateController to begin listening for state change requests
    state_controller.start()

    app = QApplication(sys.argv)
    window.show()

    logger.info("Application started successfully")
    app.exec()


if __name__ == "__main__":
    main()
