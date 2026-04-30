#!/usr/bin/env python3
"""
Single-image deck occupancy tool: one photo → JSON with per-slot state (A1–D3).

Uses trained YOLO for object boxes; maps each detection center to a slot using either:
  - deck homography from optional_deck_corners_norm (sidecar or --labels-json), or
  - uniform image grid if no corners are available.

From repo root:
  uv run python vision/scripts/deck_occupy.py --image vision/data/frames/samples/deck_mvp_13.jpeg

  uv run python vision/scripts/deck_occupy.py --image /path/to/photo.jpg \\
    --labels-json /path/to/corners.labels.json

Default weights: vision/models/weights/deck_v2_best.pt (override with --weights).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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


def run_occupancy(
    image_path: Path,
    *,
    weights: Path,
    conf: float = 0.25,
    labels_json: Path | None = None,
) -> dict:
    """Run YOLO once and return a report dict including `occupancy` (per-slot)."""
    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise RuntimeError("Install deps: uv sync") from e

    image_path = image_path.expanduser().resolve()
    weights = weights.expanduser().resolve()
    if not image_path.is_file():
        raise FileNotFoundError(str(image_path))
    if not weights.is_file():
        raise FileNotFoundError(f"weights not found: {weights}")

    labels_arg = labels_json.expanduser().resolve() if labels_json else None
    model = YOLO(str(weights))
    names = getattr(model, "names", None) or {}
    results = model.predict(str(image_path), conf=conf, verbose=False)
    if not results:
        return {
            "image": str(image_path),
            "error": "no_results",
            "occupancy": {},
        }

    report = build_report_for_image(
        image_path,
        results=results,
        names=names,
        conf_threshold=conf,
        labels_file=labels_arg,
    )
    report["occupancy"] = report["slot_observations"]
    report["weights"] = str(weights)
    report["conf"] = conf
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--image", type=Path, required=True, help="Path to one JPEG/PNG")
    ap.add_argument(
        "--weights",
        type=Path,
        default=_DEFAULT_WEIGHTS,
        help=f"YOLO weights (default: {_DEFAULT_WEIGHTS})",
    )
    ap.add_argument(
        "--labels-json",
        type=Path,
        default=None,
        help="Optional path to *.labels.json with optional_deck_corners_norm (overrides sidecar lookup)",
    )
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write JSON to this file (default: stdout only)",
    )
    args = ap.parse_args()

    try:
        payload = run_occupancy(
            args.image,
            weights=args.weights,
            conf=args.conf,
            labels_json=args.labels_json,
        )
    except (FileNotFoundError, RuntimeError) as e:
        print(str(e), file=sys.stderr)
        return 1

    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        out = args.out.expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(str(out))
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
