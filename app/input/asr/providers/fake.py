"""Fake ASR provider for testing and development."""

import time

from app.input.asr.providers.base import ASRProvider, ASRProviderError, ASRRequest, ASRResponse


class FakeASRProvider(ASRProvider):
    """Fake ASR provider that returns a configured transcript after a delay.

    Does not use a microphone, does not access the network, and does not
    persist any audio data.
    """

    def __init__(
        self,
        transcript: str = "这是一次语音输入测试。",
        delay_seconds: float = 0.1,
        should_fail: bool = False,
    ) -> None:
        """Initialize FakeASRProvider.

        Args:
            transcript: The fixed text to return on success.
            delay_seconds: Simulated recognition latency.
            should_fail: If True, raise ASRProviderError instead of returning.
        """
        self._transcript = transcript
        self._delay_seconds = delay_seconds
        self._should_fail = should_fail

    def recognize(self, request: ASRRequest) -> ASRResponse:
        """Return the configured transcript after a delay.

        Args:
            request: The ASR request (unused in fake mode).

        Returns:
            ASRResponse with the configured transcript.

        Raises:
            ASRProviderError: If should_fail is True or transcript is blank.
        """
        time.sleep(self._delay_seconds)

        if self._should_fail:
            raise ASRProviderError("Fake ASR recognition failed")

        if not self._transcript.strip():
            raise ASRProviderError("Fake ASR recognition failed")

        return ASRResponse(text=self._transcript)
