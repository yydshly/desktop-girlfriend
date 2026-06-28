"""Tests for Prompt Registry."""

from app.brain.prompts.registry import DEFAULT_SYSTEM_PROMPT, PromptMessage, PromptRegistry


def test_default_prompt_registry_has_system_prompt() -> None:
    registry = PromptRegistry()

    assert registry.default_system_prompt
    assert "小云" in registry.default_system_prompt
    assert "桌面" in registry.default_system_prompt
    assert "AI" in registry.default_system_prompt


def test_system_prompt_contains_persona_keywords() -> None:
    """Test that the system prompt contains key persona and safety keywords."""
    prompt = DEFAULT_SYSTEM_PROMPT
    assert "不要频繁说" in prompt
    assert "不是假装真人" in prompt
    assert "共情" in prompt or "陪伴" in prompt


def test_system_prompt_avoids_frequent_ai_claims() -> None:
    """Test that the system prompt limits frequent AI self-references."""
    assert "不要频繁说" in DEFAULT_SYSTEM_PROMPT


def test_system_prompt_contains_safety_boundaries() -> None:
    """Test that the system prompt contains safety boundaries."""
    prompt = DEFAULT_SYSTEM_PROMPT
    assert "不替代" in prompt
    assert "高风险" in prompt or "安全" in prompt


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


def test_build_chat_messages_returns_two_messages() -> None:
    registry = PromptRegistry(default_system_prompt="system")

    messages = registry.build_chat_messages("Hi")

    assert len(messages) == 2
    assert messages[0].role == "system"
    assert messages[1].role == "user"


def test_system_prompt_does_not_leak_secrets() -> None:
    """Test that the system prompt does not contain API key or auth keywords."""
    prompt = DEFAULT_SYSTEM_PROMPT.lower()
    assert "api" not in prompt or "key" not in prompt
    assert "bearer" not in prompt
    assert "authorization" not in prompt
