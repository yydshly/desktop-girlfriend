"""Product status view builder (V11-A)."""

from __future__ import annotations

from app.core.config import AppConfig
from app.ui.avatar_action import AvatarAction
from app.ui.product_status import ProductStatusItem, ProductStatusView


def build_product_status_view(
    *,
    config: AppConfig,
    avatar_action: AvatarAction,
) -> ProductStatusView:
    """Build a product status view from app configuration.

    Args:
        config: The application configuration.
        avatar_action: The current avatar action state.

    Returns:
        A ProductStatusView describing all enabled/disabled features.
    """
    items: list[ProductStatusItem] = [
        ProductStatusItem("对话", True, "已启用"),
        ProductStatusItem("记忆上下文", config.memory_context_enabled),
        ProductStatusItem("记忆建议", config.memory_suggestions_enabled),
        ProductStatusItem("记忆管理", config.memory_management_enabled),
        ProductStatusItem("主动陪伴", config.proactive_enabled),
        ProductStatusItem("主动陪伴 TTS", config.proactive_tts_enabled),
        ProductStatusItem("勿扰时间", config.proactive_quiet_hours_enabled),
        ProductStatusItem("当前角色状态", True, avatar_action.value),
    ]

    return ProductStatusView(items=tuple(items))
