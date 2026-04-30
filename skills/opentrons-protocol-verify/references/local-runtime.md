# Local Runtime Notes

## What The Wrapper Expects

By default the helper script uses the current Python environment and checks whether it can import:

- `opentrons.cli`
- `opentrons.simulate`

If you want to validate against an external source checkout instead, pass one of:

- `--workspace-root /path/to/source-root`
- `--api-root /path/to/opentrons/api`
- `--shared-data-root /path/to/opentrons/shared-data`

In source-checkout mode it prefers `opentrons/api/.venv/bin/python` when that interpreter exists. Otherwise it falls back to the current Python.

## Preferred Python Tooling

Use `uv` as the default environment manager for this repository.

- create `.venv` with `uv venv .venv`
- execute helpers with `uv run python ...`
- treat fallback to a non-`uv` interpreter as a compatibility path, not the preferred workflow

## Why The Wrapper Injects `opentrons._version`

The shim is only needed in source-checkout mode. Some raw Opentrons source trees expect a generated `_version.py` file that only exists after packaging or installation. The wrapper injects a minimal module at runtime so import resolution can proceed without mutating that external source tree.

## What It Does Not Hide

The wrapper still fails fast when real dependencies are missing. Examples include:

- `typing_extensions`
- `click`
- `anyio`
- incomplete external source trees missing sibling packages

That behavior is intentional. A failed import means the protocol was not actually analyzed or simulated.

## Recommended Usage Pattern

1. Run `preflight` on the protocol file for static mistakes (invalid Flex pipette names, apiLevel vs `protocol.params` / liquid-class hints).
2. Run `doctor`.
3. If imports are good, run `analyze`.
4. Run `simulate` only when the environment is stable enough to support it.
5. If local validation is blocked, consider remote analysis on a robot via the `opentrons-robot-lan` skill.
