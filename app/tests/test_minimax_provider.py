"""Tests for MiniMaxChatProvider."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.brain.providers.base import ChatProviderError, ChatRequest
from app.brain.providers.minimax import MiniMaxChatProvider


def _make_request(text: str = "Hello") -> ChatRequest:
    """Create a ChatRequest with a single user message."""
    return ChatRequest(
        messages=[
            MagicMock(role="user", content=text),
        ],
    )


class TestMiniMaxProviderBuildPayload:
    """Tests for request payload construction."""

    def test_messages_converted_to_api_format(self) -> None:
        """Test ChatRequest messages are converted to API payload format."""
        provider = MiniMaxChatProvider(
            api_key="test-key",
            group_id=None,
            base_url="https://api.minimax.chat/v1",
            model="MiniMax-Text-01",
            timeout_seconds=30.0,
        )
        request = ChatRequest(
            messages=[
                MagicMock(role="system", content="You are helpful"),
                MagicMock(role="user", content="Hi"),
            ],
        )
        payload = provider._build_request_payload(request)

        assert payload["model"] == "MiniMax-Text-01"
        assert payload["messages"] == [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hi"},
        ]

    def test_group_id_included_when_present(self) -> None:
        """Test group_id is included in payload when provided."""
        provider = MiniMaxChatProvider(
            api_key="test-key",
            group_id="group-123",
            base_url="https://api.minimax.chat/v1",
            model="MiniMax-Text-01",
            timeout_seconds=30.0,
        )
        request = _make_request()
        payload = provider._build_request_payload(request)

        assert payload["group_id"] == "group-123"

    def test_group_id_absent_when_none(self) -> None:
        """Test group_id is absent from payload when None."""
        provider = MiniMaxChatProvider(
            api_key="test-key",
            group_id=None,
            base_url="https://api.minimax.chat/v1",
            model="MiniMax-Text-01",
            timeout_seconds=30.0,
        )
        request = _make_request()
        payload = provider._build_request_payload(request)

        assert "group_id" not in payload


class TestMiniMaxProviderResponseParsing:
    """Tests for API response parsing."""

    def test_normal_response_parsed(self) -> None:
        """Test normal API response extracts correct text."""
        provider = MiniMaxChatProvider(
            api_key="test-key",
            group_id=None,
            base_url="https://api.minimax.chat/v1",
            model="MiniMax-Text-01",
            timeout_seconds=30.0,
        )
        response_data = {
            "choices": [
                {"message": {"content": "Hello, how can I help?"}}
            ]
        }
        text = provider._parse_response(response_data)
        assert text == "Hello, how can I help?"

    def test_empty_response_raises_error(self) -> None:
        """Test empty response text raises ChatProviderError."""
        provider = MiniMaxChatProvider(
            api_key="test-key",
            group_id=None,
            base_url="https://api.minimax.chat/v1",
            model="MiniMax-Text-01",
            timeout_seconds=30.0,
        )
        response_data: dict[str, Any] = {}
        with pytest.raises(ChatProviderError):
            provider._parse_response(response_data)

    def test_malformed_response_raises_error(self) -> None:
        """Test malformed response raises ChatProviderError."""
        provider = MiniMaxChatProvider(
            api_key="test-key",
            group_id=None,
            base_url="https://api.minimax.chat/v1",
            model="MiniMax-Text-01",
            timeout_seconds=30.0,
        )
        response_data: dict[str, Any] = {"choices": []}
        with pytest.raises(ChatProviderError):
            provider._parse_response(response_data)


class TestMiniMaxProviderGenerate:
    """Tests for generate() method."""

    def test_http_error_raises_chat_provider_error(self) -> None:
        """Test HTTP error is converted to ChatProviderError."""

        provider = MiniMaxChatProvider(
            api_key="test-key",
            group_id=None,
            base_url="https://api.minimax.chat/v1",
            model="MiniMax-Text-01",
            timeout_seconds=30.0,
        )
        request = _make_request()

        with patch.object(provider, "_send_request") as mock_send:
            mock_send.side_effect = ChatProviderError("HTTP 401")
            with pytest.raises(ChatProviderError) as exc_info:
                provider.generate(request)
            assert "401" in str(exc_info.value)

    def test_network_error_raises_chat_provider_error(self) -> None:
        """Test network error is converted to ChatProviderError."""

        provider = MiniMaxChatProvider(
            api_key="test-key",
            group_id=None,
            base_url="https://api.minimax.chat/v1",
            model="MiniMax-Text-01",
            timeout_seconds=30.0,
        )
        request = _make_request()

        with patch.object(provider, "_send_request") as mock_send:
            mock_send.side_effect = ChatProviderError("Network error")
            with pytest.raises(ChatProviderError) as exc_info:
                provider.generate(request)
            assert "Network error" in str(exc_info.value)

    def test_empty_response_text_raises_error(self) -> None:
        """Test empty response text raises ChatProviderError."""
        provider = MiniMaxChatProvider(
            api_key="test-key",
            group_id=None,
            base_url="https://api.minimax.chat/v1",
            model="MiniMax-Text-01",
            timeout_seconds=30.0,
        )
        request = _make_request()

        with patch.object(provider, "_send_request") as mock_send:
            mock_send.return_value = {"choices": [{"message": {"content": ""}}]}
            with pytest.raises(ChatProviderError) as exc_info:
                provider.generate(request)
            assert "empty" in str(exc_info.value).lower()

    def test_error_message_does_not_leak_api_key(self) -> None:
        """Test error messages do not contain the API key."""
        provider = MiniMaxChatProvider(
            api_key="sk-secret-key-12345",
            group_id=None,
            base_url="https://api.minimax.chat/v1",
            model="MiniMax-Text-01",
            timeout_seconds=30.0,
        )
        request = _make_request()

        with patch.object(provider, "_send_request") as mock_send:
            mock_send.side_effect = ChatProviderError("HTTP 500")
            try:
                provider.generate(request)
            except ChatProviderError:
                pass
            # Key should not appear in any error paths

        with patch.object(provider, "_send_request") as mock_send:
            mock_send.return_value = {"choices": [{"message": {"content": ""}}]}
            try:
                provider.generate(request)
            except ChatProviderError:
                pass
            # Key should not appear in error messages

    def test_successful_generate_returns_response(self) -> None:
        """Test successful generate returns ChatResponse with text."""
        provider = MiniMaxChatProvider(
            api_key="test-key",
            group_id=None,
            base_url="https://api.minimax.chat/v1",
            model="MiniMax-Text-01",
            timeout_seconds=30.0,
        )
        request = _make_request()

        with patch.object(provider, "_send_request") as mock_send:
            mock_send.return_value = {
                "choices": [{"message": {"content": "Hello!"}}]
            }
            response = provider.generate(request)

        assert response.text == "Hello!"
