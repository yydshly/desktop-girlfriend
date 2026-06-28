"""Voice input controller — bridges ASR to the dialogue system."""

import logging
import threading
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING

from app.contracts.events import (
    ASR_TEXT_RECOGNIZED,
    STATE_CHANGE_REQUESTED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    VOICE_INPUT_REQUESTED,
    BaseEvent,
)
from app.contracts.states import AppState
from app.input.asr.providers.base import ASRProvider, ASRProviderError, ASRRequest

if TYPE_CHECKING:
    from app.core.event_bus import EventBus

logger = logging.getLogger(__name__)


class VoiceInputController:
    """Listens for voice input requests and drives a fake ASR pipeline.

    On success, publishes ASR_TEXT_RECOGNIZED (for debugging/logging) and then
    USER_TEXT_SUBMITTED so the existing dialogue chain handles the recognized text.

    On failure, publishes SYSTEM_ERROR and ERROR state.
    """

    def __init__(
        self,
        event_bus: "EventBus",
        provider: ASRProvider,
        dispatch_event: Callable[[BaseEvent], None],
    ) -> None:
        """Initialize VoiceInputController.

        Args:
            event_bus: Event bus for subscribing to voice.input_requested.
            provider: ASR provider (fake or real).
            dispatch_event: Callback to dispatch events to the UI thread safely.
        """
        self._event_bus = event_bus
        self._provider = provider
        self._dispatch_event = dispatch_event
        self._is_listening = False
        self._is_stopped = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start listening for voice input events."""
        with self._lock:
            self._is_stopped = False
        self._event_bus.subscribe(VOICE_INPUT_REQUESTED, self._on_voice_input_requested)

    def stop(self) -> None:
        """Stop listening and prevent late worker results from dispatching events."""
        with self._lock:
            self._is_stopped = True
            self._is_listening = False
        self._event_bus.unsubscribe(VOICE_INPUT_REQUESTED, self._on_voice_input_requested)

    def _on_voice_input_requested(self, event: BaseEvent) -> None:
        """Handle voice.input_requested event.

        Args:
            event: The voice.input_requested event.
        """
        with self._lock:
            if self._is_stopped:
                return
            if self._is_listening:
                # Already processing a request — silently ignore duplicate
                return
            self._is_listening = True

        request_id = event.request_id or str(uuid.uuid4())

        # Request LISTENING state on the UI thread immediately
        self._request_state(AppState.LISTENING, "voice_input_request", request_id)

        # Start worker thread
        thread = threading.Thread(
            target=self._recognize,
            args=(request_id,),
            daemon=True,
        )
        thread.start()

    def _recognize(self, request_id: str) -> None:
        """Worker thread: call ASR provider and dispatch result events.

        Args:
            request_id: Request ID for tracking.
        """
        try:
            response = self._provider.recognize(ASRRequest())

            if self._should_discard_result():
                return

            recognized_text = response.text
            if not recognized_text.strip():
                self._dispatch_error(
                    request_id, "语音识别失败，请稍后重试。"
                )
                self._dispatch_state_request(AppState.ERROR, "asr_error", request_id)
                return

            # Publish ASR_TEXT_RECOGNIZED for debugging/logging
            self._dispatch_event(
                BaseEvent(
                    event_type=ASR_TEXT_RECOGNIZED,
                    request_id=request_id,
                    source="voice_input_controller",
                    payload={"text": recognized_text},
                )
            )

            # Publish USER_TEXT_SUBMITTED to drive the existing dialogue chain
            self._dispatch_event(
                BaseEvent(
                    event_type=USER_TEXT_SUBMITTED,
                    request_id=request_id,
                    source="voice_input_controller",
                    payload={"text": recognized_text},
                )
            )

        except ASRProviderError:
            if self._should_discard_result():
                return
            self._dispatch_error(request_id, "语音识别失败，请稍后重试。")
            self._dispatch_state_request(AppState.ERROR, "asr_error", request_id)

        except Exception:
            if self._should_discard_result():
                return
            logger.exception("Unexpected ASR error")
            self._dispatch_error(request_id, "语音识别失败，请稍后重试。")
            self._dispatch_state_request(AppState.ERROR, "asr_error", request_id)

        finally:
            with self._lock:
                self._is_listening = False

    def _should_discard_result(self) -> bool:
        """Return True when this controller has been stopped."""
        with self._lock:
            return self._is_stopped

    def _request_state(
        self, target_state: AppState, reason: str, request_id: str
    ) -> None:
        """Request a state change on the UI thread.

        Args:
            target_state: The target state to transition to.
            reason: The reason for the state change.
            request_id: Request ID for tracking.
        """
        event = BaseEvent(
            event_type=STATE_CHANGE_REQUESTED,
            request_id=request_id,
            source="voice_input_controller",
            payload={"target_state": target_state.value, "reason": reason},
        )
        self._event_bus.publish(event)

    def _dispatch_state_request(
        self, target_state: AppState, reason: str, request_id: str
    ) -> None:
        """Dispatch a state change request from worker thread to UI thread.

        Args:
            target_state: The target state to transition to.
            reason: The reason for the state change.
            request_id: Request ID for tracking.
        """
        event = BaseEvent(
            event_type=STATE_CHANGE_REQUESTED,
            request_id=request_id,
            source="voice_input_controller",
            payload={"target_state": target_state.value, "reason": reason},
        )
        self._dispatch_event(event)

    def _dispatch_error(self, request_id: str, message: str) -> None:
        """Dispatch a system error event from worker thread to UI thread.

        Args:
            request_id: Request ID for tracking.
            message: The error message (user-safe, no secrets).
        """
        event = BaseEvent(
            event_type=SYSTEM_ERROR,
            request_id=request_id,
            source="voice_input_controller",
            payload={"message": message},
        )
        self._dispatch_event(event)
