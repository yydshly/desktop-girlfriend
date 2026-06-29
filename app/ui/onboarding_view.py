"""Onboarding view types and builders (Phase 3-B).

Provides pure functions for building and rendering the first-run onboarding card.
No Qt, no file I/O, no LLM/TTS/ASR.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OnboardingAction:
    """A single action button in the onboarding card."""

    text: str
    intent: str


@dataclass(frozen=True)
class OnboardingView:
    """The onboarding card content."""

    title: str
    subtitle: str
    bullets: tuple[str, ...]
    primary_action: OnboardingAction
    secondary_action: OnboardingAction


def build_onboarding_view(
    companion_name: str = "小云",
) -> OnboardingView:
    """Build the onboarding view content.

    Args:
        companion_name: The name of the companion assistant.

    Returns:
        An OnboardingView describing the onboarding card.
    """
    return OnboardingView(
        title=f"你好，我是{companion_name}",
        subtitle="我会在桌面上陪你聊天、倾听，也可以在你空闲时轻轻出现。",
        bullets=(
            "直接在输入框里和我说话。",
            "点击「语音输入」可以用语音和我交流。",
            "点击「设置」可以查看对话、语音、记忆和主动陪伴配置。",
            "点击「状态」可以查看当前能力是否启用。",
            "我可以置顶、小窗，也可以隐藏到托盘里。",
            "我只会保存你确认或手动添加的记忆，不会自动保存完整聊天。",
        ),
        primary_action=OnboardingAction(text="知道了", intent="dismiss"),
        secondary_action=OnboardingAction(text="打开设置", intent="open_settings"),
    )


def render_onboarding_text(view: OnboardingView) -> str:
    """Render an OnboardingView to a plain-text string.

    Args:
        view: The onboarding view to render.

    Returns:
        A newline-separated string suitable for display.
    """
    bullet_text = "\n".join(f"• {item}" for item in view.bullets)
    return f"{view.title}\n{view.subtitle}\n\n{bullet_text}"
