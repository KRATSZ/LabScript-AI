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

## Module Control via Maintenance Run

For direct hardware control (e.g., setting module temperature, opening/closing lids), use **maintenance runs**:

### 1. Create Maintenance Run
```bash
curl -X POST "http://<robot_ip>:31950/maintenance_runs" \
  -H "Opentrons-Version: 3" \
  -H "Content-Type: application/json" \
  -d '{"data": {}}'
# Returns: maintenance run id, e.g., "32566eb9-8e9a-4551-8163-c72bd098b9ea"
```

### 2. Load Module (if not already loaded)
```bash
curl -X POST "http://<robot_ip>:31950/maintenance_runs/<run_id>/commands" \
  -H "Opentrons-Version: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "commandType": "loadModule",
      "params": {
        "model": "thermocyclerModuleV2",
        "location": {"slotName": "B1"}
      }
    }
  }'
# Returns: moduleId, e.g., "360cfd15-f099-483a-a442-854152fc05c6"
```

### 3. Queue Module Commands
```bash
# Set temperature
curl -X POST "http://<robot_ip>:31950/maintenance_runs/<run_id>/commands" \
  -H "Opentrons-Version: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "commandType": "thermocycler/setTargetBlockTemperature",
      "params": {"moduleId": "<module_id>", "celsius": 25}
    }
  }'

# Open lid
curl -X POST "http://<robot_ip>:31950/maintenance_runs/<run_id>/commands" \
  -d '{
    "data": {
      "commandType": "thermocycler/openLid",
      "params": {"moduleId": "<module_id>"}
    }
  }'
```

### 4. Check Module Status
```bash
curl -s "http://<robot_ip>:31950/modules" | python3 -m json.tool
# Returns status, currentTemperature, lidStatus, etc.
```

### Common Module Commands
| Command Type | Params |
|--------------|--------|
| `thermocycler/setTargetBlockTemperature` | `moduleId`, `celsius`, `holdTime` (sec) |
| `thermocycler/setTargetLidTemperature` | `moduleId`, `celsius` |
| `thermocycler/openLid` | `moduleId` |
| `thermocycler/closeLid` | `moduleId` |
| `thermocycler/runProfile` | `moduleId`, `profile[]`, optional `blockMaxVolumeUl` |
| `temperatureModule/setTargetTemperature` | `moduleId`, `celsius` |
| `temperatureModule/deactivate` | `moduleId` |
| `magneticModule/engage` | `moduleId`, `height` (mm) |
| `magneticModule/disengage` | `moduleId` |
| `heaterShaker/setTargetTemperature` | `moduleId`, `celsius` |
| `heaterShaker/setShakeSpeed` | `moduleId`, `rpm` |
| `heaterShaker/setAndWaitForShakeSpeed` | `moduleId`, `rpm` |
| `heaterShaker/deactivateHeater` | `moduleId` |
| `heaterShaker/deactivateShaker` | `moduleId` |
| `heaterShaker/openLabwareLatch` | `moduleId` |
| `heaterShaker/closeLabwareLatch` | `moduleId` |
| `captureImage` | optional `fileName`, `resolution`, `zoom`, `pan`, `contrast`, `brightness`, `saturation` |

**Key Learnings:**
- Always `loadModule` first in maintenance context before sending module commands
- `location` param requires object format: `{"slotName": "B1"}` not just string
- Commands are queued; poll status or wait before checking results
- Use `/modules` endpoint to verify final state
- `heaterShaker/deactivateShaker` may fail unless the latch is explicitly closed in the current context
- `captureImage` rejects filenames containing `.`
- Historical generated robot images can be listed with `GET /dataFiles` and downloaded with `GET /dataFiles/{dataFileId}/download`

## Notes

- The helper is stdlib-only and uses `urllib.request`.
- Preview capture writes raw bytes to the output path you specify.
- HTTP error responses are surfaced as formatted JSON so Claude Code can reason about them.
- **Maintenance runs** are safer than protocol runs for one-off hardware manipulation.
- Command queue requires polling `/runs/{runId}/commands` to check completion status.

