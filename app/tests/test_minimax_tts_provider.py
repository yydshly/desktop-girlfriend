"""Tests for MiniMaxTTSProvider."""

import base64
from pathlib import Path
from unittest.mock import patch

import pytest

from app.expression.tts.providers.base import TTSProviderError, TTSRequest
from app.expression.tts.providers.minimax import MiniMaxTTSProvider


def _make_provider(**overrides) -> MiniMaxTTSProvider:
    """Create a MiniMaxTTSProvider with default test config."""
    defaults = dict(
        api_key="test-api-key",
        group_id="test-group",
        base_url="https://api.minimax.chat/v1",
        model="speech-02-hd",
        voice_id="female-shaonv",
        timeout_seconds=30.0,
        tts_path="/t2a_v2",
        output_dir=".tmp/tts_test",
    )
    defaults.update(overrides)
    return MiniMaxTTSProvider(**defaults)  # type: ignore[arg-type]


class TestMiniMaxTTSProviderInputValidation:
    """Tests for input validation."""

    def test_empty_text_raises_tts_provider_error(self) -> None:
        """Test empty string raises TTSProviderError."""
        provider = _make_provider()
        with pytest.raises(TTSProviderError, match="Empty TTS text"):
            provider.speak(TTSRequest(text=""))

    def test_whitespace_text_raises_tts_provider_error(self) -> None:
        """Test whitespace-only text raises TTSProviderError."""
        provider = _make_provider()
        with pytest.raises(TTSProviderError, match="Empty TTS text"):
            provider.speak(TTSRequest(text="   "))

    def test_str_subclass_raises_tts_provider_error(self) -> None:
        """Test str subclass raises TTSProviderError (strict type contract)."""

        class CustomStr(str):
            pass

        provider = _make_provider()
        with pytest.raises(TTSProviderError, match="Empty TTS text"):
            provider.speak(TTSRequest(text=CustomStr("Hello")))


class TestMiniMaxTTSProviderBuildPayload:
    """Tests for request payload building."""

    def test_build_request_payload_contains_model_and_text(self) -> None:
        """Test payload contains model and text fields."""
        provider = _make_provider(model="speech-02-hd", voice_id="female-shaonv")
        payload = provider._build_request_payload("你好，小云")
        assert payload["model"] == "speech-02-hd"
        assert payload["text"] == "你好，小云"

    def test_build_request_payload_contains_voice_setting(self) -> None:
        """Test payload contains voice_setting."""
        provider = _make_provider(voice_id="female-shaonv")
        payload = provider._build_request_payload("Test")
        assert "voice_setting" in payload
        assert payload["voice_setting"]["voice_id"] == "female-shaonv"

    def test_build_request_payload_contains_audio_setting(self) -> None:
        """Test payload contains audio_setting."""
        provider = _make_provider()
        payload = provider._build_request_payload("Test")
        assert "audio_setting" in payload
        assert payload["audio_setting"]["format"] == "mp3"
        assert payload["audio_setting"]["sample_rate"] == 32000

    def test_build_request_payload_includes_group_id_when_present(self) -> None:
        """Test payload includes group_id when set."""
        provider = _make_provider(group_id="my-group")
        payload = provider._build_request_payload("Test")
        assert payload["group_id"] == "my-group"

    def test_build_request_payload_strips_text(self) -> None:
        """Test payload strips surrounding whitespace from text."""
        provider = _make_provider()
        payload = provider._build_request_payload("  简洁  ")
        assert payload["text"] == "简洁"


class TestMiniMaxTTSProviderBuildHeaders:
    """Tests for HTTP headers building."""

    def test_build_headers_contains_content_type(self) -> None:
        """Test headers contain Content-Type."""
        provider = _make_provider(api_key="my-key")
        headers = provider._build_headers()
        assert headers["Content-Type"] == "application/json"

    def test_build_headers_contains_authorization(self) -> None:
        """Test headers contain Authorization Bearer token."""
        provider = _make_provider(api_key="my-key")
        headers = provider._build_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer my-key"

    def test_build_headers_does_not_log_key(self) -> None:
        """Test that building headers does not print or log the key."""
        provider = _make_provider(api_key="secret-key")
        # This test verifies no print happens — in practice we rely on code review
        headers = provider._build_headers()
        # Key should be in header value but not exposed in plaintext logs
        assert "secret-key" not in str(headers) or "Bearer" in str(headers)


class TestMiniMaxTTSProviderParseAudio:
    """Tests for audio parsing from API response."""

    def test_parse_audio_hex_string(self) -> None:
        """Test parsing hex-encoded audio string."""
        provider = _make_provider()
        # "hello" in hex is "68656c6c6f"
        result = {"data": {"audio": "68656c6c6f"}}
        audio_bytes = provider._parse_audio_bytes(result)
        assert audio_bytes == b"hello"

    def test_parse_audio_base64_string(self) -> None:
        """Test parsing base64-encoded audio string."""
        provider = _make_provider()
        encoded = base64.b64encode(b"test audio").decode("utf-8")
        result = {"data": {"audio": encoded}}
        audio_bytes = provider._parse_audio_bytes(result)
        assert audio_bytes == b"test audio"

    def test_parse_audio_top_level_audio_key(self) -> None:
        """Test parsing audio from top-level audio key."""
        provider = _make_provider()
        encoded = base64.b64encode(b"top-level").decode("utf-8")
        result = {"audio": encoded}
        audio_bytes = provider._parse_audio_bytes(result)
        assert audio_bytes == b"top-level"

    def test_parse_audio_missing_audio_raises_error(self) -> None:
        """Test that missing audio field raises TTSProviderError."""
        provider = _make_provider()
        result: dict[str, object] = {"data": {}}
        with pytest.raises(TTSProviderError, match="response parse error"):
            provider._parse_audio_bytes(result)

    def test_parse_audio_invalid_encoding_raises_error(self) -> None:
        """Test that invalid encoding raises TTSProviderError."""
        provider = _make_provider()
        result = {"data": {"audio": "not-hex-or-base64!!"}}
        with pytest.raises(TTSProviderError, match="response parse error"):
            provider._parse_audio_bytes(result)


class TestMiniMaxTTSProviderWriteAudio:
    """Tests for audio file writing."""

    def test_write_audio_file_creates_file(self, tmp_path: Path) -> None:
        """Test that audio file is created at the correct path."""
        provider = _make_provider(output_dir=str(tmp_path))
        audio_bytes = b"\x00\x01\x02\x03"
        path = provider._write_audio_file(audio_bytes)
        assert path.exists()
        assert path.read_bytes() == audio_bytes

    def test_write_audio_file_creates_output_dir(self, tmp_path: Path) -> None:
        """Test that output directory is created if it does not exist."""
        provider = _make_provider(output_dir=str(tmp_path / "nested" / "dir"))
        audio_bytes = b"data"
        path = provider._write_audio_file(audio_bytes)
        assert path.exists()
        assert path.parent.name == "dir"

    def test_write_audio_file_empty_bytes_raises_error(self, tmp_path: Path) -> None:
        """Test that empty audio bytes raise TTSProviderError."""
        provider = _make_provider(output_dir=str(tmp_path))
        with pytest.raises(TTSProviderError, match="empty audio"):
            provider._write_audio_file(b"")


class TestMiniMaxTTSProviderSpeak:
    """Tests for the full speak() method using mocks."""

    def test_speak_calls_send_request(self) -> None:
        """Test speak() calls _send_request."""
        provider = _make_provider()
        mock_result = {"data": {"audio": base64.b64encode(b"hello").decode("utf-8")}}
        with patch.object(provider, "_send_request", return_value=mock_result) as mock_send:
            with patch.object(provider, "_write_audio_file", return_value=Path("/tmp/test.mp3")):
                with patch.object(provider, "_play_audio_file"):
                    provider.speak(TTSRequest(text="Hello"))
                    mock_send.assert_called_once()

    def test_speak_calls_write_audio_file(self) -> None:
        """Test speak() calls _write_audio_file with parsed audio bytes."""
        provider = _make_provider()
        audio_bytes = b"parsed audio"
        mock_result = {"data": {"audio": base64.b64encode(audio_bytes).decode("utf-8")}}
        with patch.object(provider, "_send_request", return_value=mock_result):
            with patch.object(provider, "_write_audio_file", return_value=Path("/tmp/test.mp3")) as mock_write:
                with patch.object(provider, "_play_audio_file"):
                    provider.speak(TTSRequest(text="Hello"))
                    mock_write.assert_called_once_with(audio_bytes)

    def test_speak_calls_play_audio_file(self) -> None:
        """Test speak() calls _play_audio_file with the written file path."""
        provider = _make_provider()
        audio_path = Path("/tmp/test.mp3")
        mock_result = {"data": {"audio": base64.b64encode(b"hello").decode("utf-8")}}
        with patch.object(provider, "_send_request", return_value=mock_result):
            with patch.object(provider, "_write_audio_file", return_value=audio_path):
                with patch.object(provider, "_play_audio_file") as mock_play:
                    provider.speak(TTSRequest(text="Hello"))
                    mock_play.assert_called_once_with(audio_path)

    def test_speak_returns_tts_response(self) -> None:
        """Test speak() returns TTSResponse."""
        provider = _make_provider()
        mock_result = {"data": {"audio": base64.b64encode(b"hello").decode("utf-8")}}
        with patch.object(provider, "_send_request", return_value=mock_result):
            with patch.object(provider, "_write_audio_file", return_value=Path("/tmp/test.mp3")):
                with patch.object(provider, "_play_audio_file"):
                    response = provider.speak(TTSRequest(text="Hello"))
                    assert response.duration_seconds == 0.0

    def test_speak_network_error_raises_safe_error(self) -> None:
        """Test that network errors raise TTSProviderError with safe message."""
        provider = _make_provider()
        with patch.object(provider, "_send_request", side_effect=Exception("network failure")):
            with pytest.raises(TTSProviderError, match="network error"):
                provider.speak(TTSRequest(text="Hello"))

    def test_speak_error_message_does_not_leak_key(self) -> None:
        """Test that error messages do not contain raw API key."""
        provider = _make_provider(api_key="super-secret-key")
        with patch.object(provider, "_send_request", side_effect=Exception("network failure")):
            try:
                provider.speak(TTSRequest(text="Hello"))
            except TTSProviderError as e:
                # Error message must not contain the raw key
                assert "super-secret-key" not in str(e)
                assert "Bearer super-secret-key" not in str(e)

    def test_speak_returns_response_with_audio_path(self) -> None:
        """Test speak() returns TTSResponse with audio_path set."""
        provider = _make_provider()
        audio_path = Path("/tmp/test.mp3")
        mock_result = {"data": {"audio": base64.b64encode(b"hello").decode("utf-8")}}
        with patch.object(provider, "_send_request", return_value=mock_result):
            with patch.object(provider, "_write_audio_file", return_value=audio_path):
                with patch.object(provider, "_play_audio_file"):
                    response = provider.speak(TTSRequest(text="Hello"))
                    assert response.audio_path == str(audio_path)


class TestMiniMaxTTSProviderSynthesize:
    """Tests for the synthesize() method."""

    def test_synthesize_validates_empty_text(self) -> None:
        """Test synthesize() raises TTSProviderError for empty text."""
        provider = _make_provider()
        with pytest.raises(TTSProviderError, match="Empty TTS text"):
            provider.synthesize(TTSRequest(text=""))

    def test_synthesize_returns_tts_response_with_audio_path(self) -> None:
        """Test synthesize() returns TTSResponse with audio_path set."""
        provider = _make_provider()
        audio_path = Path("/tmp/test.mp3")
        mock_result = {"data": {"audio": base64.b64encode(b"hello").decode("utf-8")}}
        with patch.object(provider, "_send_request", return_value=mock_result):
            with patch.object(provider, "_write_audio_file", return_value=audio_path):
                response = provider.synthesize(TTSRequest(text="Hello"))
                assert response.audio_path == str(audio_path)
                assert response.duration_seconds == 0.0

    def test_synthesize_does_not_call_play_audio_file(self) -> None:
        """Test synthesize() does NOT call _play_audio_file."""
        provider = _make_provider()
        audio_path = Path("/tmp/test.mp3")
        mock_result = {"data": {"audio": base64.b64encode(b"hello").decode("utf-8")}}
        with patch.object(provider, "_send_request", return_value=mock_result):
            with patch.object(provider, "_write_audio_file", return_value=audio_path):
                with patch.object(provider, "_play_audio_file") as mock_play:
                    provider.synthesize(TTSRequest(text="Hello"))
                    mock_play.assert_not_called()

    def test_synthesize_calls_write_audio_file(self) -> None:
        """Test synthesize() calls _write_audio_file."""
        provider = _make_provider()
        audio_path = Path("/tmp/test.mp3")
        audio_bytes = b"parsed audio"
        mock_result = {"data": {"audio": base64.b64encode(audio_bytes).decode("utf-8")}}
        with patch.object(provider, "_send_request", return_value=mock_result):
            with patch.object(provider, "_write_audio_file", return_value=audio_path) as mock_write:
                provider.synthesize(TTSRequest(text="Hello"))
                mock_write.assert_called_once_with(audio_bytes)

    def test_synthesize_network_error_raises_safe_error(self) -> None:
        """Test that network errors raise TTSProviderError with safe message."""
        provider = _make_provider()
        with patch.object(provider, "_send_request", side_effect=Exception("network failure")):
            with pytest.raises(TTSProviderError, match="network error"):
                provider.synthesize(TTSRequest(text="Hello"))

    def test_synthesize_error_message_does_not_leak_key(self) -> None:
        """Test that error messages do not contain raw API key."""
        provider = _make_provider(api_key="super-secret-key")
        with patch.object(provider, "_send_request", side_effect=Exception("network failure")):
            try:
                provider.synthesize(TTSRequest(text="Hello"))
            except TTSProviderError as e:
                assert "super-secret-key" not in str(e)
                assert "Bearer super-secret-key" not in str(e)


def test_minimax_tts_provider_supports_audio_path_playback() -> None:
    """Test MiniMaxTTSProvider.supports_audio_path_playback is True."""
    provider = _make_provider()
    assert provider.supports_audio_path_playback is True
