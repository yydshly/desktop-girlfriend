r"""Memory confirmation probe script.

Run locally (no network, no LLM):
    .venv\Scripts\python.exe scripts\probe_memory_confirmation.py

Run a specific probe case:
    .venv\Scripts\python.exe scripts\probe_memory_confirmation.py --case-id preference_like
"""

from __future__ import annotations

import argparse
import sys

from app.brain.memory import DEFAULT_MEMORY_PROBE_CASES, DeterministicMemoryExtractor
from app.brain.memory.confirmation import (
    InMemoryMemoryConfirmationStore,
    MemoryConfirmationService,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Memory confirmation probe")
    parser.add_argument(
        "--case-id",
        type=str,
        default=None,
        help="Run only the specified case. "
             "Without this flag, runs a default set of cases.",
    )
    args = parser.parse_args()

    store = InMemoryMemoryConfirmationStore()
    service = MemoryConfirmationService(store)
    extractor = DeterministicMemoryExtractor()

    # Select cases to process
    if args.case_id is not None:
        cases = tuple(c for c in DEFAULT_MEMORY_PROBE_CASES if c.case_id == args.case_id)
        if not cases:
            available = [c.case_id for c in DEFAULT_MEMORY_PROBE_CASES]
            print(f"Error: no case with id {args.case_id!r}", file=sys.stderr)
            print(f"Available case_ids: {', '.join(available)}", file=sys.stderr)
            sys.exit(1)
    else:
        # Run a default set of cases for probe
        cases = tuple(c for c in DEFAULT_MEMORY_PROBE_CASES if c.case_id in {
            "preference_like",
            "relationship",
            "boundary",
        })

    print("Memory Confirmation Probe")
    print()

    # Extract candidates from selected cases
    all_candidates: list = []
    for case in cases:
        candidates = extractor.extract(case.user_text)
        all_candidates.extend(candidates)

    print(f"submitted_candidates: {len(all_candidates)}")
    print()

    # Submit to confirmation service
    pending = service.submit_candidates(tuple(all_candidates))
    print(f"pending: {len(pending)}")
    print()

    # Show pending memories
    if pending:
        print("pending memories:")
        for p in pending:
            print(f"  id={p.id[:8]}... kind={p.candidate.kind.value} text={p.candidate.text[:40]}...")
        print()

    # Auto-confirm the first pending
    if pending:
        first_id = pending[0].id
        confirmed = service.confirm(first_id)
        print(f"confirm first: id={confirmed.id[:8]}...")

    # Auto-reject the second pending (if exists)
    remaining = service.list_pending()
    if len(remaining) >= 2:
        second_id = remaining[1].id
        rejected = service.reject(second_id, reason="probe_rejected")
        print(f"reject second: id={rejected.id[:8]}... reason={rejected.reason}")

    print()

    # Show final state
    final_pending = service.list_pending()
    final_confirmed = service.list_confirmed()
    final_rejected = service.list_rejected()

    print("final:")
    print(f"  pending: {len(final_pending)}")
    print(f"  confirmed: {len(final_confirmed)}")
    print(f"  rejected: {len(final_rejected)}")

    if final_confirmed:
        print()
        print("confirmed memories:")
        for c in final_confirmed:
            print(f"  id={c.id[:8]}... kind={c.candidate.kind.value} text={c.candidate.text[:40]}...")

    if final_rejected:
        print()
        print("rejected memories:")
        for r in final_rejected:
            print(f"  id={r.id[:8]}... kind={r.candidate.kind.value} reason={r.reason}")

    if final_pending:
        print()
        print("remaining pending:")
        for p in final_pending:
            print(f"  id={p.id[:8]}... kind={p.candidate.kind.value} text={p.candidate.text[:40]}...")


if __name__ == "__main__":
    main()
