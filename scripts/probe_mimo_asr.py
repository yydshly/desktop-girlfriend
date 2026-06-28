#!/usr/bin/env python3
"""Probe script for MiMo ASR file recognition.

Usage:
    python scripts/probe_mimo_asr.py --audio path/to/sample.wav
    python scripts/probe_mimo_asr.py --audio path/to/sample.wav --mime-type audio/wav
"""

from __future__ import annotations

import argparse
import sys
import time

from dotenv import load_dotenv

# Load .env before importing app modules
load_dotenv()

from app.core.config import get_config  # noqa: E402
from app.input.asr.providers import ASRProviderError, ASRRequest, create_asr_provider  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe MiMo ASR with a local audio file.")
    parser.add_argument(
        "--audio",
        required=True,
        help="Path to the audio file to recognize.",
    )
    parser.add_argument(
        "--mime-type",
        default="audio/wav",
        help="MIME type of the audio file. Defaults to audio/wav.",
    )
    args = parser.parse_args()

    try:
        config = get_config()
        provider = create_asr_provider(config)
    except ASRProviderError as exc:
        print(f"MiMo ASR probe failed: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        start = time.monotonic()
        response = provider.recognize(
            ASRRequest(audio_path=args.audio, mime_type=args.mime_type)
        )
        latency_ms = round((time.monotonic() - start) * 1000)
        print(f"recognized_text: {response.text}")
        print(f"latency_ms: {latency_ms}")
    except ASRProviderError as exc:
        print(f"MiMo ASR probe failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
