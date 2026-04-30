# Reference Code

This directory contains the **Opentrons Protocol Library** snapshot — a collection of 833 validated lab automation protocols for the OT-2 robot.

## Contents

| Path | Description |
|------|-------------|
| `Protocols-develop/protocols/` | 833 protocol folders, each with README + Python + fields |
| `Protocols-develop/protocol-catalog.json` | Machine-readable searchable index of all protocols |
| `Protocols-develop/protocol-catalog.md` | Human-readable catalog grouped by category |
| `Protocols-develop/protolib/` | Python library for parsing protocol metadata |
| `Protocols-develop/scripts/` | Utility scripts (catalog generation, validation, etc.) |

## Usage for Agents

The protocol catalog is the primary entry point for finding protocols:

```bash
# Regenerate the catalog after adding/removing protocols
python Protocols-develop/scripts/generate_catalog.py

# Search by keywords (fast, uses catalog index)
python skills/opentrons-protocol-library/scripts/search_protocols.py \
  search "magnetic beads" "extraction" --limit 5

# Show catalog summary
python skills/opentrons-protocol-library/scripts/search_protocols.py catalog
```

## Protocol Folder Structure

Each protocol folder contains:
- `README.md` — description, categories, labware, pipettes, process notes
- `*.ot2.apiv2.py` — Python protocol file (OT-2 API v2)
- `fields.json` — customizable parameters for the Protocol Designer UI
- `labware/` — custom labware JSON definitions (optional)

## Naming Convention

Folders use two naming styles:
- **Hex IDs** (~80%): `00222e`, `030dd8-amplify`, `0479ad-part-2`
- **Descriptive** (~20%): `normalization`, `zymo-quick`, `sci-thermofisher-magmax`

The catalog provides human-readable titles and tags for all protocols, regardless of folder name.

## Source

This is a snapshot of the [Opentrons Protocol Library](https://protocols.opentrons.com/) for offline agent use.
It is read-only reference material — do not edit protocols in place.
