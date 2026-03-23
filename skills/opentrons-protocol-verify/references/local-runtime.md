# Local Runtime Notes

## What The Wrapper Expects

The helper script looks for a workspace containing:

- `opentrons/api/src/opentrons`
- `opentrons/shared-data/python`

By default it prefers:

- `opentrons/api/.venv/bin/python`

If that interpreter does not exist, it falls back to the current Python.

## Preferred Python Tooling

Use `uv` as the default environment manager for this repository.

- create `.venv` with `uv venv .venv`
- execute helpers with `uv run python ...`
- treat fallback to a non-`uv` interpreter as a compatibility path, not the preferred workflow

## Why The Wrapper Injects `opentrons._version`

In source checkouts, the Opentrons package may expect a generated `_version.py` file that only exists after packaging or installation. The wrapper injects a minimal module at runtime so import resolution can proceed without mutating the vendored source tree.

## What It Does Not Hide

The wrapper still fails fast when real dependencies are missing. Examples include:

- `typing_extensions`
- `click`
- `anyio`
- incomplete local source trees missing sibling packages

That behavior is intentional. A failed import means the protocol was not actually analyzed or simulated.

## Recommended Usage Pattern

1. Run `doctor`.
2. If imports are good, run `analyze`.
3. Run `simulate` only when the environment is stable enough to support it.
4. If local validation is blocked, consider remote analysis on a robot via the `opentrons-robot-lan` skill.
