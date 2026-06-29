"""MiMo ASR provider using the OpenAI-compatible API."""

from __future__ import annotations

import base64
from collections.abc import Callable
from typing import Any, cast

from app.input.asr.providers.base import ASRProvider, ASRProviderError, ASRRequest, ASRResponse


class MimoASRProvider(ASRProvider):
    """MiMo ASR provider using the OpenAI-compatible API.

    Calls the MiMo-V2.5-ASR model with an audio file via the input_audio
    message content type.
    """

    ALLOWED_LANGUAGES = {"auto", "zh", "en"}

    def __init__(
        self,
        api_key: str | None,
        base_url: str,
        model: str,
        language: str,
        timeout_seconds: float,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        """Initialize MimoASRProvider.

        Args:
            api_key: MiMo API key. Required.
            base_url: MiMo API base URL.
            model: Model name for ASR (e.g. "mimo-v2.5-asr").
            language: Language hint for ASR (e.g. "auto", "zh").
            timeout_seconds: Request timeout.
            client_factory: Optional callable to create the OpenAI client.
                Defaults to the real OpenAI client. Useful for testing.

        Raises:
            ASRProviderError: If language is not one of the allowed values.
        """
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        normalized_language = language.strip().lower()
        if normalized_language not in self.ALLOWED_LANGUAGES:
            raise ASRProviderError("MIMO_ASR_LANGUAGE must be one of: auto, zh, en")
        self._language = normalized_language
        self._timeout = timeout_seconds
        self._client_factory = client_factory

    def recognize(self, request: ASRRequest) -> ASRResponse:
        """Perform ASR on the given audio file.

        Args:
            request: ASR request containing audio_path.

        Returns:
            ASRResponse with recognized text.

        Raises:
            ASRProviderError: If api_key or audio_path is missing, audio file
                does not exist, or the API call fails.
        """
        if not self._api_key:
            raise ASRProviderError("MIMO_API_KEY is required for MiMo ASR")

        if not request.audio_path:
            raise ASRProviderError("audio_path is required for MiMo ASR")

        audio_path = request.audio_path

        try:
            audio_bytes = self._read_audio_file(audio_path)
        except FileNotFoundError:
            raise ASRProviderError("audio file does not exist") from None
        except OSError as exc:
            raise ASRProviderError("audio file could not be read") from exc

        audio_base64 = base64.b64encode(audio_bytes).decode("ascii")
        audio_base64_size = len(audio_base64.encode("utf-8"))
        if audio_base64_size > 10 * 1024 * 1024:
            raise ASRProviderError("audio base64 payload exceeds 10MB limit")
        mime_type = request.mime_type or "audio/wav"
        data_url = f"data:{mime_type};base64,{audio_base64}"

        try:
            completion = self._call_api(data_url)
        except Exception as exc:
            raise ASRProviderError("MiMo ASR request failed") from exc

        text = self._parse_response(completion)
        return ASRResponse(text=text)

    def _read_audio_file(self, path: str) -> bytes:
        """Read and return bytes from an audio file."""
        with open(path, "rb") as f:
            return f.read()

    def _call_api(self, data_url: str) -> Any:
        """Call the MiMo API and return the completion object."""
        from openai import OpenAI

        client = self._client_factory(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=self._timeout,
        ) if self._client_factory else OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=self._timeout,
        )

        return client.chat.completions.create(
            model=self._model,
            messages=cast(
                "list[Any]",
                [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": data_url,
                                },
                            }
                        ],
                    }
                ],
            ),
            extra_body={
                "asr_options": {
                    "language": self._language,
                }
            },
        )

    def _parse_response(self, completion: Any) -> str:
        """Parse recognized text from the API completion object.

        Args:
            completion: The API completion response.

        Returns:
            The recognized text string.

        Raises:
            ASRProviderError: If the response is empty or unparseable.
        """
        try:
            content = completion.choices[0].message.content
        except Exception as exc:
            raise ASRProviderError("MiMo ASR returned empty text") from exc

        if content is None:
            raise ASRProviderError("MiMo ASR returned empty text")

        text = str(content).strip()
        if not text:
            raise ASRProviderError("MiMo ASR returned empty text")

        return text
