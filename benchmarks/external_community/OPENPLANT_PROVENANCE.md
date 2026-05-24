# OpenPlant Provenance Audit

Accessed: 2026-05-21

This audit separates the historical OpenPlant-style benchmark tasks from tasks
that can be traced to public OpenPlant Automation Protocols pages. The current
benchmark subset uses the source-strict set below.

## Source Policy

- `source_strict`: the task is derived from a public OpenPlant webpage and a
  linked public protocol file.
- `style_synthetic`: the task is inspired by OpenPlant-like lab automation but
  no matching public OpenPlant protocol page/file was found.
- `source_strict_adapted`: the task points at a real public source, but the
  benchmark prompt is a condensed adaptation rather than the webpage text.
- Paper-facing claims should not call `style_synthetic` tasks "real public
  OpenPlant tasks".

## External Task Source Levels

`benchmarks/external_community/tasks.yaml` now carries a `source_level` field on
all 66 tasks:

- `public_protocol_entry_adapted` (`EOPL001`-`EOPL018`): real public Opentrons
  Protocols folders/files, condensed into benchmark prompts.
- `authentic_public_source_adapted` (`EOPEN001`-`EOPEN018`): real public
  OpenPlant pages/files, condensed into benchmark prompts.
- `pylabrobot_doc_derived` (13 `EPLR` tasks): PyLabRobot documentation/API
  concept adaptations, not public wet-lab protocol entries.
- `project_synthetic_backend_stress` (17 `EPLR` tasks): project-authored
  backend-neutral stress tasks with no one-to-one PyLabRobot public example.

Paper-facing wording should say: External 66 contains 18 public Opentrons
Protocol adaptations, 18 source-strict OpenPlant adaptations, 13 PyLabRobot
documentation/API concept adaptations, and 17 project-authored backend stress
tasks. Do not claim that all 66 are real public protocol entries.

## Public Opentrons Protocols 18

The EOPL set now maps every task to a real folder under
`Opentrons/Protocols/protocols`. `EOPL012` was retargeted from an unmatched
bacterial-transformation-style prompt to a real adapter-ligation protocol.

| Task | Public folder | Public title / script | Audit status |
|---|---|---|---|
| EOPL001 | `85b0dc` | Syber Green PCR Prep with Cherrypicking / `pcr_prep.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL002 | `797dee-normalization` | Normalization with 50ml tubes / `normalization.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL003 | `0845ab` | Digestion and Bead Cleanup / `0845ab.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL004 | `29effa-mastermix` | Lyra Direct Covid-19 Mastermix Distribution / `29effa-mastermix.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL005 | `customizable_serial_dilution_ot2` | Customizable Serial Dilution for OT-2 / `customizable_serial_dilution.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL006 | `cherrypicking` | Cherrypicking / `cherrypicking.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL007 | `nucleic_acid_purification_with_magnetic_beads` | Nucleic Acid Purification with Magnetic Beads / `dna_purification.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL008 | `generic_pcr_prep_1` | Generic PCR Prep Part 1 - Mastermix Creation / `generic_pcr_prep_1.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL009 | `979d28-normalization` | Normalization / `normalization.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL010 | `7aa3fd-library-pooling` | NGS Prep Part 3/3: Library Pooling / `lib_pooling.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL011 | `384b23-plate-transfer` | Sample Transfer to 96 Well-Plate / `384b23-plate-transfer.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL012 | `4b4a80-adapter_ligation` | NEBNext Ultra II FS DNA Library Prep Kit, Adapter Ligation / `4b4a80-adapter_ligation.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL013 | `010526` | Restriction Digests / `010526.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL014 | `0fd3dd` | ELISA / `elisa.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL015 | `01a6b9` | Media Refilling / `media_filling.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL016 | `nextera-flex-library-prep-cherrypick-samples` | Nextera DNA Flex NGS Library Prep: Cherrypick Samples / `nextera_flex_cherrypick.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL017 | `thermocycler-csv` | Thermocycler from .csv / `thermocycler_csv.ot2.apiv2.py` | public_protocol_entry_adapted |
| EOPL018 | `7855ef-plate` | AgriSeq Library Prep Part 1 - DNA Transfer (96) / `7855ef-plate.ot2.apiv2.py` | public_protocol_entry_adapted |

## PyLabRobot 30 Source Judgment

PyLabRobot has strong public documentation for backend-neutral liquid-handling
objects, actions, resources, simulation, and tip tracking. It does not provide
30 public wet-lab protocol entries comparable to the Opentrons Protocols
catalog. The EPLR set is therefore split honestly:

| Source level | Count | Task IDs |
|---|---:|---|
| `pylabrobot_doc_derived` | 13 | EPLR001, EPLR003, EPLR005, EPLR007, EPLR010, EPLR011, EPLR015, EPLR020, EPLR021, EPLR023, EPLR024, EPLR025, EPLR029 |
| `project_synthetic_backend_stress` | 17 | EPLR002, EPLR004, EPLR006, EPLR008, EPLR009, EPLR012, EPLR013, EPLR014, EPLR016, EPLR017, EPLR018, EPLR019, EPLR022, EPLR026, EPLR027, EPLR028, EPLR030 |

Each `EPLR` row in `tasks.yaml` now carries either a `source_doc_url` plus
`public_doc_concept_adapted`, or a `source_note` saying it is project-authored.

## Public OpenPlant Catalog

The public OpenPlant repository describes the project as a library of tutorials,
protocols, and automation scripts for the Opentrons OT-2 platform. Its GitHub
HEAD at audit time was `405a19fe005bad7699ade05b61f0a0ea87c73d65`.

| Source ID | Public title | Public page | Public file | Audit status |
|---|---|---|---|---|
| OP_PY_001 | Glycerol stocks from 96-well cultures | https://openplant.github.io/openplant_automation_protocols/Protocols/Python/OP_PY_001/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Python/OP_PY_001/OP_PY_001.py | source_strict |
| OP_JN_001 | Glycerol stocks from 96-well cultures | https://openplant.github.io/openplant_automation_protocols/Protocols/Jupyter/OP_JN_001/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Jupyter/OP_JN_001/OP_JN_001.ipynb | source_strict |
| OP_JN_002 | DNA extraction of 96-well cultures with magnetic beads | https://openplant.github.io/openplant_automation_protocols/Protocols/Jupyter/OP_JN_002/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Jupyter/OP_JN_002/OP_JN_002.ipynb | source_strict |
| OP_JN_003 | Transformation of plasmids in 96-well format | https://openplant.github.io/openplant_automation_protocols/Protocols/Jupyter/OP_JN_003/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Jupyter/OP_JN_003/OP_JN_003.ipynb | source_strict |
| OP_JN_004 | Transformation of plasmids in 96-well format (OT thermocycler version) | https://openplant.github.io/openplant_automation_protocols/Protocols/Jupyter/OP_JN_004/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Jupyter/OP_JN_004/OP_JN_004.ipynb | source_strict |
| OP_JN_005 | Plating of cells from 96-well plates | https://openplant.github.io/openplant_automation_protocols/Protocols/Jupyter/OP_JN_005/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Jupyter/OP_JN_005/OP_JN_005.ipynb | source_strict |
| OP_PD_001 | Creating Glycerol Stocks in FluidX Tubes | https://openplant.github.io/openplant_automation_protocols/Protocols/Designer/OP_PD_001/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Designer/OP_PD_001/OP_PD_001.json | source_strict |
| OP_PD_002 | PCR Purification Using Magnetic Beads | https://openplant.github.io/openplant_automation_protocols/Protocols/Designer/OP_PD_002/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Designer/OP_PD_002/OP_PD_002.json | source_strict |
| OP_PD_003 | Plasmid Purification of 48 Samples Using the Machery Nagel Strip Kit | https://openplant.github.io/openplant_automation_protocols/Protocols/Designer/OP_PD_003/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Designer/OP_PD_003/OP_PD_003.json | source_strict |
| OP_PD_004_1 | Transformation Spreading to 6 Well Plates - Script 1 | https://openplant.github.io/openplant_automation_protocols/Protocols/Designer/OP_PD_004/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Designer/OP_PD_004/OP_PD_004_1.json | source_strict |
| OP_PD_004_2 | Transformation Spreading to 6 Well Plates - Script 2 | https://openplant.github.io/openplant_automation_protocols/Protocols/Designer/OP_PD_004/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Designer/OP_PD_004/OP_PD_004_2.json | source_strict |
| OP_PD_004_3 | Transformation Spreading to 6 Well Plates - Script 3 | https://openplant.github.io/openplant_automation_protocols/Protocols/Designer/OP_PD_004/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Designer/OP_PD_004/OP_PD_004_3.json | source_strict |
| OP_PD_004_4 | Transformation Spreading to 6 Well Plates - Script 4 | https://openplant.github.io/openplant_automation_protocols/Protocols/Designer/OP_PD_004/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Designer/OP_PD_004/OP_PD_004_4.json | source_strict |
| OP_PD_005_1 | Bacterial Transformation Protocol - Script 1 | https://openplant.github.io/openplant_automation_protocols/Protocols/Designer/OP_PD_005/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Designer/OP_PD_005/OP_PD_005_1.json | source_strict |
| OP_PD_005_2 | Bacterial Transformation Protocol - Script 2 | https://openplant.github.io/openplant_automation_protocols/Protocols/Designer/OP_PD_005/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Designer/OP_PD_005/OP_PD_005_2.json | source_strict |
| OP_PD_005_3 | Bacterial Transformation Protocol - Script 3 | https://openplant.github.io/openplant_automation_protocols/Protocols/Designer/OP_PD_005/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Designer/OP_PD_005/OP_PD_005_3.json | source_strict |
| OP_PD_005_4 | Bacterial Transformation Protocol - Script 4 | https://openplant.github.io/openplant_automation_protocols/Protocols/Designer/OP_PD_005/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Designer/OP_PD_005/OP_PD_005_4.json | source_strict |
| OP_PD_006 | PCR Plate Preparation | https://openplant.github.io/openplant_automation_protocols/Protocols/Designer/OP_PD_006/ | https://github.com/openplant/openplant_automation_protocols/blob/main/Protocols/Designer/OP_PD_006/OP_PD_006.json | source_strict |

## Current EOPEN001-EOPEN018 Mapping

The current `benchmarks/external_community/tasks.yaml` `EOPEN001`-`EOPEN018`
entries have been replaced with the source-strict OpenPlant set below. The task
IDs were kept stable so existing benchmark selection commands do not break.

| Current task | Current upstream_id | Public title / script | Audit status | Notes |
|---|---|---|---|---|
| EOPEN001 | OP_PY_001 | Glycerol stocks from 96-well cultures | source_strict_adapted | Python protocol |
| EOPEN002 | OP_JN_001 | Glycerol stocks from 96-well cultures | source_strict_adapted | Jupyter protocol |
| EOPEN003 | OP_JN_002 | DNA extraction of 96-well cultures with magnetic beads | source_strict_adapted | Jupyter protocol |
| EOPEN004 | OP_JN_003 | Transformation of plasmids in 96-well format | source_strict_adapted | Jupyter protocol |
| EOPEN005 | OP_JN_004 | Transformation of plasmids in 96-well format (OT thermocycler version) | source_strict_adapted | Jupyter protocol |
| EOPEN006 | OP_JN_005 | Plating of cells from 96-well plates | source_strict_adapted | Jupyter protocol |
| EOPEN007 | OP_PD_001 | Creating Glycerol Stocks in FluidX Tubes | source_strict_adapted | Protocol Designer JSON |
| EOPEN008 | OP_PD_002 | PCR Purification Using Magnetic Beads | source_strict_adapted | Protocol Designer JSON |
| EOPEN009 | OP_PD_003 | Plasmid Purification of 48 Samples Using the Machery Nagel Strip Kit | source_strict_adapted | Protocol Designer JSON |
| EOPEN010 | OP_PD_004_1 | Transformation Spreading to 6 Well Plates - Script 1 | source_strict_adapted | Protocol Designer JSON |
| EOPEN011 | OP_PD_004_2 | Transformation Spreading to 6 Well Plates - Script 2 | source_strict_adapted | Protocol Designer JSON |
| EOPEN012 | OP_PD_004_3 | Transformation Spreading to 6 Well Plates - Script 3 | source_strict_adapted | Protocol Designer JSON |
| EOPEN013 | OP_PD_004_4 | Transformation Spreading to 6 Well Plates - Script 4 | source_strict_adapted | Protocol Designer JSON |
| EOPEN014 | OP_PD_005_1 | Bacterial Transformation Protocol - Script 1 | source_strict_adapted | Protocol Designer JSON |
| EOPEN015 | OP_PD_005_2 | Bacterial Transformation Protocol - Script 2 | source_strict_adapted | Protocol Designer JSON |
| EOPEN016 | OP_PD_005_3 | Bacterial Transformation Protocol - Script 3 | source_strict_adapted | Protocol Designer JSON |
| EOPEN017 | OP_PD_005_4 | Bacterial Transformation Protocol - Script 4 | source_strict_adapted | Protocol Designer JSON |
| EOPEN018 | OP_PD_006 | PCR Plate Preparation | source_strict_adapted | Protocol Designer JSON |

## Source-Strict OpenPlant 18

The source-strict OpenPlant benchmark now uses:

1. `OP_PY_001`
2. `OP_JN_001`
3. `OP_JN_002`
4. `OP_JN_003`
5. `OP_JN_004`
6. `OP_JN_005`
7. `OP_PD_001`
8. `OP_PD_002`
9. `OP_PD_003`
10. `OP_PD_004_1`
11. `OP_PD_004_2`
12. `OP_PD_004_3`
13. `OP_PD_004_4`
14. `OP_PD_005_1`
15. `OP_PD_005_2`
16. `OP_PD_005_3`
17. `OP_PD_005_4`
18. `OP_PD_006`

This preserves an 18-task OpenPlant subset without pretending that unpublished
`OP_PY_002`-`OP_PY_018` protocols exist.

## Implementation Notes

- Existing `runs/authoring-pilot/openplant18-*` results should not be reused as
  evidence for the current source-strict OpenPlant 18. They were generated
  against the older OpenPlant-style prompts.
- After rewriting tasks, rerun the three rows used in the paper table:
  direct DeepSeek, direct DeepSeek + fix-loop, and LabscriptAI authoring.
