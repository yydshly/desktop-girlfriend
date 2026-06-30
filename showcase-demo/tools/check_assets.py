"""Check which showcase assets are present.

This script is intentionally dependency-free.
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "assets" / "asset-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    rows: list[tuple[str, str, str, str]] = []

    for asset_type, group_name in (
        ("background", "backgrounds"),
        ("reference", "references"),
        ("motion", "motions"),
    ):
        for key, relative_path in manifest[group_name].items():
            exists = (root / relative_path).exists()
            rows.append(("OK" if exists else "MISSING", asset_type, key, relative_path))

    widths = [max(len(row[index]) for row in rows + [("Status", "Type", "Key", "Path")]) for index in range(4)]
    header = ("Status", "Type", "Key", "Path")
    print("  ".join(value.ljust(widths[index]) for index, value in enumerate(header)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))

    missing = [row for row in rows if row[0] == "MISSING"]
    print()
    if missing:
        print(
            f"{len(missing)} asset(s) missing. "
            "The showcase will use CSS/Canvas fallbacks for missing motion files."
        )
        return 2

    print("All showcase assets are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
