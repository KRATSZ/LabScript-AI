import test from "node:test";
import assert from "node:assert/strict";
import fs from "fs";
import os from "os";
import path from "path";

import { inferLabwareFromProtocolPath, probeResultToSourceUpdate } from "./liquid-probe-results.js";

const BENCH_PROTOCOL = `"""Deck
  B2  opentrons_flex_96_tiprack_1000ul
  C2  nest_12_reservoir_15ml
  D2  nest_96_wellplate_200ul_flat
"""
from opentrons import protocol_api

def run(protocol):
    tip_rack = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "B2")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "C2")
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "D2")
`;

test("inferLabwareFromProtocolPath uses slot when tiprack is loaded first", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "probe-infer-"));
  const protocolPath = path.join(dir, "bench.py");
  fs.writeFileSync(protocolPath, BENCH_PROTOCOL, "utf8");
  assert.equal(inferLabwareFromProtocolPath(protocolPath, { slotName: "D2" }), "nest_96_wellplate_200ul_flat");
  assert.equal(inferLabwareFromProtocolPath(protocolPath, { slotName: "C2" }), "nest_12_reservoir_15ml");
  // Without slot, first load_labware wins (tiprack) — callers should pass slot for destination writeback.
  assert.equal(inferLabwareFromProtocolPath(protocolPath), "opentrons_flex_96_tiprack_1000ul");
});

test("probeResultToSourceUpdate records measure_height for destination writeback", () => {
  const update = probeResultToSourceUpdate(
    { well: "A1", mode: "measure_height", success: true, value: 5.4 },
    {
      slotName: "D2",
      labwareLoadName: "nest_96_wellplate_200ul_flat",
      runId: "run-1",
    },
  );
  assert.equal(update.slot_name, "D2");
  assert.equal(update.well_name, "A1");
  assert.equal(update.labware_load_name, "nest_96_wellplate_200ul_flat");
  assert.equal(update.observed_height_mm, 5.4);
  assert.equal(update.observed_presence, true);
});
