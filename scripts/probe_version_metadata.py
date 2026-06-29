"""Version metadata probe for release candidate.

No Qt, no network, no real LLM/TTS/ASR, no memory access.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _check_version_file() -> bool:
    version_file = REPO_ROOT / "VERSION"
    if not version_file.is_file():
        print("VERSION: missing")
        return False
    content = version_file.read_text(encoding="utf-8").strip()
    if content != "0.2.0-alpha.2":
        print(f"VERSION: unexpected content '{content}'")
        return False
    print("VERSION: OK")
    return True


def _check_app_version() -> bool:
    from app.core.version import get_app_version

    ver = get_app_version()
    if ver.version != "0.2.0-alpha.2":
        print(f"app version: unexpected '{ver.version}'")
        return False
    if ver.release_stage != "alpha":
        print(f"release_stage: unexpected '{ver.release_stage}'")
        return False
    print("app version: OK")
    return True


def _check_rc_docs() -> bool:
    rc_md = REPO_ROOT / "RELEASE_CANDIDATE.md"
    content = rc_md.read_text(encoding="utf-8")
    if "0.1.0-rc.3" not in content:
        print("release candidate docs: missing version string")
        return False
    if "tag plan" not in content.lower():
        print("release candidate docs: missing tag plan")
        return False
    if "v0.1.0-rc.0" not in content:
        print("release candidate docs: missing git tag history reference")
        return False
    print("release candidate docs: OK")
    return True


def _check_product_status() -> bool:
    from app.core.config import AppConfig
    from app.core.version import get_app_version
    from app.ui.avatar_action import AvatarAction
    from app.ui.product_status_builder import build_product_status_view

    cfg = AppConfig()
    ver = get_app_version()
    avatar = AvatarAction.IDLE

    view = build_product_status_view(
        config=cfg,
        avatar_action=avatar,
        app_version=ver,
    )
    labels = [item.label for item in view.items]

    has_version = any(item.detail == "0.2.0-alpha.2" for item in view.items)
    has_stage = any(item.detail == "alpha" for item in view.items)
    has_version_label = "版本" in labels
    has_stage_label = "发布阶段" in labels

    if not has_version:
        print("product status: missing version text")
        return False
    if not has_stage:
        print("product status: missing release stage text")
        return False
    if not has_version_label:
        print("product status: missing '版本' label")
        return False
    if not has_stage_label:
        print("product status: missing '发布阶段' label")
        return False

    print("product status: OK")
    return True


def main() -> int:
    print("Version Metadata Probe\n")

    checks = {
        "VERSION": _check_version_file(),
        "app version": _check_app_version(),
        "release candidate docs": _check_rc_docs(),
        "product status": _check_product_status(),
    }

    for name, ok in checks.items():
        print(f"{name}: {'OK' if ok else 'FAIL'}")

    print()
    if all(checks.values()):
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
