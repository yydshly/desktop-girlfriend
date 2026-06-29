r"""Memory extraction probe script.

Run locally (no network, no LLM):
    .venv\Scripts\python.exe scripts\probe_memory_extraction.py

Run a specific case:
    .venv\Scripts\python.exe scripts\probe_memory_extraction.py --case-id preference_like
"""

from __future__ import annotations

import argparse
import sys

from app.brain.memory import DEFAULT_MEMORY_PROBE_CASES, DeterministicMemoryExtractor
from app.brain.memory.probe_cases import MemoryProbeCase


def main() -> None:
    parser = argparse.ArgumentParser(description="Memory extraction probe")
    parser.add_argument(
        "--case-id",
        type=str,
        default=None,
        help="Run only the specified case. "
             "Without this flag, all DEFAULT_MEMORY_PROBE_CASES are run.",
    )
    args = parser.parse_args()

    if args.case_id is not None:
        cases = tuple(c for c in DEFAULT_MEMORY_PROBE_CASES if c.case_id == args.case_id)
        if not cases:
            available = [c.case_id for c in DEFAULT_MEMORY_PROBE_CASES]
            print(f"Error: no case with id {args.case_id!r}", file=sys.stderr)
            print(f"Available case_ids: {', '.join(available)}", file=sys.stderr)
            sys.exit(1)
    else:
        cases = DEFAULT_MEMORY_PROBE_CASES

    extractor = DeterministicMemoryExtractor()

    total = len(cases)
    passed = 0
    failed = 0

    print("Memory Extraction Probe")
    print(f"total_cases: {total}")
    print()

    for case in cases:
        candidates = extractor.extract(case.user_text)
        result = _evaluate_case(case, candidates)
        if result:
            passed += 1
        else:
            failed += 1

        print(f"[{case.case_id}]")
        print("user:")
        print(case.user_text)
        print()
        print("candidates:")
        if candidates:
            for c in candidates:
                print(f"- kind: {c.kind.value}")
                print(f"  importance: {c.importance.value}")
                print(f"  confidence: {c.confidence}")
                print(f"  text: {c.text}")
                print(f"  evidence: {c.evidence}")
        else:
            print("- (none)")
        print()
        print("expected_kinds:")
        for k in case.expected_kinds:
            print(f"- {k}")
        print()
        print(f"expected_count: {case.expected_count_min}-{case.expected_count_max}")
        print(f"actual_count: {len(candidates)}")
        print()
        print(f"result: {'PASS' if result else 'FAIL'}")
        print()
        print("---")

    print()
    print(f"Summary: total={total}, passed={passed}, failed={failed}")


def _evaluate_case(case: MemoryProbeCase, candidates: tuple) -> bool:
    # Check count range
    if not (case.expected_count_min <= len(candidates) <= case.expected_count_max):
        return False
    # Check that all expected kinds are present
    actual_kinds = {c.kind.value for c in candidates}
    for expected_kind in case.expected_kinds:
        if expected_kind not in actual_kinds:
            return False
    return True


if __name__ == "__main__":
    main()
