"""Release Candidate self-check probe.

No Qt, no network, no real LLM/TTS/ASR, no memory access.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _check_files() -> bool:
    required = [
        "README.md",
        "RELEASE_CANDIDATE.md",
        ".env.example",
        "scripts/run_desktop.ps1",
        "scripts/probe_environment_readiness.py",
        "scripts/probe_launch_readiness.py",
        "scripts/probe_startup_diagnostics.py",
    ]
    missing = [f for f in required if not (REPO_ROOT / f).is_file()]
    if missing:
        print(f"Missing files: {missing}")
        return False
    return True


def _check_config_defaults() -> bool:
    try:
        from app.core.config import AppConfig

        cfg = AppConfig()
        if cfg.memory_context_enabled:
            print("memory_context_enabled should be False by default")
            return False
        if cfg.proactive_enabled:
            print("proactive_enabled should be False by default")
            return False
        if cfg.proactive_tts_enabled:
            print("proactive_tts_enabled should be False by default")
            return False
        return True
    except Exception as e:
        print(f"AppConfig init failed: {e}")
        return False


def _check_privacy() -> bool:
    env_example = REPO_ROOT / ".env.example"
    content = env_example.read_text(encoding="utf-8")
    # Check no obvious real keys
    patterns = [
        r"sk-[a-zA-Z0-9]{20,}",
        r"sk-\d{10,}",
        r"AIza[a-zA-Z0-9_-]{20,}",
        r"(?i)openai.*=.*sk-",
        r"(?i)anthropic.*=.*sk-",
        r"(?i)azure.*key.*=.*[a-f0-9]{32,}",
    ]
    for pat in patterns:
        if re.search(pat, content):
            print(f"Potential real key pattern found in .env.example: {pat}")
            return False
    return True


def _check_docs() -> bool:
    rc_md = REPO_ROOT / "RELEASE_CANDIDATE.md"
    content = rc_md.read_text(encoding="utf-8")

    required = [
        "V8 Memory Runtime v0",
        "V9 Proactive Companionship v0",
        "V10 Avatar Action v0",
        "V11 Product Experience v0",
        "v0.1.0-rc.3",
        "git tag v0.1.0-rc.3",
        "environment readiness probe",
        "run_desktop.ps1",
        ".env",
    ]
    privacy_keywords = ["privacy", "隐私", "API key"]
    has_privacy = any(kw.lower() in content.lower() for kw in privacy_keywords)

    missing = [kw for kw in required if kw not in content]
    if missing:
        print(f"RELEASE_CANDIDATE.md missing: {missing}")
        return False
    if not has_privacy:
        print("RELEASE_CANDIDATE.md missing privacy/API key note")
        return False
    return True


def main() -> int:
    print("Release Candidate Probe\n")

    checks = {
        "files": _check_files(),
        "config defaults": _check_config_defaults(),
        "privacy": _check_privacy(),
        "docs": _check_docs(),
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
