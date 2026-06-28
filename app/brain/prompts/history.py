"""In-memory current session dialogue history."""

from __future__ import annotations

from dataclasses import dataclass as dc
from typing import Literal

DialogueRole = Literal["user", "assistant"]


@dc(frozen=True)
class DialogueTurn:
    """A single dialogue turn in the current session."""

    role: DialogueRole
    text: str


class CurrentSessionHistory:
    """In-memory storage for the current session dialogue history.

    Does not persist to disk. Does not network. Used only to provide
    recent context to the chat provider.
    """

    def __init__(self, max_turns: int = 6) -> None:
        """Initialize CurrentSessionHistory.

        Args:
            max_turns: Maximum number of dialogue turns to retain.
                       Excess turns are discarded, keeping only the most recent.
        """
        self._turns: list[DialogueTurn] = []
        self._max_turns = max_turns

    def append_user_text(self, text: str) -> None:
        """Append a user turn to the history.

        Args:
            text: The user's input text.

        Raises:
            ValueError: If text is not a non-empty string.
        """
        if type(text) is not str or not text.strip():
            raise ValueError("append_user_text requires a non-empty str")
        self._turns.append(DialogueTurn(role="user", text=text.strip()))
        self._trim()

    def append_assistant_text(self, text: str) -> None:
        """Append an assistant turn to the history.

        Args:
            text: The assistant's response text.

        Raises:
            ValueError: If text is not a non-empty string.
        """
        if type(text) is not str or not text.strip():
            raise ValueError("append_assistant_text requires a non-empty str")
        self._turns.append(DialogueTurn(role="assistant", text=text.strip()))
        self._trim()

    def recent_turns(self) -> list[DialogueTurn]:
        """Return a copy of recent dialogue turns.

        Returns:
            A list of the most recent dialogue turns (oldest first).
        """
        return list(self._turns)

    def clear(self) -> None:
        """Clear all dialogue turns from the session history."""
        self._turns.clear()

    def _trim(self) -> None:
        """Trim turns to keep only the most recent _max_turns."""
        if len(self._turns) > self._max_turns:
            self._turns = self._turns[-self._max_turns :]
