# Ultralytics auxiliary weights (optional)

YOLOE-26 uses a **MobileCLIP** TorchScript text encoder (`mobileclip2_b.ts`) the first time you call `set_classes(...)`. Ultralytics downloads it from GitHub releases next to other assets.

If download fails (SSL, firewall), **manually** place the file here:

- **File:** `mobileclip2_b.ts`
- **Source:** [ultralytics/assets v8.4.0 release](https://github.com/ultralytics/assets/releases/download/v8.4.0/mobileclip2_b.ts)

Ultralytics resolves paths via `SETTINGS["weights_dir"]` (defaults to `./weights` under the working directory) and the current directory.

For lab-tuned deck checkpoints, keep binaries outside git history and download them here with:

```bash
cp vision/models/weights/manifest.example.json vision/models/weights/manifest.json
bash scripts/download_vision_weights.sh
```
