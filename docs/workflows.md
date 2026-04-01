# Workflow Sequences

## New experiment (end-to-end)

```
search_protocols.py search/show/snippet  →  protocol-author draft
  →  doctor_local_runtime → simulate_protocol → parse_simulation_output
  →  (fix loop if failed)  →  run_protocol (robot_ip, file_path, session_id)
```

## Protocol validation only (no live robot)

```
doctor_local_runtime → simulate_protocol → parse_simulation_output
```
Script equivalent: `verify_protocol.py doctor` then `verify_protocol.py analyze <file>`.

## Error recovery (live robot)

```
parse_error (robot_ip, run_id) → suggest_recovery_action (error_category, target_slot)
  → execute_protocol_recovery (run_id, robot_ip, recovery_branch, ...)
```

## After MCP restart or host reboot

```
restart_review (session_id, robot_ip?) → reconcile_state (if reconcile_first)
  → robot_status → module_status → is_home_safe (before any home)
```

## Check robot status (quick)

```
robot_status → module_status → reconcile_state (if anything looks wrong)
```

## Protocol Reference Library

Location: `reference-protocols/Protocols-develop/` (833 protocols, read-only).

Always use catalog, never scan all folders:
- Search: `python skills/opentrons-protocol-library/scripts/search_protocols.py search "keywords"`
- Inspect: `python skills/opentrons-protocol-library/scripts/search_protocols.py show <slug>`
- Snippets: `python skills/opentrons-protocol-library/scripts/search_protocols.py snippet <slug> <keywords>`
- Regen catalog: `python reference-protocols/Protocols-develop/scripts/generate_catalog.py`
