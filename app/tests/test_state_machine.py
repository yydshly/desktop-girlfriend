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


def test_transition_to_returns_previous_and_current() -> None:
    """Test transition_to returns tuple of previous and current state."""
    sm = StateMachine()
    previous, current = sm.transition_to(AppState.LISTENING)
    assert previous == AppState.IDLE
    assert current == AppState.LISTENING


def test_transition_to_updates_state() -> None:
    """Test transition_to actually updates the state."""
    sm = StateMachine()
    sm.transition_to(AppState.SPEAKING)
    assert sm.get_state() == AppState.SPEAKING


def test_transition_to_with_string() -> None:
    """Test transition_to accepts string state value."""
    sm = StateMachine()
    previous, current = sm.transition_to("thinking")
    assert previous == AppState.IDLE
    assert current == AppState.THINKING


def test_transition_to_invalid_state_raises() -> None:
    """Test transition_to with invalid state raises InvalidStateError."""
    sm = StateMachine()
    with pytest.raises(InvalidStateError):
        sm.transition_to("invalid_state")


def test_transition_to_with_request_id() -> None:
    """Test transition_to accepts request_id parameter."""
    sm = StateMachine()
    previous, current = sm.transition_to(AppState.ERROR, request_id="req456")
    assert previous == AppState.IDLE
    assert current == AppState.ERROR
