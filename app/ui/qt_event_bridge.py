"""Qt event bridge for thread-safe event dispatch to UI thread."""

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from app.contracts.events import BaseEvent


class QtEventBridge(QObject):
    """Bridge to safely dispatch events from worker threads to the Qt UI thread."""

    event_ready = Signal(object)

    def __init__(self, publish_event: Callable[[BaseEvent], None]) -> None:
        """Initialize the bridge.

        Args:
            publish_event: Callback to publish event to EventBus (must be called on UI thread).
        """
        super().__init__()
        self._publish_event = publish_event
        self.event_ready.connect(self._on_event_ready)

    @Slot(object)
    def _on_event_ready(self, event: Any) -> None:
        """Receive event from worker thread and publish on UI thread.

        Args:
            event: The BaseEvent to publish.
        """
        if isinstance(event, BaseEvent):
            self._publish_event(event)
