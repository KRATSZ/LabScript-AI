---
title: "50 µL serial dilution"
description: "Serial dilution across row A, then a Fluent worklist sketch."
pubDate: 2026-09-14
author: "fluent-notes"
device: "Tecan Fluent"
pipette: "liha_1000"
deck:
  - { slot: "1", labware: "tecan_diti_200ul_tiprack" }
  - { slot: "2", labware: "tecan_96_wellplate" }
  - { slot: "3", labware: "nest_12_reservoir_15ml" }
sop:
  - "DiTi rack in grid 1, 96-well plate in grid 2, reservoir in grid 3."
  - "Aspirate 50 µL diluent from the reservoir into A1."
  - "Transfer 50 µL A1 → A2, mix once, then A2 → A3 through A6."
  - "Leave A7–A12 empty on this pack."
  - "Export is a Fluent .gwl worklist; a human still loads it in FluentControl."
script: |
  A;50;Reservoir;A1;Plate;A1
  A;50;Plate;A1;Plate;A2
  A;50;Plate;A2;Plate;A3
  A;50;Plate;A3;Plate;A4
  A;50;Plate;A4;Plate;A5
  A;50;Plate;A5;Plate;A6
scriptLang: gwl
ranOnHardware: false
seedUpvotes: 2
seedDownvotes: []
---

Fake Fluent pack. The script field here is a tiny worklist sketch, not a full `.gwl` file.
