"""Tests for FakeASRProvider."""

import time

import pytest

from app.input.asr.providers.base import ASRProviderError, ASRRequest
from app.input.asr.providers.fake import FakeASRProvider


class TestFakeASRProviderSuccess:
    """Tests for FakeASRProvider success path."""

    def test_recognize_returns_configured_transcript(self) -> None:
        """Test recognize() returns the configured transcript."""
        provider = FakeASRProvider(transcript="你好小云")
        response = provider.recognize(ASRRequest())
        assert response.text == "你好小云"

    def test_recognize_returns_default_transcript(self) -> None:
        """Test default transcript is returned when not overridden."""
        provider = FakeASRProvider()
        response = provider.recognize(ASRRequest())
        assert response.text == "这是一次语音输入测试。"

    def test_delay_zero_does_not_slow_down_test(self) -> None:
        """Test delay_seconds=0 completes quickly."""
        provider = FakeASRProvider(transcript="快速识别", delay_seconds=0.0)
        start = time.monotonic()
        provider.recognize(ASRRequest())
        elapsed = time.monotonic() - start
        assert elapsed < 0.05  # Much less than the 0.1s default


class TestFakeASRProviderFailure:
    """Tests for FakeASRProvider failure paths."""

    def test_should_fail_raises_asr_provider_error(self) -> None:
        """Test should_fail=True raises ASRProviderError."""
        provider = FakeASRProvider(should_fail=True)
        with pytest.raises(ASRProviderError):
            provider.recognize(ASRRequest())

    def test_empty_transcript_raises_asr_provider_error(self) -> None:
        """Test empty transcript raises ASRProviderError."""
        provider = FakeASRProvider(transcript="")
        with pytest.raises(ASRProviderError):
            provider.recognize(ASRRequest())

    def test_whitespace_transcript_raises_asr_provider_error(self) -> None:
        """Test whitespace-only transcript raises ASRProviderError."""
        provider = FakeASRProvider(transcript="   ")
        with pytest.raises(ASRProviderError):
            provider.recognize(ASRRequest())
