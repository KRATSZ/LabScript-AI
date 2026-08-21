import assert from "node:assert/strict";
import test from "node:test";

import {
  checkDeclaredLabwareOffsetCoverage,
  DEFAULT_LABWARE_OFFSET_MAX_AGE_DAYS,
  dedupeLabwareOffsets,
  locationSequenceMentionsSlot,
  prepareOffsetsForRunCreate,
} from "./labware-offsets.js";

const NOW = new Date("2026-08-20T12:00:00.000Z");

function offset({ id, uri, createdAt, locationSequence, z = 0 }) {
  return {
    id,
    createdAt,
    definitionUri: uri,
    locationSequence,
    vector: { x: 0, y: 0, z },
  };
}

test("DEFAULT_LABWARE_OFFSET_MAX_AGE_DAYS is an explicit 30-day threshold", () => {
  assert.equal(DEFAULT_LABWARE_OFFSET_MAX_AGE_DAYS, 30);
});

test("dedupeLabwareOffsets keeps newest createdAt per definitionUri::locationSequence", () => {
  const kept = dedupeLabwareOffsets([
    offset({
      id: "old",
      uri: "opentrons/nest_96_wellplate_200ul_flat/1",
      createdAt: "2026-01-01T00:00:00.000Z",
      locationSequence: "anyLocation",
      z: 0,
    }),
    offset({
      id: "new",
      uri: "opentrons/nest_96_wellplate_200ul_flat/1",
      createdAt: "2026-08-01T00:00:00.000Z",
      locationSequence: "anyLocation",
      z: 0.2,
    }),
  ]);
  assert.equal(kept.length, 1);
  assert.equal(kept[0].id, "new");
});

test("prepareOffsetsForRunCreate drops anyLocation (silently discarded at run create)", () => {
  const prepared = prepareOffsetsForRunCreate([
    offset({
      id: "any",
      uri: "opentrons/nest_96_wellplate_200ul_flat/1",
      createdAt: "2026-08-01T00:00:00.000Z",
      locationSequence: "anyLocation",
    }),
    offset({
      id: "slot",
      uri: "opentrons/nest_96_wellplate_200ul_flat/1",
      createdAt: "2026-08-01T00:00:00.000Z",
      locationSequence: [{ kind: "onAddressableArea", addressableAreaName: "D2" }],
    }),
  ]);
  assert.equal(prepared.length, 1);
  assert.equal(prepared[0].locationSequence[0].addressableAreaName, "D2");
});

test("locationSequenceMentionsSlot matches exact addressableAreaName only", () => {
  assert.equal(
    locationSequenceMentionsSlot(
      [{ kind: "onAddressableArea", addressableAreaName: "D2" }],
      "D2",
    ),
    true,
  );
  assert.equal(
    locationSequenceMentionsSlot(
      [
        { kind: "onModule", moduleModel: "temperatureModuleV2" },
        { kind: "onAddressableArea", addressableAreaName: "temperatureModuleV2C1" },
      ],
      "C1",
    ),
    false,
  );
});

test("offset coverage fails when declared labware has no stored offset", () => {
  const result = checkDeclaredLabwareOffsetCoverage({
    declaredLoads: [{ kind: "labware", load_name: "nest_96_wellplate_200ul_flat", slot: "C2" }],
    storedOffsets: [],
    now: NOW,
  });
  assert.equal(result.errors[0].code, "offset_missing");
  assert.equal(result.max_age_days, 30);
});

test("offset coverage fails when only anyLocation rows exist (not applied at run create)", () => {
  const result = checkDeclaredLabwareOffsetCoverage({
    declaredLoads: [{ kind: "labware", load_name: "agilent_1_reservoir_290ml", slot: "C2" }],
    storedOffsets: [
      offset({
        id: "any",
        uri: "opentrons/agilent_1_reservoir_290ml/4",
        createdAt: "2026-08-01T00:00:00.000Z",
        locationSequence: "anyLocation",
      }),
    ],
    now: NOW,
  });
  assert.equal(result.errors[0].code, "offset_not_applied");
});

test("offset coverage fails when selected offsets are for a different slot", () => {
  const result = checkDeclaredLabwareOffsetCoverage({
    declaredLoads: [{ kind: "labware", load_name: "nest_96_wellplate_200ul_flat", slot: "C2" }],
    storedOffsets: [
      offset({
        id: "d2",
        uri: "opentrons/nest_96_wellplate_200ul_flat/1",
        createdAt: "2026-08-17T00:00:00.000Z",
        locationSequence: [{ kind: "onAddressableArea", addressableAreaName: "D2" }],
      }),
    ],
    now: NOW,
  });
  assert.equal(result.errors.some(e => e.code === "offset_slot_uncovered"), true);
});

test("offset coverage fails when selected offset is older than maxAgeDays", () => {
  const result = checkDeclaredLabwareOffsetCoverage({
    declaredLoads: [{ kind: "labware", load_name: "nest_96_wellplate_100ul_pcr_full_skirt", slot: "C2" }],
    storedOffsets: [
      offset({
        id: "tc",
        uri: "opentrons/nest_96_wellplate_100ul_pcr_full_skirt/3",
        createdAt: "2026-06-09T07:48:14.734Z",
        locationSequence: [{ kind: "onAddressableArea", addressableAreaName: "C2" }],
        z: 0.002,
      }),
    ],
    maxAgeDays: 30,
    now: NOW,
  });
  assert.equal(result.errors.some(e => e.code === "offset_stale"), true);
  const stale = result.errors.find(e => e.code === "offset_stale");
  assert.equal(stale.max_age_days, 30);
  assert.ok(stale.age_days > 30);
});

test("offset coverage passes a fresh slot-matched offset", () => {
  const result = checkDeclaredLabwareOffsetCoverage({
    declaredLoads: [{ kind: "labware", load_name: "opentrons_flex_96_tiprack_1000ul", slot: "B2" }],
    storedOffsets: [
      offset({
        id: "b2",
        uri: "opentrons/opentrons_flex_96_tiprack_1000ul/1",
        createdAt: "2026-08-17T08:33:58.669Z",
        locationSequence: [{ kind: "onAddressableArea", addressableAreaName: "B2" }],
        z: 0.4,
      }),
    ],
    now: NOW,
  });
  assert.deepEqual(result.errors, []);
});

test("offset coverage skips trash_bin loads", () => {
  const result = checkDeclaredLabwareOffsetCoverage({
    declaredLoads: [{ kind: "trash_bin", load_name: null, slot: "A3" }],
    storedOffsets: [],
    now: NOW,
  });
  assert.deepEqual(result.errors, []);
});
