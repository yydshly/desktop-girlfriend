"""Tests for QtAudioPlayer."""

from pathlib import Path
from unittest.mock import MagicMock, patch


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

    def test_stop_can_be_called_safely(self) -> None:
        """Test stop() can be called without error even if nothing is playing."""
        with patch("app.expression.tts.player.QMediaPlayer"):
            with patch("app.expression.tts.player.QAudioOutput"):
                from app.expression.tts.player import QtAudioPlayer

                player = QtAudioPlayer()
                player.stop()  # Must not raise
