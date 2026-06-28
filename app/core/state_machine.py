"""State machine implementation."""

from app.contracts.states import AppState
from app.core.errors import InvalidStateError


class StateMachine:
    """Manages application state transitions."""

    def __init__(self, initial_state: AppState = AppState.IDLE) -> None:
        self._state = initial_state

    def get_state(self) -> AppState:
        """Get the current state.

        Returns:
            The current AppState.
        """
        return self._state

    def set_state(
        self, new_state: AppState | str, request_id: str | None = None
    ) -> AppState:
        """Set a new state.

        Args:
            new_state: The new state to transition to.
            request_id: Optional request ID for tracking.

        Returns:
            The new state.

        Raises:
            InvalidStateError: If the state is not a valid AppState.
        """
        if isinstance(new_state, str):
            try:
                new_state = AppState(new_state)
            except ValueError:
                raise InvalidStateError(f"Invalid state: {new_state}")

        if not isinstance(new_state, AppState):
            raise InvalidStateError(f"Invalid state type: {type(new_state)}")

        self._state = new_state
        return self._state
