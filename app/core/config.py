"""Application configuration."""

import os

from dotenv import load_dotenv

# Load .env file if it exists (but do not require it)
load_dotenv()


def _env_or_fallback(name: str, fallback: str | None) -> str | None:
    """Return env value if set and non-blank, otherwise return fallback."""
    value = os.getenv(name)
    if value is None or not value.strip():
        return fallback
    return value


def _env_or_default(name: str, default: str) -> str:
    """Return env value if set and non-blank, otherwise return default."""
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value


def _env_float_or_default(name: str, default: str) -> float:
    """Return an environment float or raise a clear configuration error."""
    value = _env_or_default(name, default)
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc


def _env_int_or_default(name: str, default: str) -> int:
    """Return an environment integer or raise a clear configuration error."""
    value = _env_or_default(name, default)
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


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
        self.minimax_timeout_seconds: float = _env_float_or_default(
            "MINIMAX_TIMEOUT_SECONDS", "30.0"
        )
        self.minimax_chat_path: str = os.getenv(
            "MINIMAX_CHAT_PATH", "/text/chatcompletion_v2"
        )

        # TTS provider configuration
        self.tts_provider_mode: str = _env_or_default("TTS_PROVIDER_MODE", "fake")
        self.minimax_tts_api_key: str | None = _env_or_fallback(
            "MINIMAX_TTS_API_KEY", self.minimax_api_key
        )
        self.minimax_tts_group_id: str | None = _env_or_fallback(
            "MINIMAX_TTS_GROUP_ID", self.minimax_group_id
        )
        self.minimax_tts_base_url: str = _env_or_default(
            "MINIMAX_TTS_BASE_URL", "https://api.minimax.chat/v1"
        )
        self.minimax_tts_model: str = _env_or_default("MINIMAX_TTS_MODEL", "speech-02-hd")
        self.minimax_tts_voice_id: str = _env_or_default(
            "MINIMAX_TTS_VOICE_ID", "female-shaonv"
        )
        self.minimax_tts_timeout_seconds: float = _env_float_or_default(
            "MINIMAX_TTS_TIMEOUT_SECONDS", "30.0"
        )
        self.minimax_tts_path: str = _env_or_default("MINIMAX_TTS_PATH", "/t2a_v2")
        self.minimax_tts_output_dir: str = _env_or_default(
            "MINIMAX_TTS_OUTPUT_DIR", ".tmp/tts"
        )

        # ASR provider configuration (V6-A: fake; V6-B0: adds MiMo file probe)
        self.asr_provider_mode: str = _env_or_default("ASR_PROVIDER_MODE", "fake")
        self.fake_asr_transcript: str = _env_or_default(
            "FAKE_ASR_TRANSCRIPT", "这是一次语音输入测试。"
        )
        self.fake_asr_delay_seconds: float = _env_float_or_default(
            "FAKE_ASR_DELAY_SECONDS", "0.1"
        )

        # MiMo ASR configuration (V6-B0)
        self.mimo_api_key: str | None = _env_or_fallback("MIMO_API_KEY", None)
        self.mimo_base_url: str = _env_or_default(
            "MIMO_BASE_URL", "https://api.xiaomimimo.com/v1"
        )
        self.mimo_asr_model: str = _env_or_default("MIMO_ASR_MODEL", "mimo-v2.5-asr")
        self.mimo_asr_language: str = _env_or_default("MIMO_ASR_LANGUAGE", "auto")
        self.mimo_asr_timeout_seconds: float = _env_float_or_default(
            "MIMO_ASR_TIMEOUT_SECONDS", "30.0"
        )

        # Persona configuration (V7-A)
        self.persona_name: str = _env_or_default("PERSONA_NAME", "小云")
        self.persona_user_address: str = _env_or_default("PERSONA_USER_ADDRESS", "你")

        # ASR recording configuration (V6-B1)
        self.asr_recording_output_dir: str = _env_or_default(
            "ASR_RECORDING_OUTPUT_DIR", ".tmp/asr"
        )
        self.asr_recording_sample_rate: int = _env_int_or_default(
            "ASR_RECORDING_SAMPLE_RATE", "16000"
        )
        self.asr_recording_channels: int = _env_int_or_default(
            "ASR_RECORDING_CHANNELS", "1"
        )
        self.asr_recording_max_seconds: float = _env_float_or_default(
            "ASR_RECORDING_MAX_SECONDS", "10.0"
        )
        self.asr_recording_default_seconds: float = _env_float_or_default(
            "ASR_RECORDING_DEFAULT_SECONDS", "4.0"
        )

        # Validate ASR recording default seconds
        if self.asr_recording_default_seconds <= 0:
            raise ValueError("ASR_RECORDING_DEFAULT_SECONDS must be positive")
        if self.asr_recording_default_seconds > self.asr_recording_max_seconds:
            raise ValueError(
                "ASR_RECORDING_DEFAULT_SECONDS must be <= ASR_RECORDING_MAX_SECONDS"
            )


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
