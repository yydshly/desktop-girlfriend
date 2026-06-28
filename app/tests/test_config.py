"""Tests for app configuration."""

import pytest

from app.core.config import AppConfig, get_config, reset_config
from app.tests.conftest import clear_config_env


def test_default_chat_provider_mode_is_fake(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test default chat provider mode is fake."""
    clear_config_env(monkeypatch)
    config = AppConfig()
    assert config.chat_provider_mode == "fake"


def test_default_minimax_base_url_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test default minimax base URL is set."""
    clear_config_env(monkeypatch)
    config = AppConfig()
    assert config.minimax_base_url == "https://api.minimax.chat/v1"


def test_default_minimax_timeout_seconds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test default minimax timeout is 30.0."""
    clear_config_env(monkeypatch)
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


def test_invalid_minimax_timeout_has_clear_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test invalid chat timeout fails with a clear config error."""
    reset_config()
    monkeypatch.setenv("MINIMAX_TIMEOUT_SECONDS", "not-a-number")

    with pytest.raises(ValueError, match="MINIMAX_TIMEOUT_SECONDS must be a number"):
        AppConfig()


def test_default_minimax_chat_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test default minimax chat path is set."""
    clear_config_env(monkeypatch)
    config = AppConfig()
    assert config.minimax_chat_path == "/text/chatcompletion_v2"


def test_env_vars_override_chat_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test environment variables override chat path."""
    reset_config()
    monkeypatch.setenv("MINIMAX_CHAT_PATH", "/custom/chat/path")
    config = AppConfig()
    assert config.minimax_chat_path == "/custom/chat/path"


def test_get_config_returns_singleton(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_config returns the same instance."""
    clear_config_env(monkeypatch)
    c1 = get_config()
    c2 = get_config()
    assert c1 is c2


# TTS env fallback tests


def test_minimax_tts_api_key_fallback_from_chat_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test MINIMAX_TTS_API_KEY falls back to MINIMAX_API_KEY when unset."""
    reset_config()
    monkeypatch.setenv("MINIMAX_API_KEY", "chat-key")
    monkeypatch.delenv("MINIMAX_TTS_API_KEY", raising=False)
    config = AppConfig()
    assert config.minimax_tts_api_key == "chat-key"


def test_minimax_tts_api_key_fallback_when_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test MINIMAX_TTS_API_KEY='' falls back to MINIMAX_API_KEY."""
    reset_config()
    monkeypatch.setenv("MINIMAX_API_KEY", "chat-key")
    monkeypatch.setenv("MINIMAX_TTS_API_KEY", "")
    config = AppConfig()
    assert config.minimax_tts_api_key == "chat-key"


def test_minimax_tts_api_key_preferred_when_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test MINIMAX_TTS_API_KEY='tts-key' is used over MINIMAX_API_KEY."""
    reset_config()
    monkeypatch.setenv("MINIMAX_API_KEY", "chat-key")
    monkeypatch.setenv("MINIMAX_TTS_API_KEY", "tts-key")
    config = AppConfig()
    assert config.minimax_tts_api_key == "tts-key"


def test_minimax_tts_group_id_fallback_when_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test MINIMAX_TTS_GROUP_ID='' falls back to MINIMAX_GROUP_ID."""
    reset_config()
    monkeypatch.setenv("MINIMAX_GROUP_ID", "chat-group")
    monkeypatch.setenv("MINIMAX_TTS_GROUP_ID", "")
    config = AppConfig()
    assert config.minimax_tts_group_id == "chat-group"


def test_tts_provider_mode_fallback_when_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test TTS_PROVIDER_MODE='' falls back to 'fake'."""
    reset_config()
    monkeypatch.setenv("TTS_PROVIDER_MODE", "")
    config = AppConfig()
    assert config.tts_provider_mode == "fake"


def test_tts_api_key_values_stored_correctly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test TTS API key values are stored correctly in config."""
    reset_config()
    monkeypatch.setenv("MINIMAX_API_KEY", "secret-chat-key")
    monkeypatch.setenv("MINIMAX_TTS_API_KEY", "secret-tts-key")
    config = AppConfig()
    # Verify both keys are present in config object
    assert config.minimax_api_key == "secret-chat-key"
    assert config.minimax_tts_api_key == "secret-tts-key"
    # Note: actual logging/printing sanitization is handled by the caller,
    # not by AppConfig itself — this test confirms the values are stored.


def test_invalid_minimax_tts_timeout_has_clear_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test invalid TTS timeout fails with a clear config error."""
    reset_config()
    monkeypatch.setenv("MINIMAX_TTS_TIMEOUT_SECONDS", "not-a-number")

    with pytest.raises(ValueError, match="MINIMAX_TTS_TIMEOUT_SECONDS must be a number"):
        AppConfig()


# ASR config tests


def test_default_asr_provider_mode_is_fake(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test default ASR provider mode is fake."""
    clear_config_env(monkeypatch)
    config = AppConfig()
    assert config.asr_provider_mode == "fake"


def test_default_fake_asr_transcript(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test default fake ASR transcript is set."""
    clear_config_env(monkeypatch)
    config = AppConfig()
    assert config.fake_asr_transcript == "这是一次语音输入测试。"


def test_default_fake_asr_delay_seconds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test default fake ASR delay is 0.1."""
    clear_config_env(monkeypatch)
    config = AppConfig()
    assert config.fake_asr_delay_seconds == 0.1


def test_env_vars_override_fake_asr_transcript(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test FAKE_ASR_TRANSCRIPT env var is used."""
    reset_config()
    monkeypatch.setenv("FAKE_ASR_TRANSCRIPT", "自定义语音识别文本")
    config = AppConfig()
    assert config.fake_asr_transcript == "自定义语音识别文本"


def test_env_vars_override_fake_asr_delay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test FAKE_ASR_DELAY_SECONDS env var is used."""
    reset_config()
    monkeypatch.setenv("FAKE_ASR_DELAY_SECONDS", "0.5")
    config = AppConfig()
    assert config.fake_asr_delay_seconds == 0.5


def test_invalid_fake_asr_delay_raises_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test invalid FAKE_ASR_DELAY_SECONDS raises ValueError."""
    reset_config()
    monkeypatch.setenv("FAKE_ASR_DELAY_SECONDS", "not-a-number")

    with pytest.raises(ValueError, match="FAKE_ASR_DELAY_SECONDS must be a number"):
        AppConfig()


# MiMo ASR config tests


def test_default_mimo_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test default MiMo base URL is set."""
    clear_config_env(monkeypatch)
    config = AppConfig()
    assert config.mimo_base_url == "https://api.xiaomimimo.com/v1"


def test_default_mimo_asr_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test default MiMo ASR model is mimo-v2.5-asr."""
    clear_config_env(monkeypatch)
    config = AppConfig()
    assert config.mimo_asr_model == "mimo-v2.5-asr"


def test_default_mimo_asr_language(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test default MiMo ASR language is auto."""
    clear_config_env(monkeypatch)
    config = AppConfig()
    assert config.mimo_asr_language == "auto"


def test_default_mimo_asr_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test default MiMo ASR timeout is 30.0."""
    clear_config_env(monkeypatch)
    config = AppConfig()
    assert config.mimo_asr_timeout_seconds == 30.0


def test_env_vars_override_mimo_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test MIMO_BASE_URL env var is used."""
    reset_config()
    monkeypatch.setenv("MIMO_BASE_URL", "https://custom.mimo.com/v1")
    config = AppConfig()
    assert config.mimo_base_url == "https://custom.mimo.com/v1"


def test_env_vars_override_mimo_asr_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test MIMO_ASR_MODEL env var is used."""
    reset_config()
    monkeypatch.setenv("MIMO_ASR_MODEL", "custom-asr-model")
    config = AppConfig()
    assert config.mimo_asr_model == "custom-asr-model"


def test_env_vars_override_mimo_asr_language(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test MIMO_ASR_LANGUAGE env var is used."""
    reset_config()
    monkeypatch.setenv("MIMO_ASR_LANGUAGE", "zh")
    config = AppConfig()
    assert config.mimo_asr_language == "zh"


def test_env_vars_override_mimo_asr_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test MIMO_ASR_TIMEOUT_SECONDS env var is used."""
    reset_config()
    monkeypatch.setenv("MIMO_ASR_TIMEOUT_SECONDS", "60.0")
    config = AppConfig()
    assert config.mimo_asr_timeout_seconds == 60.0


def test_invalid_mimo_asr_timeout_raises_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test invalid MIMO_ASR_TIMEOUT_SECONDS raises ValueError."""
    reset_config()
    monkeypatch.setenv("MIMO_ASR_TIMEOUT_SECONDS", "not-a-number")

    with pytest.raises(ValueError, match="MIMO_ASR_TIMEOUT_SECONDS must be a number"):
        AppConfig()
