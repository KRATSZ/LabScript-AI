#!/usr/bin/env python3
"""
Convert LabelMe JSON exports to YOLOv8 detection labels (normalized xywh).

Expects:
  - One LabelMe JSON per image (same stem as .jpg/.jpeg/.png).
  - Rectangle or polygon shapes; polygons are converted to axis-aligned bounding boxes.
  - Classes listed in a text file, one name per line (index = class id).

Ignores shapes whose label is not in the class list (e.g. deck_quad for geometry-only).

Optional:
  - --val-ratio: split labeled images into images/train and images/val (sidecars copied per split).
  - Sidecars: if --images/<stem> has a sibling path --images/labels/<stem>.labels.json
    (e.g. from export_deck_sidecars_from_labelme.py), copy to output
    images/{train|val}/labels/<stem>.labels.json next to the copied image.

Example:
  uv run python vision/scripts/labelme_to_yolo.py \\
    --images vision/data/frames/samples \\
    --labelme-dir vision/data/frames/samples \\
    --classes vision/data/datasets/classes.txt \\
    --out vision/data/datasets/yolo_pilot \\
    --background-images deck_vid2_07.jpg \\
    --val-ratio 0.2 --seed 42
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path


def polygon_to_bbox(points: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def to_yolo_line(
    cls_id: int,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    img_w: int,
    img_h: int,
) -> str:
    w = x2 - x1
    h = y2 - y1
    cx = x1 + w / 2
    cy = y1 + h / 2
    return f"{cls_id} {cx/img_w:.6f} {cy/img_h:.6f} {w/img_w:.6f} {h/img_h:.6f}"


def parse_yolo_lines_from_labelme(data: dict, name_to_id: dict[str, int], w: int, h: int) -> list[str]:
    lines: list[str] = []
    for sh in data.get("shapes", []):
        label = str(sh.get("label", "")).strip()
        if label not in name_to_id:
            continue
        cid = name_to_id[label]
        st = sh.get("shape_type", "")
        pts = sh.get("points", [])
        if not pts:
            continue
        if st == "rectangle" and len(pts) >= 2:
            (x1, y1), (x2, y2) = pts[0], pts[1]
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
        elif st == "polygon":
            x1, y1, x2, y2 = polygon_to_bbox(pts)
        else:
            continue
        x1 = max(0, min(w, x1))
        x2 = max(0, min(w, x2))
        y1 = max(0, min(h, y1))
        y2 = max(0, min(h, y2))
        if x2 <= x1 or y2 <= y1:
            continue
        lines.append(to_yolo_line(cid, x1, y1, x2, y2, w, h))
    return lines


def copy_sidecar_if_present(
    src_images_dir: Path,
    stem: str,
    dst_image_path: Path,
) -> None:
    side = src_images_dir / "labels" / f"{stem}.labels.json"
    if not side.is_file():
        return
    dest_dir = dst_image_path.parent / "labels"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{stem}.labels.json"
    shutil.copy2(side, dest)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--images", type=Path, required=True, help="Directory of images")
    ap.add_argument("--labelme-dir", type=Path, required=True, help="Directory of LabelMe JSON files")
    ap.add_argument("--classes", type=Path, required=True, help="classes.txt one class per line")
    ap.add_argument("--out", type=Path, required=True, help="Output YOLO dataset root")
    ap.add_argument(
        "--background-images",
        nargs="*",
        default=[],
        metavar="FILENAME",
        help="Files in --images with no JSON: copy + empty label txt (YOLO background)",
    )
    ap.add_argument(
        "--val-ratio",
        type=float,
        default=0.0,
        help="Fraction of labeled images to put in val (0 = train only, val yaml points to train)",
    )
    ap.add_argument("--seed", type=int, default=42, help="RNG seed for val split")
    args = ap.parse_args()

    names = [ln.strip() for ln in args.classes.read_text(encoding="utf-8").splitlines() if ln.strip()]
    name_to_id = {n: i for i, n in enumerate(names)}

    img_dir = args.images.expanduser().resolve()
    json_dir = args.labelme_dir.expanduser().resolve()
    out_root = args.out.expanduser().resolve()

    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

    labeled: list[tuple[Path, list[str], str]] = []
    for img_path in sorted(img_dir.iterdir()):
        if not img_path.is_file() or img_path.suffix.lower() not in exts:
            continue
        jpath = json_dir / f"{img_path.stem}.json"
        if not jpath.is_file():
            continue
        data = json.loads(jpath.read_text(encoding="utf-8"))
        h, w = data.get("imageHeight"), data.get("imageWidth")
        if not h or not w:
            print(f"Skip {jpath.name}: missing imageHeight/imageWidth", file=sys.stderr)
            continue
        lines = parse_yolo_lines_from_labelme(data, name_to_id, int(w), int(h))
        labeled.append((img_path, lines, img_path.stem))

    rng = random.Random(args.seed)
    val_ratio = max(0.0, min(0.9, float(args.val_ratio)))

    train_items: list[tuple[Path, list[str], str]] = []
    val_items: list[tuple[Path, list[str], str]] = []

    if val_ratio > 0.0 and len(labeled) >= 2:
        idx = list(range(len(labeled)))
        rng.shuffle(idx)
        n_val = max(1, int(round(len(labeled) * val_ratio)))
        n_val = min(n_val, len(labeled) - 1)
        val_set = set(idx[:n_val])
        for i, item in enumerate(labeled):
            if i in val_set:
                val_items.append(item)
            else:
                train_items.append(item)
    else:
        train_items = list(labeled)
        val_items = []

    def write_split(
        items: list[tuple[Path, list[str], str]],
        split: str,
    ) -> int:
        (out_root / "images" / split).mkdir(parents=True, exist_ok=True)
        (out_root / "labels" / split).mkdir(parents=True, exist_ok=True)
        n = 0
        for img_path, lines, stem in items:
            dst_img = out_root / "images" / split / img_path.name
            dst_img.write_bytes(img_path.read_bytes())
            (out_root / "labels" / split / f"{stem}.txt").write_text(
                "\n".join(lines) + ("\n" if lines else ""),
                encoding="utf-8",
            )
            copy_sidecar_if_present(img_dir, stem, dst_img)
            n += 1
        return n

    train_n = write_split(train_items, "train")
    val_n = write_split(val_items, "val") if val_items else 0

    for fname in args.background_images:
        img_path = img_dir / fname
        if not img_path.is_file():
            print(f"Skip background (not found): {fname}", file=sys.stderr)
            continue
        if img_path.suffix.lower() not in exts:
            print(f"Skip background (unsupported ext): {fname}", file=sys.stderr)
            continue
        dst_img = out_root / "images" / "train" / img_path.name
        dst_img.write_bytes(img_path.read_bytes())
        (out_root / "labels" / "train" / f"{img_path.stem}.txt").write_text("", encoding="utf-8")
        train_n += 1
        print(f"Background image (empty labels): {fname}", file=sys.stderr)

    names_yaml = "\n".join(f"  - {n}" for n in names)
    yaml = out_root / "dataset.yaml"
    if val_n > 0:
        val_path = "images/val"
    else:
        val_path = "images/train"
    yaml.write_text(
        f"path: {out_root.as_posix()}\n"
        "train: images/train\n"
        f"val: {val_path}\n"
        f"nc: {len(names)}\n"
        "names:\n"
        f"{names_yaml}\n",
        encoding="utf-8",
    )
    print(
        f"Converted train={train_n} val={val_n} (labeled src={len(labeled)}) -> {out_root}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
