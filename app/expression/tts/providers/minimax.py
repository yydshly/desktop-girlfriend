"""MiniMax TTS provider implementation."""

import base64
import binascii
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.expression.tts.providers.base import (
    TTSProvider,
    TTSProviderError,
    TTSRequest,
    TTSResponse,
)


@dataclass(frozen=True)
class MiniMaxTTSConfig:
    """Configuration for MiniMax TTS provider."""

    api_key: str
    group_id: str | None
    base_url: str
    model: str
    voice_id: str
    timeout_seconds: float
    tts_path: str
    output_dir: str


class MiniMaxTTSProvider(TTSProvider):
    """MiniMax TTS provider using the MiniMax T2A v2 API."""

    supports_audio_path_playback = True

    def __init__(
        self,
        api_key: str,
        group_id: str | None,
        base_url: str,
        model: str,
        voice_id: str,
        timeout_seconds: float,
        tts_path: str,
        output_dir: str,
    ) -> None:
        """Initialize MiniMaxTTSProvider.

        Args:
            api_key: MiniMax API key.
            group_id: Optional MiniMax group ID.
            base_url: MiniMax API base URL.
            model: TTS model name.
            voice_id: Voice identifier.
            timeout_seconds: HTTP request timeout.
            tts_path: API endpoint path.
            output_dir: Directory to store temporary audio files.
        """
        self._config = MiniMaxTTSConfig(
            api_key=api_key,
            group_id=group_id,
            base_url=base_url,
            model=model,
            voice_id=voice_id,
            timeout_seconds=timeout_seconds,
            tts_path=tts_path,
            output_dir=output_dir,
        )

    def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize text to an audio file without playing it.

        Args:
            request: The TTS request containing text to synthesize.

        Returns:
            TTSResponse with audio_path set.

        Raises:
            TTSProviderError: If synthesis or HTTP fails.
        """
        text = request.text

        # Strict validation
        if type(text) is not str or not text.strip():
            raise TTSProviderError("Empty TTS text")

        try:
            payload = self._build_request_payload(text)
            headers = self._build_headers()
            result = self._send_request(payload, headers)
            audio_bytes = self._parse_audio_bytes(result)
            audio_path = self._write_audio_file(audio_bytes)
            return TTSResponse(duration_seconds=0.0, audio_path=str(audio_path))
        except TTSProviderError:
            raise
        except Exception as e:
            raise TTSProviderError("MiniMax TTS network error") from e

    def speak(self, request: TTSRequest) -> TTSResponse:
        """Synthesize and play back the given text.

        Args:
            request: The TTS request containing text to speak.

        Returns:
            TTSResponse with the playback duration.

        Raises:
            TTSProviderError: If synthesis, HTTP, or playback fails.
        """
        response = self.synthesize(request)
        if response.audio_path is None:
            raise TTSProviderError("MiniMax TTS returned empty audio")
        self._play_audio_file(Path(response.audio_path))
        return response

    def _build_request_payload(self, text: str) -> dict[str, Any]:
        """Build the TTS API request payload."""
        payload: dict[str, Any] = {
            "model": self._config.model,
            "text": text.strip(),
            "voice_setting": {
                "voice_id": self._config.voice_id,
                "speed": 1.0,
                "vol": 1.0,
                "pitch": 0,
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1,
            },
        }
        if self._config.group_id:
            payload["group_id"] = self._config.group_id
        return payload

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for the TTS API request."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._config.api_key}",
        }

    def _send_request(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        """Send the TTS API request and return the parsed JSON response.

        Args:
            payload: Request body dict.
            headers: HTTP headers dict.

        Returns:
            Parsed JSON response dict.

        Raises:
            TTSProviderError: On HTTP errors or non-OK status codes.
        """
        import json
        import urllib.request

        url = f"{self._config.base_url.rstrip('/')}{self._config.tts_path}"
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self._config.timeout_seconds) as resp:
                status = resp.status
                if status != 200:
                    raise TTSProviderError("MiniMax TTS HTTP error")
                result: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
                return result
        except urllib.error.HTTPError as e:
            raise TTSProviderError("MiniMax TTS HTTP error") from e
        except urllib.error.URLError as e:
            raise TTSProviderError("MiniMax TTS network error") from e

    def _parse_audio_bytes(self, result: dict[str, Any]) -> bytes:
        """Extract audio bytes from the API response.

        Args:
            result: Parsed API response dict.

        Returns:
            Raw audio bytes.

        Raises:
            TTSProviderError: If audio data is missing or cannot be decoded.
        """
        audio_text: str | None = None

        # Try common response shapes
        if "data" in result and isinstance(result["data"], dict):
            audio_data = result["data"]
            if "audio" in audio_data:
                audio_text = audio_data["audio"]
        elif "audio" in result:
            audio_text = result["audio"]

        if audio_text is None:
            raise TTSProviderError("MiniMax TTS response parse error")

        audio_text = audio_text.strip()

        # Try hex decoding first
        try:
            if all(c in "0123456789abcdefABCDEF" for c in audio_text) and len(audio_text) % 2 == 0:
                return bytes.fromhex(audio_text)
        except (ValueError, binascii.Error):
            pass

        # Try base64 decoding
        try:
            return base64.b64decode(audio_text)
        except (ValueError, binascii.Error):
            pass

        raise TTSProviderError("MiniMax TTS response parse error")

    def _write_audio_file(self, audio_bytes: bytes) -> Path:
        """Write audio bytes to a temporary file.

        Args:
            audio_bytes: Raw audio data.

        Returns:
            Path to the written file.

        Raises:
            TTSProviderError: If the file cannot be written or bytes are empty.
        """
        if not audio_bytes:
            raise TTSProviderError("MiniMax TTS returned empty audio")

        output_dir = Path(self._config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        audio_path = output_dir / f"tts_{uuid.uuid4().hex}.mp3"
        audio_path.write_bytes(audio_bytes)
        return audio_path

    def _play_audio_file(self, path: Path) -> None:
        """Play the audio file using the system default player.

        Args:
            path: Path to the audio file to play.
        """
        path_str = str(path)
        if hasattr(os, "startfile"):
            os.startfile(path_str)
        else:
            import subprocess
            subprocess.run(["xdg-open", path_str], check=False, capture_output=True)
