"""Tests for startup diagnostics (V11-C)."""

from __future__ import annotations

from app.core.startup_diagnostics import (
    StartupDiagnosticIssue,
    StartupDiagnosticLevel,
    StartupDiagnostics,
    run_startup_diagnostics,
)
from app.ui.startup_diagnostics_view import (
    render_startup_diagnostics_details,
    render_startup_diagnostics_summary,
)


class FakeConfigDefault:
    """Minimal config with default safe values."""
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


class FakeConfigProactiveTtsNoProactive:
    """Config with proactive_tts=true but proactive=false."""
    memory_context_enabled = False
    memory_suggestions_enabled = False
    memory_management_enabled = False
    memory_store_path = ""
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


class FakeConfigProactiveTtsNoTts:
    """Config with proactive_tts=true but TTS not enabled."""
    memory_context_enabled = False
    memory_suggestions_enabled = False
    memory_management_enabled = False
    memory_store_path = ".tmp/memory.json"
    proactive_enabled = True
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


class FakeConfigMemoryEnabledNoPath:
    """Config with memory enabled but no store path."""
    memory_context_enabled = True
    memory_suggestions_enabled = False
    memory_management_enabled = False
    memory_store_path = ""
    proactive_enabled = False
    proactive_tts_enabled = False
    proactive_idle_seconds = 300
    proactive_cooldown_seconds = 1800
    proactive_max_per_session = 3
    proactive_quiet_hours_enabled = False
    proactive_quiet_start_hour = 23
    proactive_quiet_end_hour = 8
    proactive_feedback_pause_seconds = 3600


class FakeConfigBadQuietHours:
    """Config with invalid quiet hours."""
    memory_context_enabled = False
    memory_suggestions_enabled = False
    memory_management_enabled = False
    memory_store_path = ".tmp/memory.json"
    proactive_enabled = False
    proactive_tts_enabled = False
    proactive_idle_seconds = 300
    proactive_cooldown_seconds = 1800
    proactive_max_per_session = 3
    proactive_quiet_hours_enabled = True
    proactive_quiet_start_hour = 99  # invalid
    proactive_quiet_end_hour = 8
    proactive_feedback_pause_seconds = 3600


class FakeConfigNegativeIdle:
    """Config with negative idle seconds."""
    memory_context_enabled = False
    memory_suggestions_enabled = False
    memory_management_enabled = False
    memory_store_path = ".tmp/memory.json"
    proactive_enabled = True
    proactive_tts_enabled = False
    proactive_idle_seconds = -10
    proactive_cooldown_seconds = 1800
    proactive_max_per_session = 3
    proactive_quiet_hours_enabled = False
    proactive_quiet_start_hour = 23
    proactive_quiet_end_hour = 8
    proactive_feedback_pause_seconds = 3600


class TestDefaultDiagnostics:
    """Tests for default config diagnostics."""

    def test_default_config_no_errors(self) -> None:
        """Default AppConfig diagnostics has no errors."""
        from app.core.config import get_config
        config = get_config()
        diag = run_startup_diagnostics(config)
        assert not diag.has_errors, f"Default should have no errors: {diag.issues}"


class TestWarningDiagnostics:
    """Tests for warning-level diagnostics."""

    def test_proactive_tts_no_proactive_warning(self) -> None:
        """proactive_tts=true but proactive=false triggers warning."""
        diag = run_startup_diagnostics(FakeConfigProactiveTtsNoProactive())
        assert diag.has_warnings, "Should have warning"
        assert not diag.has_errors, "Should not have errors"
        warning = next(i for i in diag.issues if i.level == StartupDiagnosticLevel.WARNING)
        assert "主动陪伴 TTS" in warning.message

    def test_proactive_tts_no_tts_warning(self) -> None:
        """proactive_tts=true but TTS not enabled triggers warning."""
        diag = run_startup_diagnostics(FakeConfigProactiveTtsNoTts())
        assert diag.has_warnings, "Should have warning"
        assert not diag.has_errors, "Should not have errors"

    def test_memory_enabled_no_path_warning(self) -> None:
        """Memory enabled but store_path empty triggers warning."""
        diag = run_startup_diagnostics(FakeConfigMemoryEnabledNoPath())
        assert diag.has_warnings, "Should have warning"
        warning = next(i for i in diag.issues if "MEMORY_STORE_PATH" in i.message)
        assert warning is not None


class TestErrorDiagnostics:
    """Tests for error-level diagnostics."""

    def test_bad_quiet_start_hour_error(self) -> None:
        """Invalid quiet_start_hour triggers error."""
        diag = run_startup_diagnostics(FakeConfigBadQuietHours())
        assert diag.has_errors, "Should have error"

    def test_negative_idle_seconds_error(self) -> None:
        """Negative proactive_idle_seconds triggers error."""
        diag = run_startup_diagnostics(FakeConfigNegativeIdle())
        assert diag.has_errors, "Should have error"
        error = next(i for i in diag.issues if "IDLE_SECONDS" in i.message)
        assert error is not None


class TestRenderDiagnosticsSummary:
    """Tests for render_startup_diagnostics_summary."""

    def test_summary_ok(self) -> None:
        """OK summary when no issues."""
        diag = StartupDiagnostics(issues=())
        assert render_startup_diagnostics_summary(diag) == "OK"

    def test_summary_has_warnings(self) -> None:
        """有警告 when has_warnings."""
        diag = StartupDiagnostics(
            issues=(StartupDiagnosticIssue(StartupDiagnosticLevel.WARNING, "test"),)
        )
        assert render_startup_diagnostics_summary(diag) == "有警告"

    def test_summary_has_errors(self) -> None:
        """有错误 when has_errors."""
        diag = StartupDiagnostics(
            issues=(StartupDiagnosticIssue(StartupDiagnosticLevel.ERROR, "test"),)
        )
        assert render_startup_diagnostics_summary(diag) == "有错误"


class TestRenderDiagnosticsDetails:
    """Tests for render_startup_diagnostics_details."""

    def test_details_ok(self) -> None:
        """OK message when no issues."""
        diag = StartupDiagnostics(issues=())
        result = render_startup_diagnostics_details(diag)
        assert "OK" in result

    def test_details_warning(self) -> None:
        """Details show warning with ⚠️."""
        diag = StartupDiagnostics(
            issues=(StartupDiagnosticIssue(StartupDiagnosticLevel.WARNING, "test warning"),)
        )
        result = render_startup_diagnostics_details(diag)
        assert "⚠️" in result
        assert "test warning" in result

    def test_details_error(self) -> None:
        """Details show error with ❌."""
        diag = StartupDiagnostics(
            issues=(StartupDiagnosticIssue(StartupDiagnosticLevel.ERROR, "test error"),)
        )
        result = render_startup_diagnostics_details(diag)
        assert "❌" in result
        assert "test error" in result


class TestProductStatusBuilderWithDiagnostics:
    """Tests for product_status_builder with diagnostics."""

    def test_builder_includes_startup_check(self) -> None:
        """build_product_status_view includes 启动检查 when diagnostics passed."""
        from app.core.config import get_config
        from app.ui.avatar_action import AvatarAction
        from app.ui.product_status_builder import build_product_status_view

        config = get_config()
        diag = run_startup_diagnostics(config)
        view = build_product_status_view(
            config=config,
            avatar_action=AvatarAction.IDLE,
            startup_diagnostics=diag,
        )
        labels = [item.label for item in view.items]
        assert "启动检查" in labels


class TestViewModelDiagnosticsText:
    """Tests for ViewModel startup_diagnostics_text."""

    def test_set_startup_diagnostics_text_does_not_change_state(self) -> None:
        """set_startup_diagnostics_text does not change AppState."""
        from app.contracts.states import AppState
        from app.ui.view_model import DesktopViewModel

        vm = DesktopViewModel()
        assert vm.state == AppState.IDLE
        vm.set_startup_diagnostics_text("❌ some error")
        assert vm.state == AppState.IDLE

    def test_set_startup_diagnostics_text_does_not_clear_chat_messages(self) -> None:
        """set_startup_diagnostics_text does not clear chat_messages."""
        from app.ui.chat_message import ChatMessage
        from app.ui.view_model import DesktopViewModel

        vm = DesktopViewModel()
        vm.chat_messages.append(ChatMessage(role="user", text="hello"))
        assert len(vm.chat_messages) == 1
        vm.set_startup_diagnostics_text("OK")
        assert len(vm.chat_messages) == 1
