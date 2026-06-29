"""Startup diagnostics view renderers (V11-C)."""

from __future__ import annotations

from app.core.startup_diagnostics import (
    StartupDiagnosticIssue,
    StartupDiagnosticLevel,
    StartupDiagnostics,
)


def render_startup_diagnostics_summary(diagnostics: StartupDiagnostics) -> str:
    """Render a one-line summary of startup diagnostics.

    Args:
        diagnostics: The startup diagnostics to summarize.

    Returns:
        "有错误", "有警告", or "OK".
    """
    if diagnostics.has_errors:
        return "有错误"
    if diagnostics.has_warnings:
        return "有警告"
    return "OK"


def render_startup_diagnostic_issue(issue: StartupDiagnosticIssue) -> str:
    """Render a single diagnostic issue.

    Args:
        issue: The diagnostic issue to render.

    Returns:
        A string like "❌ message" or "⚠️ message".
    """
    if issue.level == StartupDiagnosticLevel.ERROR:
        return f"❌ {issue.message}"
    if issue.level == StartupDiagnosticLevel.WARNING:
        return f"⚠️ {issue.message}"
    return f"ℹ️ {issue.message}"


def render_startup_diagnostics_details(diagnostics: StartupDiagnostics) -> str:
    """Render all diagnostic issues as multi-line text.

    Args:
        diagnostics: The startup diagnostics to render.

    Returns:
        A newline-separated string of rendered issues.
    """
    if not diagnostics.issues:
        return "✅ 启动检查：OK"
    return "\n".join(render_startup_diagnostic_issue(issue) for issue in diagnostics.issues)
