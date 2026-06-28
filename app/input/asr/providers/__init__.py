from __future__ import annotations

from typing import TYPE_CHECKING

from app.input.asr.providers.base import ASRProvider, ASRProviderError, ASRRequest, ASRResponse
from app.input.asr.providers.fake import FakeASRProvider

if TYPE_CHECKING:
    from app.core.config import AppConfig

__all__ = [
    "ASRProvider",
    "ASRProviderError",
    "ASRRequest",
    "ASRResponse",
    "FakeASRProvider",
]


def create_asr_provider(config: AppConfig) -> ASRProvider:
    """Create an ASR provider based on configuration.

    Args:
        config: Application configuration.

    Returns:
        An ASR provider instance.

    Raises:
        ASRProviderError: If the mode is unsupported.
    """
    mode = config.asr_provider_mode.lower().strip()
    if mode == "fake":
        return FakeASRProvider(
            transcript=config.fake_asr_transcript,
            delay_seconds=config.fake_asr_delay_seconds,
        )
    raise ASRProviderError(f"Unsupported ASR_PROVIDER_MODE: {config.asr_provider_mode}")
