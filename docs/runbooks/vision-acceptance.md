# Vision integration acceptance (Flexagent)

Use this checklist after wiring in-repo `vision` weights and MCP `vision_check`. End-to-end tool order for the lab agent stack: [`workflows.md`](../rules/workflows.md) → **Optional deck vision (observation-only)**.

## Contract

- Vision is **observation-only**. It does **not** mutate `data/session-state/` or override `reconcile_state` / committed deck truth.
- Default camera artifact directory: `artifacts/camera-captures` when present; otherwise the MCP server falls back to `vision/data/camera-captures` and only then the legacy sibling `../labagentyolo/data/camera-captures`.

## Weight auto-priority (no `weights` argument)

1. `OPENTRONS_DECK_YOLO_WEIGHTS` (explicit `.pt` path), if the file exists.
2. `vision/models/weights/deck_v2_best.pt`, if present.
3. `vision/models/weights/deck_pilot_best.pt`, if present.
4. `vision/runs/detect/deck_v2/weights/best.pt`, if present.
5. `vision/runs/detect/deck_pilot/weights/best.pt`, if present.
6. legacy sibling `../labagentyolo/runs/detect/.../weights/best.pt`, if present.
7. `OPENTRONS_YOLOE_WEIGHTS`, if set.
8. `vision/models/weights/yoloe-26s-seg.pt`, if present.
9. `yoloe-26s-seg.pt` (YOLOE + text prompts; requires CLIP / vision extra).

## Manual checks

### A — Offline (recommended first)

From repo root, with `uv sync --extra vision`, local sample images under `vision/data/frames/samples/`, and weights available:

```bash
echo '{"mode":"deck","image_path":"'"$(pwd)"'/vision/data/frames/samples/deck_mvp_01.jpeg","conf_threshold":0.25}' \
  | uv run python mcp-servers/opentrons-mcp/scripts/vision_check.py
```

Expect:

- JSON with `slot_observations`, `observed_items`, `model.weights_effective` pointing at a `best.pt` when those files exist.
- When lab weights are used: `model.lab_tuned` is `true`, detection `evidence` is `trained_yolo_detection`, slot `source` is `trained_yolo`.
- Annotated image should show operator overlay elements, not only raw YOLO boxes: slot grid, slot labels, deck corners when available, and mismatch/review colors.
- `needs_human_review` may still be `true` for ambiguous slots, low confidence, or mismatches vs `expected_layout` — that is expected.

### B — MCP path

- `capture_preview_image` saves under the resolved camera artifact directory and returns a path.
- `vision_check` with only `image_path` runs without requiring an explicit `weights` argument.

### C — Live robot (optional)

- `camera_status` reflects capability; some Flex builds lack full camera POST support — failures must be surfaced, not silently ignored.
- After preview: run `vision_check`, then **`reconcile_state`** for authoritative comparison.

## Regression

- `cd mcp-servers/opentrons-mcp && npm test` (includes `vision-check` JS tests).
- `uv run python -m unittest discover -s tests -v` should cover pure logic regressions such as legacy multi-point `deck_quad` extraction and slot uncertainty rules.
