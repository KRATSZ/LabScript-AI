import test from "node:test";
import assert from "node:assert/strict";
import fs from "fs";
import os from "os";
import path from "path";

import {
  estimateTipBudget,
  inspectLabwareDefinition,
  validateLabwareLoadName,
} from "../lib/authoring-tools.js";

function writeDefinition(definitionsDir, folderName, version, definition) {
  const folder = path.join(definitionsDir, folderName);
  fs.mkdirSync(folder, { recursive: true });
  fs.writeFileSync(path.join(folder, `${version}.json`), JSON.stringify(definition, null, 2));
}

function withDefinitionsDir(fn) {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "opentrons-labware-defs-"));
  const definitionsDir = path.join(
    tempDir,
    "opentrons_shared_data",
    "data",
    "labware",
    "definitions",
    "2",
  );
  fs.mkdirSync(definitionsDir, { recursive: true });

  const original = process.env.OPENTRONS_LABWARE_DEFINITIONS_DIR;
  process.env.OPENTRONS_LABWARE_DEFINITIONS_DIR = definitionsDir;

  try {
    writeDefinition(definitionsDir, "nest_12_reservoir_15ml", 1, {
      namespace: "opentrons",
      version: 1,
      parameters: {
        loadName: "nest_12_reservoir_15ml",
        isTiprack: false,
      },
      metadata: {
        displayName: "NEST 12-Well Reservoir 15 mL",
        displayCategory: "reservoir",
      },
      wells: Object.fromEntries(
        Array.from({ length: 12 }, (_, index) => {
          const wellName = `A${index + 1}`;
          return [
            wellName,
            {
              depth: 18.5,
              diameter: 15.2,
              totalLiquidVolume: 15000,
            },
          ];
        }),
      ),
    });

    writeDefinition(definitionsDir, "opentrons_flex_96_tiprack_1000ul", 1, {
      namespace: "opentrons",
      version: 1,
      parameters: {
        loadName: "opentrons_flex_96_tiprack_1000ul",
        isTiprack: true,
      },
      metadata: {
        displayName: "Opentrons Flex 96 Tip Rack 1000 uL",
        displayCategory: "tiprack",
      },
      wells: {
        A1: {
          depth: 50,
          diameter: 5,
          totalLiquidVolume: 1000,
        },
      },
    });

    writeDefinition(definitionsDir, "corning_96_wellplate_360ul_flat", 1, {
      namespace: "corning",
      version: 1,
      parameters: {
        loadName: "corning_96_wellplate_360ul_flat",
        isTiprack: false,
      },
      metadata: {
        displayName: "Corning 96 Well Plate 360 uL Flat",
        displayCategory: "wellPlate",
      },
      wells: {
        A1: {
          depth: 11,
          xDimension: 6.4,
          yDimension: 6.4,
          totalLiquidVolume: 360,
        },
      },
    });

    return fn({ tempDir, definitionsDir });
  } finally {
    if (original === undefined) {
      delete process.env.OPENTRONS_LABWARE_DEFINITIONS_DIR;
    } else {
      process.env.OPENTRONS_LABWARE_DEFINITIONS_DIR = original;
    }
  }
}

test("validate_labware_name finds exact matches in the local definition index", () =>
  withDefinitionsDir(() => {
    const result = validateLabwareLoadName("nest_12_reservoir_15ml");
    assert.equal(result.ok, true);
    assert.equal(result.known, true);
    assert.equal(result.exact_matches[0].loadName, "nest_12_reservoir_15ml");
    assert.equal(result.suggestions[0].displayName, "NEST 12-Well Reservoir 15 mL");
  }));

test("inspect_labware_definition returns geometry and dead-volume guidance", () =>
  withDefinitionsDir(() => {
    const result = inspectLabwareDefinition("nest_12_reservoir_15ml");
    assert.equal(result.ok, true);
    assert.equal(result.known, true);
    assert.equal(result.definition.wellCount, 12);
    assert.equal(result.geometry.well_count, 12);
    assert.equal(result.geometry.representative_well.total_liquid_volume_ul, 15000);
    assert.equal(result.geometry.representative_well.shape, "circular");
    assert.equal(result.geometry.dead_volume_hint.estimated_ul, 1900);
    assert.match(result.geometry.dead_volume_hint.reason, /reservoir/i);
  }));

test("inspect_labware_definition returns zero dead-volume guidance for tip racks", () =>
  withDefinitionsDir(() => {
    const result = inspectLabwareDefinition("opentrons_flex_96_tiprack_1000ul");
    assert.equal(result.known, true);
    assert.equal(result.definition.isTiprack, true);
    assert.equal(result.geometry.dead_volume_hint.estimated_ul, 0);
  }));

test("estimate_tip_budget counts multi-destination transfers and flags low-volume pipettes", () =>
  withDefinitionsDir(() => {
    const protocolSource = `
from opentrons import protocol_api

metadata = {"apiLevel": "2.24"}

def run(protocol: protocol_api.ProtocolContext):
    pipette = protocol.load_instrument("flex_1channel_1000", "left")
    protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "C2")
    source = protocol.load_labware("nest_12_reservoir_15ml", "B3")
    dest = protocol.load_labware("corning_96_wellplate_360ul_flat", "C3")
    pipette.transfer(50, source["A1"], [dest["A1"], dest["A2"], dest["A3"]], new_tip="always")
`;

    const result = estimateTipBudget({ protocol_source: protocolSource });
    assert.equal(result.ok, true);
    assert.equal(result.tip_rack_count, 1);
    assert.equal(result.estimated_tip_uses, 3);
    assert.equal(result.within_budget, true);
    assert.equal(result.precision_warnings.length, 1);
    assert.equal(result.precision_warnings[0].pipette_name, "flex_1channel_1000");
  }));

test("estimate_tip_budget only flags the pipette that makes the low-volume call", () =>
  withDefinitionsDir(() => {
    const protocolSource = `
from opentrons import protocol_api

metadata = {"apiLevel": "2.24"}

def run(protocol: protocol_api.ProtocolContext):
    p50 = protocol.load_instrument("flex_1channel_50", "left")
    p1000 = protocol.load_instrument("flex_1channel_1000", "right")
    source = protocol.load_labware("nest_12_reservoir_15ml", "B3")
    dest = protocol.load_labware("corning_96_wellplate_360ul_flat", "C3")
    p50.transfer(4, source["A1"], dest["A1"])
`;

    const result = estimateTipBudget({ protocol_source: protocolSource });
    assert.equal(result.ok, true);
    assert.equal(result.precision_warnings.length, 1);
    assert.equal(result.precision_warnings[0].pipette_name, "flex_1channel_50");
    assert.equal(result.precision_warnings[0].variable_name, "p50");
  }));

test("estimate_tip_budget respects new_tip once and never", () =>
  withDefinitionsDir(() => {
    const protocolSource = `
from opentrons import protocol_api

metadata = {"apiLevel": "2.24"}

def run(protocol: protocol_api.ProtocolContext):
    pipette = protocol.load_instrument("flex_1channel_1000", "left")
    protocol.load_labware("opentrons_flex_96_tiprack_1000ul", "C2")
    source = protocol.load_labware("nest_12_reservoir_15ml", "B3")
    dest = protocol.load_labware("corning_96_wellplate_360ul_flat", "C3")
    pipette.transfer(50, source["A1"], [dest["A1"], dest["A2"], dest["A3"]], new_tip="once")
    pipette.transfer(50, source["A1"], dest["A4"], new_tip="never")
`;

    const result = estimateTipBudget({ protocol_source: protocolSource });
    assert.equal(result.estimated_tip_uses, 1);
  }));
