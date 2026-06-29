r"""Startup diagnostics probe script (V11-C).

Run locally (no Qt, no network, no LLM, no TTS, no ASR, no memory, no file writes):
    .venv\Scripts\python.exe scripts/probe_startup_diagnostics.py
"""

from __future__ import annotations

import sys


def main() -> None:
    """Run startup diagnostics probe flow."""
    sys.stdout.reconfigure(encoding="utf-8")

    from app.core.config import get_config
    from app.core.startup_diagnostics import run_startup_diagnostics
    from app.ui.startup_diagnostics_view import render_startup_diagnostics_details

    # 1. Default AppConfig should have no errors
    config = get_config()
    diagnostics = run_startup_diagnostics(config)
    assert not diagnostics.has_errors, f"Default config should have no errors, got {diagnostics.issues}"
    print("[OK] Default AppConfig: no errors")

    # 2. Render diagnostics details (should be short OK message)
    details = render_startup_diagnostics_details(diagnostics)
    assert details, "diagnostics details should be non-empty"
    print(f"[OK] render_startup_diagnostics_details: {details!r}")

    # 3. Fake config with warnings and errors
    class FakeConfigWarnings:
        """Fake config that triggers warnings."""

        memory_context_enabled = False
        memory_suggestions_enabled = False
        memory_management_enabled = False
        memory_store_path = ""
        proactive_enabled = False
        proactive_tts_enabled = True  # TTS enabled but proactive not
        proactive_idle_seconds = 300
        proactive_cooldown_seconds = 1800
        proactive_max_per_session = 3
        proactive_quiet_hours_enabled = True
        proactive_quiet_start_hour = 99  # invalid
        proactive_quiet_end_hour = 8
        proactive_feedback_pause_seconds = 3600
        tts_enabled = False
        tts_provider_mode = "fake"

    diag_warn = run_startup_diagnostics(FakeConfigWarnings())
    assert diag_warn.has_warnings, "Should have warnings"
    assert diag_warn.has_errors, "Should have errors (invalid quiet_start_hour)"
    print(f"[OK] FakeConfigWarnings: has_warnings=True, has_errors=True ({len(diag_warn.issues)} issues)")

    # 4. Fake config with no warnings
    class FakeConfigNoWarnings:
        """Fake config with no warnings or errors."""

        memory_context_enabled = False
        memory_suggestions_enabled = False
        memory_management_enabled = False
        memory_store_path = ".tmp/memory.json"
        proactive_enabled = False
        proactive_tts_enabled = False
        proactive_idle_seconds = 300
        proactive_cooldown_seconds = 1800
        proactive_max_per_session = 3
        proactive_quiet_hours_enabled = False
        proactive_quiet_start_hour = 23
        proactive_quiet_end_hour = 8
        proactive_feedback_pause_seconds = 3600
        tts_enabled = False
        tts_provider_mode = "fake"

    diag_ok = run_startup_diagnostics(FakeConfigNoWarnings())
    assert diag_ok.ok, "Should be OK with all defaults off"
    print("[OK] FakeConfigNoWarnings: ok=True")

    # 5. Specific warning: proactive_tts but proactive not enabled
    class FakeProactiveTtsOnly:
        proactive_enabled = False
        proactive_tts_enabled = True
        proactive_idle_seconds = 300
        proactive_cooldown_seconds = 1800
        proactive_max_per_session = 3
        proactive_quiet_hours_enabled = False
        proactive_quiet_start_hour = 23
        proactive_quiet_end_hour = 8
        proactive_feedback_pause_seconds = 3600
        tts_enabled = False
        tts_provider_mode = "fake"

    diag_pt = run_startup_diagnostics(FakeProactiveTtsOnly())
    proactive_tts_warning = next(
        (i for i in diag_pt.issues if "主动陪伴 TTS" in i.message),
        None,
    )
    assert proactive_tts_warning is not None, "Should have proactive_tts warning"
    print(f"[OK] proactive_tts warning: {proactive_tts_warning.message}")

    print("\nPASS")


if __name__ == "__main__":
    main()
