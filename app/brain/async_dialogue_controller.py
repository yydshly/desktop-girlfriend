"""Asynchronous dialogue controller for non-blocking chat provider calls."""

import threading
import uuid
from collections.abc import Callable
from typing import cast

from app.brain.prompts.history import CurrentSessionHistory
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


class AsyncDialogueController:
    """Manages asynchronous text dialogue loop between user input and chat provider."""

    def __init__(
        self,
        event_bus: EventBus,
        provider: ChatProvider,
        prompt_registry: PromptRegistry,
        dispatch_event: Callable[[BaseEvent], None],
        session_history: CurrentSessionHistory | None = None,
    ) -> None:
        """Initialize AsyncDialogueController.

        Args:
            event_bus: Event bus for subscribing to user text events.
            provider: Chat provider for generating responses.
            prompt_registry: Prompt registry for building messages.
            dispatch_event: Callback to dispatch events back to UI thread safely.
            session_history: Optional in-memory session history for context.
                             If None, a default CurrentSessionHistory is created.
        """
        self._event_bus = event_bus
        self._provider = provider
        self._prompt_registry = prompt_registry
        self._dispatch_event = dispatch_event
        self._session_history = session_history if session_history is not None else CurrentSessionHistory()
        self._is_generating = False
        self._is_stopped = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start listening for user text events."""
        with self._lock:
            self._is_stopped = False
        self._event_bus.subscribe(USER_TEXT_SUBMITTED, self._on_user_text_submitted)

    def stop(self) -> None:
        """Stop listening for user text events."""
        with self._lock:
            self._is_stopped = True
            self._is_generating = False
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

        # Guard against concurrent generation
        with self._lock:
            if self._is_stopped:
                return
            if self._is_generating:
                # Silently ignore new input while generation is in progress
                return
            self._is_generating = True

        request_id = event.request_id or str(uuid.uuid4())

        # Immediately request THINKING state on UI thread
        self._request_state(AppState.THINKING, "dialogue_request")

        # Start worker thread
        thread = threading.Thread(
            target=self._generate_response,
            args=(request_id, text),
            daemon=True,
        )
        thread.start()

    def _generate_response(self, request_id: str, text: str) -> None:
        """Worker thread: call provider and dispatch result events.

        Args:
            request_id: Request ID for tracking.
            text: User input text.
        """
        try:
            history_turns = self._session_history.recent_turns()
            messages = self._prompt_registry.build_chat_messages(
                text,
                history_turns=history_turns,
            )
            prompt_messages = [
                PromptMessage(role=m.role, content=m.content) for m in messages
            ]
            request = ChatRequest(messages=cast(list[PromptMessageLike], prompt_messages))
            response = self._provider.generate(request)
            response_text = response.text

            if self._should_discard_worker_result():
                return

            # Validate response before committing to history
            if type(response_text) is not str or not response_text.strip():
                if self._should_discard_worker_result():
                    return
                self._dispatch_error(request_id, "Unexpected error during generation")
                self._dispatch_state_request(AppState.ERROR, "dialogue_error")
                return

            # Append to session history only on success
            self._session_history.append_user_text(text)
            self._session_history.append_assistant_text(response_text)

            # Mark dialogue generation complete before publishing assistant text.
            # TTS subscribers may turn assistant text into SPEAKING state.
            self._dispatch_state_request(AppState.IDLE, "dialogue_complete")
            self._dispatch_event(
                BaseEvent(
                    event_type=ASSISTANT_TEXT_RECEIVED,
                    request_id=request_id,
                    source="async_dialogue_controller",
                    payload={"text": response_text},
                )
            )

        except ChatProviderError:
            if self._should_discard_worker_result():
                return
            self._dispatch_error(request_id, "Provider failed to generate response")
            self._dispatch_state_request(AppState.ERROR, "dialogue_error")

        except Exception:
            if self._should_discard_worker_result():
                return
            self._dispatch_error(request_id, "Unexpected error during generation")
            self._dispatch_state_request(AppState.ERROR, "dialogue_error")

        finally:
            with self._lock:
                self._is_generating = False

    def _should_discard_worker_result(self) -> bool:
        """Return True when this controller has been stopped."""
        with self._lock:
            return self._is_stopped

    def _request_state(self, target_state: AppState, reason: str) -> None:
        """Request a state change via event bus (UI thread only).

        Args:
            target_state: The target state to transition to.
            reason: The reason for the state change.
        """
        event = BaseEvent(
            event_type=STATE_CHANGE_REQUESTED,
            request_id=str(uuid.uuid4()),
            source="async_dialogue_controller",
            payload={"target_state": target_state.value, "reason": reason},
        )
        self._event_bus.publish(event)

    def _dispatch_state_request(self, target_state: AppState, reason: str) -> None:
        """Dispatch a state change request from worker thread to UI thread.

        Args:
            target_state: The target state to transition to.
            reason: The reason for the state change.
        """
        event = BaseEvent(
            event_type=STATE_CHANGE_REQUESTED,
            request_id=str(uuid.uuid4()),
            source="async_dialogue_controller",
            payload={"target_state": target_state.value, "reason": reason},
        )
        self._dispatch_event(event)

    def _publish_error(self, request_id: str, message: str) -> None:
        """Publish a system error event on UI thread.

        Args:
            request_id: The request ID for tracking.
            message: The error message.
        """
        event = BaseEvent(
            event_type=SYSTEM_ERROR,
            request_id=request_id,
            source="async_dialogue_controller",
            payload={"message": message},
        )
        self._event_bus.publish(event)

    def _dispatch_error(self, request_id: str, message: str) -> None:
        """Dispatch a system error event from worker thread to UI thread.

        Args:
            request_id: The request ID for tracking.
            message: The error message.
        """
        event = BaseEvent(
            event_type=SYSTEM_ERROR,
            request_id=request_id,
            source="async_dialogue_controller",
            payload={"message": message},
        )
        self._dispatch_event(event)
