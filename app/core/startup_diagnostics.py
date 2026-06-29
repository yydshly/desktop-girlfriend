"""Startup diagnostics for configuration validation (V11-C)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class StartupDiagnosticLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class StartupDiagnosticIssue:
    """A single diagnostic issue found during startup."""

    level: StartupDiagnosticLevel
    message: str


@dataclass(frozen=True)
class StartupDiagnostics:
    """Collection of startup diagnostic issues."""

    issues: tuple[StartupDiagnosticIssue, ...]

    @property
    def has_errors(self) -> bool:
        """Return True if any issue is an error."""
        return any(issue.level == StartupDiagnosticLevel.ERROR for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        """Return True if any issue is a warning."""
        return any(issue.level == StartupDiagnosticLevel.WARNING for issue in self.issues)

    @property
    def ok(self) -> bool:
        """Return True if there are no errors and no warnings."""
        return not self.has_errors and not self.has_warnings


def run_startup_diagnostics(config: object) -> StartupDiagnostics:
    """Run startup diagnostics on the given config object.

    Args:
        config: An object with configuration attributes. Uses getattr with defaults
                to avoid tight coupling to specific config class fields.

    Returns:
        A StartupDiagnostics object containing any issues found.
    """
    issues: list[StartupDiagnosticIssue] = []

    # Check: memory enabled but store path empty
    memory_context = getattr(config, "memory_context_enabled", False)
    memory_suggestions = getattr(config, "memory_suggestions_enabled", False)
    memory_management = getattr(config, "memory_management_enabled", False)
    memory_any_enabled = memory_context or memory_suggestions or memory_management
    memory_store_path = getattr(config, "memory_store_path", "")
    if memory_any_enabled and (not memory_store_path or not memory_store_path.strip()):
        issues.append(
            StartupDiagnosticIssue(
                level=StartupDiagnosticLevel.WARNING,
                message="记忆功能已开启，但 MEMORY_STORE_PATH 为空",
            )
        )

    # Check: proactive_tts_enabled but proactive not enabled
    proactive_tts = getattr(config, "proactive_tts_enabled", False)
    proactive_enabled = getattr(config, "proactive_enabled", False)
    if proactive_tts and not proactive_enabled:
        issues.append(
            StartupDiagnosticIssue(
                level=StartupDiagnosticLevel.WARNING,
                message="主动陪伴 TTS 已开启，但主动陪伴未开启",
            )
        )

    # Check: proactive_tts but TTS not enabled (config may not have tts_enabled)
    tts_enabled = getattr(config, "tts_enabled", False)
    tts_provider_mode = getattr(config, "tts_provider_mode", "fake")
    tts_actually_enabled = tts_enabled or tts_provider_mode != "fake"
    if proactive_tts and not tts_actually_enabled:
        issues.append(
            StartupDiagnosticIssue(
                level=StartupDiagnosticLevel.WARNING,
                message="主动陪伴 TTS 已开启，但 TTS 未启用",
            )
        )

    # Check: quiet hours hours range validity
    quiet_hours_enabled = getattr(config, "proactive_quiet_hours_enabled", False)
    if quiet_hours_enabled:
        quiet_start = getattr(config, "proactive_quiet_start_hour", 0)
        quiet_end = getattr(config, "proactive_quiet_end_hour", 8)
        if not (0 <= quiet_start <= 23):
            issues.append(
                StartupDiagnosticIssue(
                    level=StartupDiagnosticLevel.ERROR,
                    message=f"PROACTIVE_QUIET_START_HOUR={quiet_start} 超出有效范围 0..23",
                )
            )
        if not (0 <= quiet_end <= 23):
            issues.append(
                StartupDiagnosticIssue(
                    level=StartupDiagnosticLevel.ERROR,
                    message=f"PROACTIVE_QUIET_END_HOUR={quiet_end} 超出有效范围 0..23",
                )
            )

    # Check: negative proactive parameters
    idle_seconds = getattr(config, "proactive_idle_seconds", 300)
    if isinstance(idle_seconds, (int, float)) and idle_seconds < 0:
        issues.append(
            StartupDiagnosticIssue(
                level=StartupDiagnosticLevel.ERROR,
                message=f"PROACTIVE_IDLE_SECONDS={idle_seconds} 不能为负数",
            )
        )

    cooldown_seconds = getattr(config, "proactive_cooldown_seconds", 1800)
    if isinstance(cooldown_seconds, (int, float)) and cooldown_seconds < 0:
        issues.append(
            StartupDiagnosticIssue(
                level=StartupDiagnosticLevel.ERROR,
                message=f"PROACTIVE_COOLDOWN_SECONDS={cooldown_seconds} 不能为负数",
            )
        )

    max_per_session = getattr(config, "proactive_max_per_session", 3)
    if isinstance(max_per_session, int) and max_per_session < 0:
        issues.append(
            StartupDiagnosticIssue(
                level=StartupDiagnosticLevel.ERROR,
                message=f"PROACTIVE_MAX_PER_SESSION={max_per_session} 不能为负数",
            )
        )

    feedback_pause = getattr(config, "proactive_feedback_pause_seconds", 3600)
    if isinstance(feedback_pause, (int, float)) and feedback_pause < 0:
        issues.append(
            StartupDiagnosticIssue(
                level=StartupDiagnosticLevel.ERROR,
                message=f"PROACTIVE_FEEDBACK_PAUSE_SECONDS={feedback_pause} 不能为负数",
            )
        )

    return StartupDiagnostics(issues=tuple(issues))
