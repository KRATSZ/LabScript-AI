#!/usr/bin/env python3
"""
Move unlabeled images out of samples/, keep one negative sample, copy a few to predict_probe/.

Unlabeled = image in samples/ with no same-stem .json (excluding meta files).
"""
from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path

_VISION_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--samples", type=Path, default=_VISION_ROOT / "data" / "frames" / "samples")
    ap.add_argument("--unused", type=Path, default=_VISION_ROOT / "data" / "frames" / "unused")
    ap.add_argument("--probe", type=Path, default=_VISION_ROOT / "data" / "frames" / "predict_probe")
    ap.add_argument(
        "--keep-negative",
        default="deck_vid2_07.jpg",
        help="Unlabeled image to KEEP in samples (YOLO background, no JSON)",
    )
    ap.add_argument("--probe-n", type=int, default=5, help="Random unlabeled copies for predict demo")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    samples = args.samples.expanduser().resolve()
    unused = args.unused.expanduser().resolve()
    probe = args.probe.expanduser().resolve()
    unused.mkdir(parents=True, exist_ok=True)
    probe.mkdir(parents=True, exist_ok=True)

    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    meta_json = {"pool_manifest.json", "rename_map.json"}

    unlabeled: list[Path] = []
    for p in sorted(samples.iterdir()):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        if p.name == args.keep_negative:
            continue
        j = samples / f"{p.stem}.json"
        if j.is_file():
            continue
        unlabeled.append(p)

    rng = random.Random(args.seed)
    k = min(args.probe_n, len(unlabeled))
    probe_pick = set(rng.sample(unlabeled, k=k)) if k else set()

    for p in sorted(probe_pick):
        shutil.copy2(p, probe / p.name)

    moved = 0
    for p in unlabeled:
        dest = unused / p.name
        shutil.move(str(p), str(dest))
        moved += 1

    print(f"Copied {len(probe_pick)} -> {probe}")
    print(f"Moved {moved} unlabeled -> {unused}")
    print(f"Kept negative in samples: {args.keep_negative}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
