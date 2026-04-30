#!/usr/bin/env python3
"""Webcam YOLO demo. Press 'q' in the window to quit.

Standard checkpoints (e.g. yolov8n, yolo11n) use fixed COCO classes.
YOLOE weights (filename contains "yoloe") need text prompts: use
--preset office|opentrons, built-in defaults, or --prompts (comma-separated,
or pipe | between phrases if a phrase itself must contain commas).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_DEFAULT_YOLOE_PROMPTS = (
    "person",
    "laptop",
    "keyboard",
    "mouse",
    "cell phone",
    "cup",
    "bottle",
    "book",
    "chair",
    "tv",
    "monitor",
)

_OFFICE_YOLOE_PROMPTS = (
    "person with visible head or torso standing or seated at desk",
    "clamshell laptop fused keyboard below screen hinge visible",
    "standalone flat monitor on arm or stand no keyboard attached",
    "external desktop keyboard separate from screen flat rectangular key grid",
    "computer mouse palm-sized beside keyboard scroll wheel or two buttons",
    "office swivel chair with wheels armrests and backrest often mesh or fabric",
    "smartphone thin glass rectangle handheld touchscreen not a desk phone",
    "desk phone landline or VoIP base with handset cradle or numeric keypad",
    "ceramic coffee mug with side handle on desk not a paper cup",
    "tall cylindrical water bottle plastic or metal upright narrow neck",
    "disposable tapered paper coffee cup without handle often white or branded",
    "loose white printer paper sheets stack spread or document pages",
    "spiral notebook or stapled pad bound edge for handwriting",
    "backpack or messenger bag fabric straps on floor chair or desk",
    "over-ear or on-ear headphones padded earcups connected by headband",
    "small potted desk plant green leaves in round or square planter",
)

_OPENTRONS_LAB_YOLOE_PROMPTS = (
    "labware well plate or reservoir frosted clear plastic grid of wells for liquid no colored tip-box rim",
    "yellow plastic Opentrons pipette tip rack bright yellow frame dense pale off-white tips pointing up",
    "blue plastic pipette tip box dominant blue perimeter grid of light gray white pipette tips visible from above",
    "purple or violet plastic tip rack Opentrons style pale whitish tips filling the holes viewed top-down",
    "robot deck waste trash bin matte black square or wedge opening not a colored labware rack",
    "on-deck lab module black plastic enclosure with silver metal faceplate heater shaker or thermocycler block",
)


def _parse_prompts_arg(raw: str) -> list[str]:
    sep = "|" if "|" in raw else ","
    return [s.strip() for s in raw.split(sep) if s.strip()]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--weights",
        default="vision/models/weights/yolov8n.pt",
        help="Model path, e.g. vision/models/weights/yolov8n.pt or vision/models/weights/yoloe-26s-seg.pt",
    )
    p.add_argument("--camera", type=int, default=0, help="OpenCV camera index (default: 0)")
    p.add_argument("--conf", type=float, default=0.25, help="confidence threshold")
    p.add_argument(
        "--preset",
        choices=("default", "office", "opentrons"),
        default="default",
        help="YOLOE only: default | office | opentrons",
    )
    p.add_argument(
        "--prompts",
        default=None,
        help="YOLOE only: overrides --preset; comma-separated, or | between entries",
    )
    args = p.parse_args()

    try:
        import cv2
        from ultralytics import YOLO
    except ImportError as e:
        print("Missing deps. From the repo root:", file=sys.stderr)
        print("  uv sync", file=sys.stderr)
        print(e, file=sys.stderr)
        return 1

    print("Opening camera…", flush=True)
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Could not open camera index {args.camera}", file=sys.stderr)
        return 2

    print(f"Loading {args.weights}…", flush=True)
    model = YOLO(args.weights)

    wname = Path(args.weights).name.lower()
    if "yoloe" in wname:
        if args.prompts:
            plist = _parse_prompts_arg(args.prompts)
        elif args.preset == "office":
            plist = list(_OFFICE_YOLOE_PROMPTS)
        elif args.preset == "opentrons":
            plist = list(_OPENTRONS_LAB_YOLOE_PROMPTS)
        else:
            plist = list(_DEFAULT_YOLOE_PROMPTS)
        src = "custom --prompts" if args.prompts else f"preset={args.preset!r}"
        print(f"YOLOE set_classes ({len(plist)} prompts, {src})…", flush=True)
        model.set_classes(plist)

    print("Webcam YOLO — press 'q' in the video window to quit.", flush=True)
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Frame grab failed", file=sys.stderr)
            break

        results = model.predict(frame, conf=args.conf, verbose=False)
        annotated = results[0].plot()

        cv2.imshow("YOLO (press q to quit)", annotated)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
