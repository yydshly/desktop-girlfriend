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
    audio_path: str | None = None


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    supports_audio_path_playback: bool = False

    def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize text to an audio file and return the response.

        Default implementation delegates to speak() for backward compatibility.

        Args:
            request: The TTS request containing text to synthesize.

        Returns:
            TTSResponse with audio_path set if synthesis succeeded.

        Raises:
            TTSProviderError: If synthesis fails.
        """
        return self.speak(request)

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
