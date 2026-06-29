r"""Proactive nudge strategy guardrails probe script (V9-C).

Run locally (no Qt, no network, no LLM, no TTS, no memory):
    .venv\Scripts\python.exe scripts\probe_proactive_strategy.py
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.brain.proactive.service import ProactiveNudgeConfig, ProactiveNudgeService


def main() -> None:
    """Run proactive strategy guardrails probe flow."""
    # 1. Create service with quiet hours 23-8 and feedback pause
    config = ProactiveNudgeConfig(
        enabled=True,
        idle_seconds=1,
        cooldown_seconds=10,
        max_per_session=3,
        quiet_hours_enabled=True,
        quiet_start_hour=23,
        quiet_end_hour=8,
        feedback_pause_seconds=3600,
    )
    service = ProactiveNudgeService(config)

    # Use a base date of June 29 2026 (a Monday) to have stable hour testing
    base = datetime(2026, 6, 29, tzinfo=UTC)

    # 2. record_user_activity at 22:00 (not in quiet hours)
    t_22 = base.replace(hour=22, minute=0, second=0, microsecond=0)
    service.record_user_activity(t_22)

    # 3. maybe_create_nudge at 22:00:02 -> should have text
    result1 = service.maybe_create_nudge(now=t_22 + timedelta(seconds=2))
    assert result1 is not None, f"Expected nudge at 22:00, got {result1!r}"
    service.record_nudge_sent(t_22 + timedelta(seconds=2))
    print("[OK] 22:00 - nudge triggered (outside quiet hours)")

    # 4. record_user_activity at 23:00 (in quiet hours)
    t_23 = base.replace(hour=23, minute=0, second=0, microsecond=0)
    service.record_user_activity(t_23)

    # 5. maybe_create_nudge at 23:00:02 -> None (quiet time)
    result2 = service.maybe_create_nudge(now=t_23 + timedelta(seconds=2))
    assert result2 is None, f"Expected None at 23:00 (quiet), got {result2!r}"
    print("[OK] 23:00 - no nudge (quiet hours)")

    # 6. record_user_message with "别打扰" at 10:00 next day
    # (simulated as base + 11 hours = 10:00 next day since 23:00 - 8:00 spans midnight)
    t_10 = base.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(hours=11)
    service.record_user_message("别打扰", now=t_10)

    # 7. maybe_create_nudge at 10:00:02 -> None (paused)
    result3 = service.maybe_create_nudge(now=t_10 + timedelta(seconds=2))
    assert result3 is None, f"Expected None (paused), got {result3!r}"
    print("[OK] 10:00+pause - no nudge (user suppressed)")

    # 8. After 1 hour pause, activity refreshed, can nudge again
    t_11 = t_10 + timedelta(hours=1, seconds=60)  # 11:01
    service.record_user_activity(t_11)  # refresh activity
    result4 = service.maybe_create_nudge(now=t_11 + timedelta(seconds=2))
    assert result4 is not None, f"Expected nudge after pause, got {result4!r}"
    print("[OK] After pause + activity - nudge triggered")

    print("PASS")


if __name__ == "__main__":
    main()
