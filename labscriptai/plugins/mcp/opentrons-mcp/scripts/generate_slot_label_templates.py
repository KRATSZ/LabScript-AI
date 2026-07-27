#!/usr/bin/env python3
"""
Emit empty per-image JSON templates for MVP CHECKSLOT labeling (12 Flex slots).

Usage (from repo root):
  uv run python mcp-servers/opentrons-mcp/scripts/generate_slot_label_templates.py \\
    --images-dir artifacts/camera-captures/mvp-annotation-batch \\
    --out-dir artifacts/camera-captures/mvp-annotation-batch/labels

Fill each JSON: for every slot set one of
  tiprack | plate | reservoir | module | trash_bin | empty | unknown
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FLEX_SLOTS = [
    "A1",
    "A2",
    "A3",
    "B1",
    "B2",
    "B3",
    "C1",
    "C2",
    "C3",
    "D1",
    "D2",
    "D3",
]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--images-dir",
        type=Path,
        default=Path("artifacts/camera-captures/mvp-annotation-batch"),
        help="Directory containing *.jpeg deck images",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("artifacts/camera-captures/mvp-annotation-batch/labels"),
        help="Where to write <stem>.labels.json templates",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing template files",
    )
    args = p.parse_args()

    img_dir: Path = args.images_dir
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    images = sorted(img_dir.glob("*.jpeg")) + sorted(img_dir.glob("*.jpg"))
    if not images:
        raise SystemExit(f"No JPEGs under {img_dir}")

    empty_slots = {s: "unknown" for s in FLEX_SLOTS}
    written = 0
    skipped = 0
    for img in images:
        dest = out_dir / f"{img.stem}.labels.json"
        if dest.exists() and not args.force:
            skipped += 1
            continue
        payload = {
            "image_file": img.name,
            "slots": dict(empty_slots),
            "notes": "",
            "optional_deck_corners_norm": None,
        }
        dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written += 1

    print(f"Wrote {written} templates to {out_dir} (skipped existing: {skipped})")


if __name__ == "__main__":
    main()
