"""Normalize an external motion video into the showcase WebM format.

Example:
    python tools/normalize_motion.py wave C:\Downloads\wave.mp4 --replace

Without --replace, the script writes a .candidate.webm next to the final asset.
Use --replace when you want the showcase page to load it immediately.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def load_motion_keys(root: Path) -> dict[str, str]:
    manifest_path = root / "assets" / "asset-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return dict(manifest["motions"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize a motion video for showcase-demo.")
    parser.add_argument("motion_key", help="Motion key from assets/asset-manifest.json, e.g. wave")
    parser.add_argument("input_video", help="Input video path, e.g. wave.mp4")
    parser.add_argument("--replace", action="store_true", help="Overwrite the active showcase WebM")
    parser.add_argument("--duration", type=float, default=4.0, help="Output duration in seconds")
    parser.add_argument("--width", type=int, default=1280, help="Output width")
    parser.add_argument("--height", type=int, default=720, help="Output height")
    parser.add_argument("--crf", type=int, default=32, help="VP9 CRF, lower is higher quality")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    input_video = Path(args.input_video).expanduser().resolve()
    ffmpeg = shutil.which("ffmpeg")
    motion_map = load_motion_keys(root)

    if ffmpeg is None:
        print("ffmpeg not found on PATH.")
        return 1
    if args.motion_key not in motion_map:
        valid = ", ".join(sorted(motion_map))
        print(f"Unknown motion key: {args.motion_key}")
        print(f"Valid keys: {valid}")
        return 1
    if not input_video.exists():
        print(f"Input video not found: {input_video}")
        return 1

    final_output = root / motion_map[args.motion_key]
    output = final_output if args.replace else final_output.with_suffix(".candidate.webm")
    output.parent.mkdir(parents=True, exist_ok=True)

    video_filter = (
        f"scale={args.width}:{args.height}:force_original_aspect_ratio=decrease,"
        f"pad={args.width}:{args.height}:(ow-iw)/2:(oh-ih)/2:color=0x111820,"
        "fps=24,format=yuv420p"
    )
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_video),
        "-t",
        str(args.duration),
        "-vf",
        video_filter,
        "-an",
        "-c:v",
        "libvpx-vp9",
        "-b:v",
        "0",
        "-crf",
        str(args.crf),
        str(output),
    ]

    subprocess.run(command, check=True)
    print(f"wrote {output.relative_to(root)}")
    if not args.replace:
        print("Preview this candidate first. Re-run with --replace to activate it in the showcase.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
