"""Chat message data structures."""

from dataclasses import dataclass
from typing import Literal

ChatRole = Literal["user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    """A single chat message."""

    role: ChatRole
    text: str
