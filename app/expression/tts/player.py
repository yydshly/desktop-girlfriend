"""Qt-based audio player for embedded TTS playback."""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

_SAFE_PLAYBACK_ERROR = "Audio playback failed"

# Capture enum values once at module level so they remain valid even when
# QMediaPlayer is replaced by a mock in tests.
_MEDIA_END_OF_MEDIA = QMediaPlayer.MediaStatus.EndOfMedia


class QtAudioPlayer:
    """Audio player using QMediaPlayer for embedded playback."""

    def __init__(self) -> None:
        """Initialize the audio player with QMediaPlayer and QAudioOutput."""
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._on_finished: Callable[[], None] | None = None
        self._on_error: Callable[[str], None] | None = None
        self._is_playing = False
        # Set to True when stop() is called, to suppress spurious callbacks
        self._manual_stop_requested = False

        self._player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._player.errorOccurred.connect(self._on_error_occurred)

    @property
    def is_playing(self) -> bool:
        """Return True if audio is currently playing."""
        return self._is_playing

    def play(
        self,
        path: str,
        on_finished: Callable[[], None],
        on_error: Callable[[str], None],
    ) -> None:
        """Play the audio file at the given path.

        Args:
            path: Path to the audio file to play.
            on_finished: Callback invoked when playback finishes successfully.
            on_error: Callback invoked when playback fails.
        """
        audio_path = Path(path)
        if not audio_path.exists():
            on_error(_SAFE_PLAYBACK_ERROR)
            return

        self._on_finished = on_finished
        self._on_error = on_error
        self._is_playing = True
        self._manual_stop_requested = False

        self._player.setSource(QUrl.fromLocalFile(str(audio_path.resolve())))
        self._player.play()

    def stop(self) -> bool:
        """Stop any currently playing audio.

        Returns:
            True if audio was playing and has been stopped, False otherwise.
            Does NOT trigger on_finished or on_error callbacks.
        """
        self._manual_stop_requested = True

        if not self._is_playing:
            try:
                self._player.stop()
            except Exception:
                pass
            self._on_finished = None
            self._on_error = None
            return False

        self._is_playing = False
        try:
            self._player.stop()
        except Exception:
            pass
        self._on_finished = None
        self._on_error = None
        return True

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """Handle playback state changes.

        This is no longer the primary mechanism for detecting playback completion.
        StoppedState can occur for many reasons (manual stop, source change, etc.)
        and is not a reliable indicator of natural playback end.

        Args:
            state: The new playback state.
        """
        # No-op: completion is detected via mediaStatusChanged(EndOfMedia)

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        """Handle media status changes.

        Detects natural playback end via EndOfMedia status.

        Args:
            status: The new media status.
        """
        if not self._is_playing:
            return

        if self._manual_stop_requested:
            return

        if status == _MEDIA_END_OF_MEDIA:
            self._is_playing = False
            callback = self._on_finished
            self._on_finished = None
            self._on_error = None
            if callback is not None:
                callback()

    def _on_error_occurred(
        self, error: QMediaPlayer.Error, error_string: str
    ) -> None:
        """Handle playback errors.

        Args:
            error: The error code.
            error_string: Human-readable error description.
        """
        if not self._is_playing:
            return

        if self._manual_stop_requested:
            return

        self._is_playing = False
        callback = self._on_error
        self._on_finished = None
        self._on_error = None
        if callback is not None:
            callback(_SAFE_PLAYBACK_ERROR)
