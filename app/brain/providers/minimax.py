"""MiniMax chat provider implementation."""

import json
import urllib.error
import urllib.request
from typing import Any, cast

from app.brain.providers.base import (
    ChatProvider,
    ChatProviderError,
    ChatRequest,
    ChatResponse,
)


class MiniMaxChatProvider(ChatProvider):
    """Chat provider backed by MiniMax chat completion API."""

    def __init__(
        self,
        api_key: str,
        group_id: str | None,
        base_url: str,
        model: str,
        timeout_seconds: float,
    ) -> None:
        """Initialize MiniMaxChatProvider.

        Args:
            api_key: MiniMax API key.
            group_id: MiniMax group ID (optional).
            base_url: Base URL for MiniMax API.
            model: Model name to use.
            timeout_seconds: Request timeout in seconds.
        """
        self._api_key = api_key
        self._group_id = group_id
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds

    def generate(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat response via MiniMax API.

        Args:
            request: The chat request.

        Returns:
            ChatResponse with the generated text.

        Raises:
            ChatProviderError: On network error, HTTP error, or parse error.
        """
        payload = self._build_request_payload(request)
        headers = self._build_headers()

        try:
            result = self._send_request(payload, headers)
        except ChatProviderError:
            raise
        except Exception as e:
            raise ChatProviderError(f"MiniMax request failed: {e}") from e

        text = self._parse_response(result)
        if not text:
            raise ChatProviderError("MiniMax returned empty response text")

        return ChatResponse(text=text)

    def _build_request_payload(self, request: ChatRequest) -> dict[str, Any]:
        """Build the API request payload."""
        messages = [
            {"role": m.role, "content": m.content} for m in request.messages
        ]
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if self._group_id:
            payload["group_id"] = self._group_id
        return payload

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

    def _send_request(
        self, payload: dict[str, Any], headers: dict[str, str]
    ) -> dict[str, Any]:
        """Send HTTP request to MiniMax API."""
        url = f"{self._base_url}/text/chatcompletion_v2"
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            raise ChatProviderError(
                f"MiniMax API HTTP {e.code}: {body[:200]}"
            ) from e
        except urllib.error.URLError as e:
            raise ChatProviderError(f"MiniMax network error: {e.reason}") from e

        try:
            return cast(dict[str, Any], json.loads(body))
        except json.JSONDecodeError as e:
            raise ChatProviderError(
                f"MiniMax response parse error: {e}"
            ) from e

    def _parse_response(self, result: dict[str, Any]) -> str:
        """Parse the MiniMax API response to extract reply text."""
        try:
            choices = result.get("choices", [])
            if not choices:
                raise ChatProviderError("MiniMax response has no choices")
            first = choices[0]
            message: dict[str, Any] = first.get("message", {})
            content: str = message.get("content", "")
            return content
        except (KeyError, IndexError, TypeError) as e:
            raise ChatProviderError(
                f"MiniMax response structure error: {e}"
            ) from e
