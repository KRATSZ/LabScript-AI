#!/usr/bin/env python3
"""
Rename files under data/frames/samples/ to short stable names:

  deck_vid1_01.jpg .. deck_vid1_10.jpg  (per input video, ordered by time_sec)
  deck_mvp_01.jpeg ..                     (MVP batch copies, sorted by old basename)

Refreshes manifest_*.json frame paths and rebuilds pool_manifest.json.
Writes rename_map.json (from -> to for this run).

Re-run safe: skips when file already has target name.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    samples = root / "data/frames/samples"
    if not samples.is_dir():
        print(f"No directory: {samples}", file=sys.stderr)
        return 1

    rename_log: list[dict[str, str]] = []

    manifest_paths = sorted(p for p in samples.glob("manifest_*.json") if p.name != "pool_manifest.json")
    video_stems = sorted({p.stem.removeprefix("manifest_") for p in manifest_paths})

    for vid_n, stem in enumerate(video_stems, start=1):
        mf = samples / f"manifest_{stem}.json"
        if not mf.is_file():
            continue
        data = json.loads(mf.read_text(encoding="utf-8"))
        frames = sorted(data.get("frames", []), key=lambda x: float(x.get("time_sec", 0)))
        new_frames: list[dict] = []
        for i, fr in enumerate(frames, start=1):
            old_path = Path(fr["path"]).resolve()
            new_name = f"deck_vid{vid_n}_{i:02d}.jpg"
            new_path = (samples / new_name).resolve()
            if not old_path.is_file():
                print(f"Skip missing: {old_path}", file=sys.stderr)
                new_frames.append(fr)
                continue
            if old_path.name != new_name:
                if new_path.exists():
                    print(f"Refuse overwrite: {new_path}", file=sys.stderr)
                    return 2
                old_path.rename(new_path)
                rename_log.append({"from": old_path.name, "to": new_name})
            fr = dict(fr)
            fr["path"] = str(new_path)
            new_frames.append(fr)
        data["frames"] = new_frames
        mf.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    mvp_files = sorted(
        list(samples.glob("mvp_*.jpeg")) + list(samples.glob("mvp_*.jpg")),
        key=lambda p: p.name.lower(),
    )
    for i, old_path in enumerate(mvp_files, start=1):
        ext = old_path.suffix.lower()
        new_name = f"deck_mvp_{i:02d}{ext}"
        new_path = samples / new_name
        if old_path.name == new_name:
            continue
        if new_path.exists():
            print(f"Refuse overwrite: {new_path}", file=sys.stderr)
            return 2
        rename_log.append({"from": old_path.name, "to": new_name})
        old_path.rename(new_path)

    # Rebuild pool_manifest.json from manifests + deck_mvp_*
    entries: list[dict] = []
    for stem in video_stems:
        mf = samples / f"manifest_{stem}.json"
        if not mf.is_file():
            continue
        data = json.loads(mf.read_text(encoding="utf-8"))
        video_path = data.get("video", "")
        for fr in data.get("frames", []):
            entries.append(
                {
                    "source": "video_sample",
                    "video": video_path,
                    "manifest": mf.name,
                    "time_sec": fr.get("time_sec"),
                    "path": fr.get("path"),
                }
            )
    for p in sorted(samples.glob("deck_mvp_*.jpeg")) + sorted(samples.glob("deck_mvp_*.jpg")):
        entries.append({"source": "mvp_annotation_batch", "path": str(p.resolve())})

    jpg_n = len(list(samples.glob("deck_vid*.jpg")))
    mvp_j = len(list(samples.glob("deck_mvp*.jpeg")))
    mvp_j2 = len(list(samples.glob("deck_mvp*.jpg")))
    pool = {
        "summary": {
            "samples_dir": str(samples.resolve()),
            "video_manifests": [f"manifest_{s}.json" for s in video_stems],
            "mvp_copies": mvp_j + mvp_j2,
            "jpg_count": jpg_n,
            "jpeg_count": mvp_j + mvp_j2,
            "total_images": jpg_n + mvp_j + mvp_j2,
            "naming": "deck_vid{N}_{ff}.jpg from video; deck_mvp_{nn}.jpeg from MVP batch",
        },
        "entries": entries,
    }
    (samples / "pool_manifest.json").write_text(json.dumps(pool, indent=2, ensure_ascii=False), encoding="utf-8")

    prev = samples / "rename_map.json"
    history: list = []
    if prev.is_file():
        try:
            raw = json.loads(prev.read_text(encoding="utf-8"))
            history = raw.get("renames_cumulative") or raw.get("renames") or []
        except json.JSONDecodeError:
            pass
    (samples / "rename_map.json").write_text(
        json.dumps(
            {
                "samples_dir": str(samples.resolve()),
                "renames_this_run": rename_log,
                "renames_cumulative": history + rename_log,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"Renamed {len(rename_log)} files this run. pool_manifest.json updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
