"""Chat provider interface definitions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class ChatProviderError(Exception):
    """Raised when a chat provider fails to generate a response."""

    pass


@runtime_checkable
class PromptMessageLike(Protocol):
    """Protocol for prompt message objects from PromptRegistry."""

    role: str
    content: str


@dataclass(frozen=True)
class ChatRequest:
    """Provider-neutral chat request."""

    messages: list["PromptMessageLike"]
    temperature: float = 0.7
    max_tokens: int = 512


@dataclass(frozen=True)
class ChatResponse:
    """Provider-neutral chat response."""

    text: str


class ChatProvider(ABC):
    """Abstract base class for chat providers."""

    @abstractmethod
    def generate(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat response.

        Args:
            request: The chat request containing messages and parameters.

        Returns:
            ChatResponse with the generated text.

        Raises:
            ChatProviderError: If the provider fails to generate a response.
        """
        ...
