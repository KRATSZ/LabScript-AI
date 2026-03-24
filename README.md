# Opentrons Lab Agent Skills

[Agent Skills](https://agentskills.io) are a simple, open format for giving AI agents new capabilities. This repository contains Opentrons-focused skills that extend Claude's abilities for working with Opentrons OT-2 and Flex laboratory robots.

## About

These skills teach Claude how to:

- **Write and revise Python protocols** for OT-2 and Flex robots with proper deck setup, labware loading, pipette configuration, and camera capture
- **Validate protocols locally** using Opentrons's analyze and simulate tools, with environment readiness checks
- **Control robots via LAN HTTP API** for health checks, camera preview, protocol upload, run creation, and playback control
- **Reference validated protocol library** with 800+ example protocols and common code patterns

## Skills Included

| Skill | Description | When to Use |
|--------|-------------|--------------|
| `opentrons-protocol-author` | Drafts or refactors Python protocols for Opentrons robots | Writing new protocols, editing existing ones, or reviewing protocol code |
| `opentrons-protocol-verify` | Analyzes and simulates protocols using local Opentrons runtime | Checking if a protocol is valid, simulating execution, diagnosing environment issues |
| `opentrons-robot-lan` | Interacts with robots over LAN HTTP API | Querying robot status, viewing camera, uploading protocols, controlling runs |
| `opentrons-protocol-library` | References validated protocols and Cookbook patterns | Searching for existing protocols, finding code examples, referencing protocol patterns |

## Using with Claude Code

### Option 1: Project-Level Skills (Recommended)

The simplest way is to keep skills in your project under the `skills/` directory. Claude Code automatically discovers skills in the following locations:

| Location | Scope |
|----------|--------|
| `<project>/skills/` | Project-specific skills (this repository's structure) |
| `<project>/.claude/skills/` | Claude Code native location |
| `~/.claude/skills/` | User-level skills available across projects |

**To use these skills with Claude Code:**

1. Clone or copy this repository to your project directory
2. Ensure the `skills/` folder is in your working directory
3. Start Claude Code in that directory
4. Claude will automatically discover and load the skills

When working on a protocol, simply describe what you need:

```
Write an OT-2 protocol that transfers liquid from a 96-well plate to a 384-well plate.
```

Claude will automatically use the `opentrons-protocol-author` skill.

### Option 2: Install as Claude Code Plugin

You can package these skills as a Claude Code plugin for easier distribution:

```bash
/plugin marketplace add <your-org>/opentrons-lab-agent-skills
```

Or install individual skills by copying them to `~/.claude/skills/`.

### Option 3: Manual Skill Installation

Copy individual skill directories to your Claude Code skills location:

```bash
# Linux/macOS
cp -r skills/opentrons-protocol-author ~/.claude/skills/
cp -r skills/opentrons-protocol-verify ~/.claude/skills/
cp -r skills/opentrons-robot-lan ~/.claude/skills/

# Windows
xcopy /E /I skills\opentrons-protocol-author %USERPROFILE%\.claude\skills\
```

## Python Environment

These skills assume Python is managed with `uv` for reproducible environments.

```bash
# Create local virtual environment
uv venv .venv

# Run scripts through uv
uv run python skills/opentrons-protocol-verify/scripts/verify_protocol.py doctor
uv run python skills/opentrons-robot-lan/scripts/opentrons_robot_api.py --host 192.168.1.50 health
```

## Skill Structure

Each skill follows the [Agent Skills specification](https://agentskills.io/specification):

```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/           # Optional: executable code
├── references/        # Optional: documentation
├── assets/           # Optional: templates, resources
└── evals/            # Recommended: test cases
```

The `SKILL.md` file contains:
- **Frontmatter**: `name`, `description`, `license`, `compatibility`
- **Instructions**: Step-by-step guidance for Claude
- **References**: Links to bundled resources

## Example Usage

### Writing a Protocol

```
I need a Flex protocol that does a serial dilution starting with 100ul
in the first well and 1:2 dilution across 8 wells of a 96 plate.
```

### Validating a Protocol

```
Check if this protocol is valid: protocols/my_protocol.py
```

### Controlling a Robot

```
My OT-2 is at 192.168.1.50. Check its health status and show me
the camera preview.
```

## Testing and Evaluation

Each skill includes `evals/evals.json` test cases following the [Agent Skills evaluation pattern](https://agentskills.io/docs/skill-creation/evaluating-skills):

```bash
# Validate skill structure
skills-ref validate ./skills/opentrons-protocol-author
skills-ref validate ./skills/opentrons-protocol-verify
skills-ref validate ./skills/opentrons-robot-lan
skills-ref validate ./skills/opentrons-protocol-library
```

## Repository Layout

```
Opentrons-Lab-Agent/
├── skills/
│   ├── opentrons-protocol-author/    # Protocol authoring skill
│   ├── opentrons-protocol-verify/    # Protocol validation skill
│   ├── opentrons-robot-lan/         # Robot API control skill
│   └── opentrons-protocol-library/  # Protocol knowledge base (requires Protocols-develop/)
├── src/opentrons_lab_agent/             # Helper modules
├── tests/                               # Unit tests
├── README.md
└── CONTRIBUTING.md                        # Development guidelines
```

## Protocol Library Knowledge Base

The `opentrons-protocol-library` skill references the `Protocols-develop` directory which contains:

- **800+ validated protocols** with README documentation
- **Cookbook.md** with common code patterns (liquid level tracking, wash steps, loops, CSV handling, etc.)
- **Protocol templates** for new protocol development
- **Helper functions** in the `protolib/` directory

### Searching the Library

```bash
# Search protocols by keywords
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  search "magnetic beads" "DNA cleanup"

# List Cookbook patterns
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py cookbook

# List protocol categories
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py categories
```

### Example Queries

- "Is there a protocol for magnetic bead DNA cleanup?"
- "Show me how to implement liquid level tracking"
- "Find me a protocol that does serial dilution"
- "What's the pattern for CSV-based plate layout?"

## Local Opentrons Runtime Assumptions

The verification skill is intentionally defensive about local Opentrons runtime readiness:

- Checks if Python can import `opentrons.cli` and `opentrons.simulate`
- Injects a minimal `opentrons._version` shim if needed
- Reports missing dependencies clearly instead of pretending validation succeeded

This ensures Claude Code provides accurate feedback about what can and cannot be executed locally.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on developing and validating new skills.

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## References

- [Agent Skills Specification](https://agentskills.io/specification)
- [Adding Skills Support](https://agentskills.io/docs/client-implementation/adding-skills-support)
- [Example Skills](https://github.com/anthropics/skills)
- [Opentrons Protocol API Documentation](https://docs.opentrons.com/)
