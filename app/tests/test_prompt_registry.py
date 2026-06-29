"""Tests for Prompt Registry."""

from app.brain.persona import DEFAULT_XIAOYUN_PERSONA, PersonaProfile, PersonaPromptBuilder
from app.brain.prompts.history import DialogueTurn
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


def test_build_chat_messages_without_history_returns_two_messages() -> None:
    """Test build_chat_messages without history keeps old two-message structure."""
    registry = PromptRegistry(default_system_prompt="system")
    messages = registry.build_chat_messages("Hi")
    assert len(messages) == 2
    assert messages[0].role == "system"
    assert messages[1].role == "user"
    assert messages[1].content == "Hi"


def test_build_chat_messages_with_history_includes_all_turns() -> None:
    """Test build_chat_messages with history returns system + history + current user."""
    registry = PromptRegistry(default_system_prompt="system")
    history = [
        DialogueTurn(role="user", text="你好"),
        DialogueTurn(role="assistant", text="我在"),
    ]
    messages = registry.build_chat_messages("刚才我说什么了？", history_turns=history)
    roles = [m.role for m in messages]
    assert roles == ["system", "user", "assistant", "user"]


def test_build_chat_messages_current_user_is_last() -> None:
    """Test that current user text is always the last message."""
    registry = PromptRegistry(default_system_prompt="system")
    history = [
        DialogueTurn(role="user", text="你好"),
        DialogueTurn(role="assistant", text="我在"),
    ]
    messages = registry.build_chat_messages("现在几点了？", history_turns=history)
    assert messages[-1].role == "user"
    assert messages[-1].content == "现在几点了？"


def test_build_chat_messages_user_text_is_stripped() -> None:
    """Test that current user text is stripped."""
    registry = PromptRegistry(default_system_prompt="system")
    messages = registry.build_chat_messages("  Hello  ")
    assert messages[-1].content == "Hello"


def test_build_chat_messages_empty_history_ignored() -> None:
    """Test that empty history produces only system + current user."""
    registry = PromptRegistry(default_system_prompt="system")
    messages = registry.build_chat_messages("Hi", history_turns=[])
    assert len(messages) == 2
    assert messages[0].role == "system"
    assert messages[-1].role == "user"


def test_build_chat_messages_history_with_empty_text_ignored() -> None:
    """Test that history turns with empty text are ignored."""
    registry = PromptRegistry(default_system_prompt="system")
    history = [
        DialogueTurn(role="user", text=""),
        DialogueTurn(role="assistant", text="valid"),
    ]
    messages = registry.build_chat_messages("Hi", history_turns=history)
    # Empty text turn should be skipped
    roles = [m.role for m in messages]
    assert "assistant" in roles
    assert messages[-1].role == "user"


def test_build_chat_messages_history_roles_mapped_correctly() -> None:
    """Test that history roles are mapped to PromptMessage roles correctly."""
    registry = PromptRegistry(default_system_prompt="system")
    history = [
        DialogueTurn(role="user", text="user text"),
        DialogueTurn(role="assistant", text="assistant text"),
    ]
    messages = registry.build_chat_messages("current", history_turns=history)
    user_msgs = [m for m in messages if m.role == "user"]
    assistant_msgs = [m for m in messages if m.role == "assistant"]
    assert len(user_msgs) == 2  # history user + current user
    assert len(assistant_msgs) == 1  # history assistant only
    assert user_msgs[0].content == "user text"
    assert assistant_msgs[0].content == "assistant text"
    assert user_msgs[1].content == "current"


def test_build_chat_messages_none_history_defaults_to_no_history() -> None:
    """Test that history_turns=None produces only system + current user."""
    registry = PromptRegistry(default_system_prompt="system")
    messages = registry.build_chat_messages("Hi", history_turns=None)
    assert len(messages) == 2
    assert messages[0].role == "system"
    assert messages[-1].role == "user"


# Persona tests


def test_default_registry_uses_default_xiaoyun_persona() -> None:
    """Test that default PromptRegistry uses DEFAULT_XIAOYUN_PERSONA."""
    registry = PromptRegistry()
    assert "小云" in registry.default_system_prompt


def test_explicit_default_system_prompt_takes_priority() -> None:
    """Test that explicit default_system_prompt is used when provided."""
    explicit = "You are a helpful assistant."
    registry = PromptRegistry(default_system_prompt=explicit)
    assert registry.default_system_prompt == explicit


def test_persona_profile_argument_is_used() -> None:
    """Test that persona_profile argument is used to build system prompt."""
    custom = PersonaProfile(
        name="小爱",
        identity="测试AI",
        role="测试角色",
        user_address="你",
        core_traits=("安静",),
        speaking_style=("简洁",),
        emotional_support=("陪伴",),
        behavior_rules=("不说谎",),
        safety_boundaries=("安全",),
        output_rules=("短",),
    )
    registry = PromptRegistry(persona_profile=custom)
    assert "小爱" in registry.default_system_prompt
    assert "测试AI" in registry.default_system_prompt


def test_persona_prompt_builder_argument_is_used() -> None:
    """Test that persona_prompt_builder argument is used to build system prompt."""
    custom = PersonaProfile(
        name="小爱",
        identity="测试AI",
        role="测试角色",
        user_address="你",
        core_traits=("安静",),
        speaking_style=("简洁",),
        emotional_support=("陪伴",),
        behavior_rules=("不说谎",),
        safety_boundaries=("安全",),
        output_rules=("短",),
    )
    builder = PersonaPromptBuilder(custom)
    registry = PromptRegistry(persona_prompt_builder=builder)
    assert "小爱" in registry.default_system_prompt


def test_persona_builder_generates_short_replies_rule() -> None:
    """Test that DEFAULT_XIAOYUN_PERSONA builder includes short reply rule."""
    registry = PromptRegistry()  # uses DEFAULT_XIAOYUN_PERSONA
    assert "1 到 4 句话" in registry.default_system_prompt or "简短" in registry.default_system_prompt


def test_build_chat_messages_system_first_with_persona() -> None:
    """Test build_chat_messages still returns system message first with persona."""
    registry = PromptRegistry(persona_profile=DEFAULT_XIAOYUN_PERSONA)
    messages = registry.build_chat_messages("你好")
    assert messages[0].role == "system"
    assert len(messages[0].content) > 10


def test_build_chat_messages_history_order_preserved_with_persona() -> None:
    """Test history turns are in correct order with persona system prompt."""
    registry = PromptRegistry(persona_profile=DEFAULT_XIAOYUN_PERSONA)
    history = [
        DialogueTurn(role="user", text="早上好"),
        DialogueTurn(role="assistant", text="早"),
    ]
    messages = registry.build_chat_messages("今天天气如何？", history_turns=history)
    roles = [m.role for m in messages]
    assert roles == ["system", "user", "assistant", "user"]


def test_build_chat_messages_current_user_last_with_persona() -> None:
    """Test current user text is last even with persona."""
    registry = PromptRegistry(persona_profile=DEFAULT_XIAOYUN_PERSONA)
    messages = registry.build_chat_messages("现在几点了？")
    assert messages[-1].role == "user"
    assert messages[-1].content == "现在几点了？"


def test_persona_system_prompt_no_api_keys_or_secrets() -> None:
    """Test persona system prompt contains no API keys or secrets."""
    registry = PromptRegistry()  # uses DEFAULT_XIAOYUN_PERSONA
    prompt = registry.default_system_prompt.lower()
    assert "api" not in prompt or "key" not in prompt
    assert "bearer" not in prompt
    assert "authorization" not in prompt

