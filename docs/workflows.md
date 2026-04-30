# Workflow sequences (canonical)

This file is the **single source of truth** for end-to-end and tool-order workflows. Other docs (root `README.md`, `CLAUDE.md`, skill files) should link here instead of copying full sequences.

## New experiment (end-to-end)

```
user intent / SOP
  →  (optional) one blocking clarification round
  →  protocol-author draft
  →  doctor_local_runtime → simulate_protocol → parse_simulation_output
  →  (fix loop if failed)
  →  return status: ready | needs_confirmation | blocked
  →  run_protocol (robot_ip, file_path, session_id) only after confirmation
```

## Protocol validation only (no live robot)

```
doctor_local_runtime → simulate_protocol → parse_simulation_output
```
Script equivalent: `verify_protocol.py doctor` then `verify_protocol.py analyze <file>`.

Before simulating a new draft, it is worth calling `validate_labware_name` on unfamiliar load names, `inspect_labware_definition` when geometry or dead volume matters, and `estimate_tip_budget` on the draft protocol source. Those checks catch the highest-frequency authoring mistakes before the slower sim step.
If the user only wants validation or labware inspection, stop after the check and report findings; do not fabricate a full `protocol.py`.

## User-facing defaults

- If code exists and is runnable, simulate is the default next action.
- Ask at most one clarification round before drafting.
- Only block on missing information that would change safety, deck truth, robot compatibility, or module choice.

## Error recovery (live robot)

```
parse_error (robot_ip, run_id) → suggest_recovery_action (error_category, target_slot)
  → execute_protocol_recovery (run_id, robot_ip, recovery_branch, ...)
```

## After MCP restart or host reboot

```
safe_next_action (session_id, robot_ip?)   # same data as restart_review + recommended_next_tool / operator_steps
  OR restart_review (session_id, robot_ip?)
  → reconcile_state (if reconcile_first)
  → robot_status → module_status → is_home_safe (before any home)
```

`safe_next_action` is a thin wrapper: one call returns full `restart_review` data plus `safe_next_action.recommended_next_tool` (usually `reconcile_state` or `robot_status`) and numbered `operator_steps`. Atomic tools are unchanged.

## Check robot status (quick)

```
robot_status → module_status → reconcile_state (if anything looks wrong)
```

## Optional deck vision (observation-only)

Use this **only when the operator explicitly asks** for a visual deck check, camera preview, or image-based confirmation. Vision does **not** replace committed deck truth — compare results with **`reconcile_state`** and robot APIs (see `docs/safety-policy.md`).

**Setup (once per machine):**

- Python: `uv sync --extra vision` from the repo root (Ultralytics / optional YOLOE extras).
- Weights: either download them into `vision/models/weights/` via `bash scripts/download_vision_weights.sh`, or set `OPENTRONS_DECK_YOLO_WEIGHTS` / `OPENTRONS_YOLOE_WEIGHTS` per `docs/vision-acceptance.md`. Legacy sibling `../labagentyolo/...` paths still work as a fallback while migrating older workspaces.

**Tool sequence (MCP `opentrons-lab-mcp`):**

```
camera_status → capture_preview_image → vision_check (image_path = path returned by capture)
```

- If the camera API is unavailable on a given Flex build, `camera_status` / capture may fail — surface the error; do not silently skip.
- For offline validation without a robot, call `vision_check` with a local image path only (see checklist A in `docs/vision-acceptance.md`).

## Protocol Reference Library

Location: `reference-protocols/Protocols-develop/` (833 protocols, read-only).

Always use catalog, never scan all folders:
- Search: `python skills/opentrons-protocol-library/scripts/search_protocols.py search "keywords"`
- Inspect: `python skills/opentrons-protocol-library/scripts/search_protocols.py show <slug>`
- Snippets: `python skills/opentrons-protocol-library/scripts/search_protocols.py snippet <slug> <keywords>`
- Regen catalog: `python reference-protocols/Protocols-develop/scripts/generate_catalog.py`
