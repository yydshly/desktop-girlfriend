"""Tests for QtEventBridge."""

from PySide6.QtCore import QCoreApplication

from app.contracts.events import BaseEvent
from app.ui.qt_event_bridge import QtEventBridge


def _get_qcore_app() -> QCoreApplication:
    """Get or create a QCoreApplication instance."""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


def test_qt_event_bridge_publishes_emitted_base_event() -> None:
    """Test that emitting a BaseEvent triggers the publish callback."""
    app = _get_qcore_app()
    received: list[BaseEvent] = []

    bridge = QtEventBridge(received.append)
    event = BaseEvent(event_type="test.event", request_id="req1", source="test")

    bridge.event_ready.emit(event)
    app.processEvents()

    assert received == [event]


def test_qt_event_bridge_ignores_non_base_event() -> None:
    """Test that emitting a non-BaseEvent object is ignored."""
    app = _get_qcore_app()
    received: list[BaseEvent] = []

    bridge = QtEventBridge(received.append)

    bridge.event_ready.emit("not a base event")
    bridge.event_ready.emit(123)
    bridge.event_ready.emit({"dict": "value"})
    app.processEvents()

    assert received == []
