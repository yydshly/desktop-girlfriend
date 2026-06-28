"""Tests for AsyncDialogueController."""

import threading
import time
from collections.abc import Callable
from unittest.mock import MagicMock

from app.brain.async_dialogue_controller import AsyncDialogueController
from app.brain.prompts.history import CurrentSessionHistory
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


class SpyProvider(ChatProvider):
    """Fake provider that captures the last ChatRequest and returns a canned response."""

    def __init__(self, reply_text: str = "Spy reply") -> None:
        self._reply_text = reply_text
        self.last_request: ChatRequest | None = None

    def generate(self, request: ChatRequest) -> ChatResponse:
        self.last_request = request
        return ChatResponse(text=self._reply_text)


class EmptyResponseFakeProvider(ChatProvider):
    """Fake provider that returns an empty or whitespace-only response."""

    def __init__(self, reply_text: str = "") -> None:
        self._reply_text = reply_text

    def generate(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(text=self._reply_text)


class BlockingChatProvider(ChatProvider):
    """Fake provider that blocks until explicitly released."""

    def __init__(self, reply_text: str = "Late reply") -> None:
        self.reply_text = reply_text
        self.generate_started = threading.Event()
        self.release = threading.Event()

    def generate(self, request: ChatRequest) -> ChatResponse:
        self.generate_started.set()
        self.release.wait()
        return ChatResponse(text=self.reply_text)


class StoppableBlockingChatProvider(ChatProvider):
    """Fake provider that blocks until stop() is called."""

    def __init__(self, reply_text: str = "Stopped reply") -> None:
        self.reply_text = reply_text
        self.generate_started = threading.Event()
        self.generate_finished = threading.Event()
        self._stop_requested = threading.Event()
        self.stop_called = False

    def generate(self, request: ChatRequest) -> ChatResponse:
        self.generate_started.set()
        self._stop_requested.wait()
        self.generate_finished.set()
        return ChatResponse(text=self.reply_text)

    def stop(self) -> None:
        self.stop_called = True
        self._stop_requested.set()


class StopFailingChatProvider(ChatProvider):
    """Fake provider whose stop() raises."""

    def generate(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(text="ok")

    def stop(self) -> None:
        raise RuntimeError("stop failed")


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

    def test_success_path_publishes_thinking_then_idle_and_response(self) -> None:
        """Test success path publishes THINKING, IDLE, then ASSISTANT_TEXT_RECEIVED."""
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

        # Check worker dispatched IDLE and ASSISTANT_TEXT_RECEIVED
        assert len(dispatch_events) >= 2
        event_types = [e.event_type for e in dispatch_events]
        assert "assistant.text_received" in event_types
        assert "state.change_requested" in event_types

        # Verify IDLE state request
        idle_events = [
            e for e in dispatch_events if e.payload.get("target_state") == "idle"
        ]
        assert len(idle_events) >= 1
        assert dispatch_events.index(idle_events[0]) < event_types.index(
            "assistant.text_received"
        )

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

    def test_stop_discards_late_provider_response(self) -> None:
        """Test stop() prevents a late worker response from dispatching UI events."""
        event_bus = MagicMock()
        provider = BlockingChatProvider(reply_text="Too late")
        registry = PromptRegistry()
        dispatch_events, dispatch_event = make_dispatch_collector()

        controller = AsyncDialogueController(
            event_bus=event_bus,
            provider=provider,
            prompt_registry=registry,
            dispatch_event=dispatch_event,
        )
        controller.start()

        controller._on_user_text_submitted(self._make_event("Hello"))
        assert provider.generate_started.wait(timeout=1.0)

        controller.stop()
        provider.release.set()
        time.sleep(0.05)

        assert dispatch_events == []

    def test_stop_forwards_cancellation_to_provider(self) -> None:
        """Test stop() asks the provider to cancel active generation."""
        event_bus = MagicMock()
        provider = StoppableBlockingChatProvider(reply_text="Too late")
        registry = PromptRegistry()
        dispatch_events, dispatch_event = make_dispatch_collector()

        controller = AsyncDialogueController(
            event_bus=event_bus,
            provider=provider,
            prompt_registry=registry,
            dispatch_event=dispatch_event,
        )
        controller.start()

        controller._on_user_text_submitted(self._make_event("Hello"))
        assert provider.generate_started.wait(timeout=1.0)

        controller.stop()

        assert provider.stop_called is True
        assert provider.generate_finished.wait(timeout=0.5)
        assert dispatch_events == []

    def test_stop_ignores_provider_stop_error_and_unsubscribes(self) -> None:
        """Test provider stop errors do not break controller shutdown."""
        event_bus = MagicMock()
        provider = StopFailingChatProvider()
        registry = PromptRegistry()
        dispatch_events, dispatch_event = make_dispatch_collector()

        controller = AsyncDialogueController(
            event_bus=event_bus,
            provider=provider,
            prompt_registry=registry,
            dispatch_event=dispatch_event,
        )
        controller.start()

        controller.stop()

        event_bus.unsubscribe.assert_called_with(
            "user.text_submitted",
            controller._on_user_text_submitted,
        )
        assert dispatch_events == []


class TestAsyncDialogueControllerSessionHistory:
    """Tests for AsyncDialogueController session history integration."""

    def _make_event(self, text: str) -> BaseEvent:
        return BaseEvent(
            event_type="user.text_submitted",
            request_id="req1",
            source="test",
            payload={"text": text},
        )

    def test_provider_receives_history_messages_before_current_user(self) -> None:
        """Test that provider receives history messages before current user text."""
        event_bus = MagicMock()
        spy_provider = SpyProvider(reply_text="I heard you")
        registry = PromptRegistry(default_system_prompt="system")
        session_history = CurrentSessionHistory()
        dispatch_events, dispatch_event = make_dispatch_collector()

        # Pre-populate session history
        session_history.append_user_text("你好")
        session_history.append_assistant_text("我在")

        controller = AsyncDialogueController(
            event_bus=event_bus,
            provider=spy_provider,
            prompt_registry=registry,
            dispatch_event=dispatch_event,
            session_history=session_history,
        )

        controller._on_user_text_submitted(self._make_event("刚才我说了什么？"))
        time.sleep(0.05)

        # Provider should have received system + history user + history assistant + current user
        assert spy_provider.last_request is not None
        messages = spy_provider.last_request.messages
        roles = [m.role for m in messages]
        assert roles == ["system", "user", "assistant", "user"]
        assert messages[1].content == "你好"
        assert messages[2].content == "我在"
        assert messages[3].content == "刚才我说了什么？"

    def test_successful_generation_appends_user_and_assistant_to_history(self) -> None:
        """Test that successful generation appends both user and assistant to session_history."""
        event_bus = MagicMock()
        spy_provider = SpyProvider(reply_text="我的回复")
        registry = PromptRegistry()
        session_history = CurrentSessionHistory()
        dispatch_events, dispatch_event = make_dispatch_collector()

        controller = AsyncDialogueController(
            event_bus=event_bus,
            provider=spy_provider,
            prompt_registry=registry,
            dispatch_event=dispatch_event,
            session_history=session_history,
        )

        controller._on_user_text_submitted(self._make_event("我的问题"))
        time.sleep(0.05)

        turns = session_history.recent_turns()
        assert len(turns) == 2
        assert turns[0].role == "user"
        assert turns[0].text == "我的问题"
        assert turns[1].role == "assistant"
        assert turns[1].text == "我的回复"

    def test_failed_provider_does_not_append_to_history(self) -> None:
        """Test that failed provider does not append user or assistant to session_history."""
        event_bus = MagicMock()
        provider = FailingFakeProvider()
        registry = PromptRegistry()
        session_history = CurrentSessionHistory()
        dispatch_events, dispatch_event = make_dispatch_collector()

        controller = AsyncDialogueController(
            event_bus=event_bus,
            provider=provider,
            prompt_registry=registry,
            dispatch_event=dispatch_event,
            session_history=session_history,
        )

        controller._on_user_text_submitted(self._make_event("我的问题"))
        time.sleep(0.05)

        # History should still be empty after failed generation
        assert session_history.recent_turns() == []

    def test_history_isolation_between_controllers(self) -> None:
        """Test that two controllers have isolated session histories."""
        event_bus = MagicMock()
        registry = PromptRegistry()
        dispatch_events, dispatch_event = make_dispatch_collector()

        history1 = CurrentSessionHistory()
        history2 = CurrentSessionHistory()

        controller1 = AsyncDialogueController(
            event_bus=event_bus,
            provider=SpyProvider(reply_text="Reply1"),
            prompt_registry=registry,
            dispatch_event=dispatch_event,
            session_history=history1,
        )

        controller2 = AsyncDialogueController(
            event_bus=event_bus,
            provider=SpyProvider(reply_text="Reply2"),
            prompt_registry=registry,
            dispatch_event=dispatch_event,
            session_history=history2,
        )

        controller1._on_user_text_submitted(self._make_event("User1"))
        time.sleep(0.05)

        controller2._on_user_text_submitted(self._make_event("User2"))
        time.sleep(0.05)

        # Each history should only have its own turns
        assert len(history1.recent_turns()) == 2
        assert len(history2.recent_turns()) == 2
        assert history1.recent_turns()[0].text == "User1"
        assert history2.recent_turns()[0].text == "User2"

    def test_empty_assistant_response_does_not_append_to_history(self) -> None:
        """Test that empty/whitespace assistant response does not append to history."""
        event_bus = MagicMock()
        provider = EmptyResponseFakeProvider(reply_text="")
        registry = PromptRegistry()
        session_history = CurrentSessionHistory()
        dispatch_events, dispatch_event = make_dispatch_collector()

        controller = AsyncDialogueController(
            event_bus=event_bus,
            provider=provider,
            prompt_registry=registry,
            dispatch_event=dispatch_event,
            session_history=session_history,
        )

        controller._on_user_text_submitted(self._make_event("我的问题"))
        time.sleep(0.05)

        # History should still be empty - user was not appended because response was empty
        assert session_history.recent_turns() == []

        # Should have dispatched system.error
        error_events = [e for e in dispatch_events if e.event_type == "system.error"]
        assert len(error_events) >= 1

        # Should have dispatched error state
        error_state_events = [
            e for e in dispatch_events
            if e.event_type == "state.change_requested" and e.payload.get("target_state") == "error"
        ]
        assert len(error_state_events) >= 1

        # Should NOT have dispatched assistant.text_received
        assistant_events = [
            e for e in dispatch_events if e.event_type == "assistant.text_received"
        ]
        assert len(assistant_events) == 0

    def test_whitespace_assistant_response_treated_as_empty(self) -> None:
        """Test that whitespace-only assistant response is treated as empty."""
        event_bus = MagicMock()
        provider = EmptyResponseFakeProvider(reply_text="   ")
        registry = PromptRegistry()
        session_history = CurrentSessionHistory()
        dispatch_events, dispatch_event = make_dispatch_collector()

        controller = AsyncDialogueController(
            event_bus=event_bus,
            provider=provider,
            prompt_registry=registry,
            dispatch_event=dispatch_event,
            session_history=session_history,
        )

        controller._on_user_text_submitted(self._make_event("我的问题"))
        time.sleep(0.05)

        # History should still be empty
        assert session_history.recent_turns() == []

        # Should NOT have dispatched assistant.text_received
        assistant_events = [
            e for e in dispatch_events if e.event_type == "assistant.text_received"
        ]
        assert len(assistant_events) == 0

