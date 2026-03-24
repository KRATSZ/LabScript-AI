---
name: opentrons-protocol-author
description: Use when writing, revising, or reviewing Opentrons Python protocols for OT-2 or Flex robots, including deck setup, labware loading, pipette usage, runtime parameters, and camera capture with ProtocolContext.capture_image().
license: Apache-2.0
compatibility: Requires Python 3.8+, uv for package management, and access to Opentrons protocol documentation.
---

# Opentrons Protocol Author

Use this skill when the user wants a Python protocol drafted or edited for an Opentrons robot.

## What To Do

1. Identify the target robot first: `OT-2` or `Flex`.
2. Read `references/python-protocol-patterns.md` before inventing protocol structure.
3. Start from `assets/protocol_template.py` for new protocols instead of writing one from scratch.
4. Keep the protocol explicit about labware, instruments, mounts, slots, and any runtime parameters.
5. If the user asks whether the protocol actually analyzes or simulates, switch to the `opentrons-protocol-verify` skill instead of guessing.

## Working Rules

- Prefer `requirements = {"robotType": "...", "apiLevel": "..."}` for modern protocols.
- Keep protocol code readable and operational, not tutorial-style fluff.
- When camera capture is needed, use `protocol.capture_image(...)` only when the requested API level supports it.
- If the protocol depends on custom labware, call that out clearly in the file and in your response.
- Do not claim a protocol is validated unless you actually ran the verify tooling or the user provided a validated result.

## Reference Files

- Protocol structure and authoring patterns: `references/python-protocol-patterns.md`
- Starter file: `assets/protocol_template.py`

