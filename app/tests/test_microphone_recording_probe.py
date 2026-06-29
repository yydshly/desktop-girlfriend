"""Tests for probe_microphone_recording.py script."""

from __future__ import annotations

import argparse


class TestProbeMicrophoneRecordingArgParsing:
    """Tests for argument parsing of probe_microphone_recording.py."""

    def test_seconds_arg_is_required(self):
        """Test that --seconds argument is required."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--seconds", type=float, required=True)
        parser.add_argument("--output-dir", default=None)
        ns = parser.parse_args(["--seconds", "3.0"])
        assert ns.seconds == 3.0

    def test_output_dir_is_optional(self):
        """Test that --output-dir is optional."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--seconds", type=float, required=True)
        parser.add_argument("--output-dir", default=None)
        ns = parser.parse_args(["--seconds", "3.0"])
        assert ns.output_dir is None

    def test_output_dir_with_value(self):
        """Test that --output-dir accepts a value."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--seconds", type=float, required=True)
        parser.add_argument("--output-dir", default=None)
        ns = parser.parse_args(["--seconds", "3.0", "--output-dir", "/tmp/rec"])
        assert ns.output_dir == "/tmp/rec"
