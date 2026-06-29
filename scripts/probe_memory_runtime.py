r"""Memory runtime probe script.

Run locally (no network, no LLM):
    .venv\Scripts\python.exe scripts/probe_memory_runtime.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.brain.memory.repository import LocalJsonMemoryRepository
from app.brain.memory.runtime import create_local_memory_runtime


def main() -> None:
    print("Memory Runtime Probe")
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "memory.json"
        repository = LocalJsonMemoryRepository(path)
        runtime = create_local_memory_runtime(repository)

        # Submit user texts
        pending1 = runtime.submit_user_text("我喜欢你回复短一点。")
        pending2 = runtime.submit_user_text("我女朋友叫红红，这件事不要记住。")
        print(f"pending_after_submit: {len(pending1) + len(pending2)}")

        # Confirm first pending (preference)
        if pending1:
            confirmed = runtime.confirm_pending(pending1[0].id)
            print(f"confirmed_records: 1 (id={confirmed.id[:8]}...)")

        # Reject boundary pending
        if pending2:
            rejected = runtime.reject_pending(pending2[0].id, reason="user_declined")
            print(f"rejected: 1 (reason={rejected.reason})")

        # List active records
        active = runtime.list_active_records()
        print(f"active_after_confirm: {len(active)}")

        # Build session context
        context_before = runtime.build_session_context()
        print(f"context_before_delete_chars: {len(context_before)}")

        # Delete the active record
        if active:
            deleted = runtime.delete_record(active[0].id)
            print(f"deleted_status: {deleted.status.value}")

        # Build context again
        context_after = runtime.build_session_context()
        print(f"context_after_delete_chars: {len(context_after)}")

        # Final state
        final_active = runtime.list_active_records()
        print(f"active_after_delete: {len(final_active)}")

        print()
        print("PASS")


if __name__ == "__main__":
    main()
