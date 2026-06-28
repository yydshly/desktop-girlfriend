"""State controller - integrates EventBus with StateMachine."""

import uuid

from app.contracts.events import (
    STATE_CHANGE_REQUESTED,
    STATE_CHANGED,
    SYSTEM_ERROR,
    BaseEvent,
)
from app.contracts.payloads import StateChangedPayload
from app.core.errors import InvalidStateError
from app.core.event_bus import EventBus
from app.core.state_machine import StateMachine


class StateController:
    """Integrates EventBus with StateMachine for state-driven events."""

    def __init__(self, event_bus: EventBus, state_machine: StateMachine) -> None:
        self._event_bus = event_bus
        self._state_machine = state_machine

    def start(self) -> None:
        """Start listening for state change requests."""
        self._event_bus.subscribe(STATE_CHANGE_REQUESTED, self._on_state_change_requested)

    def stop(self) -> None:
        """Stop listening for state change requests."""
        self._event_bus.unsubscribe(STATE_CHANGE_REQUESTED, self._on_state_change_requested)

    def _on_state_change_requested(self, event: BaseEvent) -> None:
        """Handle state change request event.

        Args:
            event: The state.change_requested event containing target_state in payload.
        """
        request_id = event.request_id or str(uuid.uuid4())
        target_state = event.payload.get("target_state")

        if target_state is None:
            self._publish_error(request_id, "Missing target_state in payload")
            return

        try:
            previous_state, current_state = self._state_machine.transition_to(
                target_state, request_id
            )
        except InvalidStateError as e:
            self._publish_error(request_id, str(e))
            return

        # Publish state.changed event
        state_changed_event = BaseEvent(
            event_type=STATE_CHANGED,
            request_id=request_id,
            source="state_controller",
            payload=StateChangedPayload(
                previous_state=previous_state,
                current_state=current_state,
            ).__dict__,
        )
        self._event_bus.publish(state_changed_event)

    def _publish_error(self, request_id: str, message: str) -> None:
        """Publish a system.error event.

        Args:
            request_id: The request ID for tracking.
            message: The error message.
        """
        error_event = BaseEvent(
            event_type=SYSTEM_ERROR,
            request_id=request_id,
            source="state_controller",
            payload={"message": message},
        )
        self._event_bus.publish(error_event)
