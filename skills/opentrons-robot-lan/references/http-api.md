# HTTP API Coverage

This skill wraps the local endpoint shapes that appear in `opentrons/api-client/src/`.

## Read-Only Calls

- `health` -> `GET /health`
- `list-protocols` -> `GET /protocols`
- `list-runs` -> `GET /runs`
- `get-run <run_id>` -> `GET /runs/{runId}`
- `get-camera` -> `GET /camera`

## Protocol Lifecycle

- `upload-protocol ...` -> `POST /protocols`
  - multipart form data
  - supports `files`, optional `key`, optional `protocolKind`
- `analyze-protocol <protocol_key>` -> `POST /protocols/{protocolKey}/analyses`
  - JSON body under `data`
  - supports runtime parameter values and runtime parameter files
- `create-run --protocol-id <id>` -> `POST /runs`
- `run-action <run_id> play|pause|stop|resume-from-recovery|resume-from-recovery-assuming-false-positive`
  -> `POST /runs/{runId}/actions`

## Camera Calls

- `set-camera` -> `POST /camera`
- `set-camera-image` -> `POST /camera/cameraSettings`
- `capture-preview` -> `POST /camera/capturePreviewImage`

## Auth And Headers

The script sends:

- `Opentrons-Version: 3`
- optional `authenticationBearer` when `--token` is provided

## Notes

- The helper is stdlib-only and uses `urllib.request`.
- Preview capture writes raw bytes to the output path you specify.
- HTTP error responses are surfaced as formatted JSON so Claude Code can reason about them.

