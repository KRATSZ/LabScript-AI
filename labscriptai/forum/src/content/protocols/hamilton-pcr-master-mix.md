---
title: "Hamilton STAR: 20 µL PCR mix × 8"
description: "Dispense master mix from the reservoir into eight sample wells. Fake pack."
pubDate: 2026-09-12
author: "mix-tech"
device: "Hamilton STAR"
pipette: "star_1000"
deck:
  - { slot: "1", labware: "hamilton_96_tiprack_300ul" }
  - { slot: "2", labware: "corning_96_wellplate_360ul_flat" }
  - { slot: "3", labware: "nest_12_reservoir_15ml" }
sop:
  - "Load 300 µL tips in slot 1, Corning 96-well plate in slot 2, 12-row reservoir in slot 3."
  - "Fill reservoir column 1 with PCR master mix."
  - "Aspirate 20 µL from the reservoir."
  - "Dispense 20 µL into plate wells A1 through H1."
  - "Do not mix in the plate on this pack."
script: |
  # Plan-IR style steps (not a live Hamilton run)
  steps = [
      {"op": "pick_tip", "slot": "1"},
      {"op": "aspirate", "ul": 20, "labware": "reservoir", "well": "A1"},
      {"op": "dispense", "ul": 20, "labware": "plate", "wells": ["A1","B1","C1","D1","E1","F1","G1","H1"]},
      {"op": "drop_tip"},
  ]
scriptLang: python
ranOnHardware: false
seedUpvotes: 1
seedDownvotes:
  - { reason: leak }
---

Simulation-only sample. One seeded downvote is a **leak** on the reservoir aspirate — that is why a reason category is required.
