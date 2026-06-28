"""TTS controller for managing text-to-speech playback."""

import threading
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING

from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGE_REQUESTED,
    SYSTEM_ERROR,
    BaseEvent,
)
from app.contracts.states import AppState
from app.expression.tts.providers.base import TTSProvider, TTSProviderError, TTSRequest

if TYPE_CHECKING:
    from app.core.event_bus import EventBus

_SAFE_TTS_ERROR_MESSAGE = "语音播放失败，请稍后重试。"


class TTSController:
    """Manages TTS playback in response to assistant text events."""

    def __init__(
        self,
        event_bus: "EventBus",
        provider: TTSProvider,
        dispatch_event: Callable[[BaseEvent], None],
    ) -> None:
        """Initialize TTSController.

        Args:
            event_bus: Event bus for subscribing to events.
            provider: TTS provider for speech synthesis and playback.
            dispatch_event: Callback to dispatch events back to UI thread safely.
        """
        self._event_bus = event_bus
        self._provider = provider
        self._dispatch_event = dispatch_event
        self._is_speaking = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start listening for assistant text received events."""
        self._event_bus.subscribe(ASSISTANT_TEXT_RECEIVED, self._on_assistant_text_received)

    def stop(self) -> None:
        """Stop listening for assistant text received events."""
        self._event_bus.unsubscribe(ASSISTANT_TEXT_RECEIVED, self._on_assistant_text_received)

    def _on_assistant_text_received(self, event: BaseEvent) -> None:
        """Handle assistant.text_received event.

        Args:
            event: The assistant.text_received event.
        """
        if event.event_type != ASSISTANT_TEXT_RECEIVED:
            return

        text = event.payload.get("text")

        # Strict validation: only accept exact str, not subclass
        if type(text) is not str or not text.strip():
            # Invalid payload: silently ignore, no error, no state change
            return

        # In-flight guard: ignore new events while speaking
        with self._lock:
            if self._is_speaking:
                return
            self._is_speaking = True

        # Request SPEAKING state on UI thread immediately
        self._request_state(AppState.SPEAKING, "tts_start")

        # Start worker thread
        thread = threading.Thread(
            target=self._speak_text,
            args=(event.request_id or str(uuid.uuid4()), text),
            daemon=True,
        )
        thread.start()

    def _speak_text(self, request_id: str, text: str) -> None:
        """Worker thread: call provider.speak() and dispatch result events.

        Args:
            request_id: Request ID for tracking.
            text: Text to speak.
        """
        try:
            request = TTSRequest(text=text)
            self._provider.speak(request)
            self._dispatch_state_request(AppState.IDLE, "tts_complete")
        except TTSProviderError:
            self._dispatch_error(request_id, _SAFE_TTS_ERROR_MESSAGE)
            self._dispatch_state_request(AppState.ERROR, "tts_error")
        except Exception:
            self._dispatch_error(request_id, _SAFE_TTS_ERROR_MESSAGE)
            self._dispatch_state_request(AppState.ERROR, "tts_error")
        finally:
            with self._lock:
                self._is_speaking = False

    def _request_state(self, target_state: AppState, reason: str) -> None:
        """Request a state change via event bus (UI thread only).

        Args:
            target_state: The target state to transition to.
            reason: The reason for the state change.
        """
        event = BaseEvent(
            event_type=STATE_CHANGE_REQUESTED,
            request_id=str(uuid.uuid4()),
            source="tts_controller",
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
            source="tts_controller",
            payload={"target_state": target_state.value, "reason": reason},
        )
        self._dispatch_event(event)

    def _dispatch_error(self, request_id: str, message: str) -> None:
        """Dispatch a system error event from worker thread to UI thread.

        Args:
            request_id: The request ID for tracking.
            message: The safe error message (no secrets).
        """
        event = BaseEvent(
            event_type=SYSTEM_ERROR,
            request_id=request_id,
            source="tts_controller",
            payload={"message": message},
        )
        self._dispatch_event(event)
