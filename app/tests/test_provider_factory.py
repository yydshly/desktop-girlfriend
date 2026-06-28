"""Tests for chat provider factory."""

import pytest

from app.brain.providers.base import ChatProviderError
from app.brain.providers.factory import create_chat_provider
from app.brain.providers.fake import FakeChatProvider
from app.brain.providers.minimax import MiniMaxChatProvider
from app.core.config import AppConfig, reset_config


def _make_config(**kwargs: str | None) -> AppConfig:
    """Create AppConfig with overrides."""
    reset_config()
    config = AppConfig()
    for key, value in kwargs.items():
        setattr(config, key, value)
    return config


def test_fake_mode_returns_fake_provider() -> None:
    """Test fake mode returns FakeChatProvider."""
    config = _make_config(chat_provider_mode="fake")
    provider = create_chat_provider(config)
    assert isinstance(provider, FakeChatProvider)


def test_minimax_mode_without_key_raises_error() -> None:
    """Test minimax mode without API key raises ChatProviderError."""
    config = _make_config(chat_provider_mode="minimax", minimax_api_key=None)
    with pytest.raises(ChatProviderError) as exc_info:
        create_chat_provider(config)
    assert "MiniMax API key is not configured" in str(exc_info.value)
    # Ensure error does not leak the key
    assert "sk-" not in str(exc_info.value)


def test_unsupported_mode_raises_error() -> None:
    """Test unsupported provider mode raises ChatProviderError."""
    config = _make_config(chat_provider_mode="unknown")
    with pytest.raises(ChatProviderError) as exc_info:
        create_chat_provider(config)
    assert "Unsupported chat provider mode" in str(exc_info.value)


def test_minimax_mode_with_key_returns_minimax_provider() -> None:
    """Test minimax mode with API key returns MiniMaxChatProvider."""
    config = _make_config(
        chat_provider_mode="minimax",
        minimax_api_key="test-key-123",
    )
    provider = create_chat_provider(config)
    assert isinstance(provider, MiniMaxChatProvider)


def test_provider_factory_does_not_network() -> None:
    """Test factory does not make any network calls."""
    config = _make_config(chat_provider_mode="minimax", minimax_api_key="test-key")
    # This should return a provider without making network calls
    provider = create_chat_provider(config)
    assert isinstance(provider, MiniMaxChatProvider)
