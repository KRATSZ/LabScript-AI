#!/usr/bin/env python3
"""
Quick YOLOE visual feedback for prompt tuning (single image or webcam).

Default prompts match mcp-servers/opentrons-mcp/scripts/vision_check.py (Flex-tuned list).

Examples (from Opentrons-Lab-Agent/):
  uv run python mcp-servers/opentrons-mcp/scripts/yoloe_deck_preview.py artifacts/camera-captures/mvp-annotation-batch/00_....jpeg
  uv run python mcp-servers/opentrons-mcp/scripts/yoloe_deck_preview.py 0 --conf 0.2
  uv run python mcp-servers/opentrons-mcp/scripts/yoloe_deck_preview.py path/to.jpg --no-show --out /tmp/p.jpg

Requires: uv sync --extra vision
"""

from __future__ import annotations

import argparse
import json
import runpy
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    ap = argparse.ArgumentParser(description="YOLOE deck preview for fast prompt iteration.")
    ap.add_argument(
        "source",
        help="Image path, or 0 (or webcam) for live camera index 0",
    )
    ap.add_argument("--weights", default="yoloe-26s-seg.pt")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument(
        "--prompts-json",
        type=Path,
        help='JSON with "class_prompts" list (and optional "canonical_labels" for vision_check; ignored here)',
    )
    ap.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open a GUI window; write --out image instead",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/camera-captures/vision-annotated/yoloe-preview.jpg"),
    )
    args = ap.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError:
        print("Install vision extra: uv sync --extra vision", file=sys.stderr)
        sys.exit(1)

    if args.prompts_json:
        data = json.loads(args.prompts_json.expanduser().read_text(encoding="utf-8"))
        prompts = list(data["class_prompts"])
    else:
        vc = runpy.run_path(str(Path(__file__).resolve().parent / "vision_check.py"))
        prompts = list(vc["YOLOE_CLASS_PROMPTS"])

    model = YOLO(args.weights)
    model.set_classes(prompts)

    src: str | int
    if args.source in ("0", "webcam"):
        src = 0
    elif args.source.isdigit():
        src = int(args.source)
    else:
        src = str(Path(args.source).expanduser().resolve())
        if not Path(src).is_file():
            print("Not a file:", src, file=sys.stderr)
            sys.exit(1)

    if args.no_show:
        import cv2

        results = model.predict(source=src, conf=args.conf, verbose=False, show=False)
        if not results:
            print("No results", file=sys.stderr)
            sys.exit(1)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(args.out), results[0].plot())
        print(args.out.resolve())
        return

    # Live webcam: stream with show; single file: one window
    if isinstance(src, int):
        for _ in model.predict(source=src, conf=args.conf, stream=True, verbose=True, show=True):
            pass
    else:
        model.predict(source=src, conf=args.conf, verbose=True, show=True)


if __name__ == "__main__":
    main()
