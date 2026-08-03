import assert from "node:assert/strict";
import test from "node:test";

import {
  buildWellRoleMap,
  deriveInstrumentContactClasses,
  resolveWellRole,
} from "./live-state.js";

test("resolveWellRole prefers session contract role over labware inference", () => {
  const role = resolveWellRole({
    sourceKey: "D2.A1",
    sessionState: {
      liquid_tracking: {
        sources: {
          "D2.A1": {
            role: "sample",
            labware_load_name: "nest_12_reservoir_15ml",
          },
        },
      },
    },
  });
  assert.equal(role, "sample");
});

test("resolveWellRole infers reservoir as common_stock and plate as sample", () => {
  const protocolSource = `
  C2  nest_12_reservoir_15ml
  D2  nest_96_wellplate_200ul_flat
`;
  assert.equal(
    resolveWellRole({
      slotName: "C2",
      wellName: "A1",
      protocolSource,
      labwareLoadName: "nest_12_reservoir_15ml",
    }),
    "common_stock",
  );
  assert.equal(
    resolveWellRole({
      slotName: "D2",
      wellName: "A1",
      protocolSource,
      labwareLoadName: "nest_96_wellplate_200ul_flat",
    }),
    "sample",
  );
});

test("contact_class becomes sample after probe on sample well and resets on new tip", () => {
  const instruments = [{ mount: "left", instrument_name: "p1000_single_flex", tip_detected: true }];
  const wellRoles = {
    "D2.A1": "sample",
    "C2.A1": "common_stock",
    "D2.*": "sample",
    "C2.*": "common_stock",
  };
  const run = {
    labware: [
      { id: "plate-1", loadName: "nest_96_wellplate_200ul_flat", location: { slotName: "D2" } },
      { id: "res-1", loadName: "nest_12_reservoir_15ml", location: { slotName: "C2" } },
    ],
  };

  const afterSampleProbe = deriveInstrumentContactClasses({
    instruments,
    wellRoles,
    run,
    commands: [
      { id: "pick-1", commandType: "pickUpTip", status: "succeeded" },
      {
        id: "probe-1",
        commandType: "liquidProbe",
        status: "succeeded",
        params: { labwareId: "plate-1", wellName: "A1" },
      },
    ],
  });
  assert.equal(afterSampleProbe[0].contact_class, "sample");

  const afterNewTip = deriveInstrumentContactClasses({
    instruments,
    wellRoles,
    run,
    commands: [
      { id: "pick-1", commandType: "pickUpTip", status: "succeeded" },
      {
        id: "probe-1",
        commandType: "liquidProbe",
        status: "succeeded",
        params: { labwareId: "plate-1", wellName: "A1" },
      },
      { id: "drop-1", commandType: "dropTip", status: "succeeded" },
      { id: "pick-2", commandType: "pickUpTip", status: "succeeded" },
    ],
  });
  assert.equal(afterNewTip[0].contact_class, "clean");
});

test("buildWellRoleMap exposes session and protocol-inferred roles", () => {
  const roles = buildWellRoleMap({
    sessionState: {
      liquid_tracking: {
        sources: {
          "C2.A1": {
            slot_name: "C2",
            well_name: "A1",
            role: "source",
            labware_load_name: "nest_12_reservoir_15ml",
          },
        },
        containers: {
          "D2.A1": {
            slot_name: "D2",
            well_name: "A1",
            role: "sample",
            labware_load_name: "nest_96_wellplate_200ul_flat",
          },
        },
      },
    },
    protocolSource: `
  C2  nest_12_reservoir_15ml
  D2  nest_96_wellplate_200ul_flat
`,
  });
  assert.equal(roles["C2.A1"], "common_stock");
  assert.equal(roles["D2.A1"], "sample");
});
