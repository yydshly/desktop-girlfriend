"""Shared pytest fixtures and helpers for config tests."""

from __future__ import annotations

import pytest

from app.core.config import reset_config

# All environment variables used by AppConfig that need isolation
CONFIG_ENV_NAMES = [
    "APP_ENV",
    "CHAT_PROVIDER_MODE",
    "MINIMAX_API_KEY",
    "MINIMAX_GROUP_ID",
    "MINIMAX_BASE_URL",
    "MINIMAX_MODEL",
    "MINIMAX_TIMEOUT_SECONDS",
    "MINIMAX_CHAT_PATH",
    "TTS_PROVIDER_MODE",
    "MINIMAX_TTS_API_KEY",
    "MINIMAX_TTS_GROUP_ID",
    "MINIMAX_TTS_BASE_URL",
    "MINIMAX_TTS_MODEL",
    "MINIMAX_TTS_VOICE_ID",
    "MINIMAX_TTS_TIMEOUT_SECONDS",
    "MINIMAX_TTS_PATH",
    "MINIMAX_TTS_OUTPUT_DIR",
]


def clear_config_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear all config-related environment variables and reset global config.

    Use this in tests that depend on default values to ensure isolation from
    the developer's local .env file.
    """
    for name in CONFIG_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    reset_config()
