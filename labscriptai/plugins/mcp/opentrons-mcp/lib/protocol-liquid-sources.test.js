import test from "node:test";
import assert from "node:assert/strict";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

import {
  parseProtocolDeckHints,
  parseProtocolLiquidSourceMap,
  parseProtocolTransferContinuationHints,
  seedProtocolLiquidSourceMap,
} from "./protocol-liquid-sources.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const protocol03 = fs.readFileSync(
  path.resolve(__dirname, "../../../../../local/protocol/03_primary_reserve_buffer.py"),
  "utf8",
);

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
