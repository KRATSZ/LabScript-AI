# Opentrons-Lab-Agent

`Opentrons-Lab-Agent` is a Claude Code plugin-style repository that packages Opentrons-focused Agent Skills for three jobs:

- writing and revising Python protocols
- checking whether a local Opentrons runtime is able to analyze or simulate a protocol
- driving an OT-2 or Flex robot over the LAN HTTP API, including camera-related actions

The layout follows Anthropic's public skills conventions: each skill lives in its own folder with a `SKILL.md`, optional `scripts/`, `references/`, and `assets/`, and the repository also includes `.claude-plugin/plugin.json` so the repo can be treated as a Claude Code plugin root.

## Python Environment

This project assumes Python is managed with `uv`.

- create the local virtual environment with `uv venv .venv`
- run commands with `uv run ...`
- avoid mixing in `pip install` or a system Python unless you are intentionally debugging environment issues

If you want the project-local interpreter explicitly, activate `.venv` created by `uv`, but the default examples below assume `uv run`.

## Included Skills

- `skills/opentrons-protocol-author`
  - Drafts or refactors Python protocols.
  - Includes a template and concise references for OT-2/Flex metadata, runtime parameters, and `capture_image()`.
- `skills/opentrons-protocol-verify`
  - Wraps local `opentrons` analyze/simulate entry points with environment checks.
  - Detects missing dependencies and missing source layout before trying to execute.
- `skills/opentrons-robot-lan`
  - Talks to a robot over the Opentrons HTTP API.
  - Covers health, camera settings, preview capture, protocol upload, analysis creation, run creation, and run actions.

## Repository Layout

```text
Opentrons-Lab-Agent/
├── .claude-plugin/plugin.json
├── skills/
│   ├── opentrons-protocol-author/
│   ├── opentrons-protocol-verify/
│   └── opentrons-robot-lan/
├── src/opentrons_lab_agent/
└── tests/
```

## Using It In Claude Code

This repository is already shaped like a Claude Code plugin:

- plugin metadata lives at `.claude-plugin/plugin.json`
- skills live under `skills/`
- helper code lives under `src/`

If you distribute skills through a Claude Code plugin or marketplace workflow, this repo is ready for that structure. If you use direct skills folders, you can also copy the individual skill directories under `skills/` into the Claude Code skills location used in your environment.

## Local Opentrons Runtime Assumptions

The verification skill is intentionally defensive.

It assumes the Opentrons source tree may be vendored into the same workspace, but not necessarily installed as a working Python package. In the current workspace snapshot, the available `opentrons/` tree contains `api/`, `api-client/`, and `shared-data/`, but it does not include a fully usable local development environment. Because of that:

- the verification wrapper injects a minimal `opentrons._version` module at runtime
- the wrapper checks whether Python can import the modules needed for `opentrons.cli` and `opentrons.simulate`
- if third-party dependencies or sibling packages are missing, it exits with a clear diagnostic instead of pretending validation succeeded

This keeps Claude Code honest about what can and cannot be executed locally.

## Script Examples

### Check local analyze/simulate readiness

```bash
uv venv .venv
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py doctor
```

### Try protocol analysis

```bash
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py analyze path/to/protocol.py -- --check
```

### Query a robot on the LAN

```bash
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 health
```

### Upload a protocol and create an analysis

```bash
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 upload-protocol path/to/protocol.py
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 analyze-protocol <protocol-id>
```

## Source Mapping

These skills were written against the Opentrons code that is present in the same workspace:

- protocol analysis entry point: `opentrons/api/src/opentrons/cli/analyze.py`
- protocol simulation entry point: `opentrons/api/src/opentrons/simulate.py`
- Python protocol camera method: `opentrons/api/src/opentrons/protocol_api/protocol_context.py`
- HTTP client endpoint wrappers: `opentrons/api-client/src/`

## Testing

The helper modules are covered with lightweight unit tests that do not require a robot:

```bash
PYTHONPATH=src uv run python -m unittest discover -s tests -v
```
