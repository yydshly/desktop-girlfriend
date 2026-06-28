"""Tests for app configuration."""

import os

import pytest

from app.core.config import AppConfig, get_config, reset_config


def test_default_chat_provider_mode_is_fake() -> None:
    """Test default chat provider mode is fake."""
    reset_config()
    # Ensure env vars don't interfere
    os.environ.pop("CHAT_PROVIDER_MODE", None)
    config = AppConfig()
    assert config.chat_provider_mode == "fake"


def test_default_minimax_base_url_exists() -> None:
    """Test default minimax base URL is set."""
    reset_config()
    config = AppConfig()
    assert config.minimax_base_url == "https://api.minimax.chat/v1"


def test_default_minimax_timeout_seconds() -> None:
    """Test default minimax timeout is 30.0."""
    reset_config()
    config = AppConfig()
    assert config.minimax_timeout_seconds == 30.0


def test_env_vars_override_provider_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test environment variables override provider mode."""
    reset_config()
    monkeypatch.setenv("CHAT_PROVIDER_MODE", "minimax")
    config = AppConfig()
    assert config.chat_provider_mode == "minimax"


def test_env_vars_override_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test environment variables override model name."""
    reset_config()
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-Text-01")
    config = AppConfig()
    assert config.minimax_model == "MiniMax-Text-01"


def test_env_vars_override_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test environment variables override timeout."""
    reset_config()
    monkeypatch.setenv("MINIMAX_TIMEOUT_SECONDS", "15.0")
    config = AppConfig()
    assert config.minimax_timeout_seconds == 15.0


def test_get_config_returns_singleton() -> None:
    """Test get_config returns the same instance."""
    reset_config()
    c1 = get_config()
    c2 = get_config()
    assert c1 is c2
