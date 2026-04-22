#!/usr/bin/env python3
"""
Read LabelMe JSON, extract polygon label `deck_quad`, write MCP-compatible sidecar:

  <images-dir>/labels/<stem>.labels.json

with `optional_deck_corners_norm`: four [nx, ny] in [0,1], order
A1 → A3 → D3 → D1 (clockwise, deck view) — same as docs/LABELME.md and vision_check.

Does not modify LabelMe files.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DECK_CORNER_ORDER_DOC = "A1_A3_D3_D1_clockwise_deck_view"


def _pick_unique_point_indices(points: list[list[float]]) -> list[int] | None:
    scorers = [
        lambda p: p[0] + p[1],   # A1: top-left
        lambda p: -(p[0] - p[1]),  # A3: top-right
        lambda p: -(p[0] + p[1]),  # D3: bottom-right
        lambda p: p[0] - p[1],  # D1: bottom-left
    ]
    chosen: list[int] = []
    used: set[int] = set()
    for scorer in scorers:
        ranked = sorted(range(len(points)), key=lambda idx: scorer(points[idx]))
        found = next((idx for idx in ranked if idx not in used), None)
        if found is None:
            return None
        chosen.append(found)
        used.add(found)
    if len(set(chosen)) != 4:
        return None
    return chosen


def _ordered_deck_corners(points: list[list[float]]) -> list[list[float]] | None:
    if len(points) < 4:
        return None
    picked = _pick_unique_point_indices(points)
    if picked is None:
        return None
    return [points[idx] for idx in picked]


def extract_deck_quad_norm(labelme: dict) -> list[list[float]] | None:
    h = int(labelme.get("imageHeight") or 0)
    w = int(labelme.get("imageWidth") or 0)
    if h < 1 or w < 1:
        return None
    for sh in labelme.get("shapes", []):
        if str(sh.get("label", "")).strip() != "deck_quad":
            continue
        if sh.get("shape_type") != "polygon":
            continue
        pts = sh.get("points") or []
        ordered = _ordered_deck_corners(pts)
        if ordered is None:
            continue
        out: list[list[float]] = []
        for p in ordered:
            if not isinstance(p, (list, tuple)) or len(p) < 2:
                return None
            x, y = float(p[0]), float(p[1])
            out.append([max(0.0, min(1.0, x / w)), max(0.0, min(1.0, y / h))])
        return out
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--labelme-dir",
        type=Path,
        required=True,
        help="Directory containing LabelMe *.json (same stem as images)",
    )
    ap.add_argument(
        "--images-dir",
        type=Path,
        required=True,
        help="Directory of images (used for image_file name and output path)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions only",
    )
    args = ap.parse_args()

    labelme_dir = args.labelme_dir.expanduser().resolve()
    images_dir = args.images_dir.expanduser().resolve()
    out_labels = images_dir / "labels"
    if not args.dry_run:
        out_labels.mkdir(parents=True, exist_ok=True)

    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    written = 0
    skipped_stems: list[str] = []
    for jpath in sorted(labelme_dir.glob("*.json")):
        if jpath.name in {"pool_manifest.json", "rename_map.json"} or jpath.name.startswith("manifest_"):
            continue
        data = json.loads(jpath.read_text(encoding="utf-8"))
        stem = jpath.stem
        corners = extract_deck_quad_norm(data)
        img_candidates = [images_dir / f"{stem}{e}" for e in exts]
        img_path = next((p for p in img_candidates if p.is_file()), None)
        image_file = img_path.name if img_path else f"{stem}.jpg"

        dest = out_labels / f"{stem}.labels.json"
        if corners is None:
            if img_path is not None:
                skipped_stems.append(stem)
            continue

        payload = {
            "image_file": image_file,
            "optional_deck_corners_norm": corners,
            "corner_order_doc": DECK_CORNER_ORDER_DOC,
        }
        if args.dry_run:
            print(f"would write {dest}")
            written += 1
            continue
        dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written += 1

    print(
        f"Wrote {written} sidecars under {out_labels}; "
        f"missing_or_invalid deck_quad (image present): {len(skipped_stems)}"
        + (f" [{', '.join(skipped_stems[:5])}]" if skipped_stems else ""),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
