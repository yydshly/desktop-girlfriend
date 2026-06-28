"""TTS controller for managing text-to-speech playback."""

import threading
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING

from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGE_REQUESTED,
    SYSTEM_ERROR,
    TTS_AUDIO_READY,
    TTS_STOP_REQUESTED,
    BaseEvent,
)
from app.contracts.states import AppState
from app.expression.tts.providers.base import TTSProvider, TTSProviderError, TTSRequest

if TYPE_CHECKING:
    from app.core.event_bus import EventBus
    from app.expression.tts.player import QtAudioPlayer

_SAFE_TTS_ERROR_MESSAGE = "语音播放失败，请稍后重试。"


class TTSController:
    """Manages TTS playback in response to assistant text events."""

    def __init__(
        self,
        event_bus: "EventBus",
        provider: TTSProvider,
        dispatch_event: Callable[[BaseEvent], None],
        audio_player: "QtAudioPlayer | None" = None,
    ) -> None:
        """Initialize TTSController.

        Args:
            event_bus: Event bus for subscribing to events.
            provider: TTS provider for speech synthesis and playback.
            dispatch_event: Callback to dispatch events back to UI thread safely.
            audio_player: Optional QtAudioPlayer for embedded playback.
                When provided, synthesize() is used instead of speak() and
                audio is played internally via QtMediaPlayer.
        """
        self._event_bus = event_bus
        self._provider = provider
        self._dispatch_event = dispatch_event
        self._audio_player = audio_player
        self._is_speaking = False
        self._active_request_id: str | None = None
        self._stop_requested_request_ids: set[str] = set()
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start listening for assistant text received events."""
        self._event_bus.subscribe(ASSISTANT_TEXT_RECEIVED, self._on_assistant_text_received)
        self._event_bus.subscribe(TTS_STOP_REQUESTED, self._on_tts_stop_requested)
        if self._audio_player is not None:
            self._event_bus.subscribe(TTS_AUDIO_READY, self._on_audio_ready)

    def stop(self) -> None:
        """Stop listening for assistant text received events."""
        self._event_bus.unsubscribe(ASSISTANT_TEXT_RECEIVED, self._on_assistant_text_received)
        self._event_bus.unsubscribe(TTS_STOP_REQUESTED, self._on_tts_stop_requested)
        if self._audio_player is not None:
            self._event_bus.unsubscribe(TTS_AUDIO_READY, self._on_audio_ready)

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
            self._active_request_id = event.request_id or str(uuid.uuid4())

        # Request SPEAKING state on UI thread immediately
        self._request_state(AppState.SPEAKING, "tts_start")

        # Start worker thread
        thread = threading.Thread(
            target=self._speak_text,
            args=(self._active_request_id, text),
            daemon=True,
        )
        thread.start()

    def _speak_text(self, request_id: str, text: str) -> None:
        """Worker thread: synthesize audio and dispatch to UI thread for playback.

        Args:
            request_id: Request ID for tracking.
            text: Text to speak.
        """
        # Determine which path to use: embedded playback requires both audio_player
        # and a provider that supports audio_path playback (not FakeTTSProvider)
        use_embedded = (
            self._audio_player is not None
            and self._provider.supports_audio_path_playback
        )

        try:
            request = TTSRequest(text=text)

            if use_embedded:
                # Embedded path: synthesize audio file, play via QtAudioPlayer
                response = self._provider.synthesize(request)
                # Check if stop was requested for this request
                with self._lock:
                    stopped = request_id in self._stop_requested_request_ids
                    if stopped:
                        self._stop_requested_request_ids.discard(request_id)
                if stopped:
                    # Stop was requested during synthesize; do not play audio
                    self._release_speaking()
                    return

                if response.audio_path is None:
                    raise TTSProviderError("TTS returned empty audio path")
                # Dispatch audio_ready event to UI thread to trigger playback
                audio_event = BaseEvent(
                    event_type=TTS_AUDIO_READY,
                    request_id=request_id,
                    source="tts_controller",
                    payload={"audio_path": response.audio_path},
                )
                self._dispatch_event(audio_event)
                # Do NOT release _is_speaking here — wait for playback to finish
            else:
                # Legacy path: provider.speak() handles playback (e.g. os.startfile)
                self._provider.speak(request)
                self._dispatch_state_request(AppState.IDLE, "tts_complete")
                self._release_speaking()
        except TTSProviderError:
            self._dispatch_error(request_id, _SAFE_TTS_ERROR_MESSAGE)
            self._dispatch_state_request(AppState.ERROR, "tts_error")
            self._release_speaking()
        except Exception:
            self._dispatch_error(request_id, _SAFE_TTS_ERROR_MESSAGE)
            self._dispatch_state_request(AppState.ERROR, "tts_error")
            self._release_speaking()

    def _on_tts_stop_requested(self, event: BaseEvent) -> None:
        """Handle tts.stop_requested event from UI.

        Args:
            event: The tts.stop_requested event.
        """
        if event.event_type != TTS_STOP_REQUESTED:
            return

        with self._lock:
            if not self._is_speaking:
                return
            request_id = self._active_request_id
            if request_id is not None:
                self._stop_requested_request_ids.add(request_id)
                self._active_request_id = None
            self._is_speaking = False

        if self._audio_player is not None:
            self._audio_player.stop()

        self._dispatch_state_request(AppState.IDLE, "tts_stopped")

    def _on_audio_ready(self, event: BaseEvent) -> None:
        """Handle tts.audio_ready event on the UI thread.

        Args:
            event: The tts.audio_ready event containing audio_path.
        """
        if event.event_type != TTS_AUDIO_READY:
            return

        audio_path = event.payload.get("audio_path")
        if not audio_path:
            self._release_speaking()
            self._dispatch_error(event.request_id, _SAFE_TTS_ERROR_MESSAGE)
            self._dispatch_state_request(AppState.ERROR, "tts_error")
            return

        # Callbacks release _is_speaking and dispatch events
        def on_finished() -> None:
            self._release_speaking()
            self._dispatch_state_request(AppState.IDLE, "tts_complete")

        def on_error(message: str) -> None:
            self._release_speaking()
            self._dispatch_error(event.request_id, _SAFE_TTS_ERROR_MESSAGE)
            self._dispatch_state_request(AppState.ERROR, "tts_error")

        assert self._audio_player is not None
        try:
            self._audio_player.play(audio_path, on_finished, on_error)
        except Exception:
            # audio_player.play() should not raise, but guard against it
            self._release_speaking()
            self._dispatch_error(event.request_id, _SAFE_TTS_ERROR_MESSAGE)
            self._dispatch_state_request(AppState.ERROR, "tts_error")

    def _release_speaking(self) -> None:
        """Release the _is_speaking flag (thread-safe)."""
        with self._lock:
            self._is_speaking = False
            self._active_request_id = None

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

