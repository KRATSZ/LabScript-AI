#!/usr/bin/env python3
"""
Stratified random frame extraction from a video (ffmpeg + ffprobe).

Splits the usable timeline into N buckets and picks one random timestamp per bucket,
so frames spread across the whole clip instead of clustering.

Requires: ffmpeg and ffprobe (PATH, or common Homebrew paths on macOS).

Example:
  uv run python vision/scripts/sample_frames.py vision/data/raw_videos/deck.mp4 -o vision/data/frames/samples -n 20
"""
from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path


def _resolve_bin(name: str) -> str:
    p = shutil.which(name)
    if p:
        return p
    for prefix in ("/opt/homebrew/bin", "/usr/local/bin"):
        cand = Path(prefix) / name
        if cand.is_file():
            return str(cand)
    return name


_FFMPEG = _resolve_bin("ffmpeg")
_FFPROBE = _resolve_bin("ffprobe")
_VISION_ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stderr}")
    return p.stdout.strip()


def probe_duration_seconds(video: Path) -> float:
    out = _run(
        [
            _FFPROBE,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video),
        ]
    )
    return float(out)


def extract_frame(video: Path, t_sec: float, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        _FFMPEG,
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{t_sec:.3f}",
        "-i",
        str(video),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        "-y",
        str(out_path),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {p.stderr}")


def stratified_timestamps(
    duration: float,
    n: int,
    *,
    trim_start: float,
    trim_end: float,
    seed: int | None,
) -> list[float]:
    usable_lo = trim_start
    usable_hi = max(usable_lo + 0.01, duration - trim_end)
    span = usable_hi - usable_lo
    if span <= 0:
        raise ValueError("trim_start/trim_end leave no usable duration")
    if n < 1:
        raise ValueError("n must be >= 1")

    rng = random.Random(seed)
    bucket = span / n
    times: list[float] = []
    for i in range(n):
        lo = usable_lo + i * bucket
        hi = usable_lo + (i + 1) * bucket
        times.append(rng.uniform(lo, hi))
    return times


def safe_stem(name: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", name)[:120]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video", type=Path, help="Input video path")
    ap.add_argument(
        "-o",
        "--out-dir",
        type=Path,
        default=_VISION_ROOT / "data" / "frames" / "samples",
        help="Output directory for JPEGs",
    )
    ap.add_argument("-n", "--num", type=int, default=20, help="Number of frames to sample")
    ap.add_argument("--trim-start", type=float, default=0.5, help="Skip first N seconds")
    ap.add_argument("--trim-end", type=float, default=0.5, help="Skip last N seconds")
    ap.add_argument("--seed", type=int, default=None, help="RNG seed for reproducibility")
    ap.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Write JSON manifest (default: <out-dir>/sample_manifest.json)",
    )
    args = ap.parse_args()

    video = args.video.expanduser().resolve()
    if not video.is_file():
        print(f"Video not found: {video}", file=sys.stderr)
        return 2

    try:
        duration = probe_duration_seconds(video)
    except Exception as e:
        print(f"ffprobe failed: {e}", file=sys.stderr)
        print("Install ffmpeg (e.g. brew install ffmpeg).", file=sys.stderr)
        if not shutil.which("ffprobe") and not Path("/opt/homebrew/bin/ffprobe").is_file():
            print(f"Tried: {_FFPROBE}", file=sys.stderr)
        return 3

    times = stratified_timestamps(
        duration,
        args.num,
        trim_start=args.trim_start,
        trim_end=args.trim_end,
        seed=args.seed,
    )

    out_dir = args.out_dir.expanduser().resolve()
    stem = safe_stem(video.stem)
    manifest: dict = {
        "video": str(video),
        "duration_sec": duration,
        "num_frames": args.num,
        "trim_start": args.trim_start,
        "trim_end": args.trim_end,
        "seed": args.seed,
        "frames": [],
    }

    for idx, t in enumerate(times):
        name = f"{stem}_t{t:.3f}s_{idx:03d}.jpg"
        out_path = out_dir / name
        try:
            extract_frame(video, t, out_path)
        except Exception as e:
            print(f"Frame {idx} @ {t:.3f}s failed: {e}", file=sys.stderr)
            return 4
        manifest["frames"].append({"time_sec": t, "path": str(out_path)})
        print(out_path)

    mpath = args.manifest or (out_dir / "sample_manifest.json")
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote manifest: {mpath}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
