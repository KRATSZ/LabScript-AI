#!/usr/bin/env bash
# Batch vision_check on MVP camera JPEGs (YOLOE deck mode, labels sidecar, default conf 0.2).
# Run from Opentrons-Lab-Agent/:  bash mcp-servers/opentrons-mcp/scripts/batch_vision_check_mvp.sh [OUT_DIR]
# Optional: OPENTRONS_VISION_CONF, OPENTRONS_YOLOE_PROMPTS_JSON, OPENTRONS_YOLOE_WEIGHTS
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
OUT="${1:-artifacts/camera-captures/vision-annotated/mvp-yoloe-deck-v2}"
export OPENTRONS_VISION_BATCH_OUT="$OUT"
uv run python mcp-servers/opentrons-mcp/scripts/batch_vision_deck_mvp.py
