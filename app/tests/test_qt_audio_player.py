"""Tests for QtAudioPlayer."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtMultimedia import QMediaPlayer


class TestQtAudioPlayerConstruction:
    """Tests for QtAudioPlayer construction."""

    def test_can_be_constructed(self) -> None:
        """Test QtAudioPlayer can be constructed without error."""
        with patch("app.expression.tts.player.QMediaPlayer") as mock_player:
            with patch("app.expression.tts.player.QAudioOutput") as mock_output:
                from app.expression.tts.player import QtAudioPlayer

                QtAudioPlayer()
                mock_player.assert_called_once()
                mock_output.assert_called_once()

    def test_player_has_audio_output(self) -> None:
        """Test QMediaPlayer has audioOutput set."""
        with patch("app.expression.tts.player.QMediaPlayer") as mock_player_cls:
            mock_player = MagicMock()
            mock_player_cls.return_value = mock_player
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                QtAudioPlayer()
                mock_player.setAudioOutput.assert_called_once()


class TestQtAudioPlayerPlay:
    """Tests for QtAudioPlayer.play()."""

    def test_play_rejects_missing_file(self, tmp_path: Path) -> None:
        """Test play() calls on_error when file does not exist."""
        with patch("app.expression.tts.player.QMediaPlayer"):
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                on_finished = MagicMock()
                on_error = MagicMock()

                player.play(
                    str(tmp_path / "nonexistent.mp3"),
                    on_finished=on_finished,
                    on_error=on_error,
                )

                on_error.assert_called_once()
                on_finished.assert_not_called()
                # Error message must be safe (no file path)
                error_msg = on_error.call_args[0][0]
                assert "nonexistent" not in error_msg

    def test_play_sets_source_for_existing_file(self, tmp_path: Path) -> None:
        """Test play() sets source on QMediaPlayer for existing file."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        with patch("app.expression.tts.player.QMediaPlayer") as mock_player_cls:
            mock_player = MagicMock()
            mock_player_cls.return_value = mock_player
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                on_finished = MagicMock()
                on_error = MagicMock()

                player.play(str(audio_file), on_finished=on_finished, on_error=on_error)

                mock_player.setSource.assert_called_once()
                mock_player.play.assert_called_once()


class TestQtAudioPlayerStop:
    """Tests for QtAudioPlayer.stop()."""

    def test_stop_returns_false_when_not_playing(self) -> None:
        """Test stop() returns False when not playing."""
        with patch("app.expression.tts.player.QMediaPlayer"):
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                assert player.stop() is False

    def test_stop_returns_true_when_playing(self, tmp_path: Path) -> None:
        """Test stop() returns True when playing."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        with patch("app.expression.tts.player.QMediaPlayer") as mock_player_cls:
            mock_player = MagicMock()
            mock_player_cls.return_value = mock_player
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                on_finished = MagicMock()
                on_error = MagicMock()
                player.play(str(audio_file), on_finished=on_finished, on_error=on_error)

                assert player.stop() is True
                on_finished.assert_not_called()
                on_error.assert_not_called()

    def test_stop_clears_callbacks(self, tmp_path: Path) -> None:
        """Test stop() clears on_finished and on_error callbacks."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        with patch("app.expression.tts.player.QMediaPlayer") as mock_player_cls:
            mock_player = MagicMock()
            mock_player_cls.return_value = mock_player
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                on_finished = MagicMock()
                on_error = MagicMock()
                player.play(str(audio_file), on_finished=on_finished, on_error=on_error)
                player.stop()

                # Callbacks should be cleared (calling them should have no effect)
                # This is implicitly tested by stop() not calling them
                assert player._on_finished is None
                assert player._on_error is None

    def test_stop_does_not_call_on_finished(self, tmp_path: Path) -> None:
        """Test stop() does not trigger on_finished callback."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        with patch("app.expression.tts.player.QMediaPlayer") as mock_player_cls:
            mock_player = MagicMock()
            mock_player_cls.return_value = mock_player
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                on_finished = MagicMock()
                on_error = MagicMock()
                player.play(str(audio_file), on_finished=on_finished, on_error=on_error)
                player.stop()

                on_finished.assert_not_called()
                on_error.assert_not_called()

    def test_stop_can_be_called_twice_safely(self, tmp_path: Path) -> None:
        """Test stop() can be called twice without error."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        with patch("app.expression.tts.player.QMediaPlayer") as mock_player_cls:
            mock_player = MagicMock()
            mock_player_cls.return_value = mock_player
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                on_finished = MagicMock()
                on_error = MagicMock()
                player.play(str(audio_file), on_finished=on_finished, on_error=on_error)

                result1 = player.stop()
                result2 = player.stop()

                assert result1 is True
                assert result2 is False
                on_finished.assert_not_called()
                on_error.assert_not_called()

    def test_is_playing_reflects_flag(self, tmp_path: Path) -> None:
        """Test is_playing property reflects current playing state."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        with patch("app.expression.tts.player.QMediaPlayer") as mock_player_cls:
            mock_player = MagicMock()
            mock_player_cls.return_value = mock_player
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                assert player.is_playing is False

                on_finished = MagicMock()
                on_error = MagicMock()
                player.play(str(audio_file), on_finished=on_finished, on_error=on_error)
                assert player.is_playing is True

                player.stop()
                assert player.is_playing is False


class TestQtAudioPlayerCompletionDetection:
    """Tests for playback completion detection via mediaStatusChanged."""

    def test_stopped_state_does_not_trigger_on_finished(self, tmp_path: Path) -> None:
        """Test that StoppedState from playbackStateChanged does not trigger on_finished.

        StoppedState can occur for many reasons (initialization, source change, etc.)
        and is not a reliable indicator of natural playback end.
        """
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        with patch("app.expression.tts.player.QMediaPlayer") as mock_player_cls:
            mock_player = MagicMock()
            mock_player_cls.return_value = mock_player
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                on_finished = MagicMock()
                on_error = MagicMock()
                player.play(str(audio_file), on_finished=on_finished, on_error=on_error)

                # Simulate a StoppedState (e.g. during initialization or source change)
                # This should NOT trigger on_finished
                player._on_playback_state_changed(
                    QMediaPlayer.PlaybackState.StoppedState
                )

                on_finished.assert_not_called()
                on_error.assert_not_called()
                assert player.is_playing is True

    def test_end_of_media_after_manual_stop_is_ignored(self, tmp_path: Path) -> None:
        """Test that EndOfMedia after stop() does not trigger on_finished."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        with patch("app.expression.tts.player.QMediaPlayer") as mock_player_cls:
            mock_player = MagicMock()
            mock_player_cls.return_value = mock_player
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                on_finished = MagicMock()
                on_error = MagicMock()
                player.play(str(audio_file), on_finished=on_finished, on_error=on_error)
                player.stop()

                # EndOfMedia arrives after manual stop — should be ignored
                player._on_media_status_changed(QMediaPlayer.MediaStatus.EndOfMedia)

                on_finished.assert_not_called()
                on_error.assert_not_called()

    def test_error_after_manual_stop_is_ignored(self, tmp_path: Path) -> None:
        """Test that error after stop() does not trigger on_error."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        with patch("app.expression.tts.player.QMediaPlayer") as mock_player_cls:
            mock_player = MagicMock()
            mock_player_cls.return_value = mock_player
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                on_finished = MagicMock()
                on_error = MagicMock()
                player.play(str(audio_file), on_finished=on_finished, on_error=on_error)
                player.stop()

                # Error arrives after manual stop — should be ignored
                player._on_error_occurred(QMediaPlayer.Error.NoError, "some error")

                on_finished.assert_not_called()
                on_error.assert_not_called()

    def test_error_triggers_on_error(self, tmp_path: Path) -> None:
        """Test that playback error triggers on_error callback."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        with patch("app.expression.tts.player.QMediaPlayer") as mock_player_cls:
            mock_player = MagicMock()
            mock_player_cls.return_value = mock_player
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                on_finished = MagicMock()
                on_error = MagicMock()
                player.play(str(audio_file), on_finished=on_finished, on_error=on_error)

                # Simulate playback error
                player._on_error_occurred(QMediaPlayer.Error.ResourceError, "resource error")

                on_error.assert_called_once()
                # Error message must be safe (no internal details)
                error_msg = on_error.call_args[0][0]
                assert error_msg == "Audio playback failed"
                on_finished.assert_not_called()
                assert player.is_playing is False

    def test_stop_does_not_raise(self, tmp_path: Path) -> None:
        """Test that stop() does not raise even if player.stop() raises."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        with patch("app.expression.tts.player.QMediaPlayer") as mock_player_cls:
            mock_player = MagicMock()
            mock_player.side_effect = Exception("player error")
            mock_player_cls.return_value = mock_player
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                on_finished = MagicMock()
                on_error = MagicMock()
                player.play(str(audio_file), on_finished=on_finished, on_error=on_error)

                # stop() should not raise
                result = player.stop()

                assert result is True
                on_finished.assert_not_called()
                on_error.assert_not_called()

    def test_end_of_media_when_not_playing_is_ignored(self, tmp_path: Path) -> None:
        """Test that EndOfMedia when not playing does not trigger on_finished."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake mp3 data")

        with patch("app.expression.tts.player.QMediaPlayer") as mock_player_cls:
            mock_player = MagicMock()
            mock_player_cls.return_value = mock_player
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                on_finished = MagicMock()
                on_error = MagicMock()

                # EndOfMedia arrives before play — should be ignored
                player._on_media_status_changed(QMediaPlayer.MediaStatus.EndOfMedia)

                on_finished.assert_not_called()
                on_error.assert_not_called()
