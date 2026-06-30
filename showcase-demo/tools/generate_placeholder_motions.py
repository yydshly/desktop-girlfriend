"""Generate placeholder WebM motion loops from the character reference image.

These videos are intentionally simple. They are not final animation assets; they
exist to exercise the same loading path as future MiniMax/Hailuo/Live2D exports.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MotionSpec:
    name: str
    amplitude: float
    period: float


MOTIONS = (
    MotionSpec("walking", 0.018, 2.0),
    MotionSpec("wave", 0.024, 1.2),
    MotionSpec("heart", 0.014, 1.6),
    MotionSpec("point", 0.020, 1.5),
    MotionSpec("think", 0.010, 2.4),
    MotionSpec("sing", 0.022, 1.4),
    MotionSpec("idle-wave", 0.014, 2.0),
    MotionSpec("idle-stretch", 0.009, 2.8),
    MotionSpec("idle-read", 0.006, 3.0),
    MotionSpec("idle-drink", 0.012, 1.9),
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    source = root / "assets" / "reference" / "character-reference.png"
    output_dir = root / "assets" / "motions"
    ffmpeg = shutil.which("ffmpeg")

    if ffmpeg is None:
        print("ffmpeg not found on PATH.")
        return 1
    if not source.exists():
        print(f"Missing character reference: {source}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    for motion in MOTIONS:
        output = output_dir / f"{motion.name}.webm"
        angle = f"{motion.amplitude}*sin(6.283185*t/{motion.period})"
        video_filter = (
            "scale=400:-2,"
            "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x111820,"
            f"rotate={angle}:fillcolor=0x111820,"
            "fps=24,format=yuv420p"
        )
        command = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-loop",
            "1",
            "-i",
            str(source),
            "-t",
            "4",
            "-vf",
            video_filter,
            "-c:v",
            "libvpx-vp9",
            "-b:v",
            "0",
            "-crf",
            "34",
            "-an",
            str(output),
        ]
        subprocess.run(command, check=True)
        print(f"generated {output.relative_to(root)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
