"""Tests for StateMachine."""

import pytest

from app.contracts.states import AppState
from app.core.errors import InvalidStateError
from app.core.state_machine import StateMachine


def test_initial_state() -> None:
    """Test initial state is IDLE."""
    sm = StateMachine()
    assert sm.get_state() == AppState.IDLE


def test_set_state() -> None:
    """Test setting state."""
    sm = StateMachine()
    sm.set_state(AppState.LISTENING)
    assert sm.get_state() == AppState.LISTENING


def test_set_state_with_string() -> None:
    """Test setting state with string value."""
    sm = StateMachine()
    sm.set_state("listening")
    assert sm.get_state() == AppState.LISTENING


def test_set_state_returns_new_state() -> None:
    """Test set_state returns the new state."""
    sm = StateMachine()
    result = sm.set_state(AppState.SPEAKING)
    assert result == AppState.SPEAKING


def test_invalid_string_raises() -> None:
    """Test invalid string state raises InvalidStateError."""
    sm = StateMachine()
    with pytest.raises(InvalidStateError):
        sm.set_state("invalid_state")


def test_set_state_with_request_id() -> None:
    """Test set_state accepts request_id parameter."""
    sm = StateMachine()
    sm.set_state(AppState.THINKING, request_id="req123")
    assert sm.get_state() == AppState.THINKING
