"""Tests for DialogueController."""

from unittest.mock import MagicMock

from app.brain.dialogue_controller import DialogueController
from app.brain.prompts.registry import PromptRegistry
from app.brain.providers.base import ChatProvider, ChatProviderError, ChatRequest, ChatResponse
from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGE_REQUESTED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)


class FakeChatProviderForTest(ChatProvider):
    """Test double for ChatProvider."""

    def __init__(self, reply_text: str = "Fake response", should_fail: bool = False) -> None:
        self._reply_text = reply_text
        self._should_fail = should_fail
        self.calls: list[ChatRequest] = []

    def generate(self, request: ChatRequest) -> ChatResponse:
        self.calls.append(request)
        if self._should_fail:
            raise ChatProviderError("Provider failed")
        return ChatResponse(text=self._reply_text)


class TestDialogueControllerSuccess:
    """Tests for DialogueController success path."""

    def _make_event(self, text: str) -> BaseEvent:
        return BaseEvent(
            event_type=USER_TEXT_SUBMITTED,
            request_id="req1",
            source="test",
            payload={"text": text},
        )

    def test_success_path_updates_state_correctly(self) -> None:
        """Test success path publishes correct events in order."""
        event_bus = MagicMock()
        provider = FakeChatProviderForTest(reply_text="Hello!")
        registry = PromptRegistry()
        controller = DialogueController(event_bus, provider, registry)

        controller._on_user_text_submitted(self._make_event("Hi there"))

        # Verify provider was called
        assert len(provider.calls) == 1
        messages = provider.calls[0].messages
        assert len(messages) == 2
        assert messages[0].role == "system"
        assert messages[1].content == "Hi there"

        # Verify event publications
        published_events = [call[0][0] for call in event_bus.publish.call_args_list]
        assert len(published_events) == 3

        # Event 1: THINKING state request
        assert published_events[0].event_type == STATE_CHANGE_REQUESTED
        assert published_events[0].payload["target_state"] == "thinking"
        assert published_events[0].payload["reason"] == "dialogue_request"

        # Event 2: IDLE state request
        assert published_events[1].event_type == STATE_CHANGE_REQUESTED
        assert published_events[1].payload["target_state"] == "idle"
        assert published_events[1].payload["reason"] == "dialogue_complete"

        # Event 3: ASSISTANT_TEXT_RECEIVED
        assert published_events[2].event_type == ASSISTANT_TEXT_RECEIVED
        assert published_events[2].payload["text"] == "Hello!"

        # No SYSTEM_ERROR
        for evt in published_events:
            assert evt.event_type != SYSTEM_ERROR


class TestDialogueControllerEmptyInput:
    """Tests for DialogueController empty input handling."""

    def test_missing_text_publishes_error_and_error_state(self) -> None:
        """Test missing text publishes SYSTEM_ERROR and ERROR state."""
        event_bus = MagicMock()
        provider = FakeChatProviderForTest()
        registry = PromptRegistry()
        controller = DialogueController(event_bus, provider, registry)

        event = BaseEvent(
            event_type=USER_TEXT_SUBMITTED,
            request_id="req2",
            source="test",
            payload={},
        )
        controller._on_user_text_submitted(event)

        published_events = [call[0][0] for call in event_bus.publish.call_args_list]
        assert len(published_events) == 2

        # Event 1: SYSTEM_ERROR
        assert published_events[0].event_type == SYSTEM_ERROR
        assert "Empty or missing" in published_events[0].payload["message"]

        # Event 2: ERROR state request
        assert published_events[1].event_type == STATE_CHANGE_REQUESTED
        assert published_events[1].payload["target_state"] == "error"
        assert published_events[1].payload["reason"] == "dialogue_error"

        # Provider should not be called
        assert len(provider.calls) == 0

    def test_whitespace_only_text_publishes_error_and_error_state(self) -> None:
        """Test whitespace-only text publishes SYSTEM_ERROR and ERROR state."""
        event_bus = MagicMock()
        provider = FakeChatProviderForTest()
        registry = PromptRegistry()
        controller = DialogueController(event_bus, provider, registry)

        event = BaseEvent(
            event_type=USER_TEXT_SUBMITTED,
            request_id="req3",
            source="test",
            payload={"text": "   "},
        )
        controller._on_user_text_submitted(event)

        published_events = [call[0][0] for call in event_bus.publish.call_args_list]
        assert len(published_events) == 2
        assert published_events[0].event_type == SYSTEM_ERROR
        assert published_events[1].event_type == STATE_CHANGE_REQUESTED
        assert published_events[1].payload["target_state"] == "error"

        # Provider should not be called
        assert len(provider.calls) == 0

    def test_non_string_text_publishes_error_and_error_state(self) -> None:
        """Test non-string text publishes SYSTEM_ERROR and ERROR state."""
        event_bus = MagicMock()
        provider = FakeChatProviderForTest()
        registry = PromptRegistry()
        controller = DialogueController(event_bus, provider, registry)

        event = BaseEvent(
            event_type=USER_TEXT_SUBMITTED,
            request_id="req4",
            source="test",
            payload={"text": None},
        )
        controller._on_user_text_submitted(event)

        published_events = [call[0][0] for call in event_bus.publish.call_args_list]
        assert len(published_events) == 2
        assert published_events[0].event_type == SYSTEM_ERROR
        assert published_events[1].event_type == STATE_CHANGE_REQUESTED
        assert published_events[1].payload["target_state"] == "error"


class TestDialogueControllerProviderFailure:
    """Tests for DialogueController provider failure handling."""

    def test_provider_failure_publishes_error_and_error_state(self) -> None:
        """Test provider failure publishes THINKING, SYSTEM_ERROR, ERROR state."""
        event_bus = MagicMock()
        provider = FakeChatProviderForTest(should_fail=True)
        registry = PromptRegistry()
        controller = DialogueController(event_bus, provider, registry)

        event = BaseEvent(
            event_type=USER_TEXT_SUBMITTED,
            request_id="req5",
            source="test",
            payload={"text": "Hello"},
        )
        controller._on_user_text_submitted(event)

        published_events = [call[0][0] for call in event_bus.publish.call_args_list]
        assert len(published_events) == 3

        # Event 1: THINKING state request
        assert published_events[0].event_type == STATE_CHANGE_REQUESTED
        assert published_events[0].payload["target_state"] == "thinking"

        # Event 2: SYSTEM_ERROR
        assert published_events[1].event_type == SYSTEM_ERROR
        assert "Provider failed" in published_events[1].payload["message"]

        # Event 3: ERROR state request
        assert published_events[2].event_type == STATE_CHANGE_REQUESTED
        assert published_events[2].payload["target_state"] == "error"
        assert published_events[2].payload["reason"] == "dialogue_error"

        # No ASSISTANT_TEXT_RECEIVED
        for evt in published_events:
            assert evt.event_type != ASSISTANT_TEXT_RECEIVED

        # Provider was called (THINKING was requested first)
        assert len(provider.calls) == 1
