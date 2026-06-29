"""Proactive nudge service (V9-A / V9-C)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

# Fixed nudge text pool - no LLM, no memory, no emotion pressure
_NUDGE_POOL: tuple[str, ...] = (
    "我还在，想聊的时候直接说就好。",
    "刚刚安静了一会儿，我在这儿。",
    "要不要休息一下眼睛？我可以陪你慢慢聊。",
)

# User phrases that suppress proactive nudges (V9-C)
_SUPPRESS_PHRASES: tuple[str, ...] = (
    "别打扰",
    "不要主动",
    "别主动",
    "安静一会",
    "安静一下",
    "先别说",
    "别说话",
    "不用提醒",
    "先不用",
)


@dataclass(frozen=True)
class ProactiveNudgeConfig:
    """Configuration for proactive nudge."""

    enabled: bool = False
    idle_seconds: int = 300
    cooldown_seconds: int = 1800
    max_per_session: int = 3
    # V9-C: Quiet hours
    quiet_hours_enabled: bool = False
    quiet_start_hour: int = 23
    quiet_end_hour: int = 8
    # V9-C: Feedback pause
    feedback_pause_seconds: int = 3600


class ProactiveNudgeService:
    """Service to determine when to send proactive nudge messages."""

    def __init__(self, config: ProactiveNudgeConfig) -> None:
        self._config = config
        self._last_user_activity: datetime | None = None
        self._last_nudge_sent: datetime | None = None
        self._sent_count: int = 0
        # V9-C: Pause after user feedback
        self._paused_until: datetime | None = None
        # Private override for testing time control
        self._test_now: datetime | None = None

    def record_user_activity(self, now: datetime | None = None) -> None:
        """Record that the user has sent a message or interacted."""
        if now is None:
            now = datetime.now(UTC)
        self._last_user_activity = now

    def record_user_message(self, text: str, now: datetime | None = None) -> None:
        """Record user message and check for suppress phrases.

        Args:
            text: The user's message text.
            now: Optional datetime for testing.
        """
        self.record_user_activity(now)
        if now is None:
            now = datetime.now(UTC)

        # Check if any suppress phrase is in the message
        for phrase in _SUPPRESS_PHRASES:
            if phrase in text:
                self._paused_until = now + timedelta(seconds=self._config.feedback_pause_seconds)
                return

    def record_nudge_sent(self, now: datetime | None = None) -> None:
        """Record that a nudge was sent (to start cooldown)."""
        if now is None:
            now = datetime.now(UTC)
        self._last_nudge_sent = now
        self._sent_count += 1

    def is_quiet_time(self, now: datetime | None = None) -> bool:
        """Check if current time is within quiet hours.

        Args:
            now: Optional datetime for testing.

        Returns:
            True if within quiet hours, False otherwise.
        """
        if not self._config.quiet_hours_enabled:
            return False

        if now is None:
            now = self._test_now or datetime.now(UTC)

        hour = now.hour
        start = self._config.quiet_start_hour
        end = self._config.quiet_end_hour

        if start == end:
            # Full-day quiet
            return True

        if start < end:
            # Normal range, e.g. 9-17
            return start <= hour < end
        else:
            # Cross-midnight range, e.g. 23-8
            return hour >= start or hour < end

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

        if now is None:
            now = self._test_now or datetime.now(UTC)

        # V9-C: Check quiet hours
        if self.is_quiet_time(now):
            return None

        # V9-C: Check paused until
        if self._paused_until is not None and now < self._paused_until:
            return None

        if self._last_user_activity is None:
            return None

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
