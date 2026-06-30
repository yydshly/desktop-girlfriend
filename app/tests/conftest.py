"""Shared pytest fixtures and helpers for config tests."""

from __future__ import annotations

import pytest

from app.core.config import reset_config

# All environment variables used by AppConfig that need isolation
CONFIG_ENV_NAMES = [
    "APP_ENV",
    "LIVE2D_DESKTOP_AUTO_LAUNCH",
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
    "ASR_PROVIDER_MODE",
    "FAKE_ASR_TRANSCRIPT",
    "FAKE_ASR_DELAY_SECONDS",
    "MIMO_API_KEY",
    "MIMO_BASE_URL",
    "MIMO_ASR_MODEL",
    "MIMO_ASR_LANGUAGE",
    "MIMO_ASR_TIMEOUT_SECONDS",
    "PERSONA_NAME",
    "PERSONA_USER_ADDRESS",
    "MEMORY_CONTEXT_ENABLED",
    "MEMORY_STORE_PATH",
    "MEMORY_SUGGESTIONS_ENABLED",
    "MEMORY_MANAGEMENT_ENABLED",
    "PROACTIVE_ENABLED",
    "PROACTIVE_IDLE_SECONDS",
    "PROACTIVE_COOLDOWN_SECONDS",
    "PROACTIVE_MAX_PER_SESSION",
    "PROACTIVE_TTS_ENABLED",
    "PROACTIVE_QUIET_HOURS_ENABLED",
    "PROACTIVE_QUIET_START_HOUR",
    "PROACTIVE_QUIET_END_HOUR",
    "PROACTIVE_FEEDBACK_PAUSE_SECONDS",
    "ASR_RECORDING_OUTPUT_DIR",
    "ASR_RECORDING_SAMPLE_RATE",
    "ASR_RECORDING_CHANNELS",
    "ASR_RECORDING_MAX_SECONDS",
    "ASR_RECORDING_DEFAULT_SECONDS",
]


def clear_config_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear all config-related environment variables and reset global config.

    Use this in tests that depend on default values to ensure isolation from
    the developer's local .env file.
    """
    for name in CONFIG_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    reset_config()


@pytest.fixture(scope="session")
def qapp():
    """Return a single QApplication instance for all Qt tests."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
