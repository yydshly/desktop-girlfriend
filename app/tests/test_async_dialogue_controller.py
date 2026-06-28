"""Tests for AsyncDialogueController."""

import time
from collections.abc import Callable
from unittest.mock import MagicMock

from app.brain.async_dialogue_controller import AsyncDialogueController
from app.brain.prompts.registry import PromptRegistry
from app.brain.providers.base import ChatProvider, ChatProviderError, ChatRequest, ChatResponse
from app.contracts.events import BaseEvent


class SlowFakeProvider(ChatProvider):
    """Fake provider that sleeps before returning."""

    def __init__(self, delay: float = 0.1, reply_text: str = "Hello!") -> None:
        self._delay = delay
        self._reply_text = reply_text

    def generate(self, request: ChatRequest) -> ChatResponse:
        time.sleep(self._delay)
        return ChatResponse(text=self._reply_text)


class FailingFakeProvider(ChatProvider):
    """Fake provider that always raises ChatProviderError."""

    def __init__(self, message: str = "Provider failed") -> None:
        self._message = message

    def generate(self, request: ChatRequest) -> ChatResponse:
        raise ChatProviderError(self._message)


class ImmediateFakeProvider(ChatProvider):
    """Fake provider that returns immediately."""

    def __init__(self, reply_text: str = "Immediate reply") -> None:
        self._reply_text = reply_text

    def generate(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(text=self._reply_text)


def make_dispatch_collector() -> tuple[list[BaseEvent], Callable[[BaseEvent], None]]:
    """Create a list and a callback that appends to it."""
    events: list[BaseEvent] = []

    def collect(event: BaseEvent) -> None:
        events.append(event)

    return events, collect


class TestAsyncDialogueController:
    """Tests for AsyncDialogueController."""

    def _make_event(self, text: str) -> BaseEvent:
        return BaseEvent(
            event_type="user.text_submitted",
            request_id="req1",
            source="test",
            payload={"text": text},
        )

    def test_success_path_publishes_thinking_then_response_and_idle(self) -> None:
        """Test success path publishes THINKING, ASSISTANT_TEXT_RECEIVED, then IDLE."""
        event_bus = MagicMock()
        provider = ImmediateFakeProvider(reply_text="Test reply")
        registry = PromptRegistry()
        dispatch_events, dispatch_event = make_dispatch_collector()

        controller = AsyncDialogueController(
            event_bus=event_bus,
            provider=provider,
            prompt_registry=registry,
            dispatch_event=dispatch_event,
        )

        controller._on_user_text_submitted(self._make_event("Hello"))

        # Wait for worker thread to complete
        time.sleep(0.05)

        # Check THINKING was published via event_bus
        thinking_calls = [
            call
            for call in event_bus.publish.call_args_list
            if call[0][0].payload.get("target_state") == "thinking"
        ]
        assert len(thinking_calls) >= 1

        # Check worker dispatched ASSISTANT_TEXT_RECEIVED and IDLE
        assert len(dispatch_events) >= 2
        event_types = [e.event_type for e in dispatch_events]
        assert "assistant.text_received" in event_types
        assert "state.change_requested" in event_types

        # Verify IDLE state request
        idle_events = [
            e for e in dispatch_events if e.payload.get("target_state") == "idle"
        ]
        assert len(idle_events) >= 1

    def test_provider_failure_dispatches_safe_error_message(self) -> None:
        """Test provider failure dispatches SYSTEM_ERROR with safe message, not raw exception."""
        event_bus = MagicMock()
        provider = FailingFakeProvider(message="Bearer secret-key-should-not-leak")
        registry = PromptRegistry()
        dispatch_events, dispatch_event = make_dispatch_collector()

        controller = AsyncDialogueController(
            event_bus=event_bus,
            provider=provider,
            prompt_registry=registry,
            dispatch_event=dispatch_event,
        )

        controller._on_user_text_submitted(self._make_event("Hello"))

        # Wait for worker thread to complete
        time.sleep(0.05)

        # Find the SYSTEM_ERROR event
        error_events = [e for e in dispatch_events if e.event_type == "system.error"]
        assert len(error_events) >= 1

        error_msg = error_events[0].payload.get("message", "")
        # Message must be the safe constant, not the raw exception
        assert error_msg == "Provider failed to generate response"
        # Must not leak the secret-like exception message
        assert "secret-key" not in error_msg

    def test_provider_failure_dispatches_error_and_error_state(self) -> None:
        """Test provider failure dispatches SYSTEM_ERROR and ERROR state."""
        event_bus = MagicMock()
        provider = FailingFakeProvider()
        registry = PromptRegistry()
        dispatch_events, dispatch_event = make_dispatch_collector()

        controller = AsyncDialogueController(
            event_bus=event_bus,
            provider=provider,
            prompt_registry=registry,
            dispatch_event=dispatch_event,
        )

        controller._on_user_text_submitted(self._make_event("Hello"))

        # Wait for worker thread to complete
        time.sleep(0.05)

        # Check worker dispatched SYSTEM_ERROR and ERROR state
        event_types = [e.event_type for e in dispatch_events]
        assert "system.error" in event_types

        error_state_events = [
            e for e in dispatch_events if e.payload.get("target_state") == "error"
        ]
        assert len(error_state_events) >= 1

    def test_empty_text_publishes_error_on_ui_thread(self) -> None:
        """Test empty text publishes SYSTEM_ERROR and ERROR state on UI thread."""
        event_bus = MagicMock()
        provider = ImmediateFakeProvider()
        registry = PromptRegistry()
        dispatch_events, dispatch_event = make_dispatch_collector()

        controller = AsyncDialogueController(
            event_bus=event_bus,
            provider=provider,
            prompt_registry=registry,
            dispatch_event=dispatch_event,
        )

        # Empty string
        controller._on_user_text_submitted(self._make_event(""))

        # Should publish error directly on event_bus, not dispatch
        assert len(dispatch_events) == 0
        error_calls = [
            call for call in event_bus.publish.call_args_list
            if call[0][0].event_type == "system.error"
        ]
        assert len(error_calls) >= 1

        # Provider should not be called
        thinking_calls = [
            call for call in event_bus.publish.call_args_list
            if call[0][0].event_type == "state.change_requested"
            and call[0][0].payload.get("target_state") == "thinking"
        ]
        assert len(thinking_calls) == 0

    def test_second_submission_while_generating_is_ignored(self) -> None:
        """Test second submission while generating is silently ignored."""
        event_bus = MagicMock()
        provider = SlowFakeProvider(delay=0.2)
        registry = PromptRegistry()
        dispatch_events, dispatch_event = make_dispatch_collector()

        controller = AsyncDialogueController(
            event_bus=event_bus,
            provider=provider,
            prompt_registry=registry,
            dispatch_event=dispatch_event,
        )

        # First submission
        controller._on_user_text_submitted(self._make_event("First"))
        # Second submission while still generating
        controller._on_user_text_submitted(self._make_event("Second"))

        # Only one THINKING should be published
        thinking_calls = [
            call
            for call in event_bus.publish.call_args_list
            if call[0][0].payload.get("target_state") == "thinking"
        ]
        assert len(thinking_calls) == 1

        # Wait for completion
        time.sleep(0.3)

    def test_inflight_guard_released_after_success(self) -> None:
        """Test in-flight guard is released after successful generation."""
        event_bus = MagicMock()
        provider = ImmediateFakeProvider()
        registry = PromptRegistry()
        dispatch_events, dispatch_event = make_dispatch_collector()

        controller = AsyncDialogueController(
            event_bus=event_bus,
            provider=provider,
            prompt_registry=registry,
            dispatch_event=dispatch_event,
        )

        controller._on_user_text_submitted(self._make_event("Hello"))
        time.sleep(0.05)

        # Guard should be released - third submission should work
        controller._on_user_text_submitted(self._make_event("After"))
        time.sleep(0.05)

        # Should have two THINKING state requests
        thinking_calls = [
            call
            for call in event_bus.publish.call_args_list
            if call[0][0].payload.get("target_state") == "thinking"
        ]
        assert len(thinking_calls) == 2
