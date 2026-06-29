"""Event bus implementation."""

import logging
import threading
from collections import defaultdict
from collections.abc import Callable

from app.contracts.events import BaseEvent

logger = logging.getLogger(__name__)


class EventBus:
    """Synchronous event bus for publish-subscribe messaging."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[BaseEvent], None]]] = defaultdict(list)
        self._lock = threading.RLock()

    def subscribe(
        self, event_type: str, handler: Callable[[BaseEvent], None]
    ) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: The type of event to subscribe to.
            handler: Callback function to invoke when event is published.
        """
        with self._lock:
            if handler in self._handlers[event_type]:
                return
            self._handlers[event_type].append(handler)

    def publish(self, event: BaseEvent) -> None:
        """Publish an event to all subscribed handlers.

        Args:
            event: The event to publish.

        Handler exceptions are logged and isolated so later subscribers still
        receive the event.
        """
        with self._lock:
            handlers = list(self._handlers.get(event.event_type, []))
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Event handler failed for event_type=%s request_id=%s",
                    event.event_type,
                    event.request_id,
                )

    def unsubscribe(
        self, event_type: str, handler: Callable[[BaseEvent], None]
    ) -> None:
        """Unsubscribe a handler from an event type.

        Args:
            event_type: The type of event to unsubscribe from.
            handler: The handler to remove.
        """
        with self._lock:
            if event_type in self._handlers:
                self._handlers[event_type] = [
                    h for h in self._handlers[event_type] if h != handler
                ]

    def clear(self) -> None:
        """Clear all subscriptions."""
        with self._lock:
            self._handlers.clear()
