"""Tests for Prompt Registry."""

from app.brain.prompts.registry import PromptMessage, PromptRegistry


def test_default_prompt_registry_has_system_prompt() -> None:
    registry = PromptRegistry()

    assert registry.default_system_prompt
    assert "desktop" in registry.default_system_prompt.lower()


def test_build_chat_messages_includes_system_and_user_text() -> None:
    registry = PromptRegistry(default_system_prompt="You are a concise companion.")

    messages = registry.build_chat_messages("Hello")

    assert messages == [
        PromptMessage(role="system", content="You are a concise companion."),
        PromptMessage(role="user", content="Hello"),
    ]


def test_build_chat_messages_trims_user_text() -> None:
    registry = PromptRegistry(default_system_prompt="system")

    messages = registry.build_chat_messages("  Hello  ")

    assert messages[-1] == PromptMessage(role="user", content="Hello")
