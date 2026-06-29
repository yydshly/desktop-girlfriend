"""Memory UX copy and builders (Phase 3-C).

Provides user-facing copy for memory suggestion cards, memory management panel,
and settings memory explanations. No Qt, no file I/O, no LLM/TTS/ASR.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemorySuggestionCopy:
    """Copy for the memory suggestion card."""

    title: str
    body: str
    privacy_hint: str
    remember_button: str
    reject_button: str


@dataclass(frozen=True)
class MemoryPanelCopy:
    """Copy for the memory management panel."""

    title: str
    empty_title: str
    empty_body: str
    privacy_body: str
    delete_hint: str


@dataclass(frozen=True)
class MemorySettingsCopy:
    """Copy for the settings panel memory section."""

    context_label: str
    suggestions_label: str
    management_label: str
    privacy_hint: str


def build_memory_suggestion_copy() -> MemorySuggestionCopy:
    """Build copy for the memory suggestion card (Phase 3-C)."""
    return MemorySuggestionCopy(
        title="要我记住这件事吗？",
        body="这可能会帮助我以后更懂你。只有你点「记住」后，我才会保存。",
        privacy_hint="小云不会自动保存完整聊天，只会保存你确认过的记忆。",
        remember_button="记住",
        reject_button="不记",
    )


def build_memory_panel_copy() -> MemoryPanelCopy:
    """Build copy for the memory management panel (Phase 3-C)."""
    return MemoryPanelCopy(
        title="小云记住的事",
        empty_title="还没有保存的记忆",
        empty_body="当你确认「记住」或手动添加后，相关记忆会出现在这里。",
        privacy_body="记忆保存在本地。小云不会保存完整原始对话，也不会在你未确认时自动保存。你可以手动添加记忆。",
        delete_hint="删除后，这条记忆不会再用于后续对话。",
    )


def build_memory_settings_copy() -> MemorySettingsCopy:
    """Build copy for the settings panel memory section (Phase 3-C)."""
    return MemorySettingsCopy(
        context_label="开启后，小云会在回复时参考你确认保存过的记忆。",
        suggestions_label="开启后，小云会在合适时建议保存一条记忆。",
        management_label="开启后，你可以查看、手动添加和删除已保存的记忆。",
        privacy_hint="隐私说明：小云不会自动保存完整聊天，只会保存你确认过或手动添加的记忆。",
    )
