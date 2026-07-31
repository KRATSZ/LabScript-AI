import test from "node:test";
import assert from "node:assert/strict";

import {
  parseProtocolDeckHints,
  parseProtocolLiquidSourceMap,
  parseProtocolTransferContinuationHints,
  seedProtocolLiquidSourceMap,
} from "./protocol-liquid-sources.js";

/** Self-contained fixture mirroring the primary/reserve Assay Buffer protocol shape. */
const protocol03 = `
"""Primary + reserve Assay Buffer transfer.

Deck:
  B2  opentrons_flex_96_tiprack_1000ul
  C2  nest_12_reservoir_15ml
  D2  nest_96_wellplate_200ul_flat
  A3  trash bin

Liquid source map:
  C2.A1  primary Assay Buffer
  C2.A2  reserve Assay Buffer (same identity)

Confirm D2.A1 after transfers.
"""
from opentrons import protocol_api

metadata = {"protocolName": "Primary reserve buffer", "author": "LabscriptAI OT"}
requirements = {"robotType": "Flex", "apiLevel": "2.24"}

def run(protocol: protocol_api.ProtocolContext) -> None:
    trash = protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "B2")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "C2")
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "D2")
    pipette = protocol.load_instrument(
        "flex_1channel_1000",
        "left",
        tip_racks=[tiprack],
    )
    water = protocol.get_liquid_class(name="water")
    primary = reservoir["A1"]
    pipette.pick_up_tip()
    pipette.transfer_with_liquid_class(
        liquid_class=water, volume=100, source=primary, dest=plate["A1"],
        new_tip="never", trash_location=trash,
    )
    pipette.transfer_with_liquid_class(
        liquid_class=water, volume=100, source=primary, dest=plate["A2"],
        new_tip="never", trash_location=trash,
    )
    pipette.transfer_with_liquid_class(
        liquid_class=water, volume=100, source=primary, dest=plate["A3"],
        new_tip="never", trash_location=trash,
    )
    pipette.drop_tip(trash)
    pipette.pick_up_tip()
    pipette.require_liquid_presence(plate["A1"])
    pipette.drop_tip(trash)
`;

test("parseProtocolLiquidSourceMap reads primary and reserve Assay Buffer wells", () => {
  const parsed = parseProtocolLiquidSourceMap(protocol03);
  assert.equal(parsed.entries.length, 2);
  assert.deepEqual(parsed.entries.map(entry => entry.key), ["C2.A1", "C2.A2"]);
  assert.equal(parsed.entries[0].liquid_name, "Assay Buffer");
  assert.equal(parsed.entries[1].liquid_name, "Assay Buffer");
  assert.equal(parsed.entries[0].labware_load_name, "nest_12_reservoir_15ml");
});

test("parseProtocolDeckHints reads pipette and tip rack from protocol source", () => {
  const hints = parseProtocolDeckHints(protocol03);
  assert.equal(hints.pipette_name, "flex_1channel_1000");
  assert.equal(hints.mount, "left");
  assert.equal(hints.tiprack_load_name, "opentrons_flex_96_tiprack_1000ul");
  assert.equal(hints.tiprack_slot, "B2");
});

test("seedProtocolLiquidSourceMap writes missing source entries only once", () => {
  const sessionState = { liquid_tracking: { containers: {}, sources: {} } };
  const first = seedProtocolLiquidSourceMap(sessionState, protocol03);
  assert.deepEqual(first.seeded, ["C2.A1", "C2.A2"]);
  const second = seedProtocolLiquidSourceMap(sessionState, protocol03);
  assert.equal(second.seeded.length, 0);
  assert.equal(second.skipped, 2);
});

test("parseProtocolTransferContinuationHints reads transfer volume and destinations from protocol 03", () => {
  const hints = parseProtocolTransferContinuationHints(protocol03);
  assert.equal(hints.transfer_volume, 100);
  assert.equal(hints.liquid_class_name, "water");
  assert.deepEqual(hints.destination_wells, ["A1", "A2", "A3"]);
  assert.equal(hints.reservoir_slot, "C2");
  assert.equal(hints.plate_slot, "D2");
  assert.equal(hints.has_confirm_probe_cycle, true);
});
