---
name: opentrons-protocol-verify
description: Use when the user wants to analyze, simulate, or sanity-check an Opentrons Python protocol locally. This skill probes the local Opentrons runtime first, then invokes opentrons.cli analyze or python -m opentrons.simulate only if imports are actually available.
---

# Opentrons Protocol Verify

Use this skill when the user wants real validation instead of a code-only review.

Prefer a `uv`-managed Python environment. In normal use, run this skill's script through `uv run python ...`.

## Workflow

1. Run `scripts/verify_protocol.py doctor` first if local runtime readiness is unknown.
2. If `doctor` says the import path is broken, report the missing prerequisite instead of pretending the protocol is validated.
3. Use `analyze` for parser and command graph checks.
4. Use `simulate` when the user wants a stronger dry run and the environment can support it.
5. Pass extra CLI flags after `--`.
6. If the goal is to keep editing until simulation passes, hand off to `opentrons-simulation-repair`.

## Commands

```bash
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py doctor
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py analyze path/to/protocol.py -- --check
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py simulate path/to/protocol.py
```

## Important Limits

- This skill can inject a minimal `opentrons._version` shim for source checkouts.
- It cannot invent missing third-party dependencies.
- It cannot fix a partial Opentrons source snapshot that omits sibling packages required by the runtime.

## Reference File

- Runtime assumptions and failure modes: `references/local-runtime.md`
