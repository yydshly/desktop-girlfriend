"""Fake TTS provider for testing and development."""

import time

from app.expression.tts.providers.base import (
    TTSProvider,
    TTSProviderError,
    TTSRequest,
    TTSResponse,
)


class FakeTTSProvider(TTSProvider):
    """Fake TTS provider that simulates synthesis and playback with a delay."""

    def __init__(self, delay_seconds: float = 0.1, should_fail: bool = False) -> None:
        """Initialize FakeTTSProvider.

        Args:
            delay_seconds: Simulated delay for TTS playback.
            should_fail: If True, raise TTSProviderError on speak.
        """
        self._delay = delay_seconds
        self._should_fail = should_fail

    def speak(self, request: TTSRequest) -> TTSResponse:
        """Simulate TTS playback with a delay.

        Args:
            request: The TTS request containing text to speak.

        Returns:
            TTSResponse with the simulated duration.

        Raises:
            TTSProviderError: If text is empty/whitespace, or should_fail is True.
        """
        text = request.text
        if not isinstance(text, str) or not text.strip():
            raise TTSProviderError("Empty TTS text")

        if self._should_fail:
            raise TTSProviderError("Fake TTS failure")

        time.sleep(self._delay)
        return TTSResponse(duration_seconds=self._delay)
