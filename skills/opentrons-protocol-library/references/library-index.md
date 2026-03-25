# Protocol Library Quick Index

This document provides quick access to the contents of an external `Protocols-develop` checkout.

## Protocol Library Location

Configure the library path with one of these:

- `--library /path/to/Protocols-develop`
- `OPENTRONS_PROTOCOL_LIBRARY_PATH=/path/to/Protocols-develop`

## Structure

```
<configured-library>/
├── protocols/           # 800+ validated protocols
│   ├── {protocol_id}/   # Each protocol has its own folder
│   │   ├── README.md    # Description, categories, setup
│   │   ├── *.ot2.apiv2.py  # Protocol file
│   │   └── fields.json  # Optional parameters
├── Cookbook.md          # Common code patterns
├── Template/            # Protocol templates
└── protolib/            # Helper functions
```

## Major Protocol Categories

### Sample Preparation
- DNA extraction (various kits)
- RNA extraction
- Magnetic bead cleanup
- Library prep (Illumina, Nextera, etc.)

### Liquid Handling
- Serial dilution
- Plate filling
- Pooling / Aliquoting
- Master mix preparation

### Assay Types
- PCR preparation
- qPCR setup
- ELISA
- Enzymatic assays

## Search the Library

Use the search script:

```bash
# Search by keywords
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  --library /path/to/Protocols-develop \
  search "magnetic beads" "DNA cleanup" --limit 5

# List Cookbook patterns
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  --library /path/to/Protocols-develop \
  cookbook

# List protocol categories
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  --library /path/to/Protocols-develop \
  categories
```

## Quick Protocol Reference

### Common Protocol Prefixes
- `00*` - Early protocols (legacy OT-1)
- `1*` - Standard OT-2 protocols
- `sci-*` - Scientific protocols (kit-specific)
- `test*` - Test/development protocols

### Popular Protocol Groups

| Group | Description | Example Prefixes |
|-------|-------------|------------------|
| Nucleic Acid Prep | DNA/RNA extraction, cleanup | `omega-biotek`, `zymo`, `sci-idt` |
| Library Prep | NGS library preparation | `illumina`, `nextera`, `kapa` |
| Plate Handling | Dilution, pooling, filling | `serial`, `pooling`, `aliquoting` |
| PCR/qPCR | PCR plate setup | `pcr`, `qpcr`, `complete-pcr` |

## Cookbook Patterns Reference

See `<configured-library>/Cookbook.md` for complete details:

1. **Basic Skeleton Protocol** - Template for any new protocol
2. **Liquid Level Tracking** - Simple, Complex, and API 2.13+ versions
3. **Refill Tips Mid-Protocol** - Tip management for long protocols
4. **Wash Steps** - Standard wash patterns
5. **Remove Supernatant** - Supernatant removal methods
6. **Loop** - Iteration patterns
7. **Using CSVs** - CSV parsing and well mapping
8. **Track Data Across Protocol Runs** - Data persistence
9. **Tip Tracking with Refills** - Advanced tip management
10. **Flash Robot Lights** - Robot status indication

## Getting Started with a Protocol

1. Identify your application (e.g., "magnetic bead DNA cleanup")
2. Search the library using keywords
3. Read the README.md of matching protocols
4. Examine the protocol code for patterns to adapt
5. Check the Cookbook for any relevant patterns
6. Adapt the code to your specific needs

## Tips for Protocol Authors

- Start from a similar protocol rather than from scratch when possible
- The Cookbook contains production-tested code patterns
- Always verify API level compatibility with your robot
- Protocol READMEs often contain valuable setup notes
- Custom labware may be required for some protocols
