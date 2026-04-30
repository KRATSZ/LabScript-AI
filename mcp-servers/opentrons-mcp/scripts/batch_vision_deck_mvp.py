#!/usr/bin/env python3
"""
Batch-run vision_check on MVP camera JPEGs (auto deck weights, labels sidecar for homography).

Run from Opentrons-Lab-Agent/:
  uv run python mcp-servers/opentrons-mcp/scripts/batch_vision_deck_mvp.py

Env:
  OPENTRONS_VISION_BATCH_OUT — output dir (default artifacts/.../mvp-deck-auto-v1)
  OPENTRONS_VISION_BATCH_SOURCE — optional JPEG directory override
  OPENTRONS_VISION_CONF — confidence threshold (default 0.2; dense Flex decks often need 0.15–0.25)
  OPENTRONS_DECK_YOLO_WEIGHTS — optional explicit deck checkpoint override
  OPENTRONS_YOLOE_WEIGHTS — optional YOLOE fallback/override
  OPENTRONS_YOLOE_PROMPTS_JSON — optional JSON file for YOLOE text prompts:
    {"class_prompts":[...], "canonical_labels":[...]}
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def resolve_image_source(root: Path) -> tuple[Path | None, list[Path], list[Path]]:
    candidates: list[Path] = []
    env_source = os.environ.get("OPENTRONS_VISION_BATCH_SOURCE")
    if env_source:
        candidates.append(Path(env_source).expanduser().resolve())
    candidates.extend(
        [
            root / "artifacts/camera-captures/mvp-annotation-batch",
            root / "vision" / "data" / "frames" / "samples",
            root / "vision" / "data" / "camera-captures" / "mvp-annotation-batch",
            root.parent / "labagentyolo" / "data" / "frames" / "samples",
            root.parent / "labagentyolo" / "data" / "camera-captures" / "mvp-annotation-batch",
        ]
    )

    for source in candidates:
        if not source.is_dir():
            continue
        images = sorted(source.glob("*.jpeg")) + sorted(source.glob("*.jpg"))
        if images:
            return source, images, candidates

    return None, [], candidates


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    os.chdir(root)
    img_dir, images, candidates = resolve_image_source(root)
    out = Path(
        os.environ.get(
            "OPENTRONS_VISION_BATCH_OUT",
            "artifacts/camera-captures/vision-annotated/mvp-deck-auto-v1",
        )
    )
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    conf = float(os.environ.get("OPENTRONS_VISION_CONF", "0.2"))
    script = Path(__file__).resolve().parent / "vision_check.py"

    if not images:
        tried = "\n  - ".join(str(p) for p in candidates)
        print("No JPEGs found in any candidate source directory:", file=sys.stderr)
        print("  -", tried, file=sys.stderr)
        sys.exit(1)

    prompts_path = os.environ.get("OPENTRONS_YOLOE_PROMPTS_JSON")
    extra: dict = {}
    if prompts_path:
        data = json.loads(Path(prompts_path).expanduser().read_text(encoding="utf-8"))
        extra["class_prompts"] = data["class_prompts"]
        extra["canonical_labels"] = data["canonical_labels"]

    summary_rows: list[dict] = []
    for img in images:
        payload = {
            "mode": "deck",
            "image_path": str(img.resolve()),
            "conf_threshold": conf,
            "load_labels_sidecar": True,
            "annotated_output_dir": str(out),
            **extra,
        }
        proc = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            cwd=str(root),
        )
        stem = img.stem
        json_path = out / f"{stem}.vision.json"
        if proc.returncode != 0:
            err_body = {
                "error": {"stderr": proc.stderr, "code": proc.returncode},
                "image": img.name,
            }
            json_path.write_text(json.dumps(err_body, ensure_ascii=False, indent=2), encoding="utf-8")
            print("FAIL", img.name, proc.stderr[:500], file=sys.stderr)
            continue
        json_path.write_text(proc.stdout, encoding="utf-8")
        j = json.loads(proc.stdout)
        summary_rows.append(
            {
                "image": img.name,
                "summary": j.get("summary"),
                "slot_mapping": j.get("slot_mapping"),
                "model": j.get("model"),
                "slot_observations": j.get("slot_observations"),
                "observed_items": j.get("observed_items"),
                "needs_human_review": j.get("needs_human_review"),
                "annotated_image_path": j.get("annotated_image_path"),
            }
        )
        print("ok", img.name, j.get("summary"))

    (out / "vision_batch_summary.json").write_text(
        json.dumps(summary_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("Wrote", out / "vision_batch_summary.json")


if __name__ == "__main__":
    main()
