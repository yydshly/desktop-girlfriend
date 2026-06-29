"""Version metadata tests for release candidate."""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.core.config import AppConfig
from app.core.version import AppVersion, get_app_version, read_version
from app.ui.avatar_action import AvatarAction
from app.ui.product_status_builder import build_product_status_view

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestVersionFile:
    @staticmethod
    def test_version_file_exists() -> None:
        assert (REPO_ROOT / "VERSION").is_file()

    @staticmethod
    def test_version_content() -> None:
        content = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        assert content == "0.2.0-alpha.2"


class TestReadVersion:
    @staticmethod
    def test_read_version_from_file() -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as f:
            f.write("1.2.3-beta.5\n")
            path = Path(f.name)

        try:
            assert read_version(path) == "1.2.3-beta.5"
        finally:
            path.unlink()

    @staticmethod
    def test_read_version_missing_file() -> None:
        assert read_version(Path("/nonexistent/version/file")) == "0.2.0-alpha.2"


class TestGetAppVersion:
    @staticmethod
    def test_get_app_version_returns_app_version() -> None:
        ver = get_app_version()
        assert isinstance(ver, AppVersion)

    @staticmethod
    def test_get_app_version_version() -> None:
        ver = get_app_version()
        assert ver.version == "0.2.0-alpha.2"

    @staticmethod
    def test_get_app_version_release_stage() -> None:
        ver = get_app_version()
        assert ver.release_stage == "alpha"


class TestProductStatusBuilder:
    @staticmethod
    def test_build_without_app_version() -> None:
        cfg = AppConfig()
        avatar = AvatarAction.IDLE
        view = build_product_status_view(config=cfg, avatar_action=avatar)
        assert len(view.items) > 0

    @staticmethod
    def test_build_with_app_version_includes_version() -> None:
        cfg = AppConfig()
        avatar = AvatarAction.IDLE
        ver = get_app_version()
        view = build_product_status_view(
            config=cfg, avatar_action=avatar, app_version=ver
        )
        labels = [item.label for item in view.items]
        details = [item.detail for item in view.items]
        assert "版本" in labels
        assert "0.2.0-alpha.2" in details

    @staticmethod
    def test_build_with_app_version_includes_release_stage() -> None:
        cfg = AppConfig()
        avatar = AvatarAction.IDLE
        ver = get_app_version()
        view = build_product_status_view(
            config=cfg, avatar_action=avatar, app_version=ver
        )
        labels = [item.label for item in view.items]
        details = [item.detail for item in view.items]
        assert "发布阶段" in labels
        assert "alpha" in details


class TestRcDocContent:
    @staticmethod
    def test_rc_md_contains_version() -> None:
        content = (REPO_ROOT / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")
        assert "0.1.0-rc.3" in content

    @staticmethod
    def test_rc_md_contains_history() -> None:
        content = (REPO_ROOT / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")
        assert "v0.1.0-rc.0" in content  # history preserved in changelog
