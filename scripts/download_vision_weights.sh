#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEST_DIR="${REPO_ROOT}/vision/models/weights"
MANIFEST_PATH=""

usage() {
  cat <<'EOF'
Download optional vision weights into vision/models/weights.

Usage:
  bash scripts/download_vision_weights.sh [--dest DIR] [--manifest FILE]

Defaults:
  --dest     vision/models/weights
  --manifest $OPENTRONS_VISION_WEIGHTS_MANIFEST or vision/models/weights/manifest.json

You can also provide URLs through env vars:
  OPENTRONS_DECK_V2_WEIGHTS_URL
  OPENTRONS_DECK_PILOT_WEIGHTS_URL
  OPENTRONS_YOLOE_WEIGHTS_URL
  OPENTRONS_MOBILECLIP_URL
  OPENTRONS_YOLO11N_URL
  OPENTRONS_YOLOV8N_URL
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest)
      DEST_DIR="$2"
      shift 2
      ;;
    --manifest)
      MANIFEST_PATH="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${MANIFEST_PATH}" ]]; then
  if [[ -n "${OPENTRONS_VISION_WEIGHTS_MANIFEST:-}" ]]; then
    MANIFEST_PATH="${OPENTRONS_VISION_WEIGHTS_MANIFEST}"
  else
    MANIFEST_PATH="${DEST_DIR}/manifest.json"
  fi
fi

mkdir -p "${DEST_DIR}"

PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python3 or python is required" >&2
  exit 1
fi

"${PYTHON_BIN}" - "${DEST_DIR}" "${MANIFEST_PATH}" <<'PY'
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path


dest_dir = Path(sys.argv[1]).expanduser().resolve()
manifest_path = Path(sys.argv[2]).expanduser()

entries: list[dict[str, str]] = []

env_map = {
    "OPENTRONS_DECK_V2_WEIGHTS_URL": "deck_v2_best.pt",
    "OPENTRONS_DECK_PILOT_WEIGHTS_URL": "deck_pilot_best.pt",
    "OPENTRONS_YOLOE_WEIGHTS_URL": "yoloe-26s-seg.pt",
    "OPENTRONS_MOBILECLIP_URL": "mobileclip2_b.ts",
    "OPENTRONS_YOLO11N_URL": "yolo11n.pt",
    "OPENTRONS_YOLOV8N_URL": "yolov8n.pt",
}

for env_name, filename in env_map.items():
    url = os.environ.get(env_name, "").strip()
    if url:
        entries.append({"name": filename, "url": url})

if manifest_path.is_file():
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in data.get("weights", []):
        name = str(item.get("name", "")).strip()
        url = str(item.get("url", "")).strip()
        if name and url:
            entries.append({"name": name, "url": url})

deduped: list[dict[str, str]] = []
seen_names: set[str] = set()
for item in entries:
    name = item["name"]
    if name in seen_names:
        continue
    seen_names.add(name)
    deduped.append(item)

if not deduped:
    print(
        "No weight URLs were provided. Copy "
        f"{dest_dir / 'manifest.example.json'} to manifest.json and fill in real URLs, "
        "or export the OPENTRONS_*_URL env vars.",
        file=sys.stderr,
    )
    sys.exit(1)

dest_dir.mkdir(parents=True, exist_ok=True)

for item in deduped:
    filename = item["name"]
    url = item["url"]
    target = dest_dir / filename
    tmp = target.with_suffix(target.suffix + ".part")
    print(f"downloading {filename} <- {url}")
    with urllib.request.urlopen(url) as response, tmp.open("wb") as fh:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            fh.write(chunk)
    tmp.replace(target)
    print(f"saved {target}")
PY
