"""Tests for FakeTTSProvider."""

import time

from app.expression.tts.providers.base import TTSProviderError, TTSRequest
from app.expression.tts.providers.fake import FakeTTSProvider


def test_speak_valid_text_returns_tts_response() -> None:
    """Test speak with valid text returns TTSResponse."""
    provider = FakeTTSProvider(delay_seconds=0.01)
    response = provider.speak(TTSRequest(text="Hello world"))

    assert response.duration_seconds == 0.01


def test_speak_empty_text_raises_tts_provider_error() -> None:
    """Test speak with empty string raises TTSProviderError."""
    provider = FakeTTSProvider(delay_seconds=0.0)

    try:
        provider.speak(TTSRequest(text=""))
        assert False, "Expected TTSProviderError"
    except TTSProviderError as e:
        assert str(e) == "Empty TTS text"


def test_speak_whitespace_text_raises_tts_provider_error() -> None:
    """Test speak with whitespace-only text raises TTSProviderError."""
    provider = FakeTTSProvider(delay_seconds=0.0)

    try:
        provider.speak(TTSRequest(text="   "))
        assert False, "Expected TTSProviderError"
    except TTSProviderError as e:
        assert str(e) == "Empty TTS text"


def test_should_fail_raises_tts_provider_error() -> None:
    """Test speak with should_fail=True raises TTSProviderError."""
    provider = FakeTTSProvider(delay_seconds=0.0, should_fail=True)

    try:
        provider.speak(TTSRequest(text="Hello"))
        assert False, "Expected TTSProviderError"
    except TTSProviderError as e:
        assert str(e) == "Fake TTS failure"


def test_delay_zero_completes_immediately() -> None:
    """Test speak with delay_seconds=0.0 completes immediately."""
    provider = FakeTTSProvider(delay_seconds=0.0)
    start = time.perf_counter()
    response = provider.speak(TTSRequest(text="Fast text"))
    elapsed = time.perf_counter() - start

    assert elapsed < 0.05
    assert response.duration_seconds == 0.0
