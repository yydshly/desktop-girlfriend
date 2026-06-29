"""Proactive nudge service (V9-A)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

# Fixed nudge text pool - no LLM, no memory, no emotion pressure
_NUDGE_POOL: tuple[str, ...] = (
    "我还在，想聊的时候直接说就好。",
    "刚刚安静了一会儿，我在这儿。",
    "要不要休息一下眼睛？我可以陪你慢慢聊。",
)


@dataclass(frozen=True)
class ProactiveNudgeConfig:
    """Configuration for proactive nudge."""

    enabled: bool = False
    idle_seconds: int = 300
    cooldown_seconds: int = 1800
    max_per_session: int = 3


class ProactiveNudgeService:
    """Service to determine when to send proactive nudge messages."""

    def __init__(self, config: ProactiveNudgeConfig) -> None:
        self._config = config
        self._last_user_activity: datetime | None = None
        self._last_nudge_sent: datetime | None = None
        self._sent_count: int = 0
        # Private override for testing time control
        self._test_now: datetime | None = None

    def record_user_activity(self, now: datetime | None = None) -> None:
        """Record that the user has sent a message or interacted."""
        if now is None:
            now = datetime.now(UTC)
        self._last_user_activity = now

    def record_nudge_sent(self, now: datetime | None = None) -> None:
        """Record that a nudge was sent (to start cooldown)."""
        if now is None:
            now = datetime.now(UTC)
        self._last_nudge_sent = now
        self._sent_count += 1

    def maybe_create_nudge(
        self,
        *,
        now: datetime | None = None,
        is_busy: bool = False,
    ) -> str | None:
        """Check if a proactive nudge should be created.

        Returns:
            A nudge text string if conditions are met, otherwise None.
        """
        if not self._config.enabled:
            return None

        if is_busy:
            return None

        if self._last_user_activity is None:
            return None

        if now is None:
            now = self._test_now or datetime.now(UTC)

        # Check idle time
        idle_elapsed = (now - self._last_user_activity).total_seconds()
        if idle_elapsed < self._config.idle_seconds:
            return None

        # Check cooldown (if we've sent at least one nudge)
        if self._last_nudge_sent is not None:
            cooldown_elapsed = (now - self._last_nudge_sent).total_seconds()
            if cooldown_elapsed < self._config.cooldown_seconds:
                return None

        # Check max per session
        if self._sent_count >= self._config.max_per_session:
            return None

        # Return a fixed nudge text
        idx = self._sent_count % len(_NUDGE_POOL)
        return _NUDGE_POOL[idx]
