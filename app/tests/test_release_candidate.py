"""Minimal smoke tests for release candidate artifacts."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.tests.conftest import clear_config_env

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestRcFiles:
    @staticmethod
    def test_rc_md_exists() -> None:
        assert (REPO_ROOT / "RELEASE_CANDIDATE.md").is_file()

    @staticmethod
    def test_run_desktop_ps1_exists() -> None:
        assert (REPO_ROOT / "scripts" / "run_desktop.ps1").is_file()

    @staticmethod
    def test_probe_release_candidate_exists() -> None:
        assert (REPO_ROOT / "scripts" / "probe_release_candidate.py").is_file()

    @staticmethod
    def test_probe_environment_readiness_exists() -> None:
        assert (REPO_ROOT / "scripts" / "probe_environment_readiness.py").is_file()


class TestRcDocContent:
    @staticmethod
    def test_rc_contains_v8() -> None:
        content = (REPO_ROOT / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")
        assert "V8 Memory Runtime v0" in content

    @staticmethod
    def test_rc_contains_v9() -> None:
        content = (REPO_ROOT / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")
        assert "V9 Proactive Companionship v0" in content

    @staticmethod
    def test_rc_contains_v10() -> None:
        content = (REPO_ROOT / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")
        assert "V10 Avatar Action v0" in content

    @staticmethod
    def test_rc_contains_v11() -> None:
        content = (REPO_ROOT / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")
        assert "V11 Product Experience v0" in content

    @staticmethod
    def test_rc_contains_run_desktop() -> None:
        content = (REPO_ROOT / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")
        assert "run_desktop.ps1" in content

    @staticmethod
    def test_rc_contains_current_version() -> None:
        content = (REPO_ROOT / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")
        assert "0.1.0-rc.3" in content

    @staticmethod
    def test_rc_contains_rc3_changelog() -> None:
        content = (REPO_ROOT / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")
        assert "### v0.1.0-rc.3" in content
        assert "environment readiness probe" in content
        assert "MiniMax Chat/TTS HTTP error details with key redaction" in content

    @staticmethod
    def test_rc_tag_plan_targets_rc3() -> None:
        content = (REPO_ROOT / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")
        assert "git tag v0.1.0-rc.3" in content
        assert "git push origin v0.1.0-rc.3" in content

    @staticmethod
    def test_rc_contains_env() -> None:
        content = (REPO_ROOT / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")
        assert ".env" in content

    @staticmethod
    def test_rc_contains_privacy_note() -> None:
        content = (REPO_ROOT / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")
        assert any(kw.lower() in content.lower() for kw in ["privacy", "隐私", "API key"])


class TestRcConfigDefaults:
    @staticmethod
    def test_memory_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
        clear_config_env(monkeypatch)
        from app.core.config import AppConfig

        cfg = AppConfig()
        assert cfg.memory_context_enabled is False

    @staticmethod
    def test_proactive_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
        clear_config_env(monkeypatch)
        from app.core.config import AppConfig

        cfg = AppConfig()
        assert cfg.proactive_enabled is False

    @staticmethod
    def test_proactive_tts_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
        clear_config_env(monkeypatch)
        from app.core.config import AppConfig

        cfg = AppConfig()
        assert cfg.proactive_tts_enabled is False
