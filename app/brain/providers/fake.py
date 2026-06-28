"""Fake chat provider for testing."""

from app.brain.providers.base import (
    ChatProvider,
    ChatProviderError,
    ChatRequest,
    ChatResponse,
)


class FakeChatProvider(ChatProvider):
    """Fake chat provider that returns deterministic responses."""

    def __init__(
        self,
        reply_text: str = "This is a fake response.",
        should_fail: bool = False,
    ) -> None:
        """Initialize FakeChatProvider.

        Args:
            reply_text: The text to return on success.
            should_fail: If True, raise ChatProviderError on generate().
        """
        self._reply_text = reply_text
        self._should_fail = should_fail

    def generate(self, request: ChatRequest) -> ChatResponse:
        """Return deterministic response or raise ChatProviderError."""
        if self._should_fail:
            raise ChatProviderError("FakeChatProvider: simulated failure")
        return ChatResponse(text=self._reply_text)
