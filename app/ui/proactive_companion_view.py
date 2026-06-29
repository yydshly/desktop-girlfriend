"""Proactive companion UX view definitions (Phase 2-G)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProactiveCompanionView:
    """Immutable view model for proactive companion UI text."""

    title: str
    subtitle: str
    message_prefix: str
    quiet_hint: str
    cooldown_hint: str


def build_proactive_companion_view(
    enabled: bool,
    quiet_hours_enabled: bool,
    cooldown_seconds: int,
) -> ProactiveCompanionView:
    """Build proactive companion view with localized strings.

    Args:
        enabled: Whether proactive companion is enabled.
        quiet_hours_enabled: Whether quiet hours are enabled.
        cooldown_seconds: Cooldown time between proactive appearances.

    Returns:
        A ProactiveCompanionView instance with proactive UI strings.
    """
    return ProactiveCompanionView(
        title="主动陪伴",
        subtitle="小云会在你空闲时轻轻出现。" if enabled else "主动陪伴当前未启用。",
        message_prefix="小云主动来陪你：",
        quiet_hint="勿扰时间已启用。" if quiet_hours_enabled else "勿扰时间未启用。",
        cooldown_hint=f"两次主动陪伴至少间隔 {cooldown_seconds} 秒。",
    )


def render_proactive_message_prefix() -> str:
    """Return the chat prefix for proactive messages.

    Returns:
        The prefix shown before proactive message text in chat.
    """
    return "小云主动来陪你："


def render_proactive_status_text() -> str:
    """Return the natural status text when proactive companion appears.

    Returns:
        A friendly status message shown when proactive appears.
    """
    return "我看到你安静了一会儿，就来陪你一下。"
