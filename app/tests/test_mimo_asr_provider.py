"""Tests for MimoASRProvider."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.input.asr.providers.base import ASRProviderError, ASRRequest
from app.input.asr.providers.mimo import MimoASRProvider


class TestMimoASRProviderLanguageValidation:
    """Tests for language validation."""

    def test_invalid_language_raises(self):
        with pytest.raises(ASRProviderError, match="MIMO_ASR_LANGUAGE must be one of"):
            MimoASRProvider(
                api_key="test-key",
                base_url="https://api.xiaomimimo.com/v1",
                model="mimo-v2.5-asr",
                language="invalid",
                timeout_seconds=30.0,
            )

    def test_language_with_spaces_normalized(self):
        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="  auto  ",
            timeout_seconds=30.0,
        )
        assert provider._language == "auto"

    def test_language_uppercase_normalized(self):
        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="ZH",
            timeout_seconds=30.0,
        )
        assert provider._language == "zh"

    def test_allowed_languages_accepted(self):
        for lang in ("auto", "zh", "en"):
            provider = MimoASRProvider(
                api_key="test-key",
                base_url="https://api.xiaomimimo.com/v1",
                model="mimo-v2.5-asr",
                language=lang,
                timeout_seconds=30.0,
            )
            assert provider._language == lang

    def test_error_message_no_key(self):
        with pytest.raises(ASRProviderError, match="MIMO_ASR_LANGUAGE must be one of"):
            MimoASRProvider(
                api_key="secret-api-key",
                base_url="https://api.xiaomimimo.com/v1",
                model="mimo-v2.5-asr",
                language="invalid",
                timeout_seconds=30.0,
            )
        with pytest.raises(ASRProviderError) as exc_info:
            MimoASRProvider(
                api_key="secret-api-key",
                base_url="https://api.xiaomimimo.com/v1",
                model="mimo-v2.5-asr",
                language="invalid",
                timeout_seconds=30.0,
            )
        assert "secret-api-key" not in str(exc_info.value)


class TestMimoASRProviderValidation:
    def test_missing_api_key_raises(self):
        provider = MimoASRProvider(
            api_key=None,
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
        )
        with pytest.raises(ASRProviderError, match="MIMO_API_KEY is required"):
            provider.recognize(ASRRequest(audio_path="/tmp/test.wav"))

    def test_missing_audio_path_raises(self):
        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
        )
        with pytest.raises(ASRProviderError, match="audio_path is required"):
            provider.recognize(ASRRequest(audio_path=None))

    def test_none_audio_path_raises(self):
        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
        )
        with pytest.raises(ASRProviderError, match="audio_path is required"):
            provider.recognize(ASRRequest())


class TestMimoASRProviderBase64Limit:
    def test_base64_over_10mb_raises(self, tmp_path):
        # Create a file large enough that base64 encoding exceeds 10MB
        # 10MB base64 = ~7.5MB raw bytes, but we need to account for encoding overhead
        # Use 8MB of data to ensure base64 exceeds 10MB
        large_audio = tmp_path / "large.wav"
        large_audio.write_bytes(b"\x00" * (8 * 1024 * 1024))

        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
        )

        with pytest.raises(ASRProviderError, match="audio base64 payload exceeds 10MB limit"):
            provider.recognize(ASRRequest(audio_path=str(large_audio)))

    def test_base64_error_message_no_base64(self, tmp_path):
        large_audio = tmp_path / "large.wav"
        large_audio.write_bytes(b"\x00" * (8 * 1024 * 1024))

        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
        )

        with pytest.raises(ASRProviderError) as exc_info:
            provider.recognize(ASRRequest(audio_path=str(large_audio)))
        error_msg = str(exc_info.value)
        # Error message should not contain actual base64 content
        assert "data:audio" not in error_msg
        assert "base64," not in error_msg


class TestMimoASRProviderApiCall:
    def test_success_parses_text(self, tmp_path, monkeypatch):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio bytes")

        captured_call = {}

        def fake_create(**kwargs):
            captured_call.update(kwargs)
            mock_result = MagicMock()
            mock_result.choices = [MagicMock(message=MagicMock(content="recognized text"))]
            return mock_result

        mock_chat = MagicMock()
        mock_chat.completions.create = fake_create

        def fake_client_factory(**kwargs):
            mock_client = MagicMock()
            mock_client.chat = mock_chat
            return mock_client

        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
            client_factory=fake_client_factory,
        )

        response = provider.recognize(ASRRequest(audio_path=str(audio_file)))
        assert response.text == "recognized text"

    def test_data_url_prefix(self, tmp_path, monkeypatch):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio bytes")

        captured_call = {}

        def fake_create(**kwargs):
            captured_call.update(kwargs)
            mock_result = MagicMock()
            mock_result.choices = [MagicMock(message=MagicMock(content="ok"))]
            return mock_result

        mock_chat = MagicMock()
        mock_chat.completions.create = fake_create

        def fake_client_factory(**kwargs):
            mock_client = MagicMock()
            mock_client.chat = mock_chat
            return mock_client

        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
            client_factory=fake_client_factory,
        )

        provider.recognize(ASRRequest(audio_path=str(audio_file), mime_type="audio/wav"))

        messages = captured_call["messages"]
        content_block = messages[0]["content"][0]
        data_url = content_block["input_audio"]["data"]
        assert data_url.startswith("data:audio/wav;base64,")

    def test_model_passed(self, tmp_path):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio bytes")

        captured_call = {}

        def fake_create(**kwargs):
            captured_call.update(kwargs)
            mock_result = MagicMock()
            mock_result.choices = [MagicMock(message=MagicMock(content="ok"))]
            return mock_result

        mock_chat = MagicMock()
        mock_chat.completions.create = fake_create

        def fake_client_factory(**kwargs):
            mock_client = MagicMock()
            mock_client.chat = mock_chat
            return mock_client

        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
            client_factory=fake_client_factory,
        )

        provider.recognize(ASRRequest(audio_path=str(audio_file)))

        assert captured_call["model"] == "mimo-v2.5-asr"

    def test_extra_body(self, tmp_path):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio bytes")

        captured_call = {}

        def fake_create(**kwargs):
            captured_call.update(kwargs)
            mock_result = MagicMock()
            mock_result.choices = [MagicMock(message=MagicMock(content="ok"))]
            return mock_result

        mock_chat = MagicMock()
        mock_chat.completions.create = fake_create

        def fake_client_factory(**kwargs):
            mock_client = MagicMock()
            mock_client.chat = mock_chat
            return mock_client

        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
            client_factory=fake_client_factory,
        )

        provider.recognize(ASRRequest(audio_path=str(audio_file)))

        extra_body = captured_call["extra_body"]
        assert extra_body["asr_options"]["language"] == "auto"

    def test_empty_content_raises(self, tmp_path):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio bytes")

        def fake_create(**kwargs):
            mock_result = MagicMock()
            mock_result.choices = [MagicMock(message=MagicMock(content=""))]
            return mock_result

        mock_chat = MagicMock()
        mock_chat.completions.create = fake_create

        def fake_client_factory(**kwargs):
            mock_client = MagicMock()
            mock_client.chat = mock_chat
            return mock_client

        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
            client_factory=fake_client_factory,
        )

        with pytest.raises(ASRProviderError, match="MiMo ASR returned empty text"):
            provider.recognize(ASRRequest(audio_path=str(audio_file)))

    def test_none_content_raises(self, tmp_path):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio bytes")

        def fake_create(**kwargs):
            mock_result = MagicMock()
            mock_result.choices = [MagicMock(message=MagicMock(content=None))]
            return mock_result

        mock_chat = MagicMock()
        mock_chat.completions.create = fake_create

        def fake_client_factory(**kwargs):
            mock_client = MagicMock()
            mock_client.chat = mock_chat
            return mock_client

        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
            client_factory=fake_client_factory,
        )

        with pytest.raises(ASRProviderError, match="MiMo ASR returned empty text"):
            provider.recognize(ASRRequest(audio_path=str(audio_file)))

    def test_sdk_exception_raises_safe_error(self, tmp_path):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio bytes")

        def failing_create(**kwargs):
            raise RuntimeError("secret API key leaked")

        mock_chat = MagicMock()
        mock_chat.completions.create = failing_create

        def fake_client_factory(**kwargs):
            mock_client = MagicMock()
            mock_client.chat = mock_chat
            return mock_client

        provider = MimoASRProvider(
            api_key="test-key",
            base_url="https://api.xiaomimimo.com/v1",
            model="mimo-v2.5-asr",
            language="auto",
            timeout_seconds=30.0,
            client_factory=fake_client_factory,
        )

        with pytest.raises(ASRProviderError, match="MiMo ASR request failed") as exc_info:
            provider.recognize(ASRRequest(audio_path=str(audio_file)))

        assert "secret API key" not in str(exc_info.value)
        assert "test-key" not in str(exc_info.value)
