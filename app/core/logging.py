"""Logging configuration."""

import logging
import sys


def setup_logging(app_env: str = "dev") -> None:
    """Configure application logging.

    Args:
        app_env: Application environment (dev, prod, etc.)
    """
    level = logging.INFO if app_env == "dev" else logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(asctime)s / %(levelname)s / %(name)s / %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
