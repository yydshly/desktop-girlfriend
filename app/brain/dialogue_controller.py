"""Dialogue controller for text-based conversation loop."""

import uuid
from typing import cast

from app.brain.prompts.registry import PromptMessage, PromptRegistry
from app.brain.providers.base import ChatProvider, ChatProviderError, ChatRequest, PromptMessageLike
from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGE_REQUESTED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.contracts.states import AppState
from app.core.event_bus import EventBus


class DialogueController:
    """Manages the text dialogue loop between user input and chat provider."""

    def __init__(
        self,
        event_bus: EventBus,
        provider: ChatProvider,
        prompt_registry: PromptRegistry,
    ) -> None:
        """Initialize DialogueController.

        Args:
            event_bus: Event bus for publishing and subscribing.
            provider: Chat provider for generating responses.
            prompt_registry: Prompt registry for building messages.
        """
        self._event_bus = event_bus
        self._provider = provider
        self._prompt_registry = prompt_registry

    def start(self) -> None:
        """Start listening for user text events."""
        self._event_bus.subscribe(USER_TEXT_SUBMITTED, self._on_user_text_submitted)

    def stop(self) -> None:
        """Stop listening for user text events."""
        self._event_bus.unsubscribe(USER_TEXT_SUBMITTED, self._on_user_text_submitted)

    def _on_user_text_submitted(self, event: BaseEvent) -> None:
        """Handle user text submitted event.

        Args:
            event: The user.text_submitted event.
        """
        text = event.payload.get("text")

        # Validate input
        if not isinstance(text, str) or not text.strip():
            self._publish_error(event.request_id, "Empty or missing user text")
            self._request_state(AppState.ERROR, "dialogue_error")
            return

        request_id = event.request_id or str(uuid.uuid4())

        # Request THINKING state
        self._request_state(AppState.THINKING, "dialogue_request")

        # Build messages and call provider
        try:
            messages = self._prompt_registry.build_chat_messages(text)
            prompt_messages = [
                PromptMessage(role=m.role, content=m.content) for m in messages
            ]
            request = ChatRequest(messages=cast(list[PromptMessageLike], prompt_messages))
            response = self._provider.generate(request)
            response_text = response.text

            if type(response_text) is not str or not response_text.strip():
                self._publish_error(request_id, "Unexpected error during generation")
                self._request_state(AppState.ERROR, "dialogue_error")
                return

            # Mark dialogue generation complete before publishing assistant text.
            # TTS subscribers may turn assistant text into SPEAKING state.
            self._request_state(AppState.IDLE, "dialogue_complete")

            # Publish assistant response
            assistant_event = BaseEvent(
                event_type=ASSISTANT_TEXT_RECEIVED,
                request_id=request_id,
                source="dialogue_controller",
                payload={"text": response_text},
            )
            self._event_bus.publish(assistant_event)

        except ChatProviderError:
            self._publish_error(request_id, "Provider failed to generate response")
            self._request_state(AppState.ERROR, "dialogue_error")

        except Exception:
            self._publish_error(request_id, "Unexpected error during generation")
            self._request_state(AppState.ERROR, "dialogue_error")

    def _request_state(self, target_state: AppState, reason: str) -> None:
        """Request a state change via event bus.

        Args:
            target_state: The target state to transition to.
            reason: The reason for the state change.
        """
        event = BaseEvent(
            event_type=STATE_CHANGE_REQUESTED,
            request_id=str(uuid.uuid4()),
            source="dialogue_controller",
            payload={"target_state": target_state.value, "reason": reason},
        )
        self._event_bus.publish(event)

    def _publish_error(self, request_id: str, message: str) -> None:
        """Publish a system error event.

        Args:
            request_id: The request ID for tracking.
            message: The error message.
        """
        event = BaseEvent(
            event_type=SYSTEM_ERROR,
            request_id=request_id,
            source="dialogue_controller",
            payload={"message": message},
        )
        self._event_bus.publish(event)
