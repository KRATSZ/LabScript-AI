---
name: opentrons-protocol-library
description: Search 833 reference protocols, find code examples, browse the bundled protocol catalog.
type: script-backed
entry: scripts/search_protocols.py
mcp_tools: []
---

# Opentrons Protocol Library

This skill provides access to a curated collection of validated Opentrons protocols and code patterns. Use this skill when:

- The user asks for an existing protocol for a specific application
- The user needs code examples for common operations (wash steps, loops, CSV handling, etc.)
- The user wants protocol patterns or reusable snippets from validated real protocols
- The user needs a template to start a new protocol

## When to Use This Skill

Trigger this skill when the user mentions:
- "existing protocols", "protocol library", "example protocols"
- "cookbook", "patterns", "code examples"
- Similar applications that may already have solutions
- Need for validated code snippets

## Library Resolution

The helper script resolves the library in this order:

1. `--library /path/to/Protocols-develop`
2. `OPENTRONS_PROTOCOL_LIBRARY_PATH=/path/to/Protocols-develop`
3. bundled `reference-protocols/Protocols-develop`
4. legacy sibling `../Protocols-develop`

The bundled snapshot is reference-only. It should be read and searched, not edited as part of normal feature work.

## Commands

```bash
# Search by keywords (uses catalog index)
uv run python scripts/search_protocols.py search "serial dilution"

# Browse available categories and method tags
uv run python scripts/search_protocols.py catalog

# Show detailed metadata for a specific protocol
uv run python scripts/search_protocols.py show <slug>

# Pull focused code or README snippets
uv run python scripts/search_protocols.py snippet <slug> <keywords>

# Regenerate catalog after library updates
python reference-protocols/Protocols-develop/scripts/generate_catalog.py
```

## Available Resources

### Protocol Catalog (`protocol-catalog.json`)

A pre-built searchable index of all 833 protocols. When available, the search script uses this for fast lookups instead of scanning all README files.

### Cookbook (`Cookbook.md`)

Reusable code patterns: Basic Skeleton, Liquid Level Tracking, Refill Tips, Wash Steps, Remove Supernatant, Loop, Using CSVs, Tip Tracking, Flash Robot Lights. Not every snapshot contains it.

### Templates (`Template/`)

`protocol_template.py` — basic protocol structure.

## Common Protocol Categories

- **Sample Preparation**: DNA/RNA extraction, purification, magnetic bead cleanup, library prep
- **Liquid Handling**: Serial dilution, plate filling, aliquoting, master mix, cherry picking
- **Assay Types**: PCR, qPCR, ELISA, enzymatic assays, Luminex

## Search Workflow

1. **Understand requirement** → 2. **Search** with keywords → 3. **Inspect** top matches → 4. **Pull snippets** → 5. **Adapt** to user needs

## Important Notes

- The bundled `protocols/` snapshot is reference material, not revalidated on every change
- Protocols cover both OT-2 and Flex (check metadata)
- Always verify API level matches user's robot
- Custom labware definitions may be needed for some protocols
