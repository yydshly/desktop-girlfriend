"""TTS provider implementations and factory."""

from app.core.config import AppConfig
from app.expression.tts.providers.base import TTSProvider, TTSProviderError, TTSRequest, TTSResponse
from app.expression.tts.providers.fake import FakeTTSProvider
from app.expression.tts.providers.minimax import MiniMaxTTSProvider

__all__ = [
    "TTSProvider",
    "TTSProviderError",
    "TTSRequest",
    "TTSResponse",
    "FakeTTSProvider",
    "MiniMaxTTSProvider",
    "create_tts_provider",
]


def create_tts_provider(config: AppConfig) -> TTSProvider:
    """Create a TTS provider based on the application configuration.

    Args:
        config: Application configuration with TTS settings.

    Returns:
        A TTSProvider instance.

    Raises:
        TTSProviderError: If the configuration is invalid or the provider cannot be created.
    """
    mode = config.tts_provider_mode.lower().strip()

    if mode == "fake":
        return FakeTTSProvider(delay_seconds=0.1)

    if mode == "minimax":
        api_key = config.minimax_tts_api_key
        if not api_key:
            raise TTSProviderError("MiniMax TTS API key is required")
        return MiniMaxTTSProvider(
            api_key=api_key,
            group_id=config.minimax_tts_group_id,
            base_url=config.minimax_tts_base_url,
            model=config.minimax_tts_model,
            voice_id=config.minimax_tts_voice_id,
            timeout_seconds=config.minimax_tts_timeout_seconds,
            tts_path=config.minimax_tts_path,
            output_dir=config.minimax_tts_output_dir,
        )

    raise TTSProviderError(f"Unsupported TTS provider mode: {mode}")
