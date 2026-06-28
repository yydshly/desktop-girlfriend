"""Tests for QtEventBridge."""

from app.contracts.events import BaseEvent
from app.ui.qt_event_bridge import QtEventBridge


def test_qt_event_bridge_publishes_emitted_base_event(qapp) -> None:
    """Test that emitting a BaseEvent triggers the publish callback."""
    received: list[BaseEvent] = []

    bridge = QtEventBridge(received.append)
    event = BaseEvent(event_type="test.event", request_id="req1", source="test")

    bridge.event_ready.emit(event)
    qapp.processEvents()

    assert received == [event]


def test_qt_event_bridge_ignores_non_base_event(qapp) -> None:
    """Test that emitting a non-BaseEvent object is ignored."""
    received: list[BaseEvent] = []

    bridge = QtEventBridge(received.append)

    bridge.event_ready.emit("not a base event")
    bridge.event_ready.emit(123)
    bridge.event_ready.emit({"dict": "value"})
    qapp.processEvents()

    assert received == []
