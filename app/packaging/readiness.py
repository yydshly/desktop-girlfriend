"""Packaging readiness checks (Phase 3-F).

Pure functions to verify the project has the minimum files needed for packaging
and distribution. No Qt, no file writes, no LLM/TTS/ASR, no real .env reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Known sensitive file patterns that should never be committed
_DANGEROUS_PATTERNS: tuple[str, ...] = (
    ".env",
    ".env.local",
    ".env.production",
)


@dataclass(frozen=True)
class PackagingCheckItem:
    """A single packaging readiness check result."""

    name: str
    ok: bool
    detail: str = ""


@dataclass(frozen=True)
class PackagingReadinessReport:
    """Result of all packaging readiness checks."""

    items: tuple[PackagingCheckItem, ...]

    @property
    def ok(self) -> bool:
        """Return True if all checks passed."""
        return all(item.ok for item in self.items)


def check_packaging_readiness(project_root: Path) -> PackagingReadinessReport:
    """Run all packaging readiness checks against the project root.

    Args:
        project_root: The project root directory (containing app/, scripts/, etc.).

    Returns:
        A PackagingReadinessReport with all check results.
    """
    items: list[PackagingCheckItem] = []

    # 1. VERSION file
    version_file = project_root / "VERSION"
    items.append(
        PackagingCheckItem(
            name="version file",
            ok=version_file.exists(),
            detail="VERSION found" if version_file.exists() else "VERSION missing",
        )
    )

    # 2. .env.example
    env_example = project_root / ".env.example"
    items.append(
        PackagingCheckItem(
            name="env example",
            ok=env_example.exists(),
            detail=".env.example found" if env_example.exists() else ".env.example missing",
        )
    )

    # 3. scripts/run_desktop.ps1
    run_script = project_root / "scripts" / "run_desktop.ps1"
    items.append(
        PackagingCheckItem(
            name="run script",
            ok=run_script.exists(),
            detail="scripts/run_desktop.ps1 found" if run_script.exists() else "scripts/run_desktop.ps1 missing",
        )
    )

    # 4. app/main.py
    main_py = project_root / "app" / "main.py"
    items.append(
        PackagingCheckItem(
            name="main entry",
            ok=main_py.exists(),
            detail="app/main.py found" if main_py.exists() else "app/main.py missing",
        )
    )

    # 5. README.md
    readme = project_root / "README.md"
    items.append(
        PackagingCheckItem(
            name="readme",
            ok=readme.exists(),
            detail="README.md found" if readme.exists() else "README.md missing",
        )
    )

    # 6. pyproject.toml
    pyproject = project_root / "pyproject.toml"
    items.append(
        PackagingCheckItem(
            name="pyproject",
            ok=pyproject.exists(),
            detail="pyproject.toml found" if pyproject.exists() else "pyproject.toml missing",
        )
    )

    # 7. Sensitive files check — fail only if unignored .env is found
    # Check if .env is gitignored; if so, it's safe even if it exists locally
    gitignore_path = project_root / ".gitignore"
    gitignored: set[str] = set()
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text(encoding="utf-8")
        for line in gitignore_content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                gitignored.add(stripped.rstrip("/"))

    sensitive_found: list[str] = []
    for pattern in _DANGEROUS_PATTERNS:
        dotenv = project_root / pattern
        if dotenv.exists():
            # Only report as problem if NOT gitignored
            if pattern not in gitignored and (pattern + "/") not in gitignored:
                sensitive_found.append(pattern)

    items.append(
        PackagingCheckItem(
            name="sensitive files",
            ok=len(sensitive_found) == 0,
            detail=(
                "no dangerous files found" if not sensitive_found
                else f"found (not gitignored): {', '.join(sensitive_found)}"
            ),
        )
    )

    # 8. .tmp in repository check — only fail if .tmp exists AND is not gitignored
    tmp_dir = project_root / ".tmp"
    tmp_gitignored = ".tmp" in gitignored or ".tmp/" in gitignored
    tmp_ok = not tmp_dir.exists() or tmp_gitignored
    items.append(
        PackagingCheckItem(
            name=".tmp cleanup",
            ok=tmp_ok,
            detail=(
                ".tmp not tracked (good)" if tmp_ok
                else ".tmp exists and not gitignored"
            ),
        )
    )

    return PackagingReadinessReport(items=tuple(items))


def render_packaging_report(report: PackagingReadinessReport) -> str:
    """Render a PackagingReadinessReport to a human-readable string.

    Args:
        report: The packaging readiness report.

    Returns:
        A multi-line string describing each check result.
    """
    lines = []
    for item in report.items:
        status = "OK" if item.ok else "FAIL"
        detail = f" - {item.detail}" if item.detail else ""
        lines.append(f"{item.name}: {status}{detail}")
    return "\n".join(lines)
