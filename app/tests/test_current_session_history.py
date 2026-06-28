"""Tests for CurrentSessionHistory."""

import pytest

from app.brain.prompts.history import CurrentSessionHistory


def test_initial_recent_turns_is_empty() -> None:
    history = CurrentSessionHistory()
    assert history.recent_turns() == []


def test_append_user_text_adds_turn() -> None:
    history = CurrentSessionHistory()
    history.append_user_text("Hello")
    turns = history.recent_turns()
    assert len(turns) == 1
    assert turns[0].role == "user"
    assert turns[0].text == "Hello"


def test_append_assistant_text_adds_turn() -> None:
    history = CurrentSessionHistory()
    history.append_assistant_text("Hi there")
    turns = history.recent_turns()
    assert len(turns) == 1
    assert turns[0].role == "assistant"
    assert turns[0].text == "Hi there"


def test_append_user_text_trims_whitespace() -> None:
    history = CurrentSessionHistory()
    history.append_user_text("  Hello  ")
    assert history.recent_turns()[0].text == "Hello"


def test_append_assistant_text_trims_whitespace() -> None:
    history = CurrentSessionHistory()
    history.append_assistant_text("  Hi  ")
    assert history.recent_turns()[0].text == "Hi"


def test_append_user_text_rejects_empty_string() -> None:
    history = CurrentSessionHistory()
    with pytest.raises(ValueError, match="non-empty str"):
        history.append_user_text("")


def test_append_user_text_rejects_whitespace_only() -> None:
    history = CurrentSessionHistory()
    with pytest.raises(ValueError, match="non-empty str"):
        history.append_user_text("   ")


def test_append_user_text_rejects_non_str() -> None:
    history = CurrentSessionHistory()
    with pytest.raises(ValueError):
        history.append_user_text(123)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        history.append_user_text(None)  # type: ignore[arg-type]


def test_append_assistant_text_rejects_empty_string() -> None:
    history = CurrentSessionHistory()
    with pytest.raises(ValueError, match="non-empty str"):
        history.append_assistant_text("")


def test_append_assistant_text_rejects_whitespace_only() -> None:
    history = CurrentSessionHistory()
    with pytest.raises(ValueError, match="non-empty str"):
        history.append_assistant_text("  ")


def test_append_assistant_text_rejects_non_str() -> None:
    history = CurrentSessionHistory()
    with pytest.raises(ValueError):
        history.append_assistant_text(456)  # type: ignore[arg-type]


def test_trims_to_max_turns() -> None:
    history = CurrentSessionHistory(max_turns=4)
    for i in range(8):
        history.append_user_text(f"User {i}")
        history.append_assistant_text(f"Assistant {i}")
    turns = history.recent_turns()
    assert len(turns) == 4


def test_recent_turns_returns_copy() -> None:
    history = CurrentSessionHistory()
    history.append_user_text("Hello")
    turns1 = history.recent_turns()
    turns1.clear()
    turns2 = history.recent_turns()
    assert len(turns2) == 1
    assert turns2[0].text == "Hello"


def test_clear_removes_all_turns() -> None:
    history = CurrentSessionHistory()
    history.append_user_text("Hello")
    history.append_assistant_text("Hi")
    history.clear()
    assert history.recent_turns() == []


def test_multiple_interleaved_turns() -> None:
    history = CurrentSessionHistory(max_turns=6)
    history.append_user_text("First user")
    history.append_assistant_text("First assistant")
    history.append_user_text("Second user")
    history.append_assistant_text("Second assistant")
    turns = history.recent_turns()
    assert [t.role for t in turns] == ["user", "assistant", "user", "assistant"]
    assert [t.text for t in turns] == [
        "First user",
        "First assistant",
        "Second user",
        "Second assistant",
    ]
