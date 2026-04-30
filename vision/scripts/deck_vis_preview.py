#!/usr/bin/env python3
"""
Draw YOLO boxes + deck_quad (four corners) + A1–D3 occupancy text on one image.

Saves a JPEG so you can visually match the JSON table to the photo.

  uv run python vision/scripts/deck_vis_preview.py --image vision/data/frames/samples/deck_mvp_13.jpeg \\
    --out vision/runs/detect/deck_vis_preview/mvp_13_vis.jpg
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from deck_infer_report import build_report_for_image  # noqa: E402

def _resolve_default_weights() -> Path:
    candidates = [
        _REPO_ROOT / "models" / "weights" / "deck_v2_best.pt",
        _REPO_ROOT / "runs" / "detect" / "deck_v2" / "weights" / "best.pt",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


_DEFAULT_WEIGHTS = _resolve_default_weights()

# deck_corners_norm order: A1 → A3 → D3 → D1 (clockwise, deck view)
_CORNER_LABELS = ("A1", "A3", "D3", "D1")


def _occupancy_lines(occ: dict) -> list[str]:
    lines: list[str] = ["A1-D3 occupancy:"]
    rows = ("A", "B", "C", "D")
    for r in rows:
        parts = []
        for c in (1, 2, 3):
            slot = f"{r}{c}"
            o = occ.get(slot) or {}
            st = o.get("state", "?")
            if st == "empty":
                parts.append(f"{slot}:empty")
            elif st == "occupied":
                lab = o.get("label") or "?"
                cf = o.get("confidence")
                cf_s = f"{cf:.2f}" if isinstance(cf, (int, float)) else ""
                parts.append(f"{slot}:{lab}{'('+cf_s+')' if cf_s else ''}")
            elif st == "ambiguous":
                labs = o.get("labels") or []
                parts.append(f"{slot}:ambig[{','.join(labs)}]")
            else:
                parts.append(f"{slot}:{st}")
        lines.append("  " + " | ".join(parts))
    return lines


def render_preview(
    image_path: Path,
    *,
    weights: Path,
    conf: float,
    labels_json: Path | None,
) -> tuple[np.ndarray, dict]:
    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise RuntimeError("Install deps: uv sync") from e

    image_path = image_path.expanduser().resolve()
    weights = weights.expanduser().resolve()
    labels_arg = labels_json.expanduser().resolve() if labels_json else None

    model = YOLO(str(weights))
    names = getattr(model, "names", None) or {}
    results = model.predict(str(image_path), conf=conf, verbose=False)
    if not results:
        raise RuntimeError("no_results")

    report = build_report_for_image(
        image_path,
        results=results,
        names=names,
        conf_threshold=conf,
        labels_file=labels_arg,
    )
    report["occupancy"] = report["slot_observations"]

    # Ultralytics BGR plot with boxes + class names
    bgr = results[0].plot()
    h, w = bgr.shape[:2]

    sm = report.get("slot_mapping") or {}
    corners = sm.get("deck_corners_norm")
    method = sm.get("method")

    if isinstance(corners, list) and len(corners) == 4:
        pts = np.array(
            [[int(float(c[0]) * w), int(float(c[1]) * h)] for c in corners],
            dtype=np.int32,
        )
        cv2.polylines(bgr, [pts], isClosed=True, color=(0, 255, 255), thickness=3)
        for i in range(4):
            x, y = int(pts[i][0]), int(pts[i][1])
            cv2.circle(bgr, (x, y), 8, (0, 255, 0), -1)
            cv2.putText(
                bgr,
                _CORNER_LABELS[i],
                (x + 6, y - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
    else:
        cv2.putText(
            bgr,
            "no deck_quad in sidecar (uniform grid)",
            (16, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 165, 255),
            2,
            cv2.LINE_AA,
        )

    title = f"mapping={method}"
    cv2.putText(
        bgr,
        title,
        (16, h - 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    occ = report.get("occupancy") or {}
    y0 = h - 100
    for i, line in enumerate(_occupancy_lines(occ)):
        cv2.putText(
            bgr,
            line[:120],
            (16, y0 + i * 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 200),
            1,
            cv2.LINE_AA,
        )

    return bgr, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--image", type=Path, required=True)
    ap.add_argument("--weights", type=Path, default=_DEFAULT_WEIGHTS)
    ap.add_argument("--labels-json", type=Path, default=None)
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--out", type=Path, required=True, help="Output JPEG path")
    ap.add_argument("--json-out", type=Path, default=None, help="Optional full report JSON path")
    args = ap.parse_args()

    try:
        bgr, report = render_preview(
            args.image,
            weights=args.weights,
            conf=args.conf,
            labels_json=args.labels_json,
        )
    except (FileNotFoundError, RuntimeError) as e:
        print(str(e), file=sys.stderr)
        return 1

    out = args.out.expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), bgr)
    print(str(out))

    if args.json_out:
        jp = args.json_out.expanduser().resolve()
        jp.parent.mkdir(parents=True, exist_ok=True)
        jp.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(str(jp))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
