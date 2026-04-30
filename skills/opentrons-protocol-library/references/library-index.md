# Protocol Library Quick Index

This document provides quick access to the bundled or overridden `Protocols-develop` reference library.

## Protocol Catalog (Recommended)

The **protocol-catalog.json** is a pre-built index of all 833 protocols. When available,
the search script uses it for fast lookups instead of scanning all folders.

- **JSON catalog**: `<configured-library>/protocol-catalog.json`
- **Markdown catalog**: `<configured-library>/protocol-catalog.md`

### Regenerating the catalog

```bash
python reference-protocols/Protocols-develop/scripts/generate_catalog.py
```

## Protocol Library Location

The helper script resolves the library path in this order:

1. `--library /path/to/Protocols-develop`
2. `OPENTRONS_PROTOCOL_LIBRARY_PATH=/path/to/Protocols-develop`
3. bundled `reference-protocols/Protocols-develop`
4. sibling `../Protocols-develop`

## Structure

```
<configured-library>/
├── protocol-catalog.json    # Searchable index (833 protocols)
├── protocol-catalog.md      # Human-readable catalog by category
├── protocols/               # 833 protocol folders
│   ├── {protocol_id}/       # Each protocol has its own folder
│   │   ├── README.md        # Description, categories, setup
│   │   ├── *.ot2.apiv2.py   # Protocol file
│   │   ├── fields.json      # Customizable parameters
│   │   └── labware/         # Custom labware definitions (optional)
├── protolib/                # Python library for parsing protocols
└── scripts/
    ├── generate_catalog.py  # Generate the catalog index
    ├── consistencyCheck.py  # Validate protocol structure
    └── ...
```

## Search Commands

```bash
# Search by keywords (uses catalog when available for fast lookup)
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  search "magnetic beads" "DNA cleanup" --limit 5

# Show catalog summary and top method tags
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  catalog

# Inspect one protocol folder
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  show 00222e

# Pull focused README/code snippets
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  snippet 00222e serial plasma

# List Cookbook patterns (when Cookbook.md exists)
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  cookbook

# List protocol categories
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py \
  categories
```

## Top Method Tags

These normalized tags are the fastest way to find protocols by purpose:

| Tag | Count | Typical Use |
|-----|-------|-------------|
| sample_prep | 291 | General sample preparation workflows |
| ngs_library_prep | 193 | NGS library preparation (Illumina, Nextera, etc.) |
| plate_filling | 143 | Plate filling, pooling, aliquoting |
| pcr | 124 | PCR-related protocols |
| pcr_prep | 101 | PCR plate setup |
| nucleic_acid_extraction | 86 | DNA/RNA extraction and purification |
| cherrypicking | 36 | Cherry-picking samples |
| normalization | 35 | Concentration normalization |
| proteins_proteomics | 28 | Protein assays and purification |
| assay | 21 | Various assay types |

## Cookbook Patterns Reference

If `Cookbook.md` exists in the selected snapshot, use:

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

1. Search the catalog: `search "your keywords" --limit 5`
2. Show protocol details: `show <slug>`
3. Pull relevant snippets: `snippet <slug> keywords...`
4. Read the protocol Python file for patterns
5. Adapt the code to your specific needs
