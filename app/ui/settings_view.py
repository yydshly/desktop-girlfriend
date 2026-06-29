"""Settings view types and builders (Phase 2-E)."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import AppConfig
from app.core.version import AppVersion


@dataclass(frozen=True)
class SettingsSection:
    """A single section within the settings panel."""

    title: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class SettingsView:
    """A collection of settings sections for display."""

    sections: tuple[SettingsSection, ...]


def render_enabled(value: bool) -> str:
    """Return a human-readable enabled/disabled label.

    Args:
        value: Whether the feature is enabled.

    Returns:
        "已启用" or "未启用".
    """
    return "已启用" if value else "未启用"


def render_provider_mode(mode: str) -> str:
    """Return a human-readable provider mode description.

    Args:
        mode: The provider mode string.

    Returns:
        A friendly description of the mode.
    """
    if mode == "fake":
        return "fake（测试模式）"
    return mode


def render_api_key_status(key: str | None) -> str:
    """Return whether an API key is configured without revealing its value.

    Args:
        key: The API key value, or None if not set.

    Returns:
        "已配置" or "未配置".
    """
    return "已配置" if key else "未配置"


_CONFIG_EXAMPLE = """
# 开启记忆功能
MEMORY_CONTEXT_ENABLED=true
MEMORY_SUGGESTIONS_ENABLED=true
MEMORY_MANAGEMENT_ENABLED=true

# 开启主动陪伴
PROACTIVE_ENABLED=true
PROACTIVE_IDLE_SECONDS=300
PROACTIVE_COOLDOWN_SECONDS=1800
PROACTIVE_MAX_PER_SESSION=3
PROACTIVE_QUIET_HOURS_ENABLED=true
PROACTIVE_QUIET_START_HOUR=23
PROACTIVE_QUIET_END_HOUR=8
""".strip()


def build_settings_view(
    config: AppConfig,
    *,
    app_version: AppVersion | None = None,
) -> SettingsView:
    """Build a read-only settings view from the current configuration.

    Args:
        config: The application configuration.
        app_version: Optional app version information.

    Returns:
        A SettingsView describing all current settings.
    """
    # Section 1: Basic info
    version_str = app_version.version if app_version else "0.1.0-rc.3"
    release_str = app_version.release_stage if app_version else "release-candidate"

    basic_lines = [
        "应用：Desktop Girlfriend",
        f"版本：{version_str}",
        f"发布阶段：{release_str}",
    ]
    if config.app_env != "dev":
        basic_lines.append(f"环境：{config.app_env}")

    # Section 2: Chat settings
    chat_api_key_status = render_api_key_status(config.minimax_api_key)
    chat_lines = [
        f"对话 provider：{render_provider_mode(config.chat_provider_mode)}",
        f"MiniMax model：{config.minimax_model}",
        f"MiniMax API Key：{chat_api_key_status}",
    ]
    if config.chat_provider_mode == "fake":
        chat_lines.append("")
        chat_lines.append("当前是 fake 测试模式，不会调用真实 LLM。")

    # Section 3: Voice settings
    voice_lines = [
        f"TTS provider：{render_provider_mode(config.tts_provider_mode)}",
        f"ASR provider：{render_provider_mode(config.asr_provider_mode)}",
        f"Mimo API Key：{render_api_key_status(config.mimo_api_key)}",
        f"主动陪伴 TTS：{render_enabled(config.proactive_tts_enabled)}",
    ]

    # Section 4: Memory settings
    memory_lines = [
        f"记忆上下文：{render_enabled(config.memory_context_enabled)}",
        f"记忆建议：{render_enabled(config.memory_suggestions_enabled)}",
        f"记忆管理：{render_enabled(config.memory_management_enabled)}",
        f"记忆文件：{config.memory_store_path}",
    ]
    if not config.memory_context_enabled:
        memory_lines.append("")
        memory_lines.append("记忆默认关闭。开启后，小云只会保存你确认过的记忆。")

    # Section 5: Proactive settings
    proactive_lines = [
        f"主动陪伴：{render_enabled(config.proactive_enabled)}",
        f"空闲触发秒数：{config.proactive_idle_seconds}",
        f"冷却时间秒数：{config.proactive_cooldown_seconds}",
        f"单次会话最大次数：{config.proactive_max_per_session}",
        f"勿扰时间：{render_enabled(config.proactive_quiet_hours_enabled)}",
        f"勿扰开始：{config.proactive_quiet_start_hour}:00",
        f"勿扰结束：{config.proactive_quiet_end_hour}:00",
        f"拒绝后暂停秒数：{config.proactive_feedback_pause_seconds}",
    ]
    if config.proactive_enabled:
        proactive_lines.append("")
        proactive_lines.append("小云会在你空闲一段时间后主动出现。")
        proactive_lines.append("冷却时间用于防止小云频繁打扰。")
        proactive_lines.append("勿扰时间开启后，小云会在指定时间段保持安静。")
        proactive_lines.append("你可以说「别打扰」「安静一会儿」让小云暂停。")

    # Section 6: Configuration example
    example_lines = (
        "以下是配置示例（只读，不写入 .env）：",
        "",
        _CONFIG_EXAMPLE,
    )

    return SettingsView(
        sections=(
            SettingsSection(title="基础信息", lines=tuple(basic_lines)),
            SettingsSection(title="对话设置", lines=tuple(chat_lines)),
            SettingsSection(title="语音设置", lines=tuple(voice_lines)),
            SettingsSection(title="记忆设置", lines=tuple(memory_lines)),
            SettingsSection(title="主动陪伴设置", lines=tuple(proactive_lines)),
            SettingsSection(title="配置示例", lines=example_lines),
        )
    )


def render_settings_view_text(view: SettingsView) -> str:
    """Render a SettingsView to a plain-text string for display.

    Args:
        view: The settings view to render.

    Returns:
        A newline-separated string suitable for a QLabel or QTextEdit.
    """
    parts: list[str] = []
    for section in view.sections:
        parts.append(f"【{section.title}】")
        parts.extend(section.lines)
        parts.append("")  # blank line after section
    # Remove trailing blank
    while parts and parts[-1] == "":
        parts.pop()
    return "\n".join(parts)
