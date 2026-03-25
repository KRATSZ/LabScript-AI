---
name: opentrons-protocol-library
description: Use when searching for existing validated Opentrons protocols, referencing protocol patterns from the Cookbook, or looking for code examples from the protocol library. This skill provides access to 800+ validated protocols, common patterns (liquid level tracking, wash steps, CSV handling, tip tracking, etc.), and protocol templates.
license: Apache-2.0
compatibility: Requires an external Protocols-develop checkout provided through --library or OPENTRONS_PROTOCOL_LIBRARY_PATH.
---

# Opentrons Protocol Library

This skill provides access to a curated collection of validated Opentrons protocols and code patterns. Use this skill when:

- The user asks for an existing protocol for a specific application
- The user needs code examples for common operations (wash steps, loops, CSV handling, etc.)
- The user wants to reference the Cookbook for protocol patterns
- The user needs a template to start a new protocol

## When to Use This Skill

Trigger this skill when the user mentions:
- "existing protocols", "protocol library", "example protocols"
- "cookbook", "patterns", "code examples"
- Similar applications that may already have solutions
- Need for validated code snippets

## External Library Configuration

Before using this skill, point the helper script at an external `Protocols-develop` checkout:

- pass `--library /path/to/Protocols-develop`, or
- set `OPENTRONS_PROTOCOL_LIBRARY_PATH=/path/to/Protocols-develop`

That external checkout is reference-only and is not part of this repository's own directory layout.

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

3. **Read the Cookbook first** - Check if a pattern exists for the core operation

4. **Examine example protocols** - Read README.md and protocol files for implementation details

5. **Adapt and customize** - Modify the pattern/protocol to fit the user's specific needs

## Important Notes

- All protocols in this library are validated and have been run on real robots
- Protocols cover both OT-2 and Flex robots (check metadata)
- The Cookbook contains production-tested code patterns used across many protocols
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
- Cookbook patterns: `<configured-library>/Cookbook.md`
- Protocol template: `<configured-library>/Template/protocol_template.py`
