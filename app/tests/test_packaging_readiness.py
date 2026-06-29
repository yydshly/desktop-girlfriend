"""Tests for packaging readiness (Phase 3-F)."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from app.packaging.readiness import (  # noqa: E402
    PackagingCheckItem,
    PackagingReadinessReport,
    check_packaging_readiness,
    render_packaging_report,
)


class TestPackagingReadinessReport:
    """Tests for PackagingReadinessReport."""

    def test_report_has_ok_property_true(self) -> None:
        """Report.ok is True when all items pass."""
        items = (
            PackagingCheckItem(name="test1", ok=True, detail=""),
            PackagingCheckItem(name="test2", ok=True, detail=""),
        )
        report = PackagingReadinessReport(items=items)
        assert report.ok is True

    def test_report_has_ok_property_false(self) -> None:
        """Report.ok is False when any item fails."""
        items = (
            PackagingCheckItem(name="test1", ok=True, detail=""),
            PackagingCheckItem(name="test2", ok=False, detail="missing"),
        )
        report = PackagingReadinessReport(items=items)
        assert report.ok is False

    def test_check_packaging_readiness_returns_report(self) -> None:
        """check_packaging_readiness returns PackagingReadinessReport."""
        report = check_packaging_readiness(PROJECT_ROOT)
        assert isinstance(report, PackagingReadinessReport)

    def test_version_file_check_exists(self) -> None:
        """VERSION file check is present."""
        report = check_packaging_readiness(PROJECT_ROOT)
        version_item = next((i for i in report.items if i.name == "version file"), None)
        assert version_item is not None

    def test_env_example_check_exists(self) -> None:
        """.env.example check is present."""
        report = check_packaging_readiness(PROJECT_ROOT)
        env_item = next((i for i in report.items if i.name == "env example"), None)
        assert env_item is not None

    def test_run_script_check_exists(self) -> None:
        """scripts/run_desktop.ps1 check is present."""
        report = check_packaging_readiness(PROJECT_ROOT)
        script_item = next((i for i in report.items if i.name == "run script"), None)
        assert script_item is not None

    def test_main_entry_check_exists(self) -> None:
        """app/main.py check is present."""
        report = check_packaging_readiness(PROJECT_ROOT)
        main_item = next((i for i in report.items if i.name == "main entry"), None)
        assert main_item is not None

    def test_readme_check_exists(self) -> None:
        """README.md check is present."""
        report = check_packaging_readiness(PROJECT_ROOT)
        readme_item = next((i for i in report.items if i.name == "readme"), None)
        assert readme_item is not None

    def test_pyproject_check_exists(self) -> None:
        """pyproject.toml check is present."""
        report = check_packaging_readiness(PROJECT_ROOT)
        pyproject_item = next((i for i in report.items if i.name == "pyproject"), None)
        assert pyproject_item is not None

    def test_sensitive_files_check_exists(self) -> None:
        """Sensitive files check is present."""
        report = check_packaging_readiness(PROJECT_ROOT)
        sensitive_item = next((i for i in report.items if i.name == "sensitive files"), None)
        assert sensitive_item is not None

    def test_version_file_ok_when_exists(self) -> None:
        """VERSION file item is ok when VERSION exists."""
        report = check_packaging_readiness(PROJECT_ROOT)
        version_item = next((i for i in report.items if i.name == "version file"), None)
        assert version_item is not None
        version_path = PROJECT_ROOT / "VERSION"
        assert version_item.ok == version_path.exists()

    def test_env_example_ok_when_exists(self) -> None:
        """.env.example item is ok when file exists."""
        report = check_packaging_readiness(PROJECT_ROOT)
        env_item = next((i for i in report.items if i.name == "env example"), None)
        assert env_item is not None
        env_path = PROJECT_ROOT / ".env.example"
        assert env_item.ok == env_path.exists()

    def test_env_example_safe_content(self) -> None:
        """.env.example does not contain obvious real API keys."""
        env_path = PROJECT_ROOT / ".env.example"
        if not env_path.exists():
            return  # skip if missing
        content = env_path.read_text(encoding="utf-8")
        # Should not contain JWT-like tokens or real API key patterns
        assert "eyJ" not in content
        assert "sk_live_" not in content

    def test_env_example_contains_memory_context(self) -> None:
        """.env.example contains MEMORY_CONTEXT_ENABLED."""
        env_path = PROJECT_ROOT / ".env.example"
        if not env_path.exists():
            return
        content = env_path.read_text(encoding="utf-8")
        assert "MEMORY_CONTEXT_ENABLED" in content

    def test_env_example_contains_proactive_enabled(self) -> None:
        """.env.example contains PROACTIVE_ENABLED."""
        env_path = PROJECT_ROOT / ".env.example"
        if not env_path.exists():
            return
        content = env_path.read_text(encoding="utf-8")
        assert "PROACTIVE_ENABLED" in content

    def test_env_example_contains_tts_enabled(self) -> None:
        """.env.example contains TTS_ENABLED."""
        env_path = PROJECT_ROOT / ".env.example"
        if not env_path.exists():
            return
        content = env_path.read_text(encoding="utf-8")
        assert "TTS_ENABLED" in content

    def test_env_example_contains_asr_enabled(self) -> None:
        """.env.example contains ASR_ENABLED."""
        env_path = PROJECT_ROOT / ".env.example"
        if not env_path.exists():
            return
        content = env_path.read_text(encoding="utf-8")
        assert "ASR_ENABLED" in content

    def test_render_packaging_report_non_empty(self) -> None:
        """render_packaging_report returns non-empty string."""
        report = check_packaging_readiness(PROJECT_ROOT)
        output = render_packaging_report(report)
        assert len(output) > 0
        assert "version file" in output
        assert "env example" in output
