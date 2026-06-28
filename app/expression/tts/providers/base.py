"""TTS provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class TTSProviderError(Exception):
    """Raised when TTS generation or playback fails."""


@dataclass(frozen=True)
class TTSRequest:
    """Request for text-to-speech synthesis and playback."""

    text: str


@dataclass(frozen=True)
class TTSResponse:
    """Response from text-to-speech synthesis and playback."""

    duration_seconds: float = 0.0


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    def speak(self, request: TTSRequest) -> TTSResponse:
        """Speak the given text and return when playback is complete.

        Args:
            request: The TTS request containing text to speak.

        Returns:
            TTSResponse with the duration of the playback.

        Raises:
            TTSProviderError: If synthesis or playback fails.
        """
        ...
