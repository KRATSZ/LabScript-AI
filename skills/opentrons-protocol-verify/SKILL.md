---
name: opentrons-protocol-verify
description: Local doctor, analyze, and simulate Opentrons Python protocols without a live robot.
type: script-backed
entry: scripts/verify_protocol.py
mcp_tools:
  - doctor_local_runtime
  - simulate_protocol
  - parse_simulation_output
---

# Protocol Verify

Use `.venv/bin/python` or `uv run python` for all commands.

## Workflow

1. Run `scripts/verify_protocol.py doctor` if runtime readiness is unknown.
2. If `doctor` reports broken imports, report the missing prerequisite — do not
   pretend the protocol is validated.
3. `analyze` — parser and command graph checks.
4. `simulate` — stronger dry run (requires working environment).
5. Pass extra CLI flags after `--`.
6. If iterating until simulation passes -> `opentrons-simulation-repair`.

## Commands

```bash
uv run python scripts/verify_protocol.py doctor
uv run python scripts/verify_protocol.py analyze path/to/protocol.py -- --check
uv run python scripts/verify_protocol.py simulate path/to/protocol.py
```

## Limits

Cannot fix missing third-party dependencies or partial Opentrons source snapshots.

Ref: `references/local-runtime.md`
