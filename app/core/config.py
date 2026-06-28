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

        # Chat provider configuration
        self.chat_provider_mode: str = os.getenv("CHAT_PROVIDER_MODE", "fake")
        self.minimax_api_key: str | None = os.getenv("MINIMAX_API_KEY")
        self.minimax_group_id: str | None = os.getenv("MINIMAX_GROUP_ID")
        self.minimax_base_url: str = os.getenv(
            "MINIMAX_BASE_URL", "https://api.minimax.chat/v1"
        )
        self.minimax_model: str = os.getenv("MINIMAX_MODEL", "MiniMax-Text-01")
        self.minimax_timeout_seconds: float = float(
            os.getenv("MINIMAX_TIMEOUT_SECONDS", "30.0")
        )
        self.minimax_chat_path: str = os.getenv(
            "MINIMAX_CHAT_PATH", "/text/chatcompletion_v2"
        )

        # TTS provider configuration
        self.tts_provider_mode: str = os.getenv("TTS_PROVIDER_MODE", "fake")
        self.minimax_tts_api_key: str | None = os.getenv(
            "MINIMAX_TTS_API_KEY", self.minimax_api_key
        )
        self.minimax_tts_group_id: str | None = os.getenv(
            "MINIMAX_TTS_GROUP_ID", self.minimax_group_id
        )
        self.minimax_tts_base_url: str = os.getenv(
            "MINIMAX_TTS_BASE_URL", "https://api.minimax.chat/v1"
        )
        self.minimax_tts_model: str = os.getenv("MINIMAX_TTS_MODEL", "speech-02-hd")
        self.minimax_tts_voice_id: str = os.getenv("MINIMAX_TTS_VOICE_ID", "female-shaonv")
        self.minimax_tts_timeout_seconds: float = float(
            os.getenv("MINIMAX_TTS_TIMEOUT_SECONDS", "30.0")
        )
        self.minimax_tts_path: str = os.getenv("MINIMAX_TTS_PATH", "/t2a_v2")
        self.minimax_tts_output_dir: str = os.getenv("MINIMAX_TTS_OUTPUT_DIR", ".tmp/tts")


_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get the global application config instance."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reset_config() -> None:
    """Reset the global config instance. Useful for testing."""
    global _config
    _config = None
