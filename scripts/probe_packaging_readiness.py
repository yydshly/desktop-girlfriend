"""Packaging Readiness Probe (Phase 3-F).

No LLM/TTS/ASR, no GUI, no file writes, no network calls.
Checks that packaging prerequisites are in place.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Project root is the directory containing scripts/
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def main() -> int:
    print("Packaging Readiness Probe\n")

    # Add project root to path for imports
    sys.path.insert(0, str(PROJECT_ROOT))

    from app.packaging.readiness import (
        check_packaging_readiness,
        render_packaging_report,
    )

    report = check_packaging_readiness(PROJECT_ROOT)

    # Print individual results
    print(render_packaging_report(report))
    print()

    if report.ok:
        print("PASS")
        return 0
    else:
        print("FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
