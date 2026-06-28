"""Tests for ASR provider factory."""

from __future__ import annotations

import pytest

from app.core.config import reset_config
from app.input.asr.providers import (
    ASRProviderError,
    FakeASRProvider,
    MimoASRProvider,
    create_asr_provider,
)
from app.tests.conftest import clear_config_env


class TestCreateAsrProvider:
    """Tests for create_asr_provider factory."""

    def test_fake_mode_returns_fake_provider(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test ASR_PROVIDER_MODE=fake returns FakeASRProvider."""
        clear_config_env(monkeypatch)
        monkeypatch.setenv("ASR_PROVIDER_MODE", "fake")
        reset_config()
        from app.core.config import AppConfig
        config = AppConfig()
        provider = create_asr_provider(config)
        assert isinstance(provider, FakeASRProvider)

    def test_mimo_mode_returns_mimo_provider(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test ASR_PROVIDER_MODE=mimo returns MimoASRProvider."""
        clear_config_env(monkeypatch)
        monkeypatch.setenv("ASR_PROVIDER_MODE", "mimo")
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        reset_config()
        from app.core.config import AppConfig
        config = AppConfig()
        provider = create_asr_provider(config)
        assert isinstance(provider, MimoASRProvider)

    def test_unsupported_mode_raises(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test unsupported ASR_PROVIDER_MODE raises ASRProviderError."""
        clear_config_env(monkeypatch)
        monkeypatch.setenv("ASR_PROVIDER_MODE", "whisper")
        reset_config()
        from app.core.config import AppConfig
        config = AppConfig()
        with pytest.raises(ASRProviderError, match="Unsupported ASR_PROVIDER_MODE"):
            create_asr_provider(config)

    def test_fake_mode_is_default(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that fake is the default mode."""
        clear_config_env(monkeypatch)
        reset_config()
        from app.core.config import AppConfig
        config = AppConfig()
        assert config.asr_provider_mode == "fake"
        provider = create_asr_provider(config)
        assert isinstance(provider, FakeASRProvider)
