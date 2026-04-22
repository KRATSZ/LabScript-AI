#!/usr/bin/env python3
"""
Run trained Ultralytics YOLO weights on images and emit deck observation JSON:

- optional_deck_corners_norm from sidecar (images/.../labels/<stem>.labels.json) when present
- slot_mapping method deck_homography vs uniform_image_grid
- observed_items: per detection with bbox, class name, confidence, slot, deck_plane_norm
- slot_observations: per A1..D3 geometric occupancy (same spirit as MCP vision_check)

Usage (from repo root):
  uv run python vision/scripts/deck_infer_report.py \\
    --weights vision/models/weights/deck_v2_best.pt \\
    --source vision/data/frames/samples \\
    --conf 0.25 \\
    --out vision/runs/detect/deck_v2/deck_report.json

Observation-only; does not change any robot state.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from deck_slot_map import (  # noqa: E402
    FLEX_SLOTS,
    DECK_CORNER_ORDER_DOC,
    build_homography_from_corners_norm,
    load_deck_corners_labels_file,
    load_sidecar_deck_corners,
    map_center_to_slot,
)


def build_report_for_image(
    image_path: Path,
    *,
    results,
    names: dict[int, str] | list[str],
    conf_threshold: float,
    corners_norm: list[list[float]] | None = None,
    labels_file: Path | None = None,
) -> dict:
    r0 = results[0]
    im = r0.orig_img
    h, w = im.shape[:2]

    corners: list[list[float]] | None = corners_norm
    corners_source: str | None = "caller" if corners_norm is not None else None
    if corners is None and labels_file is not None:
        corners = load_deck_corners_labels_file(labels_file)
        if corners is not None:
            corners_source = "labels_file_arg"
    if corners is None:
        corners = load_sidecar_deck_corners(image_path)
        if corners is not None:
            corners_source = "labels_sidecar"
    hmat = None
    homog_notes: list[str] = []
    slot_mapping_meta: dict = {
        "method": "uniform_image_grid",
        "corner_order_doc": DECK_CORNER_ORDER_DOC,
        "deck_corners_norm": None,
        "corners_source": None,
    }
    if corners is not None:
        hmat, homog_notes = build_homography_from_corners_norm(corners, w, h)
        if hmat is not None:
            slot_mapping_meta["method"] = "deck_homography"
            slot_mapping_meta["deck_corners_norm"] = corners
            slot_mapping_meta["corners_source"] = corners_source or "labels_sidecar"
        else:
            slot_mapping_meta["homography_failed_notes"] = homog_notes

    def resolve_name(cls_id: int) -> str:
        if isinstance(names, dict):
            return str(names.get(cls_id, f"class_{cls_id}"))
        if isinstance(names, (list, tuple)) and 0 <= cls_id < len(names):
            return str(names[cls_id])
        return f"class_{cls_id}"

    observed_items: list[dict] = []
    slot_to_detections: dict[str, list[dict]] = {s: [] for s in FLEX_SLOTS}

    boxes = getattr(r0, "boxes", None)
    if boxes is not None and len(boxes):
        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        clss = boxes.cls.cpu().numpy().astype(int)
        for i in range(len(xyxy)):
            x1, y1, x2, y2 = (float(xyxy[i][j]) for j in range(4))
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            nx = max(0.0, min(1.0, cx / w))
            ny = max(0.0, min(1.0, cy / h))
            cls_id = int(clss[i])
            conf = float(confs[i])
            if conf < conf_threshold:
                continue
            label = resolve_name(cls_id)
            slot, grid_notes, deck_extra = map_center_to_slot(nx, ny, w, h, hmat)
            item: dict = {
                "slot": slot,
                "label": label,
                "confidence": round(conf, 4),
                "bbox_xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                "center_norm": [round(nx, 4), round(ny, 4)],
                "evidence": "trained_yolo_detection",
            }
            if deck_extra:
                item.update(deck_extra)
            if grid_notes:
                item["uncertainties"] = grid_notes
            observed_items.append(item)
            slot_to_detections[slot].append(item)

    slot_observations: dict[str, dict] = {}
    uncertainties_global: list[str] = list(homog_notes)

    for slot in FLEX_SLOTS:
        dets = slot_to_detections.get(slot, [])
        if not dets:
            slot_observations[slot] = {
                "state": "empty",
                "source": "grid_geometry",
                "label": None,
            }
        elif len(dets) == 1:
            slot_observations[slot] = {
                "state": "occupied",
                "label": dets[0]["label"],
                "confidence": dets[0]["confidence"],
                "source": "yolo",
            }
        else:
            labels = list({d["label"] for d in dets})
            slot_observations[slot] = {
                "state": "ambiguous",
                "labels": labels,
                "detection_count": len(dets),
                "source": "yolo",
            }
            uncertainties_global.append(f"multiple_objects_in_{slot}")

    needs_human_review = bool(uncertainties_global) or any(
        slot_observations[s].get("state") == "ambiguous" for s in FLEX_SLOTS
    )

    summary = (
        f"deck infer: {len(observed_items)} detections; "
        f"mapping={slot_mapping_meta['method']}; "
        f"sidecar={'yes' if corners else 'no'}"
    )

    return {
        "image": str(image_path.resolve()),
        "summary": summary,
        "slot_mapping": slot_mapping_meta,
        "observed_items": observed_items,
        "slot_observations": slot_observations,
        "uncertainties": uncertainties_global,
        "needs_human_review": needs_human_review,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weights", type=Path, required=True, help="Trained .pt weights")
    ap.add_argument("--source", type=Path, required=True, help="Image file or directory")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--out", type=Path, default=None, help="Write JSON report (single file or dir)")
    args = ap.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError as e:
        print("Install deps: uv sync", file=sys.stderr)
        print(e, file=sys.stderr)
        return 1

    weights = args.weights.expanduser().resolve()
    source = args.source.expanduser().resolve()
    model = YOLO(str(weights))
    names = getattr(model, "names", None) or {}

    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    if source.is_file():
        images = [source]
    else:
        images = sorted(
            p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in exts
        )

    if not images:
        print("No images found", file=sys.stderr)
        return 2

    reports: list[dict] = []
    for img_path in images:
        results = model.predict(str(img_path), conf=args.conf, verbose=False)
        if not results:
            reports.append({"image": str(img_path), "error": "no_results"})
            continue
        reports.append(
            build_report_for_image(
                img_path,
                results=results,
                names=names,
                conf_threshold=args.conf,
            )
        )

    out_payload: dict | list = reports[0] if len(reports) == 1 else {"images": reports}

    if args.out:
        out_path = args.out.expanduser().resolve()
        if out_path.is_dir() or str(out_path).endswith("/"):
            out_path = Path(out_path) / "deck_report.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(str(out_path))
    else:
        print(json.dumps(out_payload, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
