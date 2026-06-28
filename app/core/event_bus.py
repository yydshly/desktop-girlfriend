"""Event bus implementation."""

from collections import defaultdict
from collections.abc import Callable

from app.contracts.events import BaseEvent


class EventBus:
    """Synchronous event bus for publish-subscribe messaging."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[BaseEvent], None]]] = defaultdict(list)

    def subscribe(
        self, event_type: str, handler: Callable[[BaseEvent], None]
    ) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: The type of event to subscribe to.
            handler: Callback function to invoke when event is published.
        """
        self._handlers[event_type].append(handler)

    def publish(self, event: BaseEvent) -> None:
        """Publish an event to all subscribed handlers.

        Args:
            event: The event to publish.

        Raises:
            Exception: Any exception raised by a handler is propagated.
        """
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            handler(event)

    def unsubscribe(
        self, event_type: str, handler: Callable[[BaseEvent], None]
    ) -> None:
        """Unsubscribe a handler from an event type.

        Args:
            event_type: The type of event to unsubscribe from.
            handler: The handler to remove.
        """
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    def clear(self) -> None:
        """Clear all subscriptions."""
        self._handlers.clear()
