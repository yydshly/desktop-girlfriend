"""Tests for EventBus."""

import threading

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


def test_subscribe_during_publish_does_not_receive_current_event() -> None:
    """Test handlers added during publish only receive future events."""
    bus = EventBus()
    received: list[str] = []

    def late_handler(_: BaseEvent) -> None:
        received.append("late")

    def first_handler(_: BaseEvent) -> None:
        received.append("first")
        bus.subscribe("test.event", late_handler)

    bus.subscribe("test.event", first_handler)

    first_event = BaseEvent(event_type="test.event", request_id="req1", source="test")
    bus.publish(first_event)

    assert received == ["first"]

    second_event = BaseEvent(event_type="test.event", request_id="req2", source="test")
    bus.publish(second_event)

    assert received == ["first", "first", "late"]


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


def test_concurrent_subscribe_unsubscribe_and_publish_does_not_raise() -> None:
    """Test EventBus tolerates concurrent subscription changes and publishing."""
    bus = EventBus()
    errors: list[Exception] = []
    received: list[BaseEvent] = []
    start = threading.Event()

    def stable_handler(event: BaseEvent) -> None:
        received.append(event)

    def temporary_handler(_: BaseEvent) -> None:
        return

    def mutate_subscriptions() -> None:
        start.wait()
        try:
            for _ in range(200):
                bus.subscribe("test.event", temporary_handler)
                bus.unsubscribe("test.event", temporary_handler)
        except Exception as exc:
            errors.append(exc)

    def publish_events() -> None:
        start.wait()
        try:
            for i in range(200):
                bus.publish(
                    BaseEvent(
                        event_type="test.event",
                        request_id=f"req-{i}",
                        source="test",
                    )
                )
        except Exception as exc:
            errors.append(exc)

    bus.subscribe("test.event", stable_handler)
    threads = [
        threading.Thread(target=mutate_subscriptions),
        threading.Thread(target=publish_events),
    ]
    for thread in threads:
        thread.start()
    start.set()
    for thread in threads:
        thread.join(timeout=2)

    assert errors == []
    assert len(received) > 0
