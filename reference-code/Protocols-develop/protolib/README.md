# `protolib` - Protocol Library protocol parser

Protolib traverses through a directory of protocols, parses supported files inside each protocol subdirectory, and creates a JSON intended for use by Opentrons Protocol Library: http://protocols.opentrons.com

## Supported protocol files

Inside `protocols/`, each subdirectory represents a single or multiple protocol(s) and can contain these files:

- `*.ot1.py`: OT1 Python protocol file(s)
- `*.ot2.py`: OT2 Python protocol file(s)
- `*.md` (preferably `README.md`): A single README files for the entire directory following a specific Markdown format

### README format

See `TEMPLATE/README.md` for a (SOMEWHAT OUTDATED) example of the README format.

Note that the `subcategory` section must be indented by a tab, not by spaces.

## Use in development

From the repo root:

```bash
make install parse-errors parse-ot1 parse-ot2 parse-README
python -m protolib
```

## Output JSON format

Contains 2 keys: `protocols` & `categories`

### `categories`

An object of the form:

```json
"categories": {
  "Proteins & Proteomics": [
    "Assay",
    "ELISA",
    "Protein Crystallography",
    "Sample Prep"
  ],
  "Cell Culture": [
    "Media Exchange"
  ]
}
```

### `protocols`

An arbitrarily-ordered array of protocol objects.

A single protocol object is of the form:

```json
{
  "slug": "10X_serial_dilution",
  "path": "protocols/10X_serial_dilution",
  "flags": {
    "feature": true,
    "skip-tests": false,
    "embedded-app": false
  },
  "files": {
    "description": ["README.md"],
    "OT 1 protocol": ["10x_serial_dilution.ot1.py"],
    "OT 2 protocol": ["10x_serial_dilution.ot2.py"]
  },
  "status": "ok",
  "protocols": {
    "OT 1 protocol": [
      {
        "instruments": [
          {
            "name": "m200",
            "axis": "a",
            "channels": 8,
            "type": "pipette",
            "min_volume": 20,
            "max_volume": 200
          }
        ],
        "containers": [
          {
            "type": "trough-12row",
            "slot": "D2",
            "name": "trough"
          },
          {
            "type": "96-PCR-flat",
            "slot": "C1",
            "name": "plate"
          },
          {
            "type": "tiprack-200ul",
            "slot": "A1",
            "name": "m200-rack"
          },
          {
            "type": "trash-box",
            "slot": "B2",
            "name": "trash-box"
          }
        ],
        "parameters": [
          {
            "name": "final_volume",
            "annotation": {
              "type": "float"
            },
            "default": 200
          }
        ]
      }
    ],
    "OT 2 protocol": [
      {
        "instruments": [
          {
            "name": "p300_multi_v1",
            "mount": "left"
          }
        ],
        "modules": [
          {
            "name": "magdeck",
            "slot": "2"
          }
        ],
        "labware": [
          {
            "type": "biorad-hardshell-96-PCR",
            "slot": "2",
            "name": "biorad-hardshell-96-PCR",
            "share": true
          }
        ],
        "parameters": [
          {
            "name": "final_volume",
            "annotation": {
              "type": "float"
            },
            "default": 200
          }
        ]
      }
    ]
  },
  "title": "Example Protocol",
  "author": "Opentrons",
  "partner": "",
  "categories": {
    "Demos": ["Examples"]
  },
  "description": "An example protocol.",
  "time-estimate": "2 minutes",
  "robot": ["OT PRO", "OT Standard", "OT Hood"],
  "modules": [],
  "reagents": ["Buffer", "DNA"],
  "process": "Process details here",
  "notes": "Notes here",
  "internal": "Internal code for record-keeping"
}
```
