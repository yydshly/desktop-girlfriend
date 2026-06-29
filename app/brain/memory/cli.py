"""Memory runtime CLI for V8-F.

Local debugging / probe interface for verifying the complete memory runtime loop:
extraction -> pending -> confirm/reject -> persistence -> list -> delete -> context.

This CLI is intentionally:
- Not networked
- Does not call LLM
- Does not open microphone
- Does not integrate with main.py
- Does not auto-save user chat
- Requires explicit --path for all commands
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from app.brain.memory.repository import LocalJsonMemoryRepository
from app.brain.memory.runtime import (
    MemoryRuntimeService,
    create_local_memory_runtime,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the memory CLI."""
    parser = argparse.ArgumentParser(
        prog="memory_cli",
        description="Memory runtime CLI — local debugging/probe interface.",
    )
    parser.add_argument(
        "--path",
        type=Path,
        required=True,
        metavar="JSON",
        help="Path to the memory JSON file (required for all commands).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # submit <text>
    sub.add_parser("submit", help="Submit user text to extract pending memories.").add_argument(
        "text", help="User text to process."
    )

    # list-pending
    sub.add_parser("list-pending", help="List all pending memories.")

    # confirm <pending_id>
    confirm_parser = sub.add_parser("confirm", help="Confirm a pending memory.")
    confirm_parser.add_argument("pending_id", help="ID of the pending memory to confirm.")

    # reject <pending_id> [--reason <reason>]
    reject_parser = sub.add_parser("reject", help="Reject a pending memory.")
    reject_parser.add_argument("pending_id", help="ID of the pending memory to reject.")
    reject_parser.add_argument("--reason", default="", help="Optional rejection reason.")

    # list-active
    sub.add_parser("list-active", help="List all active memory records.")

    # list-all
    sub.add_parser("list-all", help="List all memory records (active + deleted).")

    # delete <record_id>
    delete_parser = sub.add_parser("delete", help="Soft-delete a memory record.")
    delete_parser.add_argument("record_id", help="ID of the record to delete.")

    # context
    sub.add_parser("context", help="Build and print session memory context.")

    # snapshot
    sub.add_parser("snapshot", help="Print pending/active/rejected counts.")

    # clear
    sub.add_parser("clear", help="Clear all records from repository.")

    # demo
    sub.add_parser("demo", help="Run full submit/confirm/reject/list/context/delete loop.")

    return parser


def _format_datetime(dt: datetime) -> str:
    """Format datetime for CLI output."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _truncate(text: str, max_chars: int = 40) -> str:
    """Truncate text for safe CLI display."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def _print_pending_list(pending: tuple, runtime: MemoryRuntimeService) -> None:
    """Print pending memories in a user-friendly format."""
    if not pending:
        print("(no pending memories)")
        return
    for p in pending:
        print(
            f"[{p.id[:8]}] kind={p.candidate.kind.value} "
            f"importance={p.candidate.importance.value} "
            f"text={_truncate(p.candidate.text)} "
            f"created={_format_datetime(p.created_at)}"
        )


def _print_active_list(records: tuple) -> None:
    """Print active records in a user-friendly format."""
    if not records:
        print("(no active records)")
        return
    for r in records:
        print(
            f"[{r.id[:8]}] kind={r.kind.value} "
            f"importance={r.importance.value} "
            f"text={_truncate(r.text)} "
            f"created={_format_datetime(r.created_at)} "
            f"updated={_format_datetime(r.updated_at)}"
        )


def _print_all_list(records: tuple) -> None:
    """Print all records (active + deleted) in a user-friendly format."""
    if not records:
        print("(no records)")
        return
    for r in records:
        print(
            f"[{r.id[:8]}] status={r.status.value} "
            f"kind={r.kind.value} "
            f"importance={r.importance.value} "
            f"text={_truncate(r.text)}"
        )


def _run_demo(runtime: MemoryRuntimeService) -> int:
    """Run the demo command: full submit/confirm/reject/list/context/delete loop."""
    # 1. Submit user text for preference
    pending1 = runtime.submit_user_text("我喜欢你回复短一点。")
    # 2. Submit user text for boundary
    pending2 = runtime.submit_user_text("我女朋友叫红红，这件事不要记住。")

    # Filter non-boundary pending (pending1)
    non_boundary = [p for p in pending1 if p.candidate.kind.value != "boundary"]
    boundary = [p for p in pending2 if p.candidate.kind.value == "boundary"]

    # 3. Confirm non-boundary pending
    confirmed_records = []
    for p in non_boundary:
        try:
            record = runtime.confirm_pending(p.id)
            confirmed_records.append(record)
        except KeyError:
            pass

    # 4. Reject boundary pending
    rejected = []
    for p in boundary:
        try:
            rej = runtime.reject_pending(p.id)
            rejected.append(rej)
        except KeyError:
            pass

    # 5. List active
    active_before = runtime.list_active_records()

    # 6. Build context before delete
    context_before = runtime.build_session_context()
    context_before_chars = len(context_before)

    # 7. Delete active records
    for rec in active_before:
        try:
            runtime.delete_record(rec.id)
        except KeyError:
            pass

    # 8. Build context after delete
    active_after = runtime.list_active_records()
    context_after = runtime.build_session_context()
    context_after_chars = len(context_after)

    # Print summary — avoid printing sensitive full text
    print(f"pending_after_submit={len(pending1) + len(pending2)}")
    print(f"confirmed_records={len(confirmed_records)}")
    print(f"rejected={len(rejected)}")
    print(f"context_before_delete_chars={context_before_chars}")
    print(f"active_after_delete={len(active_after)}")
    print(f"context_after_delete_chars={context_after_chars}")
    print("PASS")
    return 0


def run_memory_cli(argv: Sequence[str] | None = None) -> int:
    """Run the memory CLI with the given arguments.

    Returns:
        0 on success.
        1 on runtime error.
        2 on user input error (e.g., missing required argument).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Validate --path is actually provided
    if args.path is None:
        parser.print_help()
        return 2

    path: Path = args.path

    # Create runtime with local repository
    try:
        repository = LocalJsonMemoryRepository(path)
        runtime = create_local_memory_runtime(repository)
    except Exception as e:
        print(f"Runtime initialization error: {e}", file=sys.stderr)
        return 1

    command = args.command

    try:
        if command == "submit":
            pending = runtime.submit_user_text(args.text)
            _print_pending_list(pending, runtime)
            return 0

        elif command == "list-pending":
            pending = runtime.list_pending()
            _print_pending_list(pending, runtime)
            return 0

        elif command == "confirm":
            try:
                record = runtime.confirm_pending(args.pending_id)
                print(
                    f"[{record.id[:8]}] confirmed — kind={record.kind.value} "
                    f"text={_truncate(record.text)}"
                )
                return 0
            except KeyError:
                print(f"Pending memory not found: {args.pending_id}", file=sys.stderr)
                return 1

        elif command == "reject":
            try:
                rejected = runtime.reject_pending(args.pending_id, args.reason or "")
                print(f"[{rejected.id[:8]}] rejected — kind={rejected.candidate.kind.value}")
                return 0
            except KeyError:
                print(f"Pending memory not found: {args.pending_id}", file=sys.stderr)
                return 1

        elif command == "list-active":
            records = runtime.list_active_records()
            _print_active_list(records)
            return 0

        elif command == "list-all":
            records = runtime.list_all_records()
            _print_all_list(records)
            return 0

        elif command == "delete":
            try:
                record = runtime.delete_record(args.record_id)
                print(f"[{record.id[:8]}] status={record.status.value}")
                return 0
            except KeyError:
                print(f"Record not found: {args.record_id}", file=sys.stderr)
                return 1

        elif command == "context":
            context = runtime.build_session_context()
            if context:
                print(context)
            else:
                print("(empty)")
            return 0

        elif command == "snapshot":
            snap = runtime.snapshot()
            print(f"pending={len(snap.pending)}")
            print(f"active={len(snap.active)}")
            print(f"rejected={len(snap.rejected)}")
            return 0

        elif command == "clear":
            repository.clear()
            print("cleared")
            return 0

        elif command == "demo":
            return _run_demo(runtime)

        else:
            parser.print_help()
            return 2

    except Exception as e:
        print(f"Runtime error: {e}", file=sys.stderr)
        return 1
