"""Tests for launch readiness (V11-B)."""

from __future__ import annotations

import re
from pathlib import Path

# Project root is the parent of app/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestEnvExample:
    """Tests for .env.example file."""

    def test_env_example_exists(self) -> None:
        """ .env.example file exists."""
        env_example = PROJECT_ROOT / ".env.example"
        assert env_example.exists(), f"{env_example} does not exist"

    def test_env_example_no_real_keys(self) -> None:
        """.env.example does not contain real-looking API keys."""
        env_example = PROJECT_ROOT / ".env.example"
        content = env_example.read_text(encoding="utf-8")
        # Real-looking key: = followed by 16+ alphanumeric chars
        suspicious = re.findall(r'(?i)(?:api[_-]?key|token|secret)\s*=\s*[a-zA-Z0-9]{16,}', content)
        assert not suspicious, f"Found suspicious real key: {suspicious[0]}"

    def test_env_example_contains_memory_config(self) -> None:
        """.env.example contains memory-related configuration."""
        env_example = PROJECT_ROOT / ".env.example"
        content = env_example.read_text(encoding="utf-8")
        assert "MEMORY_CONTEXT_ENABLED" in content
        assert "MEMORY_SUGGESTIONS_ENABLED" in content
        assert "MEMORY_MANAGEMENT_ENABLED" in content

    def test_env_example_contains_proactive_config(self) -> None:
        """.env.example contains proactive companionship configuration."""
        env_example = PROJECT_ROOT / ".env.example"
        content = env_example.read_text(encoding="utf-8")
        assert "PROACTIVE_ENABLED" in content
        assert "PROACTIVE_TTS_ENABLED" in content
        assert "PROACTIVE_QUIET_HOURS_ENABLED" in content


class TestReadme:
    """Tests for README.md content."""

    def test_readme_contains_startup_instructions(self) -> None:
        """README contains startup/run instructions."""
        readme = PROJECT_ROOT / "README.md"
        content = readme.read_text(encoding="utf-8")
        assert "启动" in content or "run" in content.lower()

    def test_readme_contains_status_panel_section(self) -> None:
        """README contains status panel description."""
        readme = PROJECT_ROOT / "README.md"
        content = readme.read_text(encoding="utf-8")
        assert "状态" in content and "面板" in content

    def test_readme_contains_memory_section(self) -> None:
        """README contains memory description."""
        readme = PROJECT_ROOT / "README.md"
        content = readme.read_text(encoding="utf-8")
        assert "记忆" in content

    def test_readme_contains_proactive_section(self) -> None:
        """README contains proactive companionship description."""
        readme = PROJECT_ROOT / "README.md"
        content = readme.read_text(encoding="utf-8")
        assert "主动陪伴" in content


class TestAppConfigDefaults:
    """Tests for AppConfig default values."""

    def test_memory_context_enabled_default_false(self) -> None:
        """MEMORY_CONTEXT_ENABLED defaults to False."""
        from app.core.config import get_config
        config = get_config()
        assert config.memory_context_enabled is False

    def test_memory_suggestions_enabled_default_false(self) -> None:
        """MEMORY_SUGGESTIONS_ENABLED defaults to False."""
        from app.core.config import get_config
        config = get_config()
        assert config.memory_suggestions_enabled is False

    def test_memory_management_enabled_default_false(self) -> None:
        """MEMORY_MANAGEMENT_ENABLED defaults to False."""
        from app.core.config import get_config
        config = get_config()
        assert config.memory_management_enabled is False

    def test_proactive_enabled_default_false(self) -> None:
        """PROACTIVE_ENABLED defaults to False."""
        from app.core.config import get_config
        config = get_config()
        assert config.proactive_enabled is False

    def test_proactive_tts_enabled_default_false(self) -> None:
        """PROACTIVE_TTS_ENABLED defaults to False."""
        from app.core.config import get_config
        config = get_config()
        assert config.proactive_tts_enabled is False
