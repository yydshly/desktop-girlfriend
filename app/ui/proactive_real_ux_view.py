"""Proactive Real UX copy (Phase 3-D).

Pure functions for proactive companion UX copy — no Qt, no file I/O,
no LLM/TTS/ASR, no direct Proactive runtime calls.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProactiveRealUxCopy:
    """All copy strings for the proactive companion real UX experience."""

    title: str
    enabled_body: str
    disabled_body: str
    idle_explanation: str
    cooldown_explanation: str
    max_per_session_explanation: str
    quiet_hours_explanation: str
    user_control_hint: str
    tray_hint: str


def build_proactive_real_ux_copy() -> ProactiveRealUxCopy:
    """Build the proactive real UX copy strings.

    Returns:
        A ProactiveRealUxCopy with all copy text.
    """
    return ProactiveRealUxCopy(
        title="主动陪伴",
        enabled_body="开启后，小云会在你空闲一段时间后轻轻出现。",
        disabled_body="主动陪伴当前未启用，小云只会在你主动说话时回应。",
        idle_explanation="空闲时间：你多久没有互动后，小云可以主动出现。",
        cooldown_explanation="冷却时间：两次主动陪伴之间至少间隔多久，避免频繁打扰。",
        max_per_session_explanation="最多次数：单次会话里小云最多主动出现几次。",
        quiet_hours_explanation="勿扰时间：开启后，小云会在指定时间段保持安静。",
        user_control_hint="你可以说「别打扰」「安静一会儿」「先别说」，让小云暂停主动陪伴。",
        tray_hint="隐藏到托盘时，小云不会强行弹出窗口打扰你。",
    )


def render_proactive_enabled_status(enabled: bool) -> str:
    """Return a human-readable proactive enabled status string.

    Args:
        enabled: Whether proactive companion is enabled.

    Returns:
        "主动陪伴已开启" or "主动陪伴未开启".
    """
    return "主动陪伴已开启" if enabled else "主动陪伴未开启"


def render_proactive_user_control_hint() -> str:
    """Return the user control hint string.

    Returns:
        The hint text for how to pause proactive companion.
    """
    return "你可以说「别打扰」让小云安静一会儿。"


def render_proactive_tray_hint() -> str:
    """Return the tray behavior hint string.

    Returns:
        The hint text for tray behavior.
    """
    return "隐藏到托盘时，小云不会强行弹出窗口。"


def render_proactive_control_status() -> str:
    """Return a compact proactive control status line for the status panel.

    Returns:
        A one-line string describing proactive control.
    """
    return "可通过「别打扰」暂停"
