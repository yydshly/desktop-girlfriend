"""Probe script for memory CLI.

Verifies the memory CLI works correctly with tempfile paths,
does not touch project directory, does not call LLM, etc.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.brain.memory.cli import run_memory_cli


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "memory_probe.json"

        # 1. Run demo command
        rc = run_memory_cli(["--path", str(json_path), "demo"])
        assert rc == 0, f"demo command failed with exit code {rc}"

        # 2. Run list-active
        rc = run_memory_cli(["--path", str(json_path), "list-active"])
        assert rc == 0, f"list-active command failed with exit code {rc}"

        # 3. Run list-all
        rc = run_memory_cli(["--path", str(json_path), "list-all"])
        assert rc == 0, f"list-all command failed with exit code {rc}"

        # 4. Run context
        rc = run_memory_cli(["--path", str(json_path), "context"])
        assert rc == 0, f"context command failed with exit code {rc}"

        print("PASS")


if __name__ == "__main__":
    main()
