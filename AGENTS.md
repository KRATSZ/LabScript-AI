# Opentrons Lab Agent

A collection of Agent Skills for working with Opentrons OT-2 and Flex laboratory robots.

## Project Overview

This project provides AI agents with specialized knowledge for:

- **Protocol Authoring** - Writing and revising Python protocols for Opentrons robots
- **Protocol Validation** - Analyzing and simulating protocols locally
- **Simulation Repair** - Iteratively fixing protocols through a simulation-first loop
- **Robot Control** - Managing robots via LAN HTTP API
- **Protocol Library** - Accessing externally provided validated protocols and code patterns

## Available Skills

The following Agent Skills are available in `skills/`:

| Skill | Description | Trigger Keywords |
|--------|-------------|------------------|
| `opentrons-protocol-author` | Draft/revise Python protocols for OT-2/Flex | protocol, draft, write, OT-2, Flex, deck setup |
| `opentrons-simulation-repair` | Repair protocols through simulate -> parse -> edit loops | repair, fix protocol, simulation failure, traceback, blocker |
| `opentrons-protocol-verify` | Validate protocols using local runtime | validate, analyze, simulate, check, environment |
| `opentrons-robot-lan` | Control robots via HTTP API | robot, camera, upload, run, play, pause, API |
| `opentrons-protocol-library` | Reference validated protocols & Cookbook | example, library, cookbook, pattern, search, reference |

## When to Use Which Skill

Use this flow to determine the appropriate skill:

1. **User asks to write/edit a protocol** → `opentrons-protocol-author`
2. **User wants to verify a protocol** → `opentrons-protocol-verify`
3. **User needs robot control/camera** → `opentrons-robot-lan`
4. **User wants iterative simulation-first fixes** → `opentrons-simulation-repair`
5. **User looks for existing examples** → `opentrons-protocol-library`

## Protocol Library

The `opentrons-protocol-library` skill can query an external `Protocols-develop` checkout when you provide it explicitly with `--library` or `OPENTRONS_PROTOCOL_LIBRARY_PATH`:

- **800+ validated protocols** with README documentation
- **Cookbook.md** - Common patterns (liquid tracking, wash steps, loops, CSV, etc.)
- **Templates** - Protocol starting points
- **protolib/** - Helper functions

Search the library:
```bash
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  --library /path/to/Protocols-develop \
  search "magnetic beads" "DNA cleanup"
```

## Python Environment

This project uses `uv` for package management:

```bash
# Create virtual environment
uv venv .venv

# Run scripts
uv run python scripts/...
```

## Commands

### Protocol Validation
```bash
# Check Opentrons runtime readiness
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py doctor

# Analyze a protocol
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py \
  analyze path/to/protocol.py -- --check
```

### Robot API
```bash
# Health check
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py \
  --host 192.168.1.50 health

# Capture camera preview
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py \
  --host 192.168.1.50 capture-preview --output /tmp/preview.png
```

## Testing

```bash
# Run unit tests
PYTHONPATH=src uv run python -m unittest discover -s tests -v

# Validate skill structure
skills-ref validate ./skills/opentrons-protocol-author
skills-ref validate ./skills/opentrons-simulation-repair
skills-ref validate ./skills/opentrons-protocol-verify
skills-ref validate ./skills/opentrons-robot-lan
skills-ref validate ./skills/opentrons-protocol-library
```

## Important Notes

- Always verify API level compatibility (OT-2 vs Flex)
- Protocols in the external library are validated and production-tested
- Local validation uses the installed Opentrons runtime by default; source checkouts are opt-in
- Robot API requires network access to the robot on LAN
- Cookbook contains production-tested code patterns - prefer using them

## References

- [Agent Skills Specification](https://agentskills.io/specification)
- [Opentrons Protocol API](https://docs.opentrons.com/)
- [Opentrons Protocol Library](http://protocols.opentrons.com/)
