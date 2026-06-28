"""Prompt registry for dialogue prompts."""

from dataclasses import dataclass

DEFAULT_SYSTEM_PROMPT = (
    "You are a warm, concise desktop AI companion. "
    "Respond naturally and helpfully in the user's language."
)


@dataclass(frozen=True)
class PromptMessage:
    """Provider-neutral prompt message."""

    role: str
    content: str


class PromptRegistry:
    """Central registry for prompt text and chat message assembly."""

    def __init__(self, default_system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> None:
        self.default_system_prompt = default_system_prompt

    def build_chat_messages(self, user_text: str) -> list[PromptMessage]:
        """Build provider-neutral chat messages for a user utterance."""
        return [
            PromptMessage(role="system", content=self.default_system_prompt),
            PromptMessage(role="user", content=user_text.strip()),
        ]
