"""Tests for MicrophoneRecorder."""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import pytest

from app.input.audio.recorder import (
    AudioRecordingError,
    MicrophoneRecorder,
    RecordingRequest,
    RecordingResponse,
)


class TestMicrophoneRecorderValidation:
    """Tests for MicrophoneRecorder parameter validation."""

    def test_negative_duration_raises(self, tmp_path):
        recorder = MicrophoneRecorder()
        request = RecordingRequest(
            duration_seconds=-1.0,
            output_dir=str(tmp_path),
            sample_rate=16000,
            channels=1,
        )
        with pytest.raises(AudioRecordingError, match="duration_seconds must be positive"):
            recorder.record(request)

    def test_zero_duration_raises(self, tmp_path):
        recorder = MicrophoneRecorder()
        request = RecordingRequest(
            duration_seconds=0.0,
            output_dir=str(tmp_path),
            sample_rate=16000,
            channels=1,
        )
        with pytest.raises(AudioRecordingError, match="duration_seconds must be positive"):
            recorder.record(request)

    def test_negative_sample_rate_raises(self, tmp_path):
        recorder = MicrophoneRecorder()
        request = RecordingRequest(
            duration_seconds=1.0,
            output_dir=str(tmp_path),
            sample_rate=-1,
            channels=1,
        )
        with pytest.raises(AudioRecordingError, match="sample_rate must be positive"):
            recorder.record(request)

    def test_zero_sample_rate_raises(self, tmp_path):
        recorder = MicrophoneRecorder()
        request = RecordingRequest(
            duration_seconds=1.0,
            output_dir=str(tmp_path),
            sample_rate=0,
            channels=1,
        )
        with pytest.raises(AudioRecordingError, match="sample_rate must be positive"):
            recorder.record(request)

    def test_invalid_channels_raises(self, tmp_path):
        recorder = MicrophoneRecorder()
        request = RecordingRequest(
            duration_seconds=1.0,
            output_dir=str(tmp_path),
            sample_rate=16000,
            channels=3,
        )
        with pytest.raises(AudioRecordingError, match="channels must be 1 or 2"):
            recorder.record(request)

    def test_zero_channels_raises(self, tmp_path):
        recorder = MicrophoneRecorder()
        request = RecordingRequest(
            duration_seconds=1.0,
            output_dir=str(tmp_path),
            sample_rate=16000,
            channels=0,
        )
        with pytest.raises(AudioRecordingError, match="channels must be 1 or 2"):
            recorder.record(request)


class TestMicrophoneRecorderSuccess:
    """Tests for successful microphone recording."""

    def test_creates_output_dir(self, tmp_path):
        output_dir = tmp_path / "recordings"
        num_frames = int(0.1 * 16000)
        fake_audio_data = np.zeros((num_frames, 1), dtype=np.int16)

        def fake_record(frames, samplerate, channels, dtype):
            return fake_audio_data

        def fake_wait():
            return None

        recorder = MicrophoneRecorder(
            record_func=fake_record,
            wait_func=fake_wait,
            uuid_factory=lambda: "testuuid",
        )
        request = RecordingRequest(
            duration_seconds=0.1,
            output_dir=str(output_dir),
            sample_rate=16000,
            channels=1,
        )
        recorder.record(request)
        assert output_dir.exists()

    def test_creates_wav_file(self, tmp_path):
        output_dir = tmp_path / "recordings"
        num_frames = int(0.1 * 16000)
        fake_audio_data = np.zeros((num_frames, 1), dtype=np.int16)

        def fake_record(frames, samplerate, channels, dtype):
            return fake_audio_data

        def fake_wait():
            return None

        recorder = MicrophoneRecorder(
            record_func=fake_record,
            wait_func=fake_wait,
            uuid_factory=lambda: "testuuid",
        )
        request = RecordingRequest(
            duration_seconds=0.1,
            output_dir=str(output_dir),
            sample_rate=16000,
            channels=1,
        )
        response = recorder.record(request)
        assert Path(response.audio_path).exists()
        assert response.audio_path.endswith(".wav")

    def test_returns_recording_response(self, tmp_path):
        output_dir = tmp_path / "recordings"
        num_frames = int(0.5 * 16000)
        fake_audio_data = np.zeros((num_frames, 2), dtype=np.int16)

        def fake_record(frames, samplerate, channels, dtype):
            return fake_audio_data

        def fake_wait():
            return None

        recorder = MicrophoneRecorder(
            record_func=fake_record,
            wait_func=fake_wait,
            uuid_factory=lambda: "testuuid",
        )
        request = RecordingRequest(
            duration_seconds=0.5,
            output_dir=str(output_dir),
            sample_rate=16000,
            channels=2,
        )
        response = recorder.record(request)

        assert isinstance(response, RecordingResponse)
        assert response.duration_seconds == 0.5
        assert response.sample_rate == 16000
        assert response.channels == 2
        assert response.audio_path.endswith("recording_testuuid.wav")

    def test_wav_file_params(self, tmp_path):
        output_dir = tmp_path / "recordings"
        num_frames = int(0.1 * 44100)
        fake_audio_data = np.zeros((num_frames, 2), dtype=np.int16)

        def fake_record(frames, samplerate, channels, dtype):
            return fake_audio_data

        def fake_wait():
            return None

        recorder = MicrophoneRecorder(
            record_func=fake_record,
            wait_func=fake_wait,
            uuid_factory=lambda: "testuuid",
        )
        request = RecordingRequest(
            duration_seconds=0.1,
            output_dir=str(output_dir),
            sample_rate=44100,
            channels=2,
        )
        response = recorder.record(request)

        with wave.open(response.audio_path, "rb") as wf:
            assert wf.getnchannels() == 2
            assert wf.getframerate() == 44100
            assert wf.getsampwidth() == 2  # 16-bit = 2 bytes


class TestMicrophoneRecorderErrors:
    """Tests for MicrophoneRecorder error handling."""

    def test_record_func_exception_raises(self, tmp_path):
        def failing_record(frames, samplerate, channels, dtype):
            raise RuntimeError("microphone device error")

        recorder = MicrophoneRecorder(
            record_func=failing_record,
            uuid_factory=lambda: "testuuid",
        )
        request = RecordingRequest(
            duration_seconds=1.0,
            output_dir=str(tmp_path),
            sample_rate=16000,
            channels=1,
        )

        with pytest.raises(AudioRecordingError, match="microphone recording failed"):
            recorder.record(request)

    def test_wait_func_exception_raises(self, tmp_path):
        num_frames = int(1.0 * 16000)
        fake_audio_data = np.zeros((num_frames, 1), dtype=np.int16)

        def fake_record(frames, samplerate, channels, dtype):
            return fake_audio_data

        def failing_wait():
            raise RuntimeError("wait failed")

        recorder = MicrophoneRecorder(
            record_func=fake_record,
            wait_func=failing_wait,
            uuid_factory=lambda: "testuuid",
        )
        request = RecordingRequest(
            duration_seconds=1.0,
            output_dir=str(tmp_path),
            sample_rate=16000,
            channels=1,
        )

        with pytest.raises(AudioRecordingError, match="microphone recording failed"):
            recorder.record(request)

    def test_error_message_no_audio_bytes(self, tmp_path):
        def failing_record(frames, samplerate, channels, dtype):
            raise RuntimeError("microphone device error")

        recorder = MicrophoneRecorder(
            record_func=failing_record,
            uuid_factory=lambda: "testuuid",
        )
        request = RecordingRequest(
            duration_seconds=1.0,
            output_dir=str(tmp_path),
            sample_rate=16000,
            channels=1,
        )

        try:
            recorder.record(request)
        except AudioRecordingError as exc:
            error_msg = str(exc)
            # Error message should not contain audio content
            assert "data:audio" not in error_msg
            assert error_msg == "microphone recording failed"
