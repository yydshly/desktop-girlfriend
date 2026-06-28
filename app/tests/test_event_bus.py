"""Tests for EventBus."""


from app.contracts.events import BaseEvent
from app.core.event_bus import EventBus


def test_subscribe_and_publish() -> None:
    """Test basic subscribe and publish."""
    bus = EventBus()
    received: list[BaseEvent] = []

    def handler(event: BaseEvent) -> None:
        received.append(event)

    bus.subscribe("test.event", handler)
    event = BaseEvent(event_type="test.event", request_id="req1", source="test")
    bus.publish(event)

    assert len(received) == 1
    assert received[0] is event


def test_multiple_handlers() -> None:
    """Test multiple handlers for same event type."""
    bus = EventBus()
    count = 0

    def handler1(_: BaseEvent) -> None:
        nonlocal count
        count += 1

    def handler2(_: BaseEvent) -> None:
        nonlocal count
        count += 2

    bus.subscribe("test.event", handler1)
    bus.subscribe("test.event", handler2)
    bus.publish(BaseEvent(event_type="test.event", request_id="req1", source="test"))

    assert count == 3


def test_duplicate_subscribe_is_ignored() -> None:
    """Test subscribing the same handler twice does not duplicate delivery."""
    bus = EventBus()
    received: list[BaseEvent] = []

    def handler(event: BaseEvent) -> None:
        received.append(event)

    bus.subscribe("test.event", handler)
    bus.subscribe("test.event", handler)
    event = BaseEvent(event_type="test.event", request_id="req1", source="test")
    bus.publish(event)

    assert received == [event]


def test_unsubscribe() -> None:
    """Test unsubscribe removes handler."""
    bus = EventBus()
    received: list[BaseEvent] = []

    def handler(event: BaseEvent) -> None:
        received.append(event)

    bus.subscribe("test.event", handler)
    bus.unsubscribe("test.event", handler)
    bus.publish(BaseEvent(event_type="test.event", request_id="req1", source="test"))

    assert len(received) == 0


def test_clear() -> None:
    """Test clear removes all handlers."""
    bus = EventBus()
    received: list[BaseEvent] = []

    def handler(event: BaseEvent) -> None:
        received.append(event)

    bus.subscribe("test.event", handler)
    bus.clear()
    bus.publish(BaseEvent(event_type="test.event", request_id="req1", source="test"))

    assert len(received) == 0


def test_publish_no_handlers() -> None:
    """Test publishing to event with no handlers does not raise."""
    bus = EventBus()
    event = BaseEvent(event_type="no.handler", request_id="req1", source="test")
    bus.publish(event)  # Should not raise


def test_handler_exception_does_not_stop_later_handlers() -> None:
    """Test a failing handler is isolated from later handlers."""
    bus = EventBus()
    received: list[BaseEvent] = []

    def failing_handler(_: BaseEvent) -> None:
        raise RuntimeError("handler failed")

    def later_handler(event: BaseEvent) -> None:
        received.append(event)

    bus.subscribe("test.event", failing_handler)
    bus.subscribe("test.event", later_handler)
    event = BaseEvent(event_type="test.event", request_id="req1", source="test")

    bus.publish(event)

    assert received == [event]
