r"""Proactive nudge probe script (V9-A).

Run locally (no Qt, no network, no LLM, no TTS, no memory):
    .venv\Scripts\python.exe scripts\probe_proactive_nudge.py
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.brain.proactive.service import ProactiveNudgeConfig, ProactiveNudgeService


def main() -> None:
    """Run proactive nudge probe flow."""
    # 1. Create service with short timeouts for fast probe
    config = ProactiveNudgeConfig(
        enabled=True,
        idle_seconds=1,
        cooldown_seconds=10,
        max_per_session=1,
    )
    service = ProactiveNudgeService(config)

    # 2. Record user activity at t0
    t0 = datetime.now(UTC)
    service.record_user_activity(t0)

    # 3. t0 + 0.5s -> should be None (idle not reached)
    t05 = t0 + timedelta(seconds=0.5)
    result1 = service.maybe_create_nudge(now=t05)
    assert result1 is None, f"Expected None at 0.5s, got {result1!r}"

    # 4. t0 + 2s -> should return text (idle reached)
    t2 = t0 + timedelta(seconds=2)
    result2 = service.maybe_create_nudge(now=t2)
    assert result2 is not None, "Expected nudge text at 2s"
    print(f"[OK] Nudge triggered at 2s: {result2!r}")

    # 5. Record nudge sent
    service.record_nudge_sent(t2)

    # 6. t0 + 3s -> should be None (cooldown not reached AND max_per_session=1 reached)
    t3 = t0 + timedelta(seconds=3)
    result3 = service.maybe_create_nudge(now=t3)
    assert result3 is None, f"Expected None at 3s (cooldown/max), got {result3!r}"

    print("PASS")


if __name__ == "__main__":
    main()
