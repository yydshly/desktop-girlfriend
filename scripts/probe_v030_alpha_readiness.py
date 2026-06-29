"""v0.3.0-alpha.1 Release Readiness Probe.

No LLM/TTS/ASR, no GUI, no file writes, no network calls.
Checks that all Phase 3 release artifacts are in place.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    print("v0.3.0-alpha.1 Readiness Probe\n")

    errors: list[str] = []

    # 1. VERSION == 0.3.0-alpha.1
    version_file = PROJECT_ROOT / "VERSION"
    if version_file.exists():
        version_content = version_file.read_text(encoding="utf-8").strip()
        if version_content == "0.3.0-alpha.1":
            print("version: OK")
        else:
            print(f"version: FAIL (got {version_content!r})")
            errors.append("version")
    else:
        print("version: FAIL (VERSION not found)")
        errors.append("version")

    # 2. release_stage == alpha
    try:
        from app.core.version import get_app_version
        v = get_app_version()
        if v.release_stage == "alpha":
            print("release stage: OK")
        else:
            print(f"release stage: FAIL (got {v.release_stage!r})")
            errors.append("release_stage")
    except Exception as e:
        print(f"release stage: FAIL ({e})")
        errors.append("release_stage")

    # 3. RELEASE_NOTES_v0.3.0-alpha.1.md exists
    release_notes = PROJECT_ROOT / "RELEASE_NOTES_v0.3.0-alpha.1.md"
    if release_notes.exists():
        print("release notes: OK")
    else:
        print("release notes: FAIL (missing)")
        errors.append("release_notes")

    # 4. packaging docs exist
    smoke_checklist = PROJECT_ROOT / "docs" / "release" / "windows_gui_smoke_checklist.md"
    packaging_doc = PROJECT_ROOT / "docs" / "release" / "packaging_readiness_v0.md"
    if smoke_checklist.exists() and packaging_doc.exists():
        print("packaging docs: OK")
    else:
        print("packaging docs: FAIL")
        errors.append("packaging_docs")

    # 5. .env.example exists
    env_example = PROJECT_ROOT / ".env.example"
    if env_example.exists():
        # Check it doesn't contain real keys
        content = env_example.read_text(encoding="utf-8")
        safe = "eyJ" not in content and "sk_live_" not in content
        if safe:
            print("env example: OK")
        else:
            print("env example: FAIL (contains suspicious key patterns)")
            errors.append("env_example_safety")
    else:
        print("env example: FAIL (missing)")
        errors.append("env_example")

    # 6. run script exists
    run_script = PROJECT_ROOT / "scripts" / "run_desktop.ps1"
    if run_script.exists():
        print("run script: OK")
    else:
        print("run script: FAIL")
        errors.append("run_script")

    # 7. All required probes exist
    required_probes = [
        "scripts/probe_packaging_readiness.py",
        "scripts/probe_settings_runtime_controls_v1.py",
        "scripts/probe_proactive_real_ux_v1.py",
        "scripts/probe_memory_ux_v1.py",
    ]
    missing_probes = []
    for p in required_probes:
        if not (PROJECT_ROOT / p).exists():
            missing_probes.append(p)
    if not missing_probes:
        print("probes: OK")
    else:
        print(f"probes: FAIL (missing: {', '.join(missing_probes)})")
        errors.append("probes")

    # 8. README exists
    readme = PROJECT_ROOT / "README.md"
    if readme.exists():
        print("readme: OK")
    else:
        print("readme: FAIL")
        errors.append("readme")

    # 9. No git-tracked .env or .tmp
    gitignore = PROJECT_ROOT / ".gitignore"
    gitignored: set[str] = set()
    if gitignore.exists():
        for line in gitignore.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                gitignored.add(stripped.rstrip("/"))

    sensitive_issues = []
    for f in [".env", ".tmp"]:
        path = PROJECT_ROOT / f
        if path.exists():
            if f not in gitignored and (f + "/") not in gitignored:
                sensitive_issues.append(f)
    if not sensitive_issues:
        print("sensitive files: OK")
    else:
        print(f"sensitive files: FAIL (not gitignored: {', '.join(sensitive_issues)})")
        errors.append("sensitive_files")

    print()
    if errors:
        print(f"FAIL ({len(errors)} error(s)): {', '.join(errors)}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
