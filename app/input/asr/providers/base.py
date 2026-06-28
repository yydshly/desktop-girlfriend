"""ASR provider base interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class ASRProviderError(Exception):
    """Raised when ASR recognition fails."""


@dataclass(frozen=True)
class ASRRequest:
    """Request for speech recognition.

    V6-A fake mode does not carry audio; this is a placeholder for the contract.
    """


@dataclass(frozen=True)
class ASRResponse:
    """Response from speech recognition."""

    text: str


class ASRProvider(ABC):
    """Abstract base class for ASR providers."""

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
