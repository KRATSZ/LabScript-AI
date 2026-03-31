---
name: opentrons-protocol-verify
description: Use when the user wants to analyze, simulate, or sanity-check an Opentrons Python protocol locally. This skill probes the local Opentrons runtime first, then invokes opentrons.cli analyze or python -m opentrons.simulate only if imports are actually available.
license: Apache-2.0
compatibility: Requires Python 3.8+, uv for package management, and local Opentrons runtime with optional simulation support.
---

# Protocol Verify

Use `uv run python ...` for all commands.

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
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py doctor
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py analyze path/to/protocol.py -- --check
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py simulate path/to/protocol.py
```

## Limits

Cannot fix missing third-party dependencies or partial Opentrons source snapshots.

Ref: `references/local-runtime.md`
