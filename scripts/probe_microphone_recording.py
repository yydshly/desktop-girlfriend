#!/usr/bin/env python3
"""Probe script for microphone recording.

Usage:
    python scripts/probe_microphone_recording.py --seconds 3
    python scripts/probe_microphone_recording.py --seconds 3 --output-dir D:\tmp\asr
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

# Load .env before importing app modules
load_dotenv()

from app.core.config import get_config  # noqa: E402
from app.input.audio import AudioRecordingError, MicrophoneRecorder, RecordingRequest  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Record audio from microphone.")
    parser.add_argument(
        "--seconds",
        type=float,
        required=True,
        help="Duration of recording in seconds.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for the recording. Defaults to config value.",
    )
    args = parser.parse_args()

    try:
        config = get_config()
    except Exception as exc:
        print(f"Microphone recording probe failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # Validate duration against max
    if args.seconds > config.asr_recording_max_seconds:
        print(
            f"Microphone recording probe failed: duration exceeds "
            f"ASR_RECORDING_MAX_SECONDS ({config.asr_recording_max_seconds})",
            file=sys.stderr,
        )
        sys.exit(1)

    output_dir = args.output_dir or config.asr_recording_output_dir

    try:
        recorder = MicrophoneRecorder()
        request = RecordingRequest(
            duration_seconds=args.seconds,
            output_dir=output_dir,
            sample_rate=config.asr_recording_sample_rate,
            channels=config.asr_recording_channels,
        )
        response = recorder.record(request)
        print(f"audio_path: {response.audio_path}")
        print(f"duration_seconds: {response.duration_seconds}")
        print(f"sample_rate: {response.sample_rate}")
        print(f"channels: {response.channels}")
    except AudioRecordingError as exc:
        print(f"Microphone recording probe failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
