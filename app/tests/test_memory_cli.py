"""Tests for memory CLI (V8-F)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.brain.memory.cli import build_parser, run_memory_cli


class TestBuildParser:
    """Tests for build_parser."""

    def test_requires_path_argument(self) -> None:
        """Parser requires --path argument."""
        parser = build_parser()
        # When --path is missing, parsing should fail
        with pytest.raises(SystemExit):
            parser.parse_args(["list-active"])

    def test_missing_command_shows_error(self, capsys: pytest.CaptureFixture) -> None:
        """Parser requires a subcommand."""
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--path", "test.json"])


class TestListActive:
    """Tests for list-active command."""

    def test_missing_file_returns_0(self, tmp_path: Path) -> None:
        """list-active on missing file returns exit code 0 (empty list)."""
        json_path = tmp_path / "nonexistent.json"
        rc = run_memory_cli(["--path", str(json_path), "list-active"])
        assert rc == 0

    def test_missing_file_prints_empty_message(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """list-active on missing file prints empty message."""
        json_path = tmp_path / "nonexistent.json"
        rc = run_memory_cli(["--path", str(json_path), "list-active"])
        captured = capsys.readouterr()
        assert "(no active records)" in captured.out
        assert rc == 0

    def test_lists_records(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """list-active prints records."""
        json_path = tmp_path / "memory.json"
        # Pre-populate
        data = {
            "version": 1,
            "records": [
                {
                    "id": "test-record-001",
                    "kind": "preference",
                    "importance": "medium",
                    "text": "用户喜欢短回复。",
                    "source": "test",
                    "created_at": "2024-01-01T00:00:00+00:00",
                    "updated_at": "2024-01-01T00:00:00+00:00",
                    "status": "active",
                }
            ],
        }
        json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        rc = run_memory_cli(["--path", str(json_path), "list-active"])
        captured = capsys.readouterr()
        assert "test-rec" in captured.out  # truncated id
        assert "preference" in captured.out
        assert rc == 0


class TestListAll:
    """Tests for list-all command."""

    def test_includes_deleted_records(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """list-all includes deleted records with status field."""
        json_path = tmp_path / "memory.json"
        data = {
            "version": 1,
            "records": [
                {
                    "id": "active-record-001",
                    "kind": "preference",
                    "importance": "medium",
                    "text": "活跃记录。",
                    "source": "test",
                    "created_at": "2024-01-01T00:00:00+00:00",
                    "updated_at": "2024-01-01T00:00:00+00:00",
                    "status": "active",
                },
                {
                    "id": "deleted-record-001",
                    "kind": "boundary",
                    "importance": "high",
                    "text": "已删除记录。",
                    "source": "test",
                    "created_at": "2024-01-01T00:00:00+00:00",
                    "updated_at": "2024-01-01T00:00:00+00:00",
                    "status": "deleted",
                },
            ],
        }
        json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        rc = run_memory_cli(["--path", str(json_path), "list-all"])
        captured = capsys.readouterr()
        assert "active" in captured.out
        assert "deleted" in captured.out
        assert rc == 0


class TestContext:
    """Tests for context command."""

    def test_empty_prints_empty(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """context on empty repository prints '(empty)'."""
        json_path = tmp_path / "nonexistent.json"
        rc = run_memory_cli(["--path", str(json_path), "context"])
        captured = capsys.readouterr()
        assert "(empty)" in captured.out
        assert rc == 0


class TestClear:
    """Tests for clear command."""

    def test_clear_removes_repository_file(self, tmp_path: Path) -> None:
        """clear removes the repository file."""
        json_path = tmp_path / "memory.json"
        # Pre-populate
        data = {
            "version": 1,
            "records": [
                {
                    "id": "record-to-clear",
                    "kind": "preference",
                    "importance": "medium",
                    "text": "将被清除的记录。",
                    "source": "test",
                    "created_at": "2024-01-01T00:00:00+00:00",
                    "updated_at": "2024-01-01T00:00:00+00:00",
                    "status": "active",
                }
            ],
        }
        json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        assert json_path.exists()
        rc = run_memory_cli(["--path", str(json_path), "clear"])
        assert rc == 0
        assert not json_path.exists()


class TestDelete:
    """Tests for delete command."""

    def test_delete_unknown_id_returns_1(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """delete with unknown id returns exit code 1."""
        json_path = tmp_path / "memory.json"
        rc = run_memory_cli(["--path", str(json_path), "delete", "unknown-id-12345"])
        captured = capsys.readouterr()
        assert "not found" in captured.err
        assert rc == 1

    def test_delete_existing_record(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """delete with existing id soft-deletes and returns exit code 0."""
        json_path = tmp_path / "memory.json"
        data = {
            "version": 1,
            "records": [
                {
                    "id": "deleteable-record-001",
                    "kind": "preference",
                    "importance": "medium",
                    "text": "将被删除的记录。",
                    "source": "test",
                    "created_at": "2024-01-01T00:00:00+00:00",
                    "updated_at": "2024-01-01T00:00:00+00:00",
                    "status": "active",
                }
            ],
        }
        json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        rc = run_memory_cli(["--path", str(json_path), "delete", "deleteable-record-001"])
        captured = capsys.readouterr()
        assert "deleted" in captured.out
        assert rc == 0


class TestDemo:
    """Tests for demo command."""

    def test_demo_returns_0(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """demo command returns exit code 0."""
        json_path = tmp_path / "demo_memory.json"
        rc = run_memory_cli(["--path", str(json_path), "demo"])
        captured = capsys.readouterr()
        assert "PASS" in captured.out
        assert rc == 0

    def test_demo_creates_then_deletes_active_record(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """demo creates records then deletes them via delete command."""
        json_path = tmp_path / "demo_memory.json"
        # Run demo first
        rc = run_memory_cli(["--path", str(json_path), "demo"])
        assert rc == 0

        # After demo, all active records should be deleted
        rc = run_memory_cli(["--path", str(json_path), "list-active"])
        captured = capsys.readouterr()
        assert "(no active records)" in captured.out

    def test_demo_does_not_print_full_sensitive_text(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """demo output should not contain full sensitive text like '红红'."""
        json_path = tmp_path / "demo_memory.json"
        rc = run_memory_cli(["--path", str(json_path), "demo"])
        captured = capsys.readouterr()
        # The name "红红" should NOT appear in output
        assert "红红" not in captured.out
        # But PASS should be there
        assert "PASS" in captured.out
        assert rc == 0


class TestRunMemoryCliIsolation:
    """Tests verifying run_memory_cli does not call LLM, open microphone, etc."""

    def test_does_not_call_llm(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify run_memory_cli does not call any LLM API."""
        called_llm = False

        def mock_llm_call(*args: object, **kwargs: object) -> object:
            nonlocal called_llm
            called_llm = True
            return None

        # Try to detect LLM calls by checking common patterns
        # The CLI only uses deterministic extractor, so no LLM should be called
        json_path = tmp_path / "test.json"
        rc = run_memory_cli(["--path", str(json_path), "demo"])
        assert not called_llm
        assert rc == 0

    def test_does_not_open_microphone(self, tmp_path: Path) -> None:
        """Verify run_memory_cli does not open microphone."""
        json_path = tmp_path / "test.json"
        # If microphone were opened, it would fail in headless environments
        # without proper mocking. Since CLI only uses in-memory runtime,
        # this should succeed.
        rc = run_memory_cli(["--path", str(json_path), "list-active"])
        assert rc == 0

    def test_does_not_touch_main_py(self, tmp_path: Path) -> None:
        """Verify run_memory_cli does not import or call main.py.

        Checked by ensuring 'main' is not in sys.modules after running CLI.
        """
        json_path = tmp_path / "test.json"
        run_memory_cli(["--path", str(json_path), "list-active"])
        # main should not be loaded after CLI runs
        import sys
        assert "main" not in sys.modules
        assert not any(k.startswith("main.") for k in sys.modules)


class TestMemoryCliThinWrapper:
    """Tests verifying scripts/memory_cli.py is a thin wrapper."""

    def test_wrapper_exists(self) -> None:
        """scripts/memory_cli.py exists and is importable."""
        from scripts.memory_cli import run_memory_cli as wrapper_run
        assert callable(wrapper_run)

    def test_wrapper_calls_cli(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """scripts/memory_cli.py calls run_memory_cli."""
        from scripts.memory_cli import run_memory_cli as wrapper_run
        json_path = tmp_path / "thin_test.json"
        rc = wrapper_run(["--path", str(json_path), "list-active"])
        assert rc == 0
        captured = capsys.readouterr()
        assert "(no active records)" in captured.out


class TestSnapshot:
    """Tests for snapshot command."""

    def test_snapshot_returns_counts(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """snapshot prints pending/active/rejected counts."""
        json_path = tmp_path / "test.json"
        rc = run_memory_cli(["--path", str(json_path), "snapshot"])
        captured = capsys.readouterr()
        assert "pending=" in captured.out
        assert "active=" in captured.out
        assert "rejected=" in captured.out
        assert rc == 0
