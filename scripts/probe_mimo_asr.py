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
from pathlib import Path

from dotenv import load_dotenv

# Load .env before importing app modules
load_dotenv()

from app.core.config import get_config  # noqa: E402
from app.input.asr.providers import ASRProviderError, ASRRequest, create_asr_provider  # noqa: E402


def infer_mime_type(audio_path: str) -> str:
    """Infer MIME type from audio file extension.

    Args:
        audio_path: Path to the audio file.

    Returns:
        The inferred MIME type.

    Raises:
        ASRProviderError: If the file extension is not supported.
    """
    suffix = Path(audio_path).suffix.lower()
    if suffix == ".wav":
        return "audio/wav"
    if suffix == ".mp3":
        return "audio/mpeg"
    raise ASRProviderError("unsupported audio file type")


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe MiMo ASR with a local audio file.")
    parser.add_argument(
        "--audio",
        required=True,
        help="Path to the audio file to recognize.",
    )
    parser.add_argument(
        "--mime-type",
        default=None,
        help="MIME type of the audio file. If omitted, inferred from extension.",
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
        mime_type = args.mime_type or infer_mime_type(args.audio)
        response = provider.recognize(
            ASRRequest(audio_path=args.audio, mime_type=mime_type)
        )
        latency_ms = round((time.monotonic() - start) * 1000)
        print(f"recognized_text: {response.text}")
        print(f"latency_ms: {latency_ms}")
    except ASRProviderError as exc:
        print(f"MiMo ASR probe failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
