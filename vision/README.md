# Vision Workspace

This subtree folds the lightweight, source-controlled parts of the former `labagentyolo` side workspace into the main repository.

Tracked here:

- vision scripts for sidecar export, dataset prep, deck inference, and preview rendering
- vision-specific docs and labeling guidance
- weight placeholders and download metadata

Intentionally not tracked here:

- `.pt` / `.ts` model binaries
- training runs under `vision/runs/`
- raw videos, captured deck photos, and generated datasets

## Layout

```text
vision/
  README.md
  .gitignore
  docs/
  scripts/
  models/
    weights/
      README.md
      manifest.example.json
  data/
    README.md
```

## Weights

Keep lab-tuned weights outside git history and download them into `vision/models/weights/`.

The repository provides:

- `scripts/download_vision_weights.sh`
- `vision/models/weights/manifest.example.json`

Typical flow:

```bash
cp vision/models/weights/manifest.example.json vision/models/weights/manifest.json
# edit manifest.json to point at GitHub Release assets, S3, OSS, etc.
bash scripts/download_vision_weights.sh
```

MCP `vision_check` auto-picks weights in this order:

1. `OPENTRONS_DECK_YOLO_WEIGHTS`
2. `vision/models/weights/deck_v2_best.pt`
3. `vision/models/weights/deck_pilot_best.pt`
4. local training runs under `vision/runs/detect/...`
5. legacy sibling `../labagentyolo/...` paths for backward compatibility
6. `OPENTRONS_YOLOE_WEIGHTS`
7. `vision/models/weights/yoloe-26s-seg.pt`
8. `yoloe-26s-seg.pt`

## Common Commands

From the repo root:

```bash
uv run python vision/scripts/export_deck_sidecars_from_labelme.py \
  --labelme-dir vision/data/labels \
  --images-dir vision/data/frames/samples

uv run python mcp-servers/opentrons-mcp/scripts/batch_vision_deck_mvp.py
```
