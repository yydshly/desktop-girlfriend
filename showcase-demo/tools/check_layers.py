from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAYER_DIR = ROOT / "assets" / "avatar" / "layers"
MANIFEST = LAYER_DIR / "manifest.json"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing_required: list[str] = []

    print("Status  Required  Role              File")
    print("------  --------  ----------------  ----------------------")

    for layer in manifest.get("layers", []):
        role = layer["role"]
        file_name = layer["file"]
        required = layer.get("required", True)
        exists = (LAYER_DIR / file_name).exists()
        status = "OK" if exists else "MISS"
        print(f"{status:<6}  {str(required):<8}  {role:<16}  {file_name}")
        if required and not exists:
            missing_required.append(file_name)

    if missing_required:
        print()
        print("Required layer PNGs are missing:")
        for file_name in missing_required:
            print(f"- assets/avatar/layers/{file_name}")
        return 1

    print()
    print("All required PNG puppet layers are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
