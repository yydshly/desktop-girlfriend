"""MiniMax chat provider smoke test script.

Run manually to verify MiniMaxChatProvider works with real API.

Usage:
    .venv\\Scripts\\python.exe scripts\\smoke_minimax_chat.py

Environment variables required:
    MINIMAX_API_KEY - your MiniMax API key
    MINIMAX_GROUP_ID - your MiniMax group ID (optional)
    MINIMAX_BASE_URL - API base URL (default: https://api.minimax.chat/v1)
    MINIMAX_CHAT_PATH - chat endpoint path (default: /text/chatcompletion_v2)
    MINIMAX_MODEL - model name (default: MiniMax-Text-01)
    MINIMAX_TIMEOUT_SECONDS - request timeout (default: 30)
"""

import os
import sys

from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def main() -> None:
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("MINIMAX_API_KEY is required")
        sys.exit(1)

    group_id = os.getenv("MINIMAX_GROUP_ID")
    base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
    chat_path = os.getenv("MINIMAX_CHAT_PATH", "/text/chatcompletion_v2")
    model = os.getenv("MINIMAX_MODEL", "MiniMax-Text-01")
    timeout_str = os.getenv("MINIMAX_TIMEOUT_SECONDS", "30")

    try:
        timeout = float(timeout_str)
    except ValueError:
        print(f"Invalid MINIMAX_TIMEOUT_SECONDS: {timeout_str}")
        sys.exit(1)

    print(f"base_url: {base_url}")
    print(f"chat_path: {chat_path}")
    print(f"model: {model}")
    print(f"group_id: {'true' if group_id else 'false'}")
    print()

    from unittest.mock import MagicMock

    from app.brain.providers.base import ChatProviderError, ChatRequest
    from app.brain.providers.minimax import MiniMaxChatProvider

    provider = MiniMaxChatProvider(
        api_key=api_key,
        group_id=group_id,
        base_url=base_url,
        model=model,
        timeout_seconds=timeout,
        chat_path=chat_path,
    )

    request = ChatRequest(
        messages=[
            MagicMock(role="user", content="你好，请用一句话回复我。"),
        ],
    )

    try:
        response = provider.generate(request)
        print("SUCCESS")
        print(f"assistant text: {response.text}")
    except ChatProviderError as e:
        print("FAILED")
        print(f"error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
