"""Application entry point."""

import logging
import sys

from PySide6.QtWidgets import QApplication

from app.core.config import get_config
from app.core.logging import setup_logging
from app.ui.window import DesktopWindow

logger = logging.getLogger(__name__)


def main() -> None:
    """Main application entry point."""
    config = get_config()
    setup_logging(config.app_env)

    logger.info("Starting %s", config.app_name)

    app = QApplication(sys.argv)
    window = DesktopWindow()
    window.show()

    logger.info("Application started successfully")
    app.exec()


if __name__ == "__main__":
    main()
