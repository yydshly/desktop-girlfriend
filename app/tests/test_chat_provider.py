"""Tests for chat providers."""

import pytest

from app.brain.providers.base import ChatProviderError, ChatRequest, ChatResponse
from app.brain.providers.fake import FakeChatProvider


class TestFakeChatProvider:
    """Tests for FakeChatProvider."""

    def test_generate_returns_deterministic_text(self) -> None:
        """Test FakeChatProvider returns default deterministic response."""
        provider = FakeChatProvider()
        request = ChatRequest(messages=[])
        response = provider.generate(request)

        assert isinstance(response, ChatResponse)
        assert response.text == "This is a fake response."

    def test_generate_returns_custom_reply_text(self) -> None:
        """Test FakeChatProvider returns custom reply_text."""
        provider = FakeChatProvider(reply_text="Custom reply")
        request = ChatRequest(messages=[])
        response = provider.generate(request)

        assert response.text == "Custom reply"

    def test_generate_raises_error_when_should_fail(self) -> None:
        """Test FakeChatProvider raises ChatProviderError when should_fail=True."""
        provider = FakeChatProvider(should_fail=True)
        request = ChatRequest(messages=[])

        with pytest.raises(ChatProviderError) as exc_info:
            provider.generate(request)

        assert "simulated failure" in str(exc_info.value)

    def test_default_stop_does_not_raise(self) -> None:
        """Test ChatProvider.stop() is safe for providers without cancellation."""
        provider = FakeChatProvider()
        provider.stop()
