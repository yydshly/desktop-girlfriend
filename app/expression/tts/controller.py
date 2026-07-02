"""TTS controller for managing text-to-speech playback."""

import logging
import threading
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING

from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGE_REQUESTED,
    SYSTEM_ERROR,
    TTS_AUDIO_READY,
    TTS_PLAYBACK_STATE_CHANGED,
    TTS_STOP_REQUESTED,
    TTS_STOPPED,
    BaseEvent,
)
from app.contracts.states import AppState
from app.expression.tts.providers.base import TTSProvider, TTSProviderError, TTSRequest

if TYPE_CHECKING:
    from app.core.event_bus import EventBus
    from app.expression.tts.player import QtAudioPlayer

logger = logging.getLogger(__name__)

_SAFE_TTS_ERROR_MESSAGE = "语音播放失败，请稍后重试。"
_WORKER_JOIN_TIMEOUT_SECONDS = 0.2


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
        self._is_stopped = False
        self._active_request_id: str | None = None
        self._stop_requested_request_ids: set[str] = set()
        self._worker_thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start listening for assistant text received events."""
        with self._lock:
            self._is_stopped = False
        self._event_bus.subscribe(ASSISTANT_TEXT_RECEIVED, self._on_assistant_text_received)
        self._event_bus.subscribe(TTS_STOP_REQUESTED, self._on_tts_stop_requested)
        if self._audio_player is not None:
            self._event_bus.subscribe(TTS_AUDIO_READY, self._on_audio_ready)

    def stop(self) -> None:
        """Stop listening for assistant text received events."""
        with self._lock:
            self._is_stopped = True
            request_id = self._active_request_id
            if request_id is not None:
                self._stop_requested_request_ids.add(request_id)
                self._active_request_id = None
            self._is_speaking = False
        self._event_bus.unsubscribe(ASSISTANT_TEXT_RECEIVED, self._on_assistant_text_received)
        self._event_bus.unsubscribe(TTS_STOP_REQUESTED, self._on_tts_stop_requested)
        self._stop_provider()
        self._join_worker_thread()
        if self._audio_player is not None:
            self._event_bus.unsubscribe(TTS_AUDIO_READY, self._on_audio_ready)
            self._audio_player.stop()

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
            if self._is_stopped:
                return
            if self._is_speaking:
                self._publish_error(
                    event.request_id,
                    "System busy: speech playback is already in progress.",
                )
                return
            self._is_speaking = True
            self._active_request_id = event.request_id or str(uuid.uuid4())

        # Request SPEAKING state on UI thread immediately
        self._request_state(AppState.SPEAKING, "tts_start")
        self._publish_playback_state(self._active_request_id, "started", text=text)

        # Start worker thread
        thread = threading.Thread(
            target=self._speak_text,
            args=(self._active_request_id, text),
            daemon=True,
        )
        with self._lock:
            self._worker_thread = thread
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
                # Check if stop was requested for this request and clean up the set.
                if self._consume_stopped_request(request_id) or self._should_discard_worker_result():
                    # Stop was requested during synthesize; do not play audio.
                    # stop handler already set _is_speaking=False and _active_request_id=None.
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
                self._dispatch_playback_state(request_id, "playing", text=text)
                self._provider.speak(request)

                # Guard: if this request was stopped, do not dispatch tts_complete
                # or release a different (newer) active request.
                if self._should_ignore_request(request_id) or self._should_discard_worker_result():
                    return

                if self._release_speaking(request_id):
                    self._dispatch_playback_state(request_id, "ended", text=text)
                    self._dispatch_state_request(AppState.IDLE, "tts_complete")
        except TTSProviderError:
            # Silently ignore if request was already stopped
            if self._should_ignore_request(request_id) or self._should_discard_worker_result():
                return
            self._dispatch_playback_state(request_id, "error", message="tts_error", text=text)
            self._dispatch_error(request_id, _SAFE_TTS_ERROR_MESSAGE)
            self._dispatch_state_request(AppState.ERROR, "tts_error")
            self._release_speaking(request_id)
        except Exception:
            # Silently ignore if request was already stopped
            if self._should_ignore_request(request_id) or self._should_discard_worker_result():
                return
            self._dispatch_playback_state(request_id, "error", message="tts_error", text=text)
            self._dispatch_error(request_id, _SAFE_TTS_ERROR_MESSAGE)
            self._dispatch_state_request(AppState.ERROR, "tts_error")
            self._release_speaking(request_id)

    def _on_tts_stop_requested(self, event: BaseEvent) -> None:
        """Handle tts.stop_requested event from UI.

        Args:
            event: The tts.stop_requested event.
        """
        if event.event_type != TTS_STOP_REQUESTED:
            return

        with self._lock:
            if self._is_stopped or not self._is_speaking:
                return
            request_id = self._active_request_id
            if request_id is not None:
                self._stop_requested_request_ids.add(request_id)
                self._active_request_id = None
            self._is_speaking = False

        if self._audio_player is not None:
            self._audio_player.stop()
        self._stop_provider()
        self._join_worker_thread()
        self._dispatch_playback_state(request_id or str(uuid.uuid4()), "interrupted")

        stopped_event = BaseEvent(
            event_type=TTS_STOPPED,
            request_id=request_id or str(uuid.uuid4()),
            source="tts_controller",
            payload={},
        )
        self._dispatch_event(stopped_event)
        self._dispatch_state_request(AppState.IDLE, "tts_stopped")

    def _on_audio_ready(self, event: BaseEvent) -> None:
        """Handle tts.audio_ready event on the UI thread.

        Args:
            event: The tts.audio_ready event containing audio_path.
        """
        if event.event_type != TTS_AUDIO_READY:
            return

        # Ignore if this request was stopped or is stale.
        # Also ignore if _is_speaking is False — stop handler already cleared state.
        with self._lock:
            if self._is_stopped:
                return
            _in_stop = event.request_id in self._stop_requested_request_ids
            _not_active = self._active_request_id != event.request_id
            _not_speaking = not self._is_speaking
            if _not_speaking or _not_active:
                # Clean up stop set only if this specific request was stopped
                # (not just stale — stale requests don't have an entry)
                if _in_stop:
                    self._stop_requested_request_ids.discard(event.request_id)
                return

        audio_path = event.payload.get("audio_path")
        if not audio_path:
            if self._release_speaking(event.request_id):
                self._dispatch_playback_state(event.request_id, "error", message="tts_error")
                self._dispatch_error(event.request_id, _SAFE_TTS_ERROR_MESSAGE)
                self._dispatch_state_request(AppState.ERROR, "tts_error")
            return

        # Callbacks release _is_speaking and dispatch events
        def on_finished() -> None:
            if self._release_speaking(event.request_id):
                self._dispatch_playback_state(event.request_id, "ended")
                self._dispatch_state_request(AppState.IDLE, "tts_complete")

        def on_error(message: str) -> None:
            if self._release_speaking(event.request_id):
                self._dispatch_playback_state(event.request_id, "error", message="tts_error")
                self._dispatch_error(event.request_id, _SAFE_TTS_ERROR_MESSAGE)
                self._dispatch_state_request(AppState.ERROR, "tts_error")

        assert self._audio_player is not None
        try:
            self._dispatch_playback_state(event.request_id, "playing")
            self._audio_player.play(audio_path, on_finished, on_error)
        except Exception:
            # audio_player.play() should not raise, but guard against it
            if self._release_speaking(event.request_id):
                self._dispatch_playback_state(event.request_id, "error", message="tts_error")
                self._dispatch_error(event.request_id, _SAFE_TTS_ERROR_MESSAGE)
                self._dispatch_state_request(AppState.ERROR, "tts_error")

    def _should_ignore_request(self, request_id: str) -> bool:
        """Check if a request should be ignored (stopped or stale).

        Atomically checks if request_id is in the stopped set (and consumes it)
        or is not the current active request. Thread-safe.

        Args:
            request_id: The request ID to check.

        Returns:
            True if the request should be ignored, False otherwise.
        """
        with self._lock:
            if request_id in self._stop_requested_request_ids:
                self._stop_requested_request_ids.discard(request_id)
                return True
            return self._active_request_id != request_id

    def _consume_stopped_request(self, request_id: str) -> bool:
        """Consume (remove) request_id from stopped set if present.

        Used to clean up after confirming a stopped request has been handled.

        Args:
            request_id: The request ID to consume.

        Returns:
            True if request_id was in the stopped set, False otherwise.
        """
        with self._lock:
            if request_id in self._stop_requested_request_ids:
                self._stop_requested_request_ids.discard(request_id)
                return True
            return False

    def _release_speaking(self, request_id: str | None = None) -> bool:
        """Release the _is_speaking flag (thread-safe).

        Args:
            request_id: Optional request ID to verify before releasing.
                       If provided, only releases if request_id matches active request.
                       If None, releases unconditionally (legacy behavior).

        Returns:
            True if released, False if request_id mismatch (guarded release).
        """
        with self._lock:
            if self._is_stopped:
                return False
            if request_id is not None and self._active_request_id != request_id:
                return False
            self._is_speaking = False
            self._active_request_id = None
            if request_id is not None:
                self._stop_requested_request_ids.discard(request_id)
            return True

    def _should_discard_worker_result(self) -> bool:
        """Return True when this controller has been stopped."""
        with self._lock:
            return self._is_stopped

    def _stop_provider(self) -> None:
        """Request provider stop without breaking controller shutdown."""
        try:
            self._provider.stop()
        except Exception:
            logger.exception("TTS provider stop failed")

    def _join_worker_thread(self) -> None:
        """Wait briefly for the current worker thread to finish."""
        with self._lock:
            worker = self._worker_thread
        if worker is not None and worker.is_alive() and worker is not threading.current_thread():
            worker.join(timeout=_WORKER_JOIN_TIMEOUT_SECONDS)

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

    def _publish_error(self, request_id: str, message: str) -> None:
        """Publish a system error event on the event bus."""
        event = BaseEvent(
            event_type=SYSTEM_ERROR,
            request_id=request_id,
            source="tts_controller",
            payload={"message": message},
        )
        self._event_bus.publish(event)

    def _publish_playback_state(
        self,
        request_id: str,
        state: str,
        *,
        text: str = "",
        message: str = "",
    ) -> None:
        """Publish a TTS playback state from the UI thread."""
        self._event_bus.publish(
            self._make_playback_state_event(
                request_id,
                state,
                text=text,
                message=message,
            )
        )

    def _dispatch_playback_state(
        self,
        request_id: str,
        state: str,
        *,
        text: str = "",
        message: str = "",
    ) -> None:
        """Dispatch a TTS playback state from worker callbacks."""
        self._dispatch_event(
            self._make_playback_state_event(
                request_id,
                state,
                text=text,
                message=message,
            )
        )

    @staticmethod
    def _make_playback_state_event(
        request_id: str,
        state: str,
        *,
        text: str = "",
        message: str = "",
    ) -> BaseEvent:
        payload = {
            "state": state,
            "source": "tts_controller",
        }
        if text:
            payload["text"] = text
        if message:
            payload["message"] = message
        return BaseEvent(
            event_type=TTS_PLAYBACK_STATE_CHANGED,
            request_id=request_id,
            source="tts_controller",
            payload=payload,
        )

