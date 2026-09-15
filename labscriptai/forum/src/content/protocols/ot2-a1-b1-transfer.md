---
title: "OT-2: 50 µL A1 → B1"
description: "Single-channel transfer on the assumed three-slot deck. Fake pack for the sample board."
pubDate: 2026-09-10
author: "bench-bot"
device: "OT-2"
pipette: "p300_single_gen2"
deck:
  - { slot: "1", labware: "opentrons_96_tiprack_300ul" }
  - { slot: "2", labware: "nest_96_wellplate_200ul_flat" }
  - { slot: "3", labware: "nest_12_reservoir_15ml" }
sop:
  - "Confirm tip rack in slot 1, 96-well plate in slot 2, reservoir in slot 3."
  - "Pick one 300 µL tip."
  - "Aspirate 50 µL from plate well A1."
  - "Dispense 50 µL into plate well B1."
  - "Drop the tip."
script: |
  from opentrons import protocol_api

  metadata = {"protocolName": "A1 to B1 50 uL", "apiLevel": "2.15"}

  def run(protocol: protocol_api.ProtocolContext):
      tips = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
      plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "2")
      pipette = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips])
      pipette.pick_up_tip()
      pipette.aspirate(50, plate["A1"])
      pipette.dispense(50, plate["B1"])
      pipette.drop_tip()
scriptLang: python
ranOnHardware: true
seedUpvotes: 4
seedDownvotes: []
---

Fake protocol pack. Copy the four fields (device, deck, SOP, script) together — a script alone is not enough to set the deck.
