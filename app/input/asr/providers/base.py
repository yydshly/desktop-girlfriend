"""ASR provider base interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class ASRProviderError(Exception):
    """Raised when ASR recognition fails."""


@dataclass(frozen=True)
class ASRRequest:
    """Request for speech recognition.

    Attributes:
        audio_path: Path to the audio file to recognize. None for fake/placeholder.
        mime_type: MIME type of the audio file. Defaults to "audio/wav".
    """

    audio_path: str | None = None
    mime_type: str = "audio/wav"


@dataclass(frozen=True)
class ASRResponse:
    """Response from speech recognition."""

    text: str


class ASRProvider(ABC):
    """Abstract base class for ASR providers."""

    requires_audio_path: bool = False

    @abstractmethod
    def recognize(self, request: ASRRequest) -> ASRResponse:
        """Perform speech recognition on the given request.

        Args:
            request: The ASR request.

        Returns:
            An ASR response containing the recognized text.

        Raises:
            ASRProviderError: If recognition fails.
        """
        ...
