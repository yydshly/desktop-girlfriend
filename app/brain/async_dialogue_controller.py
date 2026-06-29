"""Asynchronous dialogue controller for non-blocking chat provider calls."""

import logging
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

logger = logging.getLogger(__name__)

_WORKER_JOIN_TIMEOUT_SECONDS = 0.2


class AsyncDialogueController:
    """Manages asynchronous text dialogue loop between user input and chat provider."""

    def __init__(
        self,
        event_bus: EventBus,
        provider: ChatProvider,
        prompt_registry: PromptRegistry,
        dispatch_event: Callable[[BaseEvent], None],
        session_history: CurrentSessionHistory | None = None,
        complete_state_after_assistant_response: bool = True,
        session_memory_context_provider: Callable[[], str] | None = None,
    ) -> None:
        """Initialize AsyncDialogueController.

        Args:
            event_bus: Event bus for subscribing to user text events.
            provider: Chat provider for generating responses.
            prompt_registry: Prompt registry for building messages.
            dispatch_event: Callback to dispatch events back to UI thread safely.
            session_history: Optional in-memory session history for context.
                             If None, a default CurrentSessionHistory is created.
            complete_state_after_assistant_response: When True (default), dispatches
                IDLE state after successful assistant response. Set to False when
                TTSController接管 state lifecycle so DialogueController does not
                override SPEAKING with IDLE.
            session_memory_context_provider: Optional callable that returns a
                formatted session memory context string. If None (default),
                no memory context is injected.
        """
        self._event_bus = event_bus
        self._provider = provider
        self._prompt_registry = prompt_registry
        self._dispatch_event = dispatch_event
        self._session_history = session_history if session_history is not None else CurrentSessionHistory()
        self._complete_state_after_assistant_response = complete_state_after_assistant_response
        self._session_memory_context_provider = session_memory_context_provider
        self._is_generating = False
        self._is_stopped = False
        self._worker_thread: threading.Thread | None = None
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
        try:
            self._provider.stop()
        except Exception:
            logger.exception("Chat provider stop failed")
        finally:
            self._join_worker_thread()
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
                self._publish_error(
                    event.request_id,
                    "System busy: still generating the previous response.",
                )
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
        with self._lock:
            self._worker_thread = thread
        thread.start()

    def _join_worker_thread(self) -> None:
        """Wait briefly for the current worker thread to finish."""
        with self._lock:
            worker = self._worker_thread
        if worker is not None and worker.is_alive() and worker is not threading.current_thread():
            worker.join(timeout=_WORKER_JOIN_TIMEOUT_SECONDS)

    def _generate_response(self, request_id: str, text: str) -> None:
        """Worker thread: call provider and dispatch result events.

        Args:
            request_id: Request ID for tracking.
            text: User input text.
        """
        try:
            history_turns = self._session_history.recent_turns()

            # Get session memory context if provider is set
            session_memory_context: str | None = None
            if self._session_memory_context_provider is not None:
                try:
                    session_memory_context = self._session_memory_context_provider()
                except Exception:
                    logger.exception("Session memory context provider failed")
                    session_memory_context = None

            messages = self._prompt_registry.build_chat_messages(
                text,
                history_turns=history_turns,
                session_memory_context=session_memory_context,
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

            # Publish assistant text first so TTS subscribers can transition to SPEAKING
            # before DialogueController sends IDLE (when it does at all).
            self._dispatch_event(
                BaseEvent(
                    event_type=ASSISTANT_TEXT_RECEIVED,
                    request_id=request_id,
                    source="async_dialogue_controller",
                    payload={"text": response_text},
                )
            )

            if self._complete_state_after_assistant_response:
                self._dispatch_state_request(AppState.IDLE, "dialogue_complete")

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
