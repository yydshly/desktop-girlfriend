"""Proactive nudge controller (V9-A / V9-C)."""

from __future__ import annotations

import uuid
from collections.abc import Callable

from app.brain.proactive.service import ProactiveNudgeService
from app.contracts.events import (
    PROACTIVE_NUDGE_READY,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.contracts.payloads import ProactiveNudgeReadyPayload


class ProactiveController:
    """Controller for proactive nudge timing and dispatch."""

    def __init__(
        self,
        *,
        service: ProactiveNudgeService,
        subscribe: Callable[[str, Callable[[BaseEvent], None]], None],
        unsubscribe: Callable[[str, Callable[[BaseEvent], None]], None],
        dispatch_event: Callable[[BaseEvent], None],
    ) -> None:
        self._service = service
        self._subscribe = subscribe
        self._unsubscribe = unsubscribe
        self._dispatch_event = dispatch_event
        self._started = False

    def _on_user_text_submitted(self, event: BaseEvent) -> None:
        """Handle user.text_submitted to record user activity/suppress phrases.

        V9-C: Uses record_user_message to detect suppress phrases.
        """
        if event.event_type == USER_TEXT_SUBMITTED:
            text = event.payload.get("text")
            if isinstance(text, str):
                self._service.record_user_message(text)
            else:
                self._service.record_user_activity()

    def start(self) -> None:
        """Start the controller (idempotent)."""
        if self._started:
            return
        self._started = True
        self._subscribe(USER_TEXT_SUBMITTED, self._on_user_text_submitted)

    def stop(self) -> None:
        """Stop the controller (idempotent)."""
        if not self._started:
            return
        self._started = False
        self._unsubscribe(USER_TEXT_SUBMITTED, self._on_user_text_submitted)

    def tick(self, *, is_busy: bool = False) -> None:
        """Check and dispatch a proactive nudge if conditions are met.

        Args:
            is_busy: If True, skip nudge even if conditions are met.
        """
        nudge_text = self._service.maybe_create_nudge(is_busy=is_busy)
        if nudge_text is None:
            return

        # Dispatch the event
        self._dispatch_event(
            BaseEvent(
                event_type=PROACTIVE_NUDGE_READY,
                request_id=str(uuid.uuid4()),
                source="proactive_controller",
                payload=ProactiveNudgeReadyPayload(text=nudge_text).to_event_payload(),
            )
        )
        # Record after successful dispatch
        self._service.record_nudge_sent()
