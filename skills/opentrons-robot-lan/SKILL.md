---
name: opentrons-robot-lan
description: Use when interacting with an Opentrons OT-2 or Flex robot over the LAN HTTP API, including health checks, camera settings, preview capture, protocol upload, protocol analysis, run creation, and run play or pause control.
---

# Opentrons Robot LAN

Use this skill when the user wants real robot-side state or control through the robot's HTTP API.

Prefer running the helper through a `uv` virtual environment: `uv run python ...`.

## Workflow

1. Start with a read-only call such as `health`, `list-runs`, or `get-camera`.
2. For protocol execution, use the safe order:
   upload protocol -> analyze protocol -> create run -> run action
3. Use the provided script instead of ad hoc `curl` so payloads stay consistent.
4. For preview images, always save to a file path and then reference that file in the response.
5. If the user wants local dry-run verification instead of robot API analysis, switch to `opentrons-protocol-verify`.

## Commands

```bash
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 health
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 get-camera
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 upload-protocol path/to/protocol.py
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 analyze-protocol <protocol-id>
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 create-run --protocol-id <protocol-id>
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 run-action <run-id> play
```

## Reference File

- Wrapped endpoints and payloads: `references/http-api.md`
