"""Tests for optional audio dependency boundaries."""

from __future__ import annotations

import subprocess
import sys
import textwrap


def test_voice_input_controller_import_does_not_require_sounddevice() -> None:
    """Importing fake-capable ASR code should not require microphone dependencies."""
    script = textwrap.dedent(
        """
        import builtins

        real_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name == "sounddevice":
                raise ModuleNotFoundError("No module named 'sounddevice'")
            return real_import(name, *args, **kwargs)

        builtins.__import__ = guarded_import

        from app.input.asr.controller import VoiceInputController

        assert VoiceInputController is not None
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr
