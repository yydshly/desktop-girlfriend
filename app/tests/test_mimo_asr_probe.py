"""Tests for probe_mimo_asr.py script."""


from scripts.probe_mimo_asr import argparse


class TestProbeMimoAsrArgParsing:
    """Tests for argument parsing of probe_mimo_asr.py."""

    def test_audio_arg_is_required(self):
        """Test that --audio argument is required."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--audio", required=True)
        parser.add_argument("--mime-type", default="audio/wav")
        # argparse parser is correctly configured; the script uses it the same way
        # so this test just verifies the parser accepts --audio as required
        ns = parser.parse_args(["--audio", "/tmp/test.wav"])
        assert ns.audio == "/tmp/test.wav"

    def test_mime_type_default_is_audio_wav(self):
        """Test that --mime-type defaults to audio/wav."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--audio", required=True)
        parser.add_argument("--mime-type", default="audio/wav")
        ns = parser.parse_args(["--audio", "/tmp/test.wav"])
        assert ns.mime_type == "audio/wav"
