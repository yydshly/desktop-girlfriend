"""Integration tests for StateController - EventBus + StateMachine."""


from app.contracts.events import (
    STATE_CHANGE_REQUESTED,
    STATE_CHANGED,
    BaseEvent,
)
from app.contracts.states import AppState
from app.core.event_bus import EventBus
from app.core.state_controller import StateController
from app.core.state_machine import StateMachine


def test_state_change_requested_triggers_state_changed() -> None:
    """Test that publishing state.change_requested triggers state.changed."""
    event_bus = EventBus()
    state_machine = StateMachine()
    controller = StateController(event_bus, state_machine)

    received_events: list[BaseEvent] = []

    def capture_state_changed(event: BaseEvent) -> None:
        received_events.append(event)

    event_bus.subscribe(STATE_CHANGED, capture_state_changed)
    controller.start()

    # Publish state change request
    request_event = BaseEvent(
        event_type=STATE_CHANGE_REQUESTED,
        request_id="req1",
        source="test",
        payload={"target_state": AppState.LISTENING},
    )
    event_bus.publish(request_event)

    controller.stop()

    # Verify state.changed was published
    assert len(received_events) == 1
    event = received_events[0]
    assert event.event_type == STATE_CHANGED
    assert event.source == "state_controller"


def test_state_changed_payload_contains_previous_and_current() -> None:
    """Test state.changed payload contains previous_state and current_state."""
    event_bus = EventBus()
    state_machine = StateMachine()
    controller = StateController(event_bus, state_machine)

    received_events: list[BaseEvent] = []

    def capture_state_changed(event: BaseEvent) -> None:
        received_events.append(event)

    event_bus.subscribe(STATE_CHANGED, capture_state_changed)
    controller.start()

    # Request state transition to THINKING
    request_event = BaseEvent(
        event_type=STATE_CHANGE_REQUESTED,
        request_id="req2",
        source="test",
        payload={"target_state": AppState.THINKING},
    )
    event_bus.publish(request_event)

    controller.stop()

    # Verify payload contains previous and current state
    assert len(received_events) == 1
    payload = received_events[0].payload
    assert payload["previous_state"] == AppState.IDLE.value
    assert payload["current_state"] == AppState.THINKING.value


def test_state_change_requested_with_string_target() -> None:
    """Test state.change_requested accepts string target_state."""
    event_bus = EventBus()
    state_machine = StateMachine()
    controller = StateController(event_bus, state_machine)

    received_events: list[BaseEvent] = []

    def capture_state_changed(event: BaseEvent) -> None:
        received_events.append(event)

    event_bus.subscribe(STATE_CHANGED, capture_state_changed)
    controller.start()

    # Request state transition using string
    request_event = BaseEvent(
        event_type=STATE_CHANGE_REQUESTED,
        request_id="req3",
        source="test",
        payload={"target_state": "speaking"},
    )
    event_bus.publish(request_event)

    controller.stop()

    assert len(received_events) == 1
    payload = received_events[0].payload
    assert payload["previous_state"] == AppState.IDLE.value
    assert payload["current_state"] == AppState.SPEAKING.value


def test_multiple_state_changes() -> None:
    """Test multiple sequential state changes."""
    event_bus = EventBus()
    state_machine = StateMachine()
    controller = StateController(event_bus, state_machine)

    received_events: list[BaseEvent] = []

    def capture_state_changed(event: BaseEvent) -> None:
        received_events.append(event)

    event_bus.subscribe(STATE_CHANGED, capture_state_changed)
    controller.start()

    # First transition
    event_bus.publish(BaseEvent(
        event_type=STATE_CHANGE_REQUESTED,
        request_id="req4",
        source="test",
        payload={"target_state": AppState.LISTENING},
    ))

    # Second transition
    event_bus.publish(BaseEvent(
        event_type=STATE_CHANGE_REQUESTED,
        request_id="req5",
        source="test",
        payload={"target_state": AppState.THINKING},
    ))

    controller.stop()

    assert len(received_events) == 2
    assert received_events[0].payload["current_state"] == AppState.LISTENING.value
    assert received_events[1].payload["previous_state"] == AppState.LISTENING.value
    assert received_events[1].payload["current_state"] == AppState.THINKING.value


def test_state_machine_actual_state_after_transition() -> None:
    """Test StateMachine actual state is updated after controller processes request."""
    event_bus = EventBus()
    state_machine = StateMachine()
    controller = StateController(event_bus, state_machine)

    received_events: list[BaseEvent] = []

    def capture_state_changed(event: BaseEvent) -> None:
        received_events.append(event)

    event_bus.subscribe(STATE_CHANGED, capture_state_changed)
    controller.start()

    # Request state transition
    event_bus.publish(BaseEvent(
        event_type=STATE_CHANGE_REQUESTED,
        request_id="req6",
        source="test",
        payload={"target_state": AppState.ERROR},
    ))

    controller.stop()

    # Verify StateMachine actual state is updated
    assert state_machine.get_state() == AppState.ERROR
