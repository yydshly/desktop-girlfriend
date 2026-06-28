"""Application configuration."""

import os

from dotenv import load_dotenv

# Load .env file if it exists (but do not require it)
load_dotenv()


class AppConfig:
    """Application configuration."""

    def __init__(self) -> None:
        self.app_env: str = os.getenv("APP_ENV", "dev")
        self.app_name: str = "Desktop Girlfriend"
        self.window_width: int = 360
        self.window_height: int = 480


_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get the global application config instance."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config
