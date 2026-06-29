"""Settings controls view (Phase 3-E).

Pure functions for structured settings controls — no Qt, no file I/O,
no LLM/TTS/ASR, no direct runtime calls.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SettingsControlItem:
    """A single settings control item with label, value, and optional description."""

    label: str
    value: str
    description: str = ""


@dataclass(frozen=True)
class SettingsControlSection:
    """A settings section with a title and items."""

    title: str
    items: tuple[SettingsControlItem, ...]


@dataclass(frozen=True)
class SettingsControlsView:
    """A complete structured settings view."""

    sections: tuple[SettingsControlSection, ...]
    env_example: str
    restart_hint: str
    safety_hint: str


def render_bool_status(enabled: bool) -> str:
    """Return a human-readable enabled/disabled status string.

    Args:
        enabled: Whether the feature is enabled.

    Returns:
        "已开启" or "未开启".
    """
    return "已开启" if enabled else "未开启"


def render_secret_status(value: str | None) -> str:
    """Return whether a secret value is configured without revealing it.

    Args:
        value: The secret value, or None if not set.

    Returns:
        "已配置" or "未配置".
    """
    return "已配置" if value else "未配置"


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


def build_env_example() -> str:
    """Build a safe configuration example without real API keys.

    Returns:
        A safe configuration template string.
    """
    return """
# Memory
MEMORY_CONTEXT_ENABLED=true
MEMORY_SUGGESTIONS_ENABLED=true
MEMORY_MANAGEMENT_ENABLED=true
MEMORY_STORE_PATH=.tmp/memory.json

# Proactive
PROACTIVE_ENABLED=true
PROACTIVE_IDLE_SECONDS=300
PROACTIVE_COOLDOWN_SECONDS=1800
PROACTIVE_MAX_PER_SESSION=3
PROACTIVE_TTS_ENABLED=false
PROACTIVE_QUIET_HOURS_ENABLED=true
PROACTIVE_QUIET_START_HOUR=23
PROACTIVE_QUIET_END_HOUR=8

# Voice
TTS_ENABLED=false
ASR_ENABLED=false
""".strip()


def build_safety_hint() -> str:
    """Build the safety hint text.

    Returns:
        Safety hint about API key privacy.
    """
    return "API Key 只显示是否配置，不显示真实内容。"


def build_restart_hint() -> str:
    """Build the restart hint text.

    Returns:
        Restart hint for configuration changes.
    """
    return "部分配置需要重启应用后生效。"


def build_readonly_hint() -> str:
    """Build the readonly mode hint text.

    Returns:
        Hint that current version does not directly modify .env.
    """
    return "当前版本不会直接修改 .env。你可以复制配置示例后手动粘贴到 .env。"


def build_settings_controls_view(
    config,  # AppConfig — typed loosely to avoid circular imports
) -> SettingsControlsView:
    """Build a structured settings controls view from configuration.

    Args:
        config: The application configuration (AppConfig instance).

    Returns:
        A SettingsControlsView describing all settings sections and items.
    """
    from app.core.version import get_app_version

    version_info = get_app_version()
    version_str = version_info.version
    release_str = version_info.release_stage

    # Section 1: Basic info
    basic_items: tuple[SettingsControlItem, ...] = (
        SettingsControlItem("应用", "Desktop Girlfriend"),
        SettingsControlItem("版本", version_str),
        SettingsControlItem("发布阶段", release_str),
        *((SettingsControlItem("环境", config.app_env),) if config.app_env != "dev" else ()),
    )

    # Section 2: Desktop behavior
    behavior_items = (
        SettingsControlItem(
            "关闭窗口时",
            "隐藏到托盘",
            "如需退出，请从托盘菜单选择「退出」",
        ),
        SettingsControlItem(
            "首次打开时",
            "显示引导卡",
            "",
        ),
    )

    # Section 3: Chat settings
    chat_api_key_status = render_secret_status(config.minimax_api_key)
    chat_items: tuple[SettingsControlItem, ...] = (
        SettingsControlItem("对话 provider", render_provider_mode(config.chat_provider_mode)),
        SettingsControlItem("MiniMax model", config.minimax_model),
        SettingsControlItem("MiniMax API Key", chat_api_key_status),
    )
    if config.chat_provider_mode == "fake":
        chat_items = chat_items + (
            SettingsControlItem(
                "当前模式",
                "fake 测试模式",
                "不会调用真实 LLM",
            ),
        )

    # Section 4: Voice settings
    voice_items = (
        SettingsControlItem("TTS provider", render_provider_mode(config.tts_provider_mode)),
        SettingsControlItem("ASR provider", render_provider_mode(config.asr_provider_mode)),
        SettingsControlItem("Mimo API Key", render_secret_status(config.mimo_api_key)),
        SettingsControlItem("主动陪伴 TTS", render_bool_status(config.proactive_tts_enabled)),
    )

    # Section 5: Memory settings
    memory_items = (
        SettingsControlItem(
            "记忆上下文",
            render_bool_status(config.memory_context_enabled),
            "提供对话上下文给 LLM",
        ),
        SettingsControlItem(
            "记忆建议",
            render_bool_status(config.memory_suggestions_enabled),
            "自动发现值得记住的信息",
        ),
        SettingsControlItem(
            "记忆管理",
            render_bool_status(config.memory_management_enabled),
            "允许查看和删除记忆",
        ),
        SettingsControlItem("记忆文件", config.memory_store_path),
    )

    # Section 6: Proactive settings
    proactive_items: tuple[SettingsControlItem, ...] = (
        SettingsControlItem(
            "主动陪伴",
            render_bool_status(config.proactive_enabled),
            "空闲后主动出现",
        ),
        SettingsControlItem(
            "空闲触发",
            f"{config.proactive_idle_seconds} 秒",
            "多久没有互动后可以主动出现",
        ),
        SettingsControlItem(
            "冷却时间",
            f"{config.proactive_cooldown_seconds} 秒",
            "两次主动陪伴之间的最小间隔",
        ),
        SettingsControlItem(
            "最多次数",
            f"{config.proactive_max_per_session} 次",
            "单次会话里最多主动出现几次",
        ),
        SettingsControlItem(
            "勿扰时间",
            render_bool_status(config.proactive_quiet_hours_enabled),
            "指定时间段保持安静",
        ),
        *((SettingsControlItem(
            "勿扰时段",
            f"{config.proactive_quiet_start_hour}:00 – {config.proactive_quiet_end_hour}:00",
        ),) if config.proactive_quiet_hours_enabled else ()),
        SettingsControlItem(
            "用户控制",
            "「别打扰」暂停",
            "可通过语言指令暂停主动陪伴",
        ),
        SettingsControlItem(
            "托盘行为",
            "不强制弹窗",
            "隐藏到托盘时不会强行弹出",
        ),
    )

    return SettingsControlsView(
        sections=(
            SettingsControlSection(title="基础信息", items=basic_items),
            SettingsControlSection(title="桌面行为", items=behavior_items),
            SettingsControlSection(title="对话设置", items=chat_items),
            SettingsControlSection(title="语音设置", items=voice_items),
            SettingsControlSection(title="记忆设置", items=memory_items),
            SettingsControlSection(title="主动陪伴设置", items=proactive_items),
        ),
        env_example=build_env_example(),
        restart_hint=build_restart_hint(),
        safety_hint=build_safety_hint(),
    )


def render_settings_controls_as_text(view: SettingsControlsView) -> str:
    """Render a SettingsControlsView to a plain-text string.

    Args:
        view: The structured settings controls view.

    Returns:
        A newline-separated string suitable for display.
    """
    parts: list[str] = []
    for section in view.sections:
        parts.append(f"【{section.title}】")
        for item in section.items:
            if item.description:
                parts.append(f"  {item.label}：{item.value} — {item.description}")
            else:
                parts.append(f"  {item.label}：{item.value}")
        parts.append("")
    parts.append(f"说明：{view.safety_hint}")
    parts.append(f"说明：{view.restart_hint}")
    parts.append("")
    parts.append("【配置示例】")
    parts.append(view.env_example)
    return "\n".join(parts)
