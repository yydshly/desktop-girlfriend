"""Microphone recording module for ASR file generation."""

from __future__ import annotations

import os
import uuid
import wave
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

import sounddevice


class AudioRecordingError(Exception):
    """Raised when microphone recording fails."""


class MicrophoneRecorderLike(Protocol):
    """Protocol for microphone recorders compatible with VoiceInputController."""

    def record(self, request: RecordingRequest) -> RecordingResponse:
        """Record audio and return the response."""
        ...


@dataclass(frozen=True)
class RecordingRequest:
    """Request to record audio from microphone."""

    duration_seconds: float
    output_dir: str
    sample_rate: int = 16000
    channels: int = 1


@dataclass(frozen=True)
class RecordingResponse:
    """Response from a successful microphone recording."""

    audio_path: str
    duration_seconds: float
    sample_rate: int
    channels: int


class MicrophoneRecorder:
    """Records audio from the system microphone.

    Args:
        record_func: Optional callable for sounddevice.rec. Defaults to real
            sounddevice.rec. Useful for testing without real microphone.
        wait_func: Optional callable for sounddevice.wait. Defaults to real
            sounddevice.wait. Useful for testing.
        uuid_factory: Optional callable to generate UUIDs. Defaults to uuid.uuid4.
            Useful for deterministic test filenames.
    """

    def __init__(
        self,
        record_func: Callable[..., Any] | None = None,
        wait_func: Callable[[], Any] | None = None,
        uuid_factory: Callable[[], str] | None = None,
    ) -> None:
        self._record_func = record_func
        self._wait_func = wait_func
        self._uuid_factory = uuid_factory or uuid.uuid4

    def record(self, request: RecordingRequest) -> RecordingResponse:
        """Record audio from the microphone.

        Args:
            request: Recording parameters.

        Returns:
            RecordingResponse with path and metadata.

        Raises:
            AudioRecordingError: If validation fails or recording encounters an error.
        """
        # Validate parameters
        if request.duration_seconds <= 0:
            raise AudioRecordingError("duration_seconds must be positive")

        if request.sample_rate <= 0:
            raise AudioRecordingError("sample_rate must be positive")

        if request.channels not in {1, 2}:
            raise AudioRecordingError("channels must be 1 or 2")

        # Ensure output directory exists
        try:
            os.makedirs(request.output_dir, exist_ok=True)
        except OSError as exc:
            raise AudioRecordingError("microphone recording failed") from exc

        # Generate output file path
        uuid_val = self._uuid_factory()
        uuid_hex = uuid_val.hex if hasattr(uuid_val, "hex") else str(uuid_val)
        filename = f"recording_{uuid_hex}.wav"
        audio_path = os.path.join(request.output_dir, filename)

        # Record audio
        record_func = self._record_func or sounddevice.rec
        wait_func = self._wait_func or sounddevice.wait

        try:
            audio_data = record_func(
                int(request.duration_seconds * request.sample_rate),
                samplerate=request.sample_rate,
                channels=request.channels,
                dtype="int16",
            )
            wait_func()
        except Exception as exc:
            raise AudioRecordingError("microphone recording failed") from exc

        # Write WAV file using standard library wave module
        try:
            with wave.open(audio_path, "wb") as wf:
                wf.setnchannels(request.channels)
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(request.sample_rate)
                wf.writeframes(audio_data.tobytes())
        except Exception as exc:
            raise AudioRecordingError("microphone recording failed") from exc

        return RecordingResponse(
            audio_path=audio_path,
            duration_seconds=request.duration_seconds,
            sample_rate=request.sample_rate,
            channels=request.channels,
        )
