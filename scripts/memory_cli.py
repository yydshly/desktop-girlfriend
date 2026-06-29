"""Thin wrapper to run the memory CLI as a script.

Usage:
    python scripts/memory_cli.py --path <json_path> <command>
"""

from app.brain.memory.cli import run_memory_cli

if __name__ == "__main__":
    raise SystemExit(run_memory_cli())
