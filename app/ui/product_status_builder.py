"""Product status view builder (V11-A / V11-C)."""

from __future__ import annotations

from app.core.config import AppConfig
from app.core.startup_diagnostics import StartupDiagnostics
from app.core.version import AppVersion
from app.ui.avatar_action import AvatarAction
from app.ui.proactive_real_ux_view import render_proactive_control_status
from app.ui.product_status import ProductStatusItem, ProductStatusView
from app.ui.startup_diagnostics_view import render_startup_diagnostics_summary


def build_product_status_view(
    *,
    config: AppConfig,
    avatar_action: AvatarAction,
    startup_diagnostics: StartupDiagnostics | None = None,
    app_version: AppVersion | None = None,
) -> ProductStatusView:
    """Build a product status view from app configuration.

    Args:
        config: The application configuration.
        avatar_action: The current avatar action state.
        startup_diagnostics: Optional startup diagnostics to display.
        app_version: Optional app version to display.

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
        # Phase 3-D: compact proactive control hint
        ProductStatusItem("主动控制", config.proactive_enabled, render_proactive_control_status()),
        ProductStatusItem("当前角色状态", True, avatar_action.value),
    ]

    if startup_diagnostics is not None:
        items.append(
            ProductStatusItem(
                "启动检查",
                startup_diagnostics.ok,
                render_startup_diagnostics_summary(startup_diagnostics),
            )
        )

    if app_version is not None:
        items.append(ProductStatusItem("版本", True, app_version.version))
        items.append(ProductStatusItem("发布阶段", True, app_version.release_stage))

    return ProductStatusView(items=tuple(items))
