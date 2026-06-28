"""Tests for TTS provider factory."""

import pytest

from app.core.config import AppConfig, reset_config
from app.expression.tts.providers import (
    FakeTTSProvider,
    MiniMaxTTSProvider,
    TTSProviderError,
    create_tts_provider,
)


def _make_config(**overrides) -> AppConfig:
    """Create an AppConfig with overrides, resetting global state."""
    reset_config()
    config = AppConfig()
    for key, value in overrides.items():
        setattr(config, key, value)
    return config


class TestCreateTTSProvider:
    """Tests for create_tts_provider()."""

    def test_mode_fake_returns_fake_tts_provider(self) -> None:
        """Test that mode='fake' returns a FakeTTSProvider."""
        config = _make_config(tts_provider_mode="fake")
        provider = create_tts_provider(config)
        assert isinstance(provider, FakeTTSProvider)

    def test_mode_fake_case_insensitive(self) -> None:
        """Test that mode is case-insensitive."""
        config = _make_config(tts_provider_mode="FAKE")
        provider = create_tts_provider(config)
        assert isinstance(provider, FakeTTSProvider)

    def test_mode_minimax_without_api_key_raises_error(self) -> None:
        """Test that mode='minimax' without API key raises TTSProviderError."""
        config = _make_config(
            tts_provider_mode="minimax",
            minimax_tts_api_key=None,
        )
        with pytest.raises(TTSProviderError, match="API key is required"):
            create_tts_provider(config)

    def test_mode_minimax_with_api_key_returns_minimax_provider(self) -> None:
        """Test that mode='minimax' with API key returns MiniMaxTTSProvider."""
        config = _make_config(
            tts_provider_mode="minimax",
            minimax_tts_api_key="test-key",
        )
        provider = create_tts_provider(config)
        assert isinstance(provider, MiniMaxTTSProvider)

    def test_unsupported_mode_raises_error(self) -> None:
        """Test that unsupported mode raises TTSProviderError."""
        config = _make_config(tts_provider_mode="unknown")
        with pytest.raises(TTSProviderError, match="Unsupported TTS provider mode"):
            create_tts_provider(config)

    def test_error_message_does_not_leak_api_key(self) -> None:
        """Test that error messages do not contain the API key."""
        config = _make_config(
            tts_provider_mode="minimax",
            minimax_tts_api_key="super-secret-key",
        )
        try:
            create_tts_provider(config)
        except TTSProviderError as e:
            assert "super-secret-key" not in str(e)
            assert "Bearer" not in str(e)

    def test_mode_minimax_trims_whitespace(self) -> None:
        """Test that mode value is stripped of whitespace."""
        config = _make_config(tts_provider_mode="  fake  ")
        provider = create_tts_provider(config)
        assert isinstance(provider, FakeTTSProvider)


class TestConfigTTSDefaults:
    """Tests for TTS configuration defaults."""

    def test_default_tts_provider_mode_is_fake(self) -> None:
        """Test that default TTS provider mode is 'fake'."""
        reset_config()
        config = AppConfig()
        assert config.tts_provider_mode == "fake"

    def test_tts_api_key_falls_back_to_chat_api_key(self) -> None:
        """Test that TTS API key falls back to chat API key when not explicitly set."""
        reset_config()
        config = AppConfig()
        # minimax_tts_api_key should default to the value of minimax_api_key
        # (which may or may not be None depending on whether .env is loaded)
        assert config.minimax_tts_api_key == config.minimax_api_key

    def test_tts_api_key_can_be_set_explicitly(self) -> None:
        """Test that TTS API key can be set independently of chat key."""
        config = _make_config(
            minimax_api_key="chat-key",
            minimax_tts_api_key="tts-key",
        )
        assert config.minimax_tts_api_key == "tts-key"
        assert config.minimax_api_key == "chat-key"
