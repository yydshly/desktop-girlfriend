r"""Launch readiness probe script (V11-B).

Run locally (no Qt, no network, no LLM, no TTS, no memory, no file writes):
    .venv\Scripts\python.exe scripts/probe_launch_readiness.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Project root is parent of scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _check_readme() -> bool:
    """Check README.md exists and contains key sections."""
    readme = PROJECT_ROOT / "README.md"
    if not readme.exists():
        print("README.md: MISSING")
        return False

    content = readme.read_text(encoding="utf-8")
    checks = [
        ("启动" in content or "run" in content.lower(), "启动说明"),
        ("状态" in content and "面板" in content, "状态面板说明"),
        ("记忆" in content, "记忆说明"),
        ("主动陪伴" in content, "主动陪伴说明"),
        ("app.main" in content or "python -m app.main" in content, "启动命令"),
    ]
    for passed, name in checks:
        if not passed:
            print(f"README.md: missing section '{name}'")
            return False
    return True


def _check_env_example() -> bool:
    """Check .env.example exists and contains key config keys."""
    env_example = PROJECT_ROOT / ".env.example"
    if not env_example.exists():
        print(".env.example: MISSING")
        return False

    content = env_example.read_text(encoding="utf-8")
    key_checks = [
        "MEMORY_CONTEXT_ENABLED",
        "MEMORY_SUGGESTIONS_ENABLED",
        "MEMORY_MANAGEMENT_ENABLED",
        "PROACTIVE_ENABLED",
        "PROACTIVE_TTS_ENABLED",
        "PROACTIVE_QUIET_HOURS_ENABLED",
    ]
    for key in key_checks:
        if key not in content:
            print(f".env.example: missing key '{key}'")
            return False

    # Check no real-looking API keys (at least 16 alphanumeric chars after =)
    suspicious = re.findall(r'(?i)(?:api[_-]?key|token|secret)\s*=\s*[a-zA-Z0-9]{16,}', content)
    if suspicious:
        print(f".env.example: suspicious real key pattern found: {suspicious[0]}")
        return False

    return True


def _check_config_defaults() -> bool:
    """Check AppConfig defaults for memory/proactive switches."""
    try:
        from app.core.config import AppConfig
        config = AppConfig()
        checks = [
            (not config.memory_context_enabled, "MEMORY_CONTEXT_ENABLED default false"),
            (not config.memory_suggestions_enabled, "MEMORY_SUGGESTIONS_ENABLED default false"),
            (not config.memory_management_enabled, "MEMORY_MANAGEMENT_ENABLED default false"),
            (not config.proactive_enabled, "PROACTIVE_ENABLED default false"),
            (not config.proactive_tts_enabled, "PROACTIVE_TTS_ENABLED default false"),
        ]
        for passed, name in checks:
            if not passed:
                print(f"Config defaults: {name}")
                return False
        return True
    except Exception as e:
        print(f"Config check failed: {e}")
        return False


def main() -> None:
    """Run launch readiness probe."""
    sys.stdout.reconfigure(encoding="utf-8")

    print("Launch Readiness Probe\n")

    results: list[tuple[str, bool]] = []

    # 1. README
    ok = _check_readme()
    results.append(("README", ok))
    print(f"README: {'OK' if ok else 'FAIL'}")

    # 2. .env.example
    ok = _check_env_example()
    results.append((".env.example", ok))
    print(f".env.example: {'OK' if ok else 'FAIL'}")

    # 3. Config defaults
    ok = _check_config_defaults()
    results.append(("config defaults", ok))
    print(f"config defaults: {'OK' if ok else 'FAIL'}")

    # Summary
    all_passed = all(r[1] for r in results)
    print()
    if all_passed:
        print("PASS")
    else:
        failed = [r[0] for r in results if not r[1]]
        print(f"FAIL: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
