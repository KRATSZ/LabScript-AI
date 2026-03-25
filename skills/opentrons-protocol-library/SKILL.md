---
name: opentrons-protocol-library
description: Use when searching for existing validated Opentrons protocols, referencing bundled protocol patterns, or looking for code examples from the protocol library. This skill provides access to a bundled Protocols-develop snapshot plus override support for external copies.
license: Apache-2.0
compatibility: Uses the bundled reference-code/Protocols-develop snapshot by default, and also supports external Protocols-develop paths via --library or OPENTRONS_PROTOCOL_LIBRARY_PATH.
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
3. bundled `reference-code/Protocols-develop`
4. legacy sibling `../Protocols-develop`

The bundled snapshot is reference-only. It should be read and searched, not edited as part of normal feature work.

## Available Resources

### Protocol Library (`<configured-library>/protocols/`)

Contains 800+ validated protocols organized by application. Each protocol folder includes:
- `README.md` - Protocol description, categories, labware, reagents, deck setup, and process notes
- `{protocol_name}.ot2.apiv2.py` - The actual Python protocol file
- `fields.json` (optional) - Customizable parameters
- `.feature`, `.ignore`, etc. - Special flags for protocol status

**Search strategy:**
1. Identify the key application keywords (e.g., "PCR", "magnetic beads", "serial dilution")
2. Browse protocol folders by name and README descriptions
3. Read relevant protocol files for code patterns to adapt

### Cookbook (`<configured-library>/Cookbook.md`)

Comprehensive collection of reusable code patterns including:

| Pattern | Description | When to Reference |
|---------|-------------|-------------------|
| Basic Skeleton | Template for any new protocol | Starting from scratch |
| Liquid Level Tracking | Simple, Complex, and API 2.13+ versions | Working with variable liquid volumes |
| Refill Tips Mid-Protocol | Tip management for long protocols | Managing tip consumption |
| Wash Steps | Standard wash patterns | Magnetic bead cleanup, column washing |
| Remove Supernatant | Supernatant removal methods | After incubation steps |
| Loop | Loop patterns | Iterating through wells/tubes |
| Using CSVs | CSV parsing and well mapping | Importing plate layouts |
| Track Data Across Protocol Runs | Data persistence | Recording run information |
| Tip Tracking with Refills | Advanced tip management | Complex multi-refill protocols |
| Flash Robot Lights | Robot status indication | User feedback during runs |

Some snapshots do not include `Cookbook.md`. In that case, use `show` and `snippet` against matching protocol folders instead of assuming a cookbook exists.

### Templates (`<configured-library>/Template/`)

- `protocol_template.py` - Basic protocol structure
- `README.md` - Template documentation

### Protocol Library Tools (`<configured-library>/protolib/`)

Helper functions for protocol development:
- `merge.py` - Protocol merging utilities
- `parse/` - Protocol parsing tools
- `traversals/` - Code traversal helpers
- `traverse_errors.py` - Error handling patterns

## Common Protocol Categories

### Sample Preparation
- DNA extraction kits (various vendors)
- RNA extraction
- Nucleic acid purification
- Magnetic bead cleanup
- Library preparation (Illumina, Nextera, etc.)

### Liquid Handling
- Serial dilution
- Plate filling and pooling
- Aliquoting and normalization
- Master mix preparation
- Cherry picking

### Assay Types
- PCR prep and setup
- qPCR plate preparation
- ELISA setup
- Enzymatic assays
- Luminex assays

## Search and Reference Workflow

1. **Understand the user's requirement** - What specific operation or application?
2. **Search the protocol library** - Look for folders with relevant names and keywords
3. **Inspect one or two likely matches** - Use `show` for structure and metadata
4. **Pull focused snippets** - Use `snippet` for reusable code or README context
5. **Adapt and customize** - Modify the pattern/protocol to fit the user's specific needs

## Important Notes

- The bundled `protocols/` snapshot is reference material copied into this repository for agent use
- Those protocol files were originally validated protocol-library assets, but this repository does not revalidate all of them on every change
- Protocols cover both OT-2 and Flex robots (check metadata)
- `Cookbook.md` is useful when present, but not every snapshot contains it
- When referencing a protocol, always verify the API level matches the user's robot
- Custom labware definitions may be needed for some protocols

## Example Queries

- "Is there a protocol for magnetic bead DNA cleanup?"
- "Show me how to implement liquid level tracking"
- "Find me a protocol that does serial dilution"
- "What's the pattern for CSV-based plate layout?"
- "I need a PCR plate preparation protocol"

## Reference Files

- Complete protocol library: `<configured-library>/`
- Search tool: `scripts/search_protocols.py`
- Bundled agent examples: `examples/reference-protocols/`
