"""Chat provider factory."""

import logging

from app.brain.providers.base import ChatProvider, ChatProviderError
from app.brain.providers.fake import FakeChatProvider
from app.brain.providers.minimax import MiniMaxChatProvider
from app.core.config import AppConfig

logger = logging.getLogger(__name__)


def create_chat_provider(config: AppConfig) -> ChatProvider:
    """Create a chat provider based on app configuration.

    Args:
        config: Application configuration.

    Returns:
        A ChatProvider instance.

    Raises:
        ChatProviderError: If provider mode is unsupported or misconfigured.
    """
    mode = config.chat_provider_mode

    if mode == "fake":
        return FakeChatProvider()

    if mode == "minimax":
        if not config.minimax_api_key:
            raise ChatProviderError("MiniMax API key is not configured")
        return MiniMaxChatProvider(
            api_key=config.minimax_api_key,
            group_id=config.minimax_group_id,
            base_url=config.minimax_base_url,
            model=config.minimax_model,
            timeout_seconds=config.minimax_timeout_seconds,
        )

    raise ChatProviderError(f"Unsupported chat provider mode: {mode}")
